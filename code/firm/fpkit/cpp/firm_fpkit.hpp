// firm.fpkit (C++20 twin): summation, Welford, log-sum-exp and the Thomas solver, written to perform the same
// floating-point operations in the same order as the Python and Rust twins (build without -ffp-contract=fast or
// -ffast-math, or the results stop being bit-identical). One Quant Book 4, chapter 25.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace firm::fpkit {

struct SplitMix64 {
    std::uint64_t state;
    std::uint64_t next_u64() {
        state += 0x9E3779B97F4A7C15ULL;
        std::uint64_t z = state;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31);
    }
    double uniform() { return (static_cast<double>(next_u64() >> 11) + 0.5) * (1.0 / 9007199254740992.0); }
};

inline double naive_sum(const std::vector<double>& x) {
    double s = 0.0;
    for (double v : x) s += v;
    return s;
}

inline double pairwise_rec(const std::vector<double>& x, std::size_t lo, std::size_t hi, std::size_t block) {
    if (hi - lo <= block) {
        double s = 0.0;
        for (std::size_t i = lo; i < hi; ++i) s += x[i];
        return s;
    }
    const std::size_t mid = lo + (hi - lo) / 2;
    return pairwise_rec(x, lo, mid, block) + pairwise_rec(x, mid, hi, block);
}

inline double pairwise_sum(const std::vector<double>& x, std::size_t block = 8) {
    return x.empty() ? 0.0 : pairwise_rec(x, 0, x.size(), block);
}

inline double neumaier_sum(const std::vector<double>& x) {
    double s = 0.0, c = 0.0;
    for (double v : x) {
        const double t = s + v;
        if (std::fabs(s) >= std::fabs(v)) c += (s - t) + v;
        else c += (v - t) + s;
        s = t;
    }
    return s + c;
}

struct Moments { std::size_t n; double mean; double var; };

inline Moments welford(const std::vector<double>& x) {
    std::size_t n = 0;
    double mean = 0.0, m2 = 0.0;
    for (double v : x) {
        ++n;
        const double d = v - mean;
        mean += d / static_cast<double>(n);
        m2 += d * (v - mean);
    }
    return {n, mean, n > 1 ? m2 / static_cast<double>(n - 1) : NAN};
}

inline double logsumexp(const std::vector<double>& x) {
    const double m = *std::max_element(x.begin(), x.end());
    if (std::isinf(m)) return m;
    double s = 0.0;
    for (double v : x) s += std::exp(v - m);
    return m + std::log(s);
}

inline std::vector<double> thomas(const std::vector<double>& a, const std::vector<double>& b,
                                  const std::vector<double>& c, const std::vector<double>& d) {
    const std::size_t n = b.size();
    std::vector<double> cp(n, 0.0), dp(n, 0.0), x(n, 0.0);
    cp[0] = c[0] / b[0];
    dp[0] = d[0] / b[0];
    for (std::size_t i = 1; i < n; ++i) {
        const double m = b[i] - a[i] * cp[i - 1];
        cp[i] = i < n - 1 ? c[i] / m : 0.0;
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m;
    }
    x[n - 1] = dp[n - 1];
    for (std::size_t i = n - 1; i-- > 0;) x[i] = dp[i] - cp[i] * x[i + 1];
    return x;
}

}  // namespace firm::fpkit
