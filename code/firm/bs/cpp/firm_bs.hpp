#pragma once
// firm.bs -- Black-Scholes and Black kernels (build of Chapter 3, One Quant Book 5), C++20.
// Twin of firm_bs.py: price on the forward, analytic Greeks, implied volatility by Newton's
// method safeguarded by bisection inside the no-arbitrage bracket.
#include <cmath>
#include <numbers>
#include <stdexcept>

namespace firm::bs {

enum class Right { Call, Put };

inline double ncdf(double x) { return 0.5 * std::erfc(-x / std::numbers::sqrt2); }
inline double npdf(double x) { return std::exp(-0.5 * x * x) / std::sqrt(2.0 * std::numbers::pi); }

inline double black(double fwd, double strike, double t, double df, double vol, Right right) {
    const double sign = right == Right::Call ? 1.0 : -1.0;
    if (t <= 0.0 || vol <= 0.0) return df * std::max(sign * (fwd - strike), 0.0);
    const double s = vol * std::sqrt(t);
    const double d1 = std::log(fwd / strike) / s + 0.5 * s;
    return df * sign * (fwd * ncdf(sign * d1) - strike * ncdf(sign * (d1 - s)));
}

inline double bs(double spot, double strike, double t, double r, double q, double vol, Right right) {
    return black(spot * std::exp((r - q) * t), strike, t, std::exp(-r * t), vol, right);
}

struct Greeks {
    double delta, gamma, vega, theta, rho, vanna, volga;
};

inline Greeks greeks(double spot, double strike, double t, double r, double q, double vol, Right right) {
    const double sign = right == Right::Call ? 1.0 : -1.0;
    const double sq = std::sqrt(t), s = vol * sq;
    const double d1 = (std::log(spot / strike) + (r - q) * t) / s + 0.5 * s, d2 = d1 - s;
    const double eq = std::exp(-q * t), er = std::exp(-r * t), pdf = npdf(d1);
    Greeks g{};
    g.delta = sign * eq * ncdf(sign * d1);
    g.gamma = eq * pdf / (spot * s);
    g.vega = spot * eq * pdf * sq;
    g.theta = -spot * eq * pdf * vol / (2.0 * sq) - sign * r * strike * er * ncdf(sign * d2) +
              sign * q * spot * eq * ncdf(sign * d1);
    g.rho = sign * strike * t * er * ncdf(sign * d2);
    g.vanna = -eq * pdf * d2 / vol;
    g.volga = g.vega * d1 * d2 / vol;
    return g;
}

inline double implied_vol(double price, double fwd, double strike, double t, double df, Right right,
                          double tol = 1e-12, int max_iter = 100) {
    const double sign = right == Right::Call ? 1.0 : -1.0;
    const double lo_p = df * std::max(sign * (fwd - strike), 0.0);
    const double hi_p = df * (right == Right::Call ? fwd : strike);
    if (!(lo_p <= price && price < hi_p)) throw std::domain_error("price outside the arbitrage bounds");
    if (price - lo_p < 1e-15 * df * std::max(fwd, strike)) return 0.0;
    const double x = std::log(fwd / strike);
    const double c = price / df - 0.5 * sign * (fwd - strike);
    const double disc = std::max(c * c - (fwd - strike) * (fwd - strike) / std::numbers::pi, 0.0);
    const double guess = std::sqrt(2.0 * std::numbers::pi) / (fwd + strike) * (c + std::sqrt(disc)) / std::sqrt(t);
    double lo = 0.0, hi = 1.0;
    while (black(fwd, strike, t, df, hi, right) < price) {
        hi *= 2.0;
        if (hi > 100.0) throw std::domain_error("no volatility below 10000%");
    }
    double v = (guess > 0.0 && std::fabs(x) < 1.0) ? std::min(std::max(guess, 1e-4), hi) : 0.5 * hi;
    for (int i = 0; i < max_iter; ++i) {
        const double f = black(fwd, strike, t, df, v, right) - price;
        if (std::fabs(f) < tol * std::max(price, 1e-300) || hi - lo < 1e-15) return v;
        (f > 0 ? hi : lo) = v;
        const double s = v * std::sqrt(t);
        const double vega = df * fwd * npdf(x / s + 0.5 * s) * std::sqrt(t);
        const double step = vega > 0.0 ? v - f / vega : -1.0;
        v = (lo < step && step < hi) ? step : 0.5 * (lo + hi);
    }
    return v;
}

}  // namespace firm::bs
