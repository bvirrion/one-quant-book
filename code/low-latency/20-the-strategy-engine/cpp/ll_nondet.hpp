// Chapter 20: a small quoting engine with three classic sources of nondeterminism that can be switched on one at a
// time -- a wall-clock read, iteration over a hash set seeded per process, and two threads feeding one queue -- to
// count the distinct outcomes of reruns on the same recorded input.
#pragma once
#include <atomic>
#include <cstdint>
#include <ctime>
#include <random>
#include <thread>
#include <unordered_set>
#include <vector>

#include "../../../firm/bookbuilder/cpp/firm_bookbuilder.hpp"
#include "../../../firm/mpmcq/cpp/firm_mpmcq.hpp"

namespace ll::nondet {

using firm::feed2::Event;

struct Defects {
    bool wall_clock = false;     // stamp and time decisions with CLOCK_MONOTONIC instead of the event's time
    bool hash_order = false;     // keep the quotes in a hash set seeded per process (as Rust's HashMap is) and iterate it
    bool two_threads = false;    // deliver the events through a queue fed by two producer threads
};

// A hash with a seed drawn once per process from the system's random source: iteration order changes from run to run.
struct SeededHash {
    static std::uint64_t seed() {
        static const std::uint64_t s = (static_cast<std::uint64_t>(std::random_device{}()) << 32) ^ std::random_device{}();
        return s;
    }
    std::size_t operator()(const void* p) const {
        std::uint64_t z = reinterpret_cast<std::uintptr_t>(p) ^ seed();
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return static_cast<std::size_t>(z ^ (z >> 31));
    }
};

class Engine {
public:
    static constexpr int kLevels = 5;   // quotes on five levels a side

    explicit Engine(Defects d, std::uint32_t tick) : d_(d), tick_(tick), book_(tick) {
        for (int k = 0; k < kLevels; ++k) {
            quotes_.push_back(new Quote{'B', k, 0, 0});
            quotes_.push_back(new Quote{'S', k, 0, 0});
        }
        if (d_.hash_order) set_.insert(quotes_.begin(), quotes_.end());
    }
    ~Engine() {
        for (auto* q : quotes_) delete q;
    }
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    std::uint64_t hash = 0xCBF29CE484222325ULL;
    std::size_t actions = 0;

    void run(const std::vector<Event>& ev) {
        if (!d_.two_threads) {
            for (const auto& e : ev) on_event(e);
            return;
        }
        firm::mpmcq::Queue<Event> q(1 << 16);
        std::atomic<int> done{0};
        auto produce = [&](std::size_t parity) {
            for (std::size_t i = parity; i < ev.size(); i += 2)
                while (!q.try_push(ev[i])) {}
            done.fetch_add(1);
        };
        std::thread p0(produce, 0), p1(produce, 1);
        for (;;) {
            if (auto e = q.try_pop()) on_event(*e);
            else if (done.load() == 2 && !q.try_pop().has_value()) break;
        }
        p0.join();
        p1.join();
    }

private:
    struct Quote {
        char side;
        int level;
        std::uint32_t price;
        std::uint64_t id;
    };

    std::uint64_t now(const Event& e) const {
        if (!d_.wall_clock) return e.ts;
        timespec ts{};
        clock_gettime(CLOCK_MONOTONIC, &ts);
        return static_cast<std::uint64_t>(ts.tv_sec) * 1'000'000'000ULL + static_cast<std::uint64_t>(ts.tv_nsec);
    }

    void emit(std::uint64_t t, const Quote& q) {
        const std::uint64_t f[4] = {t, static_cast<std::uint64_t>(q.side), q.price, q.id};
        for (const std::uint64_t x : f)
            for (int k = 0; k < 8; ++k) hash = (hash ^ ((x >> (8 * k)) & 0xFF)) * 0x100000001B3ULL;
        ++actions;
    }

    void on_event(const Event& e) {
        book_.apply(e);
        std::uint32_t bp, ap;
        std::uint64_t bq, aq;
        if (book_.stale || !book_.best('B', bp, bq) || !book_.best('S', ap, aq)) return;
        const std::int64_t micro = (static_cast<std::int64_t>(bp) * static_cast<std::int64_t>(aq) +
                                    static_cast<std::int64_t>(ap) * static_cast<std::int64_t>(bq)) /
                                   static_cast<std::int64_t>(aq + bq);
        const std::int64_t t = tick_;
        const auto want_bid = static_cast<std::uint32_t>(std::min<std::int64_t>((micro - 2 * t) / t * t, ap - t));
        const auto want_ask = static_cast<std::uint32_t>(std::max<std::int64_t>((micro + 3 * t - 1) / t * t, bp + t));
        const std::uint64_t ts = now(e);
        auto requote = [&](Quote* q) {
            const std::uint32_t want = q->side == 'B' ? want_bid - static_cast<std::uint32_t>(q->level * t)
                                                      : want_ask + static_cast<std::uint32_t>(q->level * t);
            if (q->price != want) {
                q->price = want;
                q->id = ++next_id_;   // ids follow the order in which the quotes are visited
                emit(ts, *q);
            }
        };
        if (d_.hash_order)
            for (Quote* q : set_) requote(q);   // the set's order: set by the seed drawn at start-up
        else
            for (Quote* q : quotes_) requote(q);   // a fixed order
    }

    Defects d_;
    std::int64_t tick_;
    firm::book::LadderBook book_;
    std::vector<Quote*> quotes_;
    std::unordered_set<Quote*, SeededHash> set_;
    std::uint64_t next_id_ = 0;
};

}  // namespace ll::nondet
