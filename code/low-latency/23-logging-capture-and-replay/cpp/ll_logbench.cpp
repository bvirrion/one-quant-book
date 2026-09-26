// Chapter 23: what a log call costs on the hot path, and how fast a journal replays.
//   ll_logbench calls              ns per call (TSC, timer cost subtracted) for one message with four numbers:
//                                  firm.binlog (a writer thread drains the ring), snprintf into a buffer, fprintf to
//                                  a buffered file, std::ostringstream
//   ll_logbench replay <journal>   read a journal and run the strategy engine on it: events, seconds
#include <cstdio>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

#include "firm_binlog.hpp"
#include "firm_stratengine.hpp"
#include "firm_ubench.hpp"

namespace ub = firm::ubench;
using firm::binlog::Logger;

template <class F>
static void timed(const char* name, const ub::Clock& clk, double ovh, F&& f) {
    constexpr int N = 200'000;
    std::vector<double> v;
    v.reserve(N);
    for (int i = 0; i < N + 2000; ++i) {
        const std::uint64_t t0 = ub::tsc_start();
        f(i);
        const double ns = clk.ns(ub::rdtscp() - t0) - ovh;
        if (i >= 2000) v.push_back(ns);
    }
    for (const double q : {0.5, 0.99, 0.999}) std::printf("calls,%s,%g,%.1f\n", name, q, ub::quantile(v, q));
}

int main(int argc, char** argv) {
    const std::string mode = argc > 1 ? argv[1] : "calls";
    const ub::Clock clk = ub::Clock::calibrate();
    const double ovh = clk.ns(ub::overhead());
    if (mode == "calls") {
        {
            Logger log(1 << 18);
            firm::binlog::Writer w(log, "/dev/null");
            timed("binlog", clk, ovh, [&](int i) {
                log.log<"fill {} of {} at {}, position {}">(static_cast<std::uint64_t>(i), std::uint64_t(40),
                                                            std::int64_t{100}, std::int64_t{999'900}, std::int64_t{i});
            });
            w.stop();
            std::printf("dropped,%llu\n", static_cast<unsigned long long>(log.dropped()));
        }
        char buf[128];
        timed("snprintf", clk, ovh, [&](int i) {
            std::snprintf(buf, sizeof buf, "%d fill %d of %d at %d, position %d", i, 40, 100, 999'900, i);
            ub::do_not_optimize(buf[0]);
        });
        std::FILE* f = std::fopen("/dev/null", "w");
        std::setvbuf(f, nullptr, _IOFBF, 1 << 16);
        timed("fprintf", clk, ovh, [&](int i) {
            std::fprintf(f, "%d fill %d of %d at %d, position %d\n", i, 40, 100, 999'900, i);
        });
        std::fclose(f);
        timed("ostringstream", clk, ovh, [&](int i) {
            std::ostringstream s;
            s << i << " fill " << 40 << " of " << 100 << " at " << 999'900 << ", position " << i;
            ub::do_not_optimize(s.str().size());
        });
        return 0;
    }
    // replay: read the journal, rebuild the events, run the engine; the reading is timed with the engine
    const std::uint64_t t0 = ub::tsc_start();
    std::ifstream in(argv[2], std::ios::binary);
    const std::vector<std::uint8_t> b{std::istreambuf_iterator<char>(in), {}};
    std::vector<firm::strat::Event> ev;
    for (const auto& [recv, p] : firm::binlog::Journal::records(b)) {
        firm::strat::Event e;
        e.kind = p[0];
        e.side = p[1];
        std::memcpy(&e.seq, p + 4, 8);
        std::memcpy(&e.ts, p + 12, 8);
        std::memcpy(&e.ref, p + 20, 8);
        std::memcpy(&e.ref2, p + 28, 8);
        std::memcpy(&e.price, p + 36, 4);
        std::memcpy(&e.qty, p + 40, 8);
        ev.push_back(e);
        (void)recv;
    }
    firm::strat::Engine<> eng(static_cast<std::uint32_t>(std::atoi(argv[3])), firm::strat::Params{});
    eng.run(ev);
    const double s = clk.ns(ub::rdtscp() - t0) * 1e-9;
    std::printf("replay,%zu,%.4f,%016llx\n", ev.size(), s, static_cast<unsigned long long>(eng.hash));
    return 0;
}
