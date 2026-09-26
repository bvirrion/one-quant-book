// firm.stratengine (C++20): the engine replays the simulator's events twice to the same actions, hash and profit
// (the value in data/expected.txt, which the Rust engine reproduces too); a parameter snapshot changes what follows
// it only; the timing wheel fires in time order; and the steady state allocates nothing.
#include "firm_stratengine.hpp"
#include "../../arena/cpp/firm_alloc_count.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>

using namespace firm::strat;

static std::vector<Event> events() {
    std::ifstream f("code/firm/bookbuilder/data/events_small.bin", std::ios::binary);
    const std::vector<std::uint8_t> b{std::istreambuf_iterator<char>(f), {}};
    std::vector<Event> out;
    for (std::size_t i = 0; i + 48 <= b.size(); i += 48) {
        Event e;
        e.kind = b[i];
        e.side = b[i + 1];
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

int main() {
    int fails = 0;
    const auto ev = events();
    Engine<> a(1, Params{}), b(1, Params{});
    const auto n0 = firm::arena::allocations();
    a.run(ev);
    const auto allocs = firm::arena::allocations() - n0;
    b.run(ev);
    char h[17];
    std::snprintf(h, sizeof h, "%016llx", static_cast<unsigned long long>(a.hash));
    std::ifstream ex("code/firm/stratengine/data/expected.txt");
    std::string want;
    ex >> want;
    std::printf("actions %zu, hash %s (expected %s), position %lld, pnl %lld, allocations %llu\n", a.actions.size(), h,
                want.c_str(), static_cast<long long>(a.position), static_cast<long long>(a.pnl()),
                static_cast<unsigned long long>(allocs));
    if (a.hash != b.hash || a.actions.size() != b.actions.size() || a.pnl() != b.pnl()) ++fails;
    if (want != h || allocs != 0 || a.actions.size() < 100) ++fails;

    // a snapshot half-way: identical actions before it, different after it
    Params wide{};
    wide.version = 2;
    wide.half_spread_ticks = 4;
    const std::uint64_t mid_t = ev[ev.size() / 2].ts;
    Engine<> c(1, Params{});
    c.run(ev, {Snapshot{mid_t, wide}});
    std::size_t same = 0;
    while (same < a.actions.size() && same < c.actions.size() && a.actions[same].t < mid_t &&
           a.actions[same].price == c.actions[same].price && a.actions[same].kind == c.actions[same].kind)
        ++same;
    const bool before_same = same < c.actions.size() && c.actions[same].t >= mid_t;
    std::printf("snapshot at the middle: first %zu actions identical, later ones version %u\n", same,
                c.actions.back().version);
    if (!before_same || c.hash == a.hash || c.actions.back().version != 2) ++fails;

    // the wheel fires in time order, across slots and revolutions
    TimerWheel w(100, 8);
    std::vector<std::uint64_t> fired;
    for (const std::uint64_t t : {950u, 120u, 5000u, 130u, 121u, 2210u}) w.schedule(t, t);
    w.advance(3000, [&](const TimerWheel::Timer& t) { fired.push_back(t.t); });
    if (fired != std::vector<std::uint64_t>{120, 121, 130, 950, 2210} || w.pending() != 1) ++fails;
    std::printf("%s\n", fails ? "FAILED" : "ok");
    return fails;
}
