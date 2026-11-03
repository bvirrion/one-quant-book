#include <algorithm>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <optional>

std::optional<std::uint64_t> choose(std::uint64_t n, std::uint64_t k) {
    if (k > n) return 0;
    k = std::min(k, n - k);
    std::uint64_t r = 1;
    for (std::uint64_t i = 1; i <= k; ++i) {
        std::uint64_t g = std::gcd(r, i);        // r * (n - k + i) / i, with the common
        std::uint64_t top = (n - k + i) / (i / g);   // factor cancelled before multiplying
        if (__builtin_mul_overflow(r / g, top, &r)) return std::nullopt;
    }
    return r;
}
// Not printed: the driver for the test.
int main() {
    std::uint64_t n, k;
    while (std::cin >> n >> k) {
        auto r = choose(n, k);
        if (r) std::cout << *r << "\n";
        else std::cout << "overflow\n";
    }
}
