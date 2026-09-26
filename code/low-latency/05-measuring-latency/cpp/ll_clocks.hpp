// Chapter 5 of One Quant Book 13: the clocks a program can read, each as a function returning nanoseconds or ticks.
#pragma once
#include <sys/time.h>
#include <x86intrin.h>

#include <chrono>
#include <cstdint>
#include <ctime>

namespace ll::clocks {

inline std::uint64_t tsc() { return __rdtsc(); }
inline std::uint64_t tscp() { unsigned aux = 0; return __rdtscp(&aux); }
inline std::uint64_t steady() {
    return static_cast<std::uint64_t>(std::chrono::steady_clock::now().time_since_epoch().count());
}
inline std::uint64_t mono(clockid_t id) {
    timespec ts{};
    clock_gettime(id, &ts);
    return static_cast<std::uint64_t>(ts.tv_sec) * 1'000'000'000u + static_cast<std::uint64_t>(ts.tv_nsec);
}
inline std::uint64_t monotonic() { return mono(CLOCK_MONOTONIC); }
inline std::uint64_t monotonic_raw() { return mono(CLOCK_MONOTONIC_RAW); }
inline std::uint64_t realtime() { return mono(CLOCK_REALTIME); }
inline std::uint64_t tod() {
    timeval tv{};
    gettimeofday(&tv, nullptr);
    return static_cast<std::uint64_t>(tv.tv_sec) * 1'000'000u + static_cast<std::uint64_t>(tv.tv_usec);
}

}  // namespace ll::clocks
