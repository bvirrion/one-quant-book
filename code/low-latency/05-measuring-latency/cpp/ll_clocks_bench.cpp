// Chapter 5 benchmark: cost of one call to each clock (best of 7 batches of 1,000,000 calls, pinned by the driver),
// then the TSC's rate from 10 calibrations of 50 ms against CLOCK_MONOTONIC_RAW and CLOCK_MONOTONIC.
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <string>

#include "firm_ubench.hpp"
#include "ll_clocks.hpp"

using namespace ll::clocks;

template <class F>
double per_call(F f) {
    double best = 1e300;
    for (int r = 0; r < 7; ++r) {
        const auto t0 = std::chrono::steady_clock::now();
        std::uint64_t acc = 0;
        for (int i = 0; i < 1'000'000; ++i) acc += f();
        firm::ubench::do_not_optimize(acc);
        best = std::min(best, std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / 1e6);
    }
    return best;
}

int main(int argc, char** argv) {
    const bool calib = argc > 1 && std::string(argv[1]) == "calib";
    if (!calib) {
        std::printf("clock,ns_per_call\n");
        std::printf("rdtsc,%.2f\n", per_call(tsc));
        std::printf("rdtscp,%.2f\n", per_call(tscp));
        std::printf("steady_clock,%.2f\n", per_call(steady));
        std::printf("CLOCK_MONOTONIC,%.2f\n", per_call(monotonic));
        std::printf("CLOCK_MONOTONIC_RAW,%.2f\n", per_call(monotonic_raw));
        std::printf("CLOCK_REALTIME,%.2f\n", per_call(realtime));
        std::printf("gettimeofday,%.2f\n", per_call(tod));
    } else {
        // the same 50 ms, timed by the raw clock and by the slewed one
        std::printf("run,raw,monotonic\n");
        for (int r = 0; r < 10; ++r) {
            const double m0 = static_cast<double>(monotonic()), w0 = firm::ubench::raw_ns();
            const std::uint64_t t0 = firm::ubench::tsc_start();
            while (firm::ubench::raw_ns() - w0 < 50e6) {
            }
            const std::uint64_t t1 = firm::ubench::rdtscp();
            const double w1 = firm::ubench::raw_ns(), m1 = static_cast<double>(monotonic());
            std::printf("%d,%.6f,%.6f\n", r, static_cast<double>(t1 - t0) / (w1 - w0), static_cast<double>(t1 - t0) / (m1 - m0));
        }
    }
    return 0;
}
