// Chapter 12 benchmark. Round trips between two pinned threads through two SPSC rings (ping-pong), against a
// mutex-and-condition-variable queue, within a process and between two processes over shared memory.
// Output: transport,placement,p50,p99,p999,max (ns per round trip); then throughput lines "throughput,<msgs per s>".
#include <pthread.h>
#include <sched.h>
#include <sys/wait.h>
#include <unistd.h>

#include <condition_variable>
#include <cstdio>
#include <deque>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include "firm_ring.hpp"
#include "firm_ubench.hpp"

using namespace firm::ring;
using namespace firm::ubench;

static void pin(int cpu) { cpu_set_t s; CPU_ZERO(&s); CPU_SET(cpu, &s); pthread_setaffinity_np(pthread_self(), sizeof s, &s); }

static void report(const char* name, const char* placement, std::vector<double>& t) {
    std::printf("%s,%s,%.0f,%.0f,%.0f,%.0f\n", name, placement, quantile(t, 0.5), quantile(t, 0.99), quantile(t, 0.999), quantile(t, 1.0));
}

constexpr int kTrips = 100'000;

static void ring_pingpong(const char* placement, int ca, int cb, const Clock& clk) {
    std::vector<std::uint8_t> m1(region_size(64, 64)), m2(region_size(64, 64));
    format(m1.data(), 64, 64);
    format(m2.data(), 64, 64);
    std::thread echo([&] {
        pin(cb);
        Spsc in(m1.data()), out(m2.data());
        std::uint64_t v;
        for (int i = 0; i < kTrips; ++i) { while (in.try_read(&v, 8) < 0) {} while (!out.try_write(&v, 8)) {} }
    });
    pin(ca);
    Spsc out(m1.data()), in(m2.data());
    std::vector<double> t;
    t.reserve(kTrips);
    for (std::uint64_t i = 0; i < kTrips; ++i) {
        const std::uint64_t a = tsc_start();
        while (!out.try_write(&i, 8)) {}
        std::uint64_t v;
        while (in.try_read(&v, 8) < 0) {}
        t.push_back(clk.ns(rdtscp() - a));
    }
    echo.join();
    report("SPSC ring", placement, t);
}

struct LockedQueue {
    std::mutex m;
    std::condition_variable cv;
    std::deque<std::uint64_t> q;
    void push(std::uint64_t v) { { std::lock_guard g(m); q.push_back(v); } cv.notify_one(); }
    std::uint64_t pop() { std::unique_lock g(m); cv.wait(g, [&] { return !q.empty(); }); const auto v = q.front(); q.pop_front(); return v; }
};

static void locked_pingpong(const char* placement, int ca, int cb, const Clock& clk) {
    LockedQueue a2b, b2a;
    std::thread echo([&] { pin(cb); for (int i = 0; i < kTrips; ++i) b2a.push(a2b.pop()); });
    pin(ca);
    std::vector<double> t;
    t.reserve(kTrips);
    for (std::uint64_t i = 0; i < kTrips; ++i) {
        const std::uint64_t a = tsc_start();
        a2b.push(i);
        (void)b2a.pop();
        t.push_back(clk.ns(rdtscp() - a));
    }
    echo.join();
    report("mutex+condvar queue", placement, t);
}

static void shm_pingpong(const char* placement, int ca, int cb, const Clock& clk) {
    const std::string n1 = "/ll_rings_a_" + std::to_string(getpid()), n2 = "/ll_rings_b_" + std::to_string(getpid());
    Segment s1(n1, region_size(64, 64), true), s2(n2, region_size(64, 64), true);
    format(s1.data(), 64, 64);
    format(s2.data(), 64, 64);
    const pid_t child = fork();
    if (child == 0) {
        pin(cb);
        Segment v1(n1, region_size(64, 64), false), v2(n2, region_size(64, 64), false);
        Spsc in(v1.data()), out(v2.data());
        std::uint64_t v;
        for (int i = 0; i < kTrips; ++i) { while (in.try_read(&v, 8) < 0) {} while (!out.try_write(&v, 8)) {} }
        _exit(0);
    }
    pin(ca);
    Spsc out(s1.data()), in(s2.data());
    std::vector<double> t;
    t.reserve(kTrips);
    for (std::uint64_t i = 0; i < kTrips; ++i) {
        const std::uint64_t a = tsc_start();
        while (!out.try_write(&i, 8)) {}
        std::uint64_t v;
        while (in.try_read(&v, 8) < 0) {}
        t.push_back(clk.ns(rdtscp() - a));
    }
    int st = 0;
    waitpid(child, &st, 0);
    report("SPSC over shared memory", placement, t);
}

int main(int argc, char** argv) {
    const int near_a = argc > 2 ? std::atoi(argv[1]) : 6, near_b = argc > 2 ? std::atoi(argv[2]) : 7;
    const int far_a = argc > 4 ? std::atoi(argv[3]) : 2, far_b = argc > 4 ? std::atoi(argv[4]) : 14;
    const Clock clk = Clock::calibrate(50);
    std::printf("transport,placement,p50,p99,p999,max\n");
    ring_pingpong("neighbours", near_a, near_b, clk);
    ring_pingpong("far", far_a, far_b, clk);
    shm_pingpong("neighbours", near_a, near_b, clk);
    locked_pingpong("neighbours", near_a, near_b, clk);
    // streaming throughput, one way, 8-byte messages
    std::vector<std::uint8_t> m(region_size(4096, 64));
    format(m.data(), 4096, 64);
    constexpr std::uint64_t n = 20'000'000;
    std::thread prod([&] { pin(near_b); Spsc p(m.data()); for (std::uint64_t i = 0; i < n; ++i) while (!p.try_write(&i, 8)) {} });
    pin(near_a);
    Spsc c(m.data());
    const std::uint64_t a = tsc_start();
    std::uint64_t v = 0, sum = 0;
    for (std::uint64_t i = 0; i < n; ++i) { while (c.try_read(&v, 8) < 0) {} sum += v; }
    const double s = clk.ns(rdtscp() - a) / 1e9;
    prod.join();
    do_not_optimize(sum);
    std::printf("throughput,%.0f\n", static_cast<double>(n) / s);
    return 0;
}
