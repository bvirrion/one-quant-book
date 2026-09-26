// firm.ticktotrade (C++20): the recorded line, decoded by the feed handler, gives back the book builder's small-tick
// day event for event; the path replayed offline on those events gives the committed orders (data/expected.txt, which
// the Rust twin reproduces), twice, with no allocation in the second pass.
#include "firm_ticktotrade.hpp"
#include "../../arena/cpp/firm_alloc_count.hpp"
#include "../../feedhandler/cpp/firm_feedhandler.hpp"

#include <cstdio>
#include <fstream>
#include <iterator>

using namespace firm::t2t;

static std::vector<std::uint8_t> slurp(const char* p) {
    std::ifstream f(p, std::ios::binary);
    return {std::istreambuf_iterator<char>(f), {}};
}

int main() {
    int fails = 0;
    const auto want_ev = read_events(slurp("code/firm/bookbuilder/data/events_small.bin"));
    const auto raw = slurp("code/firm/ticktotrade/data/line.bin");
    const auto pk = firm::feed2::recorded(raw);
    std::vector<firm::strat::Event> ev;
    firm::feed2::Handler h;
    h.on_event = [&](const firm::feed2::Event& e) { ev.push_back(e); };
    h.run(pk, pk, {});
    bool same = ev.size() == want_ev.size();
    for (std::size_t i = 0; same && i < ev.size(); ++i) same = std::memcmp(&ev[i], &want_ev[i], sizeof ev[i]) == 0;
    std::printf("%zu packets -> %zu events, equal to the book builder's day: %s\n", pk.size(), ev.size(),
                same ? "yes" : "no");
    fails += !same;

    const auto exp = slurp("code/firm/ticktotrade/data/expected.txt");
    std::uint64_t hashes[2];
    unsigned long long allocs = 0;
    std::size_t orders = 0, sent = 0;
    for (int pass = 0; pass < 2; ++pass) {
        Path path(1);
        const auto a0 = firm::arena::allocations();
        for (const auto& e : ev)
            path.on_event(e, nullptr, nullptr, [&](const std::uint8_t*, std::size_t, char, std::uint64_t) { ++sent; });
        if (pass == 1) allocs = firm::arena::allocations() - a0;
        hashes[pass] = order_hash(path.out);
        orders = path.out.size();
        if (pass == 0)
            std::printf("%zu actions, %zu orders (refused: risk %llu, gateway %llu)\n", path.engine().actions.size(),
                        orders, static_cast<unsigned long long>(path.refused_risk),
                        static_cast<unsigned long long>(path.refused_gateway));
    }
    char h16[17];
    std::snprintf(h16, sizeof h16, "%016llx", static_cast<unsigned long long>(hashes[0]));
    const std::string want(exp.begin(), exp.end());
    std::printf("orders hash %s; allocations in the second pass %llu\n", h16, allocs);
    if (hashes[0] != hashes[1] || want.find(h16) == std::string::npos || allocs != 0 || sent != 2 * orders) ++fails;
    std::printf(fails ? "FAIL\n" : "ok\n");
    return fails ? 1 : 0;
}
