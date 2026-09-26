// Chapter 20: the firm's engine (firm.stratengine) on a recorded event file.
//   ll_engine_run <events.bin> <tick>          one replay: prints the output hash, the actions and the profit
//   ll_engine_run <events.bin> <tick> time     ns per event (TSC around each event, timer cost subtracted) as quantiles
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>

#include "firm_stratengine.hpp"
#include "firm_ubench.hpp"

using namespace firm::strat;

int main(int argc, char** argv) {
    if (argc < 3) return 1;
    std::ifstream f(argv[1], std::ios::binary);
    const std::vector<std::uint8_t> b{std::istreambuf_iterator<char>(f), {}};
    std::vector<Event> ev;
    for (std::size_t i = 0; i + 48 <= b.size(); i += 48) {
        Event e;
        e.kind = b[i];
        e.side = b[i + 1];
        std::memcpy(&e.ts, &b[i + 12], 8);
        std::memcpy(&e.ref, &b[i + 20], 8);
        std::memcpy(&e.ref2, &b[i + 28], 8);
        std::memcpy(&e.price, &b[i + 36], 4);
        std::memcpy(&e.qty, &b[i + 40], 8);
        ev.push_back(e);
    }
    const auto tick = static_cast<std::uint32_t>(std::atoi(argv[2]));
    if (argc > 3 && std::string(argv[3]) == "time") {
        using namespace firm::ubench;
        const Clock clk = Clock::calibrate();
        const double ovh = clk.ns(overhead());
        std::vector<double> t(ev.size());
        for (int pass = 0; pass < 2; ++pass) {
            Engine<> eng(tick, Params{});
            for (std::size_t i = 0; i < ev.size(); ++i) {
                const std::vector<Event> one{ev[i]};
                const std::uint64_t a0 = tsc_start();
                eng.run(one);
                t[i] = clk.ns(rdtscp() - a0) - ovh;
            }
        }
        for (const double q : {0.5, 0.9, 0.99, 0.999}) std::printf("time,%g,%.1f\n", q, quantile(t, q));
        return 0;
    }
    Engine<> eng(tick, Params{});
    eng.run(ev);
    std::printf("%016llx %zu %lld\n", static_cast<unsigned long long>(eng.hash), eng.actions.size(),
                static_cast<long long>(eng.pnl()));
    return 0;
}
