// Stress test: one producer and one consumer pass 2'000'000 sequence numbers; order and sum must be exact.
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <thread>

#include "iv_spsc.hpp"

int main() {
    constexpr std::uint64_t kCount = 2'000'000;
    iv::SpscQueue<std::uint64_t, 1024> q;
    std::uint64_t sum = 0, expected_next = 0;
    bool in_order = true;
    std::thread consumer([&] {
        std::uint64_t got = 0;
        while (got < kCount) {
            if (auto v = q.pop()) {
                in_order = in_order && (*v == expected_next);
                ++expected_next;
                sum += *v;
                ++got;
            }
        }
    });
    for (std::uint64_t i = 0; i < kCount; ++i)
        while (!q.push(i)) {
        }
    consumer.join();
    assert(in_order);
    assert(sum == kCount * (kCount - 1) / 2);
    assert(!q.pop().has_value());
    std::puts("iv_spsc_test: all passed");
    return 0;
}
