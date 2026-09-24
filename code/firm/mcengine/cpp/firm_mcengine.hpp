// firm.mcengine (C++20): the Monte Carlo engine of the miniature firm. One Quant Book 4, ch. 2, 4, 26.
// Stage 1: the SplitMix64 reference generator, Box-Muller normals, Brownian paths by increments and
// by dyadic Brownian-bridge construction, and the bridge crossing probability. The same stream as
// firm_mcengine.py and the Rust crate, from the same seed.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <numbers>
#include <optional>
#include <vector>

namespace firm::mcengine {

struct SplitMix64 {
    std::uint64_t state;
    explicit SplitMix64(std::uint64_t seed) : state(seed) {}
    std::uint64_t next_u64() {
        state += 0x9E3779B97F4A7C15ULL;
        std::uint64_t z = state;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31);
    }
    // top 53 bits, centred in their cell: a uniform on the open interval (0, 1)
    double uniform() { return (static_cast<double>(next_u64() >> 11) + 0.5) * 0x1.0p-53; }
};

class NormalStream {
public:
    explicit NormalStream(std::uint64_t seed) : gen_(seed) {}
    double next() {
        if (spare_) {
            const double z = *spare_;
            spare_.reset();
            return z;
        }
        const double u1 = gen_.uniform(), u2 = gen_.uniform();
        const double r = std::sqrt(-2.0 * std::log(u1));
        const double a = 2.0 * std::numbers::pi * u2;
        spare_ = r * std::sin(a);
        return r * std::cos(a);
    }

private:
    SplitMix64 gen_;
    std::optional<double> spare_;
};

// W_0 = 0, W_{k+1} = W_k + sqrt(dt) Z_k on n_steps equal steps of [0, T]
inline std::vector<double> brownian_path(std::size_t n_steps, double T, NormalStream& z) {
    std::vector<double> w(n_steps + 1, 0.0);
    const double s = std::sqrt(T / static_cast<double>(n_steps));
    for (std::size_t k = 0; k < n_steps; ++k) w[k + 1] = w[k] + s * z.next();
    return w;
}

// 2^levels steps built coarse to fine: W_T, then each midpoint from N((W_l + W_r)/2, h/4)
inline std::vector<double> bridge_path(unsigned levels, double T, NormalStream& z) {
    const std::size_t n = std::size_t{1} << levels;
    const double dt = T / static_cast<double>(n);
    std::vector<double> w(n + 1, 0.0);
    w[n] = std::sqrt(T) * z.next();
    for (std::size_t step = n; step > 1; step /= 2) {
        const std::size_t half = step / 2;
        const double sd = std::sqrt(static_cast<double>(half) * dt / 2.0);
        for (std::size_t i = half; i < n; i += step) w[i] = 0.5 * (w[i - half] + w[i + half]) + sd * z.next();
    }
    return w;
}

// probability that a Brownian bridge from x0 to x1 with variance var touches the barrier
inline double bridge_crossing_probability(double x0, double x1, double barrier, double var) {
    const double prod = (x0 - barrier) * (x1 - barrier);
    return prod > 0.0 ? std::exp(-2.0 * prod / var) : 1.0;
}

// ---- Stage 2 (chapter 4): SDE stepping -------------------------------------------------------
enum class SqrtScheme { plain, full_truncation };

// exact Ornstein-Uhlenbeck transition: X' = xbar + (X - xbar) e^{-kappa dt} + sd Z
inline std::vector<double> ou_exact_path(double x0, double kappa, double xbar, double sigma, double T,
                                         std::size_t n_steps, NormalStream& z) {
    const double dt = T / static_cast<double>(n_steps), a = std::exp(-kappa * dt);
    const double sd = sigma * std::sqrt((1.0 - a * a) / (2.0 * kappa));
    std::vector<double> x(n_steps + 1, x0);
    for (std::size_t k = 0; k < n_steps; ++k) x[k + 1] = xbar + (x[k] - xbar) * a + sd * z.next();
    return x;
}

// Euler steps of dv = kappa (vbar - v) dt + eta sqrt(v) dW; plain yields NaN after a negative value,
// full truncation uses max(v, 0) in drift and diffusion and reports max(v, 0)
inline std::vector<double> sqrt_euler_path(double v0, double kappa, double vbar, double eta, double T,
                                           std::size_t n_steps, NormalStream& z, SqrtScheme scheme) {
    const double dt = T / static_cast<double>(n_steps), sdt = std::sqrt(dt);
    std::vector<double> v(n_steps + 1, v0);
    for (std::size_t k = 0; k < n_steps; ++k) {
        const double vk = scheme == SqrtScheme::plain ? v[k] : std::max(v[k], 0.0);
        v[k + 1] = v[k] + kappa * (vbar - vk) * dt + eta * std::sqrt(vk) * sdt * z.next();
    }
    if (scheme == SqrtScheme::full_truncation)
        for (auto& x : v) x = std::max(x, 0.0);
    return v;
}

inline double feller_ratio(double kappa, double vbar, double eta) { return 2.0 * kappa * vbar / (eta * eta); }

// ---- Stage 3 (chapter 26): counter-based streams and scrambled Sobol points ------------------
// Philox4x64-10 (Salmon, Moraes, Dror and Shaw 2011): a bijection of a 256-bit counter under a 128-bit key.
using Block = std::array<std::uint64_t, 4>;

inline Block philox4x64(Block c, std::array<std::uint64_t, 2> k) {
    constexpr std::uint64_t M0 = 0xD2E7470EE14C6C93ULL, M1 = 0xCA5A826395121157ULL;
    constexpr std::uint64_t W0 = 0x9E3779B97F4A7C15ULL, W1 = 0xBB67AE8584CAA73BULL;
    for (int round = 0; round < 10; ++round) {
        const unsigned __int128 p0 = static_cast<unsigned __int128>(M0) * c[0];
        const unsigned __int128 p1 = static_cast<unsigned __int128>(M1) * c[2];
        c = {static_cast<std::uint64_t>(p1 >> 64) ^ c[1] ^ k[0], static_cast<std::uint64_t>(p1),
             static_cast<std::uint64_t>(p0 >> 64) ^ c[3] ^ k[1], static_cast<std::uint64_t>(p0)};
        k = {k[0] + W0, k[1] + W1};
    }
    return c;
}

// first eight Sobol dimensions (Joe and Kuo, new-joe-kuo-6.21201): s, a, m_1..m_s
struct JoeKuo { unsigned s, a; std::array<std::uint32_t, 5> m; };
inline constexpr std::array<JoeKuo, 7> kJoeKuo{{{1, 0, {1}}, {2, 1, {1, 3}}, {3, 1, {1, 3, 1}}, {3, 2, {1, 1, 1}},
                                                 {4, 1, {1, 1, 3, 3}}, {4, 4, {1, 3, 5, 13}}, {5, 2, {1, 1, 5, 5, 17}}}};

inline std::array<std::uint32_t, 32> sobol_directions(unsigned dim) {
    std::array<std::uint32_t, 32> v{};
    if (dim == 0) {
        for (unsigned k = 0; k < 32; ++k) v[k] = 1u << (31 - k);
        return v;
    }
    const JoeKuo& jk = kJoeKuo.at(dim - 1);
    for (unsigned k = 0; k < jk.s; ++k) v[k] = jk.m[k] << (31 - k);
    for (unsigned i = jk.s; i < 32; ++i) {
        std::uint32_t x = v[i - jk.s] ^ (v[i - jk.s] >> jk.s);
        for (unsigned k = 1; k < jk.s; ++k)
            if ((jk.a >> (jk.s - 1 - k)) & 1u) x ^= v[i - k];
        v[i] = x;
    }
    return v;
}

// point i (Gray-code order) of dimension dim, as a 32-bit integer
inline std::uint32_t sobol_point(std::uint32_t i, unsigned dim) {
    const auto v = sobol_directions(dim);
    std::uint32_t g = i ^ (i >> 1), x = 0;
    for (unsigned b = 0; g != 0; ++b, g >>= 1)
        if (g & 1u) x ^= v[b];
    return x;
}

inline std::uint64_t mix64(std::uint64_t z) {
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

// Owen (nested uniform) scrambling: digit l is flipped by the hashed bit of tree node (dim, l, top l digits)
inline std::uint32_t owen_scramble(std::uint32_t x, unsigned dim, std::uint64_t seed) {
    std::uint32_t y = x;
    for (unsigned lev = 0; lev < 32; ++lev) {
        const std::uint64_t prefix = lev == 0 ? 0 : (static_cast<std::uint64_t>(x) >> (32 - lev));
        const std::uint64_t node = (static_cast<std::uint64_t>(dim) << 40) ^ (static_cast<std::uint64_t>(lev) << 32) ^ prefix;
        const std::uint64_t bit = mix64(seed ^ mix64(node)) >> 63;
        y ^= static_cast<std::uint32_t>(bit << (31 - lev));
    }
    return y;
}

}  // namespace firm::mcengine
