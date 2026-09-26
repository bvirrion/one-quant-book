// Chapter 5: every clock is monotonic over a short loop (REALTIME may be stepped by NTP, so it is only read).
#include "ll_clocks.hpp"

#include <cstdio>

int main() {
    using namespace ll::clocks;
    std::uint64_t (*fs[])() = {tsc, tscp, steady, monotonic, monotonic_raw};
    for (auto f : fs) {
        std::uint64_t prev = f();
        for (int i = 0; i < 10000; ++i) { const std::uint64_t t = f(); if (t < prev) return 1; prev = t; }
    }
    if (realtime() == 0 || tod() == 0) return 1;
    std::puts("clocks ok");
    return 0;
}
