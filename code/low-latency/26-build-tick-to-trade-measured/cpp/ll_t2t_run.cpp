// Chapter 26: one live run of the assembled path (firm.ticktotrade) on the loopback interface.
//   ll_t2t_run <line.bin> <stretch> <cpu exchange> <cpu feed> <cpu engine> <cpu venue>
// prints one line per order, "o,<kind>,<nth>,<exch>,<recv>,<pub>,<pop>,<book>,<decide>,<risk>,<encode>,<sent>,<venue>" in
// nanoseconds from the first packet's send, then "summary,<events>,<orders>,<order hash>,<allocations after warm-up>".
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>

#include "firm_ticktotrade_live.hpp"

using namespace firm::t2t;

int main(int argc, char** argv) {
    if (argc < 7) return 1;
    std::ifstream f(argv[1], std::ios::binary);
    Config cfg;
    cfg.line.assign(std::istreambuf_iterator<char>(f), {});
    cfg.stretch = std::atof(argv[2]);
    cfg.cpu_exchange = std::atoi(argv[3]), cfg.cpu_feed = std::atoi(argv[4]);
    cfg.cpu_engine = std::atoi(argv[5]), cfg.cpu_venue = std::atoi(argv[6]);
    const Result r = run_live(cfg);
    const std::uint64_t base = r.orders.empty() ? 0 : r.orders.front().exch;
    auto ns = [&](std::uint64_t t) { return t ? static_cast<double>(t - base) / r.ticks_per_ns : -1.0; };
    for (const auto& o : r.orders) {
        std::printf("o,%c,%d,%.1f", o.s.kind, o.nth, ns(o.exch));
        for (int i = Recv; i < NStamps; ++i) std::printf(",%.1f", ns(o.s.t[i]));
        std::printf(",%.1f\n", ns(o.venue));
    }
    std::printf("summary,%llu,%zu,%016llx,%lld\n", static_cast<unsigned long long>(r.events), r.orders.size(),
                static_cast<unsigned long long>(order_hash(r.out)), r.allocations_after_warmup);
    return 0;
}
