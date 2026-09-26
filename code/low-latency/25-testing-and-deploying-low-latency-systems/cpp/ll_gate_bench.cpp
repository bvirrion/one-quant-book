// Chapter 25: one run of the performance gate's benchmark. Replays the book builder's small-tick day through the
// strategy engine three times, timing each event with the TSC, and prints the run's median and 99th percentile in ns.
//   ll_gate_bench <extra_ns>   extra_ns > 0 plants a regression: a busy wait of that many nanoseconds after each event
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <vector>

#include "firm_stratengine.hpp"
#include "firm_ubench.hpp"

using namespace firm::strat;
namespace ub = firm::ubench;

int main(int argc, char** argv) {
    const double extra_ns = argc > 1 ? std::atof(argv[1]) : 0.0;
    std::ifstream f("code/firm/bookbuilder/data/events_small.bin", std::ios::binary);
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
    const ub::Clock clk = ub::Clock::calibrate(20);
    const double ovh = clk.ns(ub::overhead());
    std::vector<double> t;
    t.reserve(3 * ev.size());
    std::vector<Event> one(1);
    for (int pass = 0; pass < 3; ++pass) {
        Engine<> eng(1, Params{});
        for (const Event& e : ev) {
            one[0] = e;
            const std::uint64_t a = ub::tsc_start();
            eng.run(one);
            if (extra_ns > 0) {                                  // the planted regression: wait a fixed time
                const std::uint64_t until = ub::rdtscp() + static_cast<std::uint64_t>(extra_ns * clk.ticks_per_ns);
                while (ub::rdtscp() < until) {
                }
            }
            t.push_back(clk.ns(ub::rdtscp() - a) - ovh);
        }
    }
    std::printf("%.2f %.2f\n", ub::quantile(t, 0.5), ub::quantile(t, 0.99));
    return 0;
}
