// Chapter 14: an options book revalued from its Greeks, stored as an array of structures (one record per option,
// with the fields a real record carries) and as a structure of arrays (one array per field).
#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>

namespace ll::simd {

// A move of the market: underlying price, implied volatility (in vol points) and time (in days).
struct Move {
    double dS, dvol, dt;
};

// One option as a record: 80 bytes, of which the revaluation reads 40.
struct OptionRow {
    std::uint64_t id;
    char symbol[24];
    double qty, delta, gamma, vega, theta;
    std::int32_t expiry;
    std::int32_t flags;
};
static_assert(sizeof(OptionRow) == 80);

// The same book as one array per field.
struct OptionColumns {
    std::vector<double> qty, delta, gamma, vega, theta;
    std::size_t size() const { return qty.size(); }
};

// Second-order revaluation: dV = q (delta dS + gamma dS^2 / 2 + vega dvol + theta dt).
inline double revalue_one(double q, double d, double g, double v, double th, const Move& m) {
    return q * (d * m.dS + 0.5 * g * m.dS * m.dS + v * m.dvol + th * m.dt);
}

inline void revalue_rows(const OptionRow* r, std::size_t n, const Move& m, double* out) {
    for (std::size_t i = 0; i < n; ++i)
        out[i] = revalue_one(r[i].qty, r[i].delta, r[i].gamma, r[i].vega, r[i].theta, m);
}

inline void revalue_columns(const OptionColumns& c, const Move& m, double* __restrict out) {
    const double* __restrict q = c.qty.data();
    const double* __restrict d = c.delta.data();
    const double* __restrict g = c.gamma.data();
    const double* __restrict v = c.vega.data();
    const double* __restrict th = c.theta.data();
    const std::size_t n = c.size();
    for (std::size_t i = 0; i < n; ++i) out[i] = revalue_one(q[i], d[i], g[i], v[i], th[i], m);
}

// A deterministic book of n options for tests and benchmarks.
inline void make_book(std::size_t n, std::vector<OptionRow>& rows, OptionColumns& cols) {
    rows.assign(n, OptionRow{});
    cols = OptionColumns{};
    std::uint64_t x = 88172645463325252ULL;
    auto next = [&] { x ^= x << 13; x ^= x >> 7; x ^= x << 17; return static_cast<double>(x % 10000) / 10000.0; };
    for (std::size_t i = 0; i < n; ++i) {
        OptionRow& r = rows[i];
        r.id = i;
        r.qty = next() < 0.5 ? -10.0 * (1 + next()) : 10.0 * (1 + next());
        r.delta = next() * 2 - 1;
        r.gamma = next() * 0.05;
        r.vega = next() * 30;
        r.theta = -next() * 5;
        cols.qty.push_back(r.qty);
        cols.delta.push_back(r.delta);
        cols.gamma.push_back(r.gamma);
        cols.vega.push_back(r.vega);
        cols.theta.push_back(r.theta);
    }
}

}  // namespace ll::simd
