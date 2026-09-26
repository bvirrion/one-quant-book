// firm.ubench -- the microbenchmark harness of One Quant Book 13 (build of chapter 2).
// Header only, C++20, x86-64. Every later chapter times its code with it.
//   do_not_optimize(x)  keep a value alive: the compiler must assume the asm reads it
//   clobber()           a compiler barrier: the compiler must assume memory changed
//   rdtscp()/tsc_start() serialised reads of the time-stamp counter
//   Clock               TSC ticks to nanoseconds, calibrated against CLOCK_MONOTONIC_RAW
//   run(fn, reps, warm) per-call cost in TSC ticks, after `warm` untimed calls
#pragma once
#include <time.h>
#include <x86intrin.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <string>
#include <thread>
#include <vector>

namespace firm::ubench {

template <class T>
inline void do_not_optimize(T const& value) {
    asm volatile("" : : "r,m"(value) : "memory");
}

inline void clobber() { asm volatile("" : : : "memory"); }

// A timed region starts with lfence;rdtsc (earlier instructions finish before the read)
// and ends with rdtscp;lfence (the read waits for the region, later work waits for it).
inline std::uint64_t tsc_start() {
    _mm_lfence();
    return __rdtsc();
}

inline std::uint64_t rdtscp() {
    unsigned aux = 0;
    const std::uint64_t t = __rdtscp(&aux);
    _mm_lfence();
    return t;
}

// Ticks per nanosecond, measured over `ms` milliseconds against CLOCK_MONOTONIC_RAW. Not against steady_clock
// (CLOCK_MONOTONIC): time synchronisation slews that clock, by about 1% on the book's virtual machine.
inline double raw_ns() {
    timespec ts{};
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return static_cast<double>(ts.tv_sec) * 1e9 + static_cast<double>(ts.tv_nsec);
}

struct Clock {
    double ticks_per_ns = 1.0;
    static Clock calibrate(int ms = 50) {
        const double w0 = raw_ns();
        const std::uint64_t t0 = tsc_start();
        while (raw_ns() - w0 < ms * 1e6) {
        }
        const std::uint64_t t1 = rdtscp();
        const double w1 = raw_ns();
        return Clock{static_cast<double>(t1 - t0) / (w1 - w0)};
    }
    double ns(std::uint64_t ticks) const { return static_cast<double>(ticks) / ticks_per_ns; }
};

// Cost of an empty timed region, in ticks (the floor every measurement carries).
inline std::uint64_t overhead(int reps = 10000) {
    std::vector<std::uint64_t> v(static_cast<std::size_t>(reps));
    for (auto& x : v) {
        const std::uint64_t a = tsc_start();
        clobber();
        x = rdtscp() - a;
    }
    std::nth_element(v.begin(), v.begin() + reps / 2, v.end());
    return v[static_cast<std::size_t>(reps / 2)];
}

// Per-call cost of fn() in ticks: `warm` untimed calls, then `reps` timed ones.
template <class F>
std::vector<std::uint64_t> run(F&& fn, std::size_t reps, std::size_t warm = 1000) {
    for (std::size_t i = 0; i < warm; ++i) fn();
    std::vector<std::uint64_t> out(reps);
    for (auto& x : out) {
        const std::uint64_t a = tsc_start();
        fn();
        x = rdtscp() - a;
    }
    return out;
}

// p in [0, 1], nearest-rank on a copy.
inline double quantile(std::vector<double> v, double p) {
    if (v.empty()) return 0.0;
    std::sort(v.begin(), v.end());
    const auto k = static_cast<std::size_t>(std::min<double>(static_cast<double>(v.size()) - 1, p * static_cast<double>(v.size())));
    return v[k];
}

}  // namespace firm::ubench
