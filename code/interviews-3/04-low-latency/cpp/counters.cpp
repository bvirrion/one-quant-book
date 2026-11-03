#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <thread>
#include <vector>

struct Counters {
    std::atomic<std::uint64_t> hits[8];
};
Counters shared_line;

void worker(int t, std::uint64_t n) {  // thread t only ever touches hits[t]
    for (std::uint64_t i = 0; i < n; ++i)
        shared_line.hits[t].fetch_add(1, std::memory_order_relaxed);
}

struct PaddedCounters {
    struct Slot {
        alignas(64) std::atomic<std::uint64_t> hits;
    };
    Slot slot[8];
};
PaddedCounters own_line;

void padded_worker(int t, std::uint64_t n) {
    for (std::uint64_t i = 0; i < n; ++i)
        own_line.slot[t].hits.fetch_add(1, std::memory_order_relaxed);
}

template <class F>
double ns_per_increment(int threads, std::uint64_t n, F f) {
    auto t0 = std::chrono::steady_clock::now();
    std::vector<std::thread> pool;
    for (int t = 0; t < threads; ++t) pool.emplace_back(f, t, n);
    for (auto& th : pool) th.join();
    std::chrono::duration<double, std::nano> dt = std::chrono::steady_clock::now() - t0;
    return dt.count() / static_cast<double>(n);
}

int main(int argc, char** argv) {
    int threads = argc > 1 ? std::atoi(argv[1]) : 4;
    std::uint64_t n = argc > 2 ? std::strtoull(argv[2], nullptr, 10) : 1000000;
    double a = ns_per_increment(threads, n, worker);
    double b = ns_per_increment(threads, n, padded_worker);
    std::uint64_t sum_a = 0, sum_b = 0;
    for (int t = 0; t < 8; ++t) {
        sum_a += shared_line.hits[t].load();
        sum_b += own_line.slot[t].hits.load();
    }
    std::printf("%zu %zu %llu %llu\n", sizeof(Counters), sizeof(PaddedCounters),
                static_cast<unsigned long long>(sum_a), static_cast<unsigned long long>(sum_b));
    std::printf("ns per increment: shared line %.2f, own line %.2f\n", a, b);
}
