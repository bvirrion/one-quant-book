// firm.stratengine -- the strategy engine in C++20 (build of One Quant Book 13, chapter 20).
// One thread runs everything to completion, event by event: market events from the feed handler (through the book
// builder), timers from a hashed timing wheel, and parameter snapshots applied between events. Time comes from an
// injected clock: the simulated clock replays a recorded day to the last bit; the real clock runs live. The example
// strategy quotes around the microprice of One Quant Book 7 in integer arithmetic, so that the C++ and Rust engines
// agree bit for bit. In the steady state nothing is allocated.
#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <vector>

#include "../../bookbuilder/cpp/firm_bookbuilder.hpp"

namespace firm::strat {

using firm::feed2::Event;

// Versioned parameters: a new snapshot takes effect between two events, never in the middle of one.
struct Params {
    std::uint32_t version = 1;
    std::int64_t half_spread_ticks = 2;    // quote this many ticks either side of the microprice
    std::uint32_t size = 100;              // lots per quote
    std::int64_t skew_ticks_per_size = 1;  // shift both quotes against the position, per `size` of position
    std::uint64_t stale_ns = 20'000'000;   // pull the quotes if no market event for this long
    std::uint64_t ack_ns = 50'000;         // the venue stub's acknowledgement latency
};

struct Snapshot {
    std::uint64_t t;   // effective from this time
    Params p;
};

// What the engine did: 'N' new quote, 'R' replace (cancel-replace), 'A' acknowledged, 'F' filled, 'P' pulled.
struct Action {
    std::uint64_t t;
    char kind, side;
    std::uint32_t price, qty, version;
    std::uint64_t id;
};

// The simulated clock is the time of the event being processed; the real clock reads CLOCK_MONOTONIC and maps it onto
// the recorded day from the first event (so that a live run and a replay read the same kind of numbers).
struct SimClock {
    std::uint64_t now(std::uint64_t event_t) const { return event_t; }
};
struct RealClock {
    std::uint64_t t0_event = 0, t0_real = 0;
    std::uint64_t now(std::uint64_t event_t) {
        timespec ts{};
        clock_gettime(CLOCK_MONOTONIC, &ts);
        const std::uint64_t r = static_cast<std::uint64_t>(ts.tv_sec) * 1'000'000'000ULL + static_cast<std::uint64_t>(ts.tv_nsec);
        if (t0_real == 0) { t0_real = r; t0_event = event_t; }
        return t0_event + (r - t0_real);
    }
};

// A hashed timing wheel: a timer goes to slot (t / granularity) mod slots; advancing to time T visits the slots of the
// ticks passed and fires, in (time, id) order, the timers due by T. A timer more than one revolution away simply stays
// in its slot until its tick comes round again.
class TimerWheel {
public:
    struct Timer {
        std::uint64_t t, id;
    };
    TimerWheel(std::uint64_t granularity_ns, std::size_t slots_pow2, std::size_t per_slot = 64)
        : gran_(granularity_ns), mask_(slots_pow2 - 1), slots_(slots_pow2) {
        for (auto& s : slots_) s.reserve(per_slot);
        due_.reserve(per_slot * 4);
    }
    void schedule(std::uint64_t t, std::uint64_t id) {
        if (!started_) { tick_ = t / gran_; started_ = true; }
        slots_[(t / gran_) & mask_].push_back({t, id});
        ++pending_;
    }
    std::size_t pending() const { return pending_; }

    // Fire every timer due at or before `to`, in (time, id) order; `fire` may schedule new timers.
    template <class F>
    void advance(std::uint64_t to, F&& fire) {
        if (!started_) { tick_ = to / gran_; started_ = true; return; }
        const std::uint64_t last = to / gran_;
        for (; tick_ <= last; ++tick_) {
            if (pending_ == 0) { tick_ = last; break; }
            auto& s = slots_[tick_ & mask_];
            for (;;) {   // timers scheduled while firing may land in this slot again
                due_.clear();
                const std::uint64_t limit = std::min(to, (tick_ + 1) * gran_ - 1);
                for (std::size_t i = 0; i < s.size();)
                    if (s[i].t <= limit) { due_.push_back(s[i]); s[i] = s.back(); s.pop_back(); }
                    else ++i;
                if (due_.empty()) break;
                std::sort(due_.begin(), due_.end(), [](const Timer& a, const Timer& b) { return a.t != b.t ? a.t < b.t : a.id < b.id; });
                pending_ -= due_.size();
                for (const auto& d : due_) fire(d);
            }
            if (tick_ == last) break;
        }
    }

private:
    std::uint64_t gran_, mask_, tick_ = 0;
    bool started_ = false;
    std::size_t pending_ = 0;
    std::vector<std::vector<Timer>> slots_;
    std::vector<Timer> due_;
};

template <class Clock = SimClock>
class Engine {
public:
    enum TimerKind : std::uint64_t { kAckBid = 1, kAckAsk = 2, kStaleCheck = 3 };

    Engine(std::uint32_t tick, Params p, Clock clock = {}, std::size_t max_actions = 1 << 20)
        : tick_(tick), p_(p), clock_(clock), book_(tick), wheel_(100'000, 1024) {
        actions.reserve(max_actions);
    }

    std::vector<Action> actions;
    std::int64_t position = 0, cash = 0;   // lots; price units x lots
    std::uint64_t hash = 0xCBF29CE484222325ULL;
    // Optional instrumentation: when set, called right after the book is updated; its value is kept in book_stamp.
    std::uint64_t (*stamp)() = nullptr;
    std::uint64_t book_stamp = 0;

    void run(const std::vector<Event>& market, const std::vector<Snapshot>& changes = {}) {
        std::size_t c = 0;
        for (const auto& e : market) {
            // run to completion: everything due before this event happens first, in a fixed order
            wheel_.advance(e.ts, [&](const TimerWheel::Timer& t) { on_timer(t); });
            while (c < changes.size() && changes[c].t <= e.ts) p_ = changes[c++].p;
            on_market(e);
        }
    }

    // Mark to the last microprice (price units x lots).
    std::int64_t pnl() const { return cash + position * static_cast<std::int64_t>(last_micro_); }
    const firm::book::LadderBook& book() const { return book_; }

private:
    struct Quote {
        std::uint32_t price = 0, qty = 0;
        bool live = false, sent = false;
        std::uint64_t id = 0;
    };

    void emit(std::uint64_t t, char kind, char side, std::uint32_t price, std::uint32_t qty, std::uint64_t id) {
        actions.push_back(Action{t, kind, side, price, qty, p_.version, id});
        // the hash covers the fields, packed little-endian (never the struct's padding bytes)
        std::uint8_t b[30];
        std::memcpy(b, &t, 8);
        b[8] = static_cast<std::uint8_t>(kind);
        b[9] = static_cast<std::uint8_t>(side);
        std::memcpy(b + 10, &price, 4);
        std::memcpy(b + 14, &qty, 4);
        std::memcpy(b + 18, &p_.version, 4);
        std::memcpy(b + 22, &id, 8);
        for (const auto c : b) hash = (hash ^ c) * 0x100000001B3ULL;
    }

    void on_timer(const TimerWheel::Timer& t) {
        if (t.id % 4 == kAckBid || t.id % 4 == kAckAsk) {   // the venue stub acknowledges a quote
            Quote& q = t.id % 4 == kAckBid ? bid_ : ask_;
            if (q.sent && q.id == t.id / 4) {
                q.live = true;
                emit(t.t, 'A', t.id % 4 == kAckBid ? 'B' : 'S', q.price, q.qty, q.id);
            }
        } else if (t.id % 4 == kStaleCheck) {               // no market data for stale_ns: pull the quotes
            if (clock_.now(t.t) >= last_market_ + p_.stale_ns) pull(t.t);
            const std::uint64_t next = last_market_ + p_.stale_ns > t.t ? last_market_ + p_.stale_ns : t.t + p_.stale_ns;
            wheel_.schedule(next, kStaleCheck);             // always one check pending
        }
    }

    void pull(std::uint64_t now) {
        for (Quote* q : {&bid_, &ask_})
            if (q->sent) {
                emit(now, 'P', q == &bid_ ? 'B' : 'S', q->price, q->qty, q->id);
                *q = Quote{};
            }
    }

    void quote(std::uint64_t now, Quote& q, char side, std::uint32_t price) {
        if (q.sent && q.price == price) return;
        const char kind = q.sent ? 'R' : 'N';
        q = Quote{price, p_.size, false, true, ++next_id_};
        emit(now, kind, side, price, q.qty, q.id);
        wheel_.schedule(now + p_.ack_ns, q.id * 4 + (side == 'B' ? kAckBid : kAckAsk));
    }

    void on_market(const Event& e) {
        const std::uint64_t now = clock_.now(e.ts);
        book_.apply(e);
        if (stamp) book_stamp = stamp();                    // instrumentation point (chapter 26)
        last_market_ = e.ts;
        if (!stale_armed_) {
            stale_armed_ = true;
            wheel_.schedule(e.ts + p_.stale_ns, kStaleCheck);
        }
        std::uint32_t bp, ap;
        std::uint64_t bq, aq;
        if (book_.stale || !book_.best('B', bp, bq) || !book_.best('S', ap, aq)) return;
        // the venue stub fills a live quote that the market has reached
        if (bid_.live && ap <= bid_.price) { fill(now, bid_, 'B'); }
        if (ask_.live && bp >= ask_.price) { fill(now, ask_, 'S'); }
        const std::int64_t micro = (static_cast<std::int64_t>(bp) * static_cast<std::int64_t>(aq) +
                                    static_cast<std::int64_t>(ap) * static_cast<std::int64_t>(bq)) /
                                   static_cast<std::int64_t>(aq + bq);
        last_micro_ = micro;
        const std::int64_t t = tick_;
        const std::int64_t skew = position * p_.skew_ticks_per_size / static_cast<std::int64_t>(p_.size) * t;
        std::int64_t b = (micro - p_.half_spread_ticks * t - skew) / t * t;
        std::int64_t a = (micro + p_.half_spread_ticks * t - skew + t - 1) / t * t;
        b = std::min<std::int64_t>(b, static_cast<std::int64_t>(ap) - t);   // never cross the market
        a = std::max<std::int64_t>(a, static_cast<std::int64_t>(bp) + t);
        quote(now, bid_, 'B', static_cast<std::uint32_t>(b));
        quote(now, ask_, 'S', static_cast<std::uint32_t>(a));
    }

    void fill(std::uint64_t now, Quote& q, char side) {
        const std::int64_t sgn = side == 'B' ? 1 : -1;
        position += sgn * static_cast<std::int64_t>(q.qty);
        cash -= sgn * static_cast<std::int64_t>(q.qty) * static_cast<std::int64_t>(q.price);
        emit(now, 'F', side, q.price, q.qty, q.id);
        q = Quote{};
    }

    std::int64_t tick_;
    Params p_;
    Clock clock_;
    firm::book::LadderBook book_;
    TimerWheel wheel_;
    Quote bid_, ask_;
    std::uint64_t next_id_ = 0, last_market_ = 0;
    std::int64_t last_micro_ = 0;
    bool stale_armed_ = false;
};

}  // namespace firm::strat
