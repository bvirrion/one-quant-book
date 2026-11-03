#include <chrono>
#include <cstdint>
#include <cstdio>

std::uint64_t work(std::uint64_t n) {
    std::uint64_t h = 1;
    for (std::uint64_t i = 0; i < n; ++i) h = h * 31 + i;
    return h;
}

int main() {
    auto t0 = std::chrono::steady_clock::now();
    work(1000000000);
    auto t1 = std::chrono::steady_clock::now();
    std::printf("%lld ns\n", static_cast<long long>((t1 - t0).count()));
}
