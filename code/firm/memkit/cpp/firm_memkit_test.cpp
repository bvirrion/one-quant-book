// Acceptance test of firm.memkit: layout and correctness, no timings.
#include "firm_memkit.hpp"

#include <atomic>
#include <cstdio>

using namespace firm::memkit;

int main() {
    static_assert(sizeof(CachePadded<std::atomic<std::uint64_t>>) == kLine);
    static_assert(alignof(CachePadded<char>) == kLine);
    static_assert(sizeof(CachePadded<char[100]>) == 2 * kLine);
    CachePadded<std::uint64_t> two[2];
    if (reinterpret_cast<std::uintptr_t>(&two[1].value) - reinterpret_cast<std::uintptr_t>(&two[0].value) != kLine) return 1;
    Buffer b(3 << 20, true);
    if (b.size() % (2u << 20) != 0 || reinterpret_cast<std::uintptr_t>(b.data()) % 4096 != 0) return 1;
    for (bool random : {false, true}) {
        const std::size_t n = 1000, stride = 64;
        chase_ring(b.data(), n, stride, random, 7);
        // a single cycle: n steps come back to the start and no earlier step does
        const void* start = b.data();
        const void* p = start;
        for (std::size_t i = 1; i <= n; ++i) {
            p = chase(p, 1);
            if ((p == start) != (i == n)) { std::puts("not a single cycle"); return 1; }
        }
    }
    std::puts("memkit ok");
    return 0;
}
