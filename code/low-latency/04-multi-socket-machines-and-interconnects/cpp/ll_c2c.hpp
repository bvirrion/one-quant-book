// Chapter 4 of One Quant Book 13: core-to-core latency, measured by bouncing one cache line between two threads.
#pragma once
#include <pthread.h>
#include <sched.h>

#include <atomic>
#include <chrono>
#include <thread>

#include "../../../firm/memkit/cpp/firm_memkit.hpp"

namespace ll::c2c {

inline bool pin(int cpu) {
    cpu_set_t s;
    CPU_ZERO(&s);
    CPU_SET(cpu, &s);
    return pthread_setaffinity_np(pthread_self(), sizeof s, &s) == 0;
}

// Thread A on cpu_a sets the flag to 1 when it sees 0; thread B on cpu_b sets it back to 0 when it sees 1.
// Each round trip moves the line to B's core and back: returns nanoseconds per one-way transfer.
inline double one_way_ns(int cpu_a, int cpu_b, int round_trips) {
    firm::memkit::CachePadded<std::atomic<int>> flag;
    flag.value.store(0);
    std::atomic<bool> go{false};
    std::thread b([&] {
        pin(cpu_b);
        while (!go.load(std::memory_order_acquire)) {
        }
        for (int i = 0; i < round_trips; ++i) {
            while (flag.value.load(std::memory_order_acquire) != 1) {
            }
            flag.value.store(0, std::memory_order_release);
        }
    });
    pin(cpu_a);
    go.store(true, std::memory_order_release);
    const auto t0 = std::chrono::steady_clock::now();
    for (int i = 0; i < round_trips; ++i) {
        while (flag.value.load(std::memory_order_acquire) != 0) {
        }
        flag.value.store(1, std::memory_order_release);
    }
    while (flag.value.load(std::memory_order_acquire) != 0) {
    }
    const auto t1 = std::chrono::steady_clock::now();
    b.join();
    return std::chrono::duration<double, std::nano>(t1 - t0).count() / (2.0 * round_trips);
}

}  // namespace ll::c2c
