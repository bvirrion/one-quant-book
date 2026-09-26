// Chapter 11 benchmark. Modes:
//   counters -> design,threads,ns_per_increment   wall time per increment of one thread (contention shows as growth)
//   litmus   -> ordering,trials,both_zero          store-buffer outcomes r1 == r2 == 0
//   aba      -> trial,operations,nodes_wrong       the untagged stack under two threads (exercise 7)
#include <chrono>
#include <cstdio>
#include <cstring>

#include "ll_lockfree.hpp"

using namespace ll::lf;

template <class F>
double ns_per(F f, int threads, std::uint64_t per) {
    double best = 1e300;
    for (int r = 0; r < 3; ++r) {
        const auto t0 = std::chrono::steady_clock::now();
        if (f(threads, per) != per * static_cast<std::uint64_t>(threads)) return -1;
        best = std::min(best, std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / static_cast<double>(per));
    }
    return best;
}

int main(int argc, char** argv) {
    if (argc < 2 || !std::strcmp(argv[1], "counters")) {
        constexpr std::uint64_t per = 1'000'000;
        std::printf("design,threads,ns_per_increment\n");
        for (int t : {1, 2, 3, 4}) {
            std::printf("mutex,%d,%.2f\n", t, ns_per(count_mutex, t, per));
            std::printf("CAS loop,%d,%.2f\n", t, ns_per(count_cas, t, per));
            std::printf("fetch_add,%d,%.2f\n", t, ns_per(count_fetch_add, t, per));
            std::printf("per-thread,%d,%.2f\n", t, ns_per(count_per_thread, t, per));
        }
    } else if (!std::strcmp(argv[1], "aba")) {
        std::printf("trial,operations,nodes_wrong\n");
        for (int trial = 0; trial < 20; ++trial) {
            UntaggedStack s(8);
            for (std::uint32_t i = 1; i <= 8; ++i) s.push(i);
            auto churn = [&] { for (int i = 0; i < 1'000'000; ++i) if (const auto n = s.pop()) s.push(n); };
            std::thread a(churn), b(churn);
            a.join();
            b.join();
            int seen[9] = {}, count = 0;
            for (std::uint32_t n; (n = s.pop()) != 0 && count < 100; ++count) ++seen[n];
            int wrong = 0;
            for (int i = 1; i <= 8; ++i) wrong += seen[i] != 1;
            std::printf("%d,2000000,%d\n", trial, wrong);
        }
    } else {
        constexpr std::uint64_t n = 1'000'000;
        std::printf("ordering,trials,both_zero\n");
        std::printf("relaxed,%llu,%llu\n", static_cast<unsigned long long>(n),
                    static_cast<unsigned long long>(store_buffer_zeros<std::memory_order_relaxed, std::memory_order_relaxed>(n)));
        std::printf("release-acquire,%llu,%llu\n", static_cast<unsigned long long>(n),
                    static_cast<unsigned long long>(store_buffer_zeros<std::memory_order_release, std::memory_order_acquire>(n)));
        std::printf("seq_cst,%llu,%llu\n", static_cast<unsigned long long>(n),
                    static_cast<unsigned long long>(store_buffer_zeros<std::memory_order_seq_cst, std::memory_order_seq_cst>(n)));
    }
    return 0;
}
