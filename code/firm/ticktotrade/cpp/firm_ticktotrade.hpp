// firm.ticktotrade (C++20): the book's trading path assembled (build of One Quant Book 13, chapter 26).
//
//   Path          the engine thread's work for one market event: the strategy engine (its book and its decision),
//                 then, for every order the decision produces, the risk gate and the order gateway, which writes the
//                 venue's message. Used as it is by the offline replay and by the live harness (ticktotrade.cpp),
//                 so that both produce the same orders; the Rust twin produces them too (data/expected.txt).
//   Stamp         the instrumentation points of one order, as TSC readings: packet received, event published on the
//                 ring, event taken off the ring, book updated, decision, risk checked, message written, message sent
//                 (and, from the other threads, packet sent by the exchange and order received by the venue).
//   OrderOut      one message to the venue: kind O (new), U (replace), X (cancel), identifiers, side, size, price.
//   order_hash    FNV-1a over the packed fields of the orders, in order.
#pragma once
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

#include "../../ordergw/cpp/firm_ordergw.hpp"
#include "../../riskgate/cpp/firm_riskgate.hpp"
#include "../../stratengine/cpp/firm_stratengine.hpp"

namespace firm::t2t {

struct OrderOut {
    std::uint64_t t;
    char kind, side;
    std::uint64_t cl, new_cl;
    std::uint32_t qty, price;
};

inline std::uint64_t order_hash(const std::vector<OrderOut>& v) {
    std::uint64_t h = 0xCBF29CE484222325ULL;
    auto mix = [&](const void* p, std::size_t n) {
        const auto* b = static_cast<const std::uint8_t*>(p);
        for (std::size_t i = 0; i < n; ++i) h = (h ^ b[i]) * 0x100000001B3ULL;
    };
    for (const OrderOut& o : v) {
        mix(&o.t, 8), mix(&o.kind, 1), mix(&o.side, 1), mix(&o.cl, 8), mix(&o.new_cl, 8), mix(&o.qty, 4),
            mix(&o.price, 4);
    }
    return h;
}

enum StampIx : int { Recv, Pub, Pop, Book, Decide, Risk, Encode, Sent, NStamps };
inline constexpr const char* kStampName[NStamps] = {"recv", "pub", "pop", "book", "decide", "risk", "encode", "sent"};

struct Stamp {
    std::uint64_t t[NStamps] = {};
    std::uint64_t pkt_seq = 0;   // the MoldUDP64 sequence number of the packet that carried the event
    char line = 0;               // the line it arrived on first
    char kind = 0;               // O, U or X
    std::uint64_t cl = 0;
};

// The limits the harness runs under: generous, so that the gate's cost is measured on accepted orders.
inline risk::Limits harness_limits() {
    risk::Limits l;
    l.version = 1, l.max_age = 1LL << 62, l.ref_max_age = 1LL << 62, l.dup_ns = 0, l.firm_gross = 1LL << 60;
    l.desk_gross = {1LL << 60};
    l.strat = {risk::StratLimits{0, 1'000'000, 10'000, 1'000'000}};
    l.instr.resize(2);
    l.instr[1] = risk::InstrLimits{10'000, 100'000, 1LL << 50, 1'000'000, 1'000'000};
    return l;
}

class Path {
public:
    explicit Path(std::uint32_t tick)
        : engine_(tick, strat::Params{}), gate_(harness_limits(), 0),
          gw_(ogw::Limits{1'000'000'000, 1'000'000'000, 1'000'000'000, 1'000'000'000}) {
        out.reserve(1 << 16);
    }

    std::vector<OrderOut> out;                       // every message written, in order
    std::uint64_t refused_risk = 0, refused_gateway = 0;

    strat::Engine<>& engine() { return engine_; }

    // One market event through the engine, then its orders through the gate and the gateway. For each message
    // written, send(buf, len, kind, cl) is called (the harness sends it; the offline replay ignores it). Stamps
    // are taken with now() when it is given.
    template <class Send>
    void on_event(const strat::Event& e, std::uint64_t (*now)(), Stamp* st, Send&& send) {
        const std::size_t first = engine_.actions.size();
        engine_.stamp = now;
        one_[0] = e;
        engine_.run(one_);
        if (now && st) st->t[Book] = engine_.book_stamp, st->t[Decide] = now();
        for (std::size_t i = first; i < engine_.actions.size(); ++i)
            act(engine_.actions[i], now, st, send);
    }

private:
    template <class Send>
    void act(const strat::Action& a, std::uint64_t (*now)(), Stamp* st, Send&& send) {
        const auto t = static_cast<std::int64_t>(a.t);
        const int k = a.side == 'B' ? 0 : 1;
        std::size_t n = 0;
        OrderOut o{a.t, 0, static_cast<char>(a.side), a.id, 0, a.qty, a.price};
        if (a.kind == 'N' || a.kind == 'R') {
            if (a.kind == 'R' && quote_[k]) gate_.on_done(quote_[k]);  // the old quote leaves the exposure
            gate_.set_reference(t, 1, a.price);
            const auto d = gate_.check(t, 0, 1, a.side, a.qty, a.price, a.id);
            if (now && st) st->t[Risk] = now();
            if (d.code != '.') {
                ++refused_risk;
                return;
            }
            if (a.kind == 'R' && live_[k]) {  // cancel-replace of the side's live quote
                n = gw_.replace(t, live_[k], a.id, a.qty, a.price, buf_);
                if (n) o.kind = 'U', o.cl = live_[k], o.new_cl = a.id, replacing_[k] = live_[k];
            }
            if (!n) n = gw_.new_order(t, a.id, a.side, a.qty, a.price, buf_), o.kind = 'O';
            quote_[k] = a.id;
        } else if (a.kind == 'P') {
            gate_.on_done(a.id);
            const std::uint64_t cl = live_[k] ? live_[k] : a.id;
            n = gw_.cancel(t, cl, buf_), o.kind = 'X', o.cl = cl;
            live_[k] = quote_[k] = replacing_[k] = 0;
        } else if (a.kind == 'A') {  // the engine's venue acknowledges its quote
            if (replacing_[k]) gw_.on_report('U', replacing_[k], 0, 0, ' ', a.id), replacing_[k] = 0;
            else gw_.on_report('A', a.id, 0, 0, ' ', 0);
            live_[k] = a.id;
            return;
        } else if (a.kind == 'F') {
            gw_.on_report('E', a.id, a.qty, 0, ' ', 0);
            gate_.on_fill(a.id, a.qty, a.price);
            live_[k] = quote_[k] = 0;
            return;
        } else {
            return;
        }
        if (!n) {
            ++refused_gateway;
            return;
        }
        if (now && st) st->t[Encode] = now(), st->kind = o.kind, st->cl = o.new_cl ? o.new_cl : o.cl;
        out.push_back(o);
        send(buf_, n, o.kind, o.new_cl ? o.new_cl : o.cl);
    }

    strat::Engine<> engine_;
    risk::Gate gate_;
    ogw::Gateway gw_;
    std::vector<strat::Event> one_ = std::vector<strat::Event>(1);
    std::uint64_t live_[2] = {0, 0}, quote_[2] = {0, 0}, replacing_[2] = {0, 0};  // per side: bid, ask
    std::uint8_t buf_[64] = {};
};

// The packed 48-byte event records of the book builder's fixtures.
inline std::vector<strat::Event> read_events(const std::vector<std::uint8_t>& b) {
    std::vector<strat::Event> out;
    for (std::size_t i = 0; i + 48 <= b.size(); i += 48) {
        strat::Event e;
        e.kind = b[i];
        e.side = b[i + 1];
        std::memcpy(&e.locate, &b[i + 2], 2);
        std::memcpy(&e.seq, &b[i + 4], 8);
        std::memcpy(&e.ts, &b[i + 12], 8);
        std::memcpy(&e.ref, &b[i + 20], 8);
        std::memcpy(&e.ref2, &b[i + 28], 8);
        std::memcpy(&e.price, &b[i + 36], 4);
        std::memcpy(&e.qty, &b[i + 40], 8);
        out.push_back(e);
    }
    return out;
}

}  // namespace firm::t2t
