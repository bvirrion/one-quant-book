// firm.riskgate (C++20): the pre-trade risk gate. Limits are precomputed into dense tables indexed by instrument
// (locate) and strategy, so that a check reads a handful of cache lines and computes every condition without a
// branch: each failed check sets one bit of a mask, and the first set bit is the refusal. Same event stream, same
// decisions as the Python reference (data/expected.txt). No allocation after construction.
#pragma once
#include "../../exchsim/cpp/exchsim_json.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace firm::risk {

// Bit i of a mask is kCodes[i]; a refusal is reported as its lowest bit.
inline constexpr char kCodes[] = "KSRCQNLHOGTD";
enum Bit : std::uint32_t { Kill, Stale, Ref, Collar, Qty, Notional, Long, Short, Open, Gross, Throttle, Dup };
inline constexpr std::int64_t kOne = 1'000'000'000;  // a token, in nano-tokens
inline constexpr int kDupSlots = 16;

struct InstrLimits {
    std::int64_t collar_bp = 0, max_qty = 0, max_notional = 0, max_long = 0, max_short = 0;
};
struct StratLimits {
    int desk = 0;
    std::int64_t rate = 0, burst = 0, max_open = 0;
};
struct Limits {
    std::int64_t version = 0, max_age = 0, ref_max_age = 0, dup_ns = 0, firm_gross = 0;
    std::vector<std::int64_t> desk_gross;
    std::vector<StratLimits> strat;
    std::vector<InstrLimits> instr;  // indexed by locate
};

// Names to indices, fixed at start-up (strategies and desks in the order of the first snapshot's keys).
struct Names {
    std::vector<std::string> strat, desk;
    int find(const std::vector<std::string>& v, const std::string& s) const {
        for (std::size_t i = 0; i < v.size(); ++i)
            if (v[i] == s) return static_cast<int>(i);
        return -1;
    }
};

inline Limits parse_limits(const exchsim::json::Value& v, Names& names) {
    Limits l;
    l.version = v["version"].i, l.max_age = v["max_age_ns"].i, l.ref_max_age = v["ref_max_age_ns"].i;
    l.dup_ns = v.get_int("dup_ns", 0), l.firm_gross = v["firm"]["max_gross"].i;
    for (const auto& [name, d] : v["desks"].o) {
        if (names.find(names.desk, name) < 0) names.desk.push_back(name);
        l.desk_gross.resize(names.desk.size());
        l.desk_gross[static_cast<std::size_t>(names.find(names.desk, name))] = d["max_gross"].i;
    }
    for (const auto& [name, s] : v["strategies"].o) {
        if (names.find(names.strat, name) < 0) names.strat.push_back(name);
        l.strat.resize(names.strat.size());
        l.strat[static_cast<std::size_t>(names.find(names.strat, name))] =
            StratLimits{names.find(names.desk, s["desk"].s), s["rate"].i, s["burst"].i, s["max_open"].i};
    }
    for (const auto& [loc, s] : v["instruments"].o) {
        const auto k = static_cast<std::size_t>(std::stoi(loc));
        if (l.instr.size() <= k) l.instr.resize(k + 1);
        l.instr[k] = InstrLimits{s["collar_bp"].i, s["max_qty"].i, s["max_notional"].i, s["max_long"].i,
                                 s["max_short"].i};
    }
    return l;
}

inline std::array<std::int64_t, kDupSlots> filled(std::int64_t v) {
    std::array<std::int64_t, kDupSlots> a;
    a.fill(v);
    return a;
}

struct Decision {
    char code;
    std::uint32_t mask;
};

class Gate {
public:
    explicit Gate(const Limits& l, std::int64_t t, std::size_t instruments = 1 << 12, std::size_t ring = 1 << 16)
        : ref_(instruments), lo_(instruments), hi_(instruments), ref_t_(instruments, -(1LL << 62)),
          pos_(instruments), open_buy_(instruments), open_sell_(instruments), orders_(ring), mask_(ring - 1) {
        set_limits(t, l);
    }

    // A whole snapshot, installed between events; strategies that have not sent yet start with a full bucket.
    void set_limits(std::int64_t t, const Limits& l) {
        lim_ = l, lim_t_ = t;
        strat_.resize(l.strat.size());
        desk_gross_.resize(l.desk_gross.size());
        desk_killed_.resize(l.desk_gross.size());
        for (std::size_t s = 0; s < strat_.size(); ++s)
            if (strat_[s].last < 0) strat_[s].tokens = l.strat[s].burst * kOne;
        for (std::size_t i = 0; i < ref_.size() && i < l.instr.size(); ++i) band(static_cast<std::uint32_t>(i));
    }
    void heartbeat(std::int64_t t) { lim_t_ = t; }
    void set_reference(std::int64_t t, std::uint32_t instr, std::int64_t price) {
        ref_[instr] = price, ref_t_[instr] = t;
        band(instr);
    }

    Decision check(std::int64_t t, int strat, std::uint32_t instr, char side, std::int64_t qty,
                   std::int64_t price, std::uint64_t cl) {
        const auto si = static_cast<std::size_t>(strat);
        const StratLimits& sl = lim_.strat[si];
        const InstrLimits& il = lim_.instr[instr];
        StratState& st = strat_[si];
        const auto desk = static_cast<std::size_t>(sl.desk);
        const bool buy = side == 'B';
        const std::int64_t notional = qty * price;
        const std::int64_t refill = st.tokens + sl.rate * (t - st.last);
        const std::int64_t tokens = st.last < 0 ? st.tokens : std::min(sl.burst * kOne, refill);
        // Duplicates: two packed words per remembered order (quantity and price are 32-bit fields
        // on the wire, so the packing is exact), 16 slots in structure-of-arrays form, no branch.
        const std::uint64_t ka = std::uint64_t(price) << 32 | std::uint32_t(qty);
        const std::uint64_t kb = std::uint64_t(instr) << 8 | static_cast<unsigned char>(side);
        bool dup = false;
        if (lim_.dup_ns != 0)  // a branch on configuration: always taken the same way
            for (int i = 0; i < kDupSlots; ++i)
                dup |= (st.ka[i] == ka) & (st.kb[i] == kb) & (t - st.kt[i] <= lim_.dup_ns);
        const std::int64_t long_ = pos_[instr] + open_buy_[instr] + qty;
        const std::int64_t short_ = -pos_[instr] + open_sell_[instr] + qty;
        std::uint32_t m = 0;
        m |= std::uint32_t(firm_killed_ | desk_killed_[desk] | st.killed) << Kill;
        m |= std::uint32_t(t - lim_t_ > lim_.max_age) << Stale;
        m |= std::uint32_t((ref_[instr] <= 0) | (t - ref_t_[instr] > lim_.ref_max_age)) << Ref;
        m |= std::uint32_t(buy ? price > hi_[instr] : price < lo_[instr]) << Collar;
        m |= std::uint32_t(qty > il.max_qty) << Qty;
        m |= std::uint32_t(notional > il.max_notional) << Notional;
        m |= std::uint32_t(buy & (long_ > il.max_long)) << Long;
        m |= std::uint32_t(!buy & (short_ > il.max_short)) << Short;
        m |= std::uint32_t(st.open >= sl.max_open) << Open;
        m |= std::uint32_t((desk_gross_[desk] + notional > lim_.desk_gross[desk]) |
                           (firm_gross_ + notional > lim_.firm_gross)) << Gross;
        m |= std::uint32_t(tokens < kOne) << Throttle;
        m |= std::uint32_t(dup) << Dup;
        if (m) return {kCodes[__builtin_ctz(m)], m};
        // accepted: spend the token, remember the order, count its exposure
        st.tokens = tokens - kOne, st.last = t, ++st.open;
        st.ka[st.head] = ka, st.kb[st.head] = kb, st.kt[st.head] = t;
        st.head = (st.head + 1) % kDupSlots;
        orders_[cl & mask_] = Order{cl, strat, instr, side, qty, price, 0};
        (buy ? open_buy_ : open_sell_)[instr] += qty;
        desk_gross_[desk] += notional, firm_gross_ += notional;
        return {'.', 0};
    }

    void on_fill(std::uint64_t cl, std::int64_t qty, std::int64_t price) {
        Order* o = find(cl);
        if (!o) return;
        o->filled += qty;
        pos_[o->instr] += o->side == 'B' ? qty : -qty;
        (o->side == 'B' ? open_buy_ : open_sell_)[o->instr] -= qty;
        const std::int64_t d = qty * (price - o->price);  // executed notional at the fill's price
        desk_gross_[static_cast<std::size_t>(lim_.strat[static_cast<std::size_t>(o->strat)].desk)] += d;
        firm_gross_ += d;
        if (o->filled == o->qty) on_done(cl);
    }
    void on_done(std::uint64_t cl) {
        Order* o = find(cl);
        if (!o) return;
        const std::int64_t rest = o->qty - o->filled;
        (o->side == 'B' ? open_buy_ : open_sell_)[o->instr] -= rest;
        desk_gross_[static_cast<std::size_t>(lim_.strat[static_cast<std::size_t>(o->strat)].desk)] -= rest * o->price;
        firm_gross_ -= rest * o->price;
        --strat_[static_cast<std::size_t>(o->strat)].open;
        o->cl = 0;
    }

    // level: 'F' firm, 'D' desk, 'S' strategy; returns the open orders under the node (to cancel) when asked.
    template <class F> void kill(char level, int idx, bool cancel, F&& on_cancel) {
        set_kill(level, idx, true);
        if (!cancel) return;
        for (const Order& o : orders_)
            if (o.cl && (level == 'F' || (level == 'S' && o.strat == idx) ||
                         (level == 'D' && lim_.strat[static_cast<std::size_t>(o.strat)].desk == idx)))
                on_cancel(o.cl);
    }
    void unkill(char level, int idx) { set_kill(level, idx, false); }

    std::int64_t position(std::uint32_t instr) const { return pos_[instr]; }
    std::int64_t firm_gross() const { return firm_gross_; }

private:
    struct StratState {
        std::int64_t tokens = 0, last = -1, open = 0;
        std::array<std::uint64_t, kDupSlots> ka{}, kb{};
        std::array<std::int64_t, kDupSlots> kt = filled(-(1LL << 62));
        int head = 0;
        bool killed = false;
    };
    struct Order {
        std::uint64_t cl = 0;
        int strat = 0;
        std::uint32_t instr = 0;
        char side = 'B';
        std::int64_t qty = 0, price = 0, filled = 0;
    };
    Order* find(std::uint64_t cl) {
        Order& o = orders_[cl & mask_];
        return o.cl == cl && cl ? &o : nullptr;
    }
    // The collar as two prices, recomputed when the reference or the limits change,
    // never during a check.
    void band(std::uint32_t i) {
        const std::int64_t bp = i < lim_.instr.size() ? lim_.instr[i].collar_bp : 0;
        const std::int64_t b = ref_[i] * bp / 10'000;
        lo_[i] = ref_[i] - b, hi_[i] = ref_[i] + b;
    }
    void set_kill(char level, int idx, bool on) {
        if (level == 'F') firm_killed_ = on;
        else if (level == 'D') desk_killed_[static_cast<std::size_t>(idx)] = on;
        else strat_[static_cast<std::size_t>(idx)].killed = on;
    }

    Limits lim_;
    std::int64_t lim_t_ = 0;
    std::vector<std::int64_t> ref_, lo_, hi_, ref_t_, pos_, open_buy_, open_sell_;
    std::vector<std::int64_t> desk_gross_;
    std::vector<char> desk_killed_;
    std::int64_t firm_gross_ = 0;
    bool firm_killed_ = false;
    std::vector<StratState> strat_;
    std::vector<Order> orders_;
    std::uint64_t mask_;
};

}  // namespace firm::risk
