// Chapter 11: the stack under two threads, the counters' totals, and sequential consistency holding in the litmus test.
#include "ll_lockfree.hpp"

#include <cstdio>

using namespace ll::lf;

int main() {
    Stack s(1000);
    for (std::uint32_t i = 1; i <= 1000; ++i) s.push(i);
    std::atomic<int> popped{0};
    auto churn = [&] {  // pop and push back 200,000 times each: nodes must never be lost or duplicated
        for (int i = 0; i < 200'000; ++i) { const auto n = s.pop(); if (n) s.push(n); else popped.fetch_add(1); }
    };
    std::thread a(churn), b(churn);
    a.join();
    b.join();
    std::vector<int> seen(1001, 0);
    for (std::uint32_t n; (n = s.pop()) != 0;) ++seen[n];
    for (std::uint32_t i = 1; i <= 1000; ++i) if (seen[i] != 1) { std::puts("stack lost or duplicated a node"); return 1; }
    for (int t : {1, 2, 4})
        if (count_mutex(t, 10'000) != 10'000u * t || count_cas(t, 10'000) != 10'000u * t || count_fetch_add(t, 10'000) != 10'000u * t ||
            count_per_thread(t, 10'000) != 10'000u * t) return 1;
    const auto z = store_buffer_zeros<std::memory_order_seq_cst, std::memory_order_seq_cst>(50'000);
    if (z != 0) { std::printf("sequential consistency violated %llu times\n", static_cast<unsigned long long>(z)); return 1; }
    std::puts("lock-free ok");
    return 0;
}
