// Chapter 3 benchmark. Modes:
//   stairs -> bytes,random_ns,random_huge_ns,sequential_ns   one dependent load per step, 64-byte stride
//   huge   -> pages,ns                          random chase over 256 MiB, 4 KiB pages against huge pages
//   false  -> layout,ns_per_increment           two threads incrementing their own counter
#include <pthread.h>
#include <sched.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <thread>

#include "firm_memkit.hpp"
#include "firm_ubench.hpp"

using namespace firm::memkit;
using sc = std::chrono::steady_clock;

static double chase_ns(const Buffer& b, std::size_t n, bool random) {
    chase_ring(b.data(), n, kLine, random, 42);
    const std::size_t steps = std::max<std::size_t>(2'000'000, 2 * n);
    const void* p = chase(b.data(), n);  // warm up: one lap
    double best = 1e300;
    for (int r = 0; r < 2; ++r) {
        const auto t0 = sc::now();
        p = chase(p, steps);
        best = std::min(best, std::chrono::duration<double, std::nano>(sc::now() - t0).count() / static_cast<double>(steps));
    }
    firm::ubench::do_not_optimize(p);
    return best;
}

static void pin(int cpu) {
    cpu_set_t s;
    CPU_ZERO(&s);
    CPU_SET(cpu, &s);
    pthread_setaffinity_np(pthread_self(), sizeof s, &s);
}

struct Shared { std::atomic<std::uint64_t> a{0}, b{0}; };

template <class Counters>
static double two_threads(Counters& c, int cpu_a, int cpu_b, std::uint64_t n) {
    std::atomic<int> ready{0};
    auto work = [&](std::atomic<std::uint64_t>& x, int cpu) {
        pin(cpu);
        ready.fetch_add(1);
        while (ready.load() < 2) {
        }
        for (std::uint64_t i = 0; i < n; ++i) x.fetch_add(1, std::memory_order_relaxed);
    };
    const auto t0 = sc::now();
    std::thread ta([&] { work(c.first(), cpu_a); });
    std::thread tb([&] { work(c.second(), cpu_b); });
    ta.join();
    tb.join();
    return std::chrono::duration<double, std::nano>(sc::now() - t0).count() / static_cast<double>(n);
}

struct SameLine { Shared s; std::atomic<std::uint64_t>& first() { return s.a; } std::atomic<std::uint64_t>& second() { return s.b; } };
struct Padded {
    CachePadded<std::atomic<std::uint64_t>> a, b;
    std::atomic<std::uint64_t>& first() { return a.value; }
    std::atomic<std::uint64_t>& second() { return b.value; }
};

int main(int argc, char** argv) {
    const char* mode = argc > 1 ? argv[1] : "stairs";
    if (!std::strcmp(mode, "stairs")) {
        Buffer b(256u << 20, false), h(256u << 20, true);
        std::printf("bytes,random_ns,random_huge_ns,sequential_ns\n");
        for (std::size_t bytes = 4096; bytes <= (256u << 20); bytes *= 2) {
            for (std::size_t sz : {bytes, bytes + bytes / 2}) {
                if (sz > b.size()) continue;
                const std::size_t n = sz / kLine;
                std::printf("%zu,%.3f,%.3f,%.3f\n", sz, chase_ns(b, n, true), chase_ns(h, n, true), chase_ns(b, n, false));
            }
        }
    } else if (!std::strcmp(mode, "huge")) {
        std::printf("pages,ns\n");
        for (bool huge : {false, true}) {
            Buffer b(256u << 20, huge);
            std::printf("%s,%.3f\n", huge ? "huge" : "4KiB", chase_ns(b, b.size() / kLine, true));
        }
    } else {
        const int ca = argc > 2 ? std::atoi(argv[2]) : 2, cb = argc > 3 ? std::atoi(argv[3]) : 4;
        const std::uint64_t n = 20'000'000;
        SameLine s;
        Padded p;
        struct One { std::atomic<std::uint64_t> x{0}; } one;
        pin(ca);
        auto t0 = sc::now();
        for (std::uint64_t i = 0; i < n; ++i) one.x.fetch_add(1, std::memory_order_relaxed);
        const double solo = std::chrono::duration<double, std::nano>(sc::now() - t0).count() / static_cast<double>(n);
        std::printf("layout,ns_per_increment\none thread,%.3f\npadded,%.3f\nsame line,%.3f\n", solo,
                    two_threads(p, ca, cb, n), two_threads(s, ca, cb, n));
        if (s.s.a.load() != n || p.a.value.load() != n) return 1;
    }
    return 0;
}
