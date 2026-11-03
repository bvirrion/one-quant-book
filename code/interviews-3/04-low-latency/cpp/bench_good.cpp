#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <vector>

[[gnu::noinline]] std::uint64_t work(std::uint64_t n) {
    std::uint64_t h = 1;
    for (std::uint64_t i = 0; i < n; ++i) h = h * 31 + i;
    return h;
}

template <class T>
inline void keep(const T& value) {
    asm volatile("" : : "r,m"(value) : "memory");
}

int main() {
    std::vector<long long> ns;
    for (int run = 0; run < 1000; ++run) {
        std::uint64_t n = 100000;
        asm volatile("" : "+r"(n));
        auto t0 = std::chrono::steady_clock::now();
        auto h = work(n);
        keep(h);
        auto t1 = std::chrono::steady_clock::now();
        using std::chrono::nanoseconds;
        ns.push_back(std::chrono::duration_cast<nanoseconds>(t1 - t0).count());
    }
    std::sort(ns.begin(), ns.end());
    std::printf("median %lld ns, p99 %lld ns, max %lld ns\n",
                ns[500], ns[990], ns[999]);
}
