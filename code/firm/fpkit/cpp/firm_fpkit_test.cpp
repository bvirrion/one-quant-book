// Acceptance tests of firm.fpkit (C++20): bit-identical results with the Python and Rust twins.
#include "firm_fpkit.hpp"
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>

using namespace firm::fpkit;

static std::uint64_t bits(double x) {
    std::uint64_t u;
    std::memcpy(&u, &x, sizeof u);
    return u;
}

int main() {
    const double pow10[9] = {1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0, 10000000.0, 100000000.0};
    SplitMix64 g{2025};
    std::vector<double> pnl(10000);
    for (std::size_t i = 0; i < pnl.size(); ++i) pnl[i] = (g.uniform() - 0.5) * pow10[i % 9];
    g = SplitMix64{7};
    std::vector<double> prices(10000);
    for (auto& p : prices) p = 10000.0 + g.uniform();
    g = SplitMix64{11};
    std::vector<double> expo(1000);
    for (auto& e : expo) e = 1000.0 * (g.uniform() - 0.5);
    g = SplitMix64{13};
    std::vector<double> a(100, -1.0), b(100), c(100, -1.0), d(100);
    for (auto& v : b) v = 2.5 + g.uniform();
    for (auto& v : d) v = g.uniform();

    assert(bits(naive_sum(pnl)) == 0xc1ba1fb24e533d44ULL);
    assert(bits(pairwise_sum(pnl)) == 0xc1ba1fb24e533d64ULL);
    assert(bits(neumaier_sum(pnl)) == 0xc1ba1fb24e533d69ULL);
    const auto m = welford(prices);
    assert(bits(m.mean) == 0x40c3883fd5280542ULL && bits(m.var) == 0x3fb4f5102e312730ULL);
    assert(bits(logsumexp(expo)) == 0x407f4af53ba8f1fbULL);
    const auto x = thomas(a, b, c, d);
    assert(bits(x[0]) == 0x3fca6da43e350286ULL && bits(x[99]) == 0x3fd69c02e4172c65ULL);
    // a fused multiply-add rounds once: 0.1 * 10 - 1 is 0 with two roundings and 2^-54 with one
    const double p = 0.1, q = 10.0, r = -1.0;
    volatile double prod = p * q;
    assert(prod + r == 0.0 && std::fma(p, q, r) == std::ldexp(1.0, -54));
    return 0;
}
