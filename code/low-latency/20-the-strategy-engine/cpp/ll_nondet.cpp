// Chapter 20: one run of the small engine on a recorded file with the chosen defects; prints its output hash.
// Usage: ll_nondet <events.bin> <tick> <none|wall_clock|hash_order|two_threads|all>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>

#include "ll_nondet.hpp"

int main(int argc, char** argv) {
    if (argc < 4) return 1;
    std::ifstream f(argv[1], std::ios::binary);
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
    const std::string m = argv[3];
    ll::nondet::Defects d;
    d.wall_clock = m == "wall_clock" || m == "all";
    d.hash_order = m == "hash_order" || m == "all";
    d.two_threads = m == "two_threads" || m == "all";
    ll::nondet::Engine eng(d, static_cast<std::uint32_t>(std::atoi(argv[2])));
    eng.run(ev);
    std::printf("%016llx %zu\n", static_cast<unsigned long long>(eng.hash), eng.actions);
    return 0;
}
