// firm.hawkes (C++20): exponential-kernel Hawkes process. One Quant Book 4, chapter 7.
// lambda_t = mu + sum_{t_i < t} alpha exp(-beta (t - t_i)); branching ratio alpha / beta.
// Simulation by Ogata's thinning, O(n) log-likelihood and compensator: the hot loops of a live
// order-flow model. Self-contained (its own SplitMix64 generator).
#pragma once
#include <cmath>
#include <cstdint>
#include <span>
#include <vector>

namespace firm::hawkes {

struct Params {
    double mu, alpha, beta;
    [[nodiscard]] double branching() const { return alpha / beta; }
    [[nodiscard]] double mean_intensity() const { return mu / (1.0 - branching()); }
};

class Rng {  // SplitMix64, uniforms on (0, 1)
public:
    explicit Rng(std::uint64_t seed) : s_(seed) {}
    double uniform() {
        s_ += 0x9E3779B97F4A7C15ULL;
        std::uint64_t z = s_;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        z ^= z >> 31;
        return (static_cast<double>(z >> 11) + 0.5) * 0x1.0p-53;
    }
    double exponential(double rate) { return -std::log(uniform()) / rate; }

private:
    std::uint64_t s_;
};

// Ogata's thinning: between events the intensity decays, so its value after the last event bounds it
inline std::vector<double> simulate_thinning(const Params& p, double T, Rng& rng) {
    std::vector<double> out;
    double t = 0.0, excite = 0.0;
    for (;;) {
        const double bound = p.mu + excite, w = rng.exponential(bound);
        t += w;
        if (t > T) break;
        excite *= std::exp(-p.beta * w);
        if (rng.uniform() * bound <= p.mu + excite) {
            out.push_back(t);
            excite += p.alpha;
        }
    }
    return out;
}

// sum_i log lambda(t_i) - int_0^T lambda dt, with A_i = e^{-beta (t_i - t_{i-1})} (1 + A_{i-1})
inline double loglik(const Params& p, std::span<const double> times, double T) {
    double total = 0.0, a = 0.0, integral = p.mu * T;
    for (std::size_t i = 0; i < times.size(); ++i) {
        if (i > 0) a = std::exp(-p.beta * (times[i] - times[i - 1])) * (1.0 + a);
        total += std::log(p.mu + p.alpha * a);
        integral += p.alpha / p.beta * (1.0 - std::exp(-p.beta * (T - times[i])));
    }
    return total - integral;
}

// Lambda(t_i): time-rescaled event times, a unit-rate Poisson process if the model is right
inline std::vector<double> compensator(const Params& p, std::span<const double> times) {
    std::vector<double> out(times.size());
    double a = 0.0;
    for (std::size_t i = 0; i < times.size(); ++i) {
        if (i > 0) a = std::exp(-p.beta * (times[i] - times[i - 1])) * (1.0 + a);
        out[i] = p.mu * times[i] + p.alpha / p.beta * (static_cast<double>(i) - a);
    }
    return out;
}

}  // namespace firm::hawkes
