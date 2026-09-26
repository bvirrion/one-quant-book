// Chapter 20: with no defect switched on the small engine is deterministic within a process; with the wall clock it
// is not even there.
#include "ll_nondet.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>

static std::vector<ll::nondet::Event> events() {
    std::ifstream f("code/firm/bookbuilder/data/events_small.bin", std::ios::binary);
    const std::vector<std::uint8_t> b{std::istreambuf_iterator<char>(f), {}};
    std::vector<ll::nondet::Event> ev;
    for (std::size_t i = 0; i + 48 <= b.size(); i += 48) {
        ll::nondet::Event e;
        e.kind = b[i];
        e.side = b[i + 1];
        std::memcpy(&e.ts, &b[i + 12], 8);
        std::memcpy(&e.ref, &b[i + 20], 8);
        std::memcpy(&e.ref2, &b[i + 28], 8);
        std::memcpy(&e.price, &b[i + 36], 4);
        std::memcpy(&e.qty, &b[i + 40], 8);
        ev.push_back(e);
    }
    return ev;
}

int main() {
    const auto ev = events();
    ll::nondet::Engine a({}, 1), b({}, 1);
    a.run(ev);
    b.run(ev);
    ll::nondet::Defects w;
    w.wall_clock = true;
    ll::nondet::Engine c(w, 1), d(w, 1);
    c.run(ev);
    d.run(ev);
    std::printf("deterministic: %016llx %016llx; wall clock: %016llx %016llx\n", static_cast<unsigned long long>(a.hash),
                static_cast<unsigned long long>(b.hash), static_cast<unsigned long long>(c.hash),
                static_cast<unsigned long long>(d.hash));
    return a.hash == b.hash && a.actions > 100 && c.hash != d.hash && c.actions == a.actions ? 0 : 1;
}
