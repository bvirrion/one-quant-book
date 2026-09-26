// firm.ordergw (C++20): the order gateway between the strategy engine and the venue's order-entry session.
// A table-driven order state machine with pending states; worst-case exposure kept as running sums, so that the check
// before every new order costs a comparison, not a scan; a token-bucket throttle in integer nano-tokens; cancel-fill
// race counting; messages encoded in place with firm.wirecodec, reports decoded from the wire. Orders are found by
// client order identifier in a ring indexed by that identifier (the gateway assigns them in sequence), so nothing is
// allocated after construction. Same journal, same summary as the Python reference (data/expected.txt).
#pragma once
#include "../../wirecodec/cpp/firm_wirecodec.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

namespace firm::ogw {

enum State : std::uint8_t { PendingNew, Live, Partial, PendingCancel, PendingReplace, Filled, Cancelled, Rejected, NStates };
enum Ev : std::uint8_t { Ack, Reject, Fill, FillAll, CancelReq, CancelAck, TooLate, ReplaceReq, ReplaceAck, NEvents };
inline constexpr std::array<const char*, NStates> kStateName{
    "pending_new", "live", "partial", "pending_cancel", "pending_replace", "filled", "cancelled", "rejected"};
inline constexpr std::uint8_t X = 0xff;  // not allowed

// kTable[state][event] -> next state; the same table as the Python reference's TABLE. CancelAck is any cancellation
// the venue reports, ours or its own (disconnect, halt, mass cancel, expiry), so it reaches every open state.
inline constexpr std::uint8_t kTable[NStates][NEvents] = {
    //            Ack  Reject    Fill  FillAll  CancelReq  CancelAck  TooLate  ReplaceReq  ReplaceAck
    /*PendNew*/ {Live, Rejected, Partial, Filled, PendingCancel, Cancelled, X, X, X},
    /*Live*/    {X, X, Partial, Filled, PendingCancel, Cancelled, X, PendingReplace, X},
    /*Partial*/ {X, X, Partial, Filled, PendingCancel, Cancelled, X, PendingReplace, X},
    /*PendCxl*/ {PendingCancel, X, PendingCancel, Filled, X, Cancelled, Filled, X, X},
    /*PendRpl*/ {X, X, PendingReplace, Filled, X, Cancelled, Filled, X, Live},
    /*Filled*/  {X, X, X, X, X, X, Filled, X, X},
    /*Cxl*/     {X, X, X, X, X, X, Cancelled, X, X},
    /*Rej*/     {X, X, X, X, X, X, X, X, X},
};

class TokenBucket {
public:
    TokenBucket(std::int64_t rate_per_s, std::int64_t burst) : rate_(rate_per_s), cap_(burst * kOne), tokens_(cap_) {}
    bool allow(std::int64_t t) {
        if (started_) tokens_ = std::min(cap_, tokens_ + rate_ * (t - last_));
        started_ = true;
        last_ = t;
        if (tokens_ < kOne) return false;
        tokens_ -= kOne;
        return true;
    }

private:
    static constexpr std::int64_t kOne = 1'000'000'000;
    std::int64_t rate_, cap_, tokens_, last_ = 0;
    bool started_ = false;
};

struct Order {
    std::uint64_t cl = 0;         // 0: the slot is free
    char side = 'B';
    std::uint8_t state = PendingNew;
    std::int64_t qty = 0, price = 0, filled = 0;
    std::int64_t pending_qty = 0, pending_price = 0;
    std::uint64_t new_cl = 0;
    std::int64_t leaves() const { return state >= Filled ? 0 : qty - filled; }
    std::int64_t worst_leaves() const {
        return state == PendingReplace ? std::max(qty - filled, pending_qty) : leaves();
    }
};

enum class Why : std::uint8_t { None, Throttle, Exposure, State };

struct Limits {
    std::int64_t rate_per_s = 1000, burst = 50, max_long = 1'000'000'000, max_short = 1'000'000'000;
};

class Gateway {
public:
    explicit Gateway(Limits l = {}, std::size_t ring = 1 << 16)
        : lim_(l), bucket_(l.rate_per_s, l.burst), orders_(ring), mask_(ring - 1) {}

    // Requests: the message is written at out (at least 38 bytes); returns its length, or 0 with why() set.
    std::size_t new_order(std::int64_t t, std::uint64_t cl, char side, std::int64_t qty,
                          std::int64_t price, std::uint8_t* out) {
        if ((side == 'B' && exp_b_ + position_ + qty > lim_.max_long) ||
            (side == 'S' && exp_s_ - position_ + qty > lim_.max_short))
            return refuse(Why::Exposure);
        Order& o = orders_[cl & mask_];
        if (o.cl && o.state < Filled) return refuse(Why::State);  // slot holds an open order
        if (!throttle(t)) return 0;
        o = Order{cl, side, PendingNew, qty, price, 0, 0, 0, 0};
        add(o, +1);
        ++live_;
        wire::InOWriter(out).cl_ord_id(cl).locate(1).side(side)
            .qty(static_cast<std::uint32_t>(qty)).price(static_cast<std::uint32_t>(price))
            .tif('D').display('Y').post_only('N').stp_mode('N');
        return wire::InO::kLength;
    }
    std::size_t cancel(std::int64_t t, std::uint64_t cl, std::uint8_t* out) {
        Order* o = slot(cl);
        if (!o || !(o->state == PendingNew || o->state == Live || o->state == Partial)) return refuse(Why::State);
        if (!throttle(t)) return 0;
        change(*o, [](Order& x) { x.state = kTable[x.state][CancelReq]; });
        wire::InXWriter(out).cl_ord_id(cl);
        return wire::InX::kLength;
    }
    std::size_t replace(std::int64_t t, std::uint64_t cl, std::uint64_t new_cl, std::int64_t qty, std::int64_t price,
                        std::uint8_t* out) {
        Order* o = slot(cl);
        if (!o || !(o->state == Live || o->state == Partial)) return refuse(Why::State);
        const std::int64_t extra = std::max<std::int64_t>(0, qty - (o->qty - o->filled));
        if ((o->side == 'B' && worst_long() + extra > lim_.max_long) ||
            (o->side == 'S' && worst_short() + extra > lim_.max_short))
            return refuse(Why::Exposure);
        if (!throttle(t)) return 0;
        change(*o, [&](Order& x) {
            x.state = kTable[x.state][ReplaceReq];
            x.pending_qty = qty, x.pending_price = price, x.new_cl = new_cl;
        });
        wire::InUWriter(out).cl_ord_id(cl).new_cl_ord_id(new_cl).qty(static_cast<std::uint32_t>(qty))
            .price(static_cast<std::uint32_t>(price));
        return wire::InU::kLength;
    }

    // Reports, as fields (the journal) or from the wire (the session).
    bool on_report(char kind, std::uint64_t cl, std::int64_t qty, std::int64_t leaves, char reason,
                   std::uint64_t new_cl) {
        Order* o = slot(cl);
        if (!o) return true;                                   // not ours (or long gone): ignore
        std::uint8_t ev;
        switch (kind) {
            case 'A': ev = Ack; break;
            case 'E':
                if (o->state == PendingCancel || o->state == PendingReplace) ++races_;
                ev = leaves == 0 ? FillAll : Fill;
                break;
            case 'C': ev = CancelAck; break;
            case 'U': ev = ReplaceAck; break;
            case 'J': ev = reason == 'L' ? TooLate : Reject; break;
            default: return false;
        }
        const std::uint8_t next = kTable[o->state][ev];
        if (next == X) return false;                           // a report the state machine does not allow
        const bool was_open = o->state < Filled;
        change(*o, [&](Order& x) {
            x.state = next;
            if (kind == 'E') {
                x.filled += qty;
                position_ += x.side == 'B' ? qty : -qty;
            } else if (kind == 'U') {
                x.qty = x.filled + x.pending_qty, x.price = x.pending_price;
            }
        });
        if (was_open && o->state >= Filled) --live_;
        if (kind == 'U') {                                     // the order continues under its new identifier
            const std::uint64_t nc = o->new_cl ? o->new_cl : new_cl;
            Order moved = *o;
            moved.cl = nc;
            o->cl = 0;
            orders_[nc & mask_] = moved;
        }
        return true;
    }
    bool on_wire(const std::uint8_t* p, std::size_t n) {
        bool ok = true;
        const bool known = wire::dispatch_out(p, n, [&](auto m) {
            using M = decltype(m);
            if constexpr (std::is_same_v<M, wire::OutA>) ok = on_report('A', m.cl_ord_id(), 0, 0, ' ', 0);
            else if constexpr (std::is_same_v<M, wire::OutE>)
                ok = on_report('E', m.cl_ord_id(), m.qty(), m.leaves(), ' ', 0);
            else if constexpr (std::is_same_v<M, wire::OutC>) ok = on_report('C', m.cl_ord_id(), 0, 0, m.reason(), 0);
            else if constexpr (std::is_same_v<M, wire::OutU>)
                ok = on_report('U', m.cl_ord_id(), 0, 0, ' ', m.new_cl_ord_id());
            else if constexpr (std::is_same_v<M, wire::OutJ>) ok = on_report('J', m.cl_ord_id(), 0, 0, m.reason(), 0);
        });
        return known && ok;
    }

    std::int64_t position() const { return position_; }
    std::int64_t worst_long() const { return position_ + exp_b_; }
    std::int64_t worst_short() const { return -position_ + exp_s_; }
    std::int64_t races() const { return races_; }
    std::int64_t open_orders() const { return live_; }
    std::int64_t sent() const { return sent_; }
    Why why() const { return why_; }
    const std::array<std::int64_t, 3>& refused() const { return refused_; }
    const Order* find(std::uint64_t cl) const {
        const Order& o = orders_[cl & mask_];
        return o.cl == cl ? &o : nullptr;
    }
    template <class F> void for_each(F&& f) const {
        for (const Order& o : orders_)
            if (o.cl) f(o);
    }
    std::string summary() const {
        std::array<int, NStates> n{};
        int total = 0;
        for_each([&](const Order& o) { ++n[o.state], ++total; });
        std::vector<std::pair<std::string, int>> st;
        for (int s = 0; s < NStates; ++s)
            if (n[s]) st.emplace_back(kStateName[s], n[s]);
        std::sort(st.begin(), st.end());
        std::string out = "orders " + std::to_string(total) + " position " + std::to_string(position_) + " races " +
                          std::to_string(races_) + " sent " + std::to_string(sent_) + " refused " +
                          std::to_string(refused_[0]) + "/" + std::to_string(refused_[1]) + "/" +
                          std::to_string(refused_[2]) + " worst " + std::to_string(worst_long()) + "/" +
                          std::to_string(worst_short()) + " states ";
        for (std::size_t i = 0; i < st.size(); ++i)
            out += (i ? "," : "") + st[i].first + ":" + std::to_string(st[i].second);
        return out;
    }

private:
    Order* slot(std::uint64_t cl) {
        Order& o = orders_[cl & mask_];
        return o.cl == cl ? &o : nullptr;
    }
    // Keep the exposure sums current: take the order's worst remaining quantity out,
    // change the order, put its new worst remaining quantity back.
    void add(const Order& o, int sign) { (o.side == 'B' ? exp_b_ : exp_s_) += sign * o.worst_leaves(); }
    template <class F> void change(Order& o, F&& f) {
        add(o, -1);
        f(o);
        add(o, +1);
    }
    std::size_t refuse(Why w) {
        why_ = w;
        ++refused_[static_cast<int>(w) - 1];
        return 0;
    }
    bool throttle(std::int64_t t) {
        if (!bucket_.allow(t)) return refuse(Why::Throttle), false;
        ++sent_;
        why_ = Why::None;
        return true;
    }

    Limits lim_;
    TokenBucket bucket_;
    std::vector<Order> orders_;
    std::uint64_t mask_;
    std::int64_t position_ = 0, exp_b_ = 0, exp_s_ = 0, races_ = 0, sent_ = 0, live_ = 0;
    std::array<std::int64_t, 3> refused_{};
    Why why_ = Why::None;
};

}  // namespace firm::ogw
