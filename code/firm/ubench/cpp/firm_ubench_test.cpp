// Acceptance test of firm.ubench: machine-independent properties only.
#include "firm_ubench.hpp"

#include <cstdio>

using namespace firm::ubench;

int main() {
    const Clock c = Clock::calibrate(20);
    // an invariant TSC ticks at a rate between 0.5 and 6 GHz on any machine this runs on
    if (!(c.ticks_per_ns > 0.5 && c.ticks_per_ns < 6.0)) { std::puts("bad calibration"); return 1; }
    // the counter is monotonic across calls
    std::uint64_t prev = rdtscp();
    for (int i = 0; i < 100000; ++i) { const std::uint64_t t = rdtscp(); if (t < prev) { std::puts("TSC went back"); return 1; } prev = t; }
    // a loop of 1000 dependent additions costs more than an empty region (ordering, not time)
    volatile std::uint64_t sink = 0;
    auto big = run([&] { std::uint64_t s = sink; for (int i = 0; i < 1000; ++i) { s = s * 3 + 1; do_not_optimize(s); } sink = s; }, 2000, 100);
    std::vector<double> bd(big.begin(), big.end());
    if (!(quantile(bd, 0.5) > static_cast<double>(overhead()))) { std::puts("ordering failed"); return 1; }
    std::puts("ubench ok");
    return 0;
}
