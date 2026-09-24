// firm.fdpricer (C++20 twin): American put by Crank-Nicolson in log-spot on a uniform grid, Rannacher
// start-up and the Brennan-Schwartz algorithm; the same arithmetic as firm_fdpricer.py (grid="uniform",
// smoothing=False), so the two agree to rounding.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>

namespace firm::fdpricer {

struct Coefficients {
    std::vector<double> lo, di, up;
};

inline std::vector<double> uniform_grid(double s0, double vol, double t, std::size_t m, double width = 5.0) {
    const double half = width * vol * std::sqrt(t);
    std::vector<double> x(m + 1);
    for (std::size_t i = 0; i <= m; ++i)
        x[i] = std::log(s0) - half + (2.0 * half) * static_cast<double>(i) / static_cast<double>(m);
    return x;
}

inline Coefficients operator_coefficients(const std::vector<double>& x, double r, double q, double vol) {
    const double nu = r - q - 0.5 * vol * vol, d2 = vol * vol;
    Coefficients c;
    for (std::size_t i = 1; i + 1 < x.size(); ++i) {
        const double hm = x[i] - x[i - 1], hp = x[i + 1] - x[i];
        c.lo.push_back(d2 / (hm * (hm + hp)) - nu * hp / (hm * (hm + hp)));
        c.di.push_back(-d2 / (hm * hp) + nu * (hp - hm) / (hm * hp) - r);
        c.up.push_back(d2 / (hp * (hm + hp)) + nu * hm / (hp * (hm + hp)));
    }
    return c;
}

// Tridiagonal solve with V >= g, eliminating from the top and projecting on the way up.
inline std::vector<double> brennan_schwartz(const std::vector<double>& a, const std::vector<double>& b,
                                            const std::vector<double>& c, const std::vector<double>& d,
                                            const std::vector<double>& g) {
    const std::size_t n = d.size();
    std::vector<double> bp(n), dp(n), out(n);
    bp[n - 1] = b[n - 1];
    dp[n - 1] = d[n - 1];
    for (std::size_t k = n - 1; k-- > 0;) {
        const double f = c[k] / bp[k + 1];
        bp[k] = b[k] - f * a[k + 1];
        dp[k] = d[k] - f * dp[k + 1];
    }
    out[0] = std::max(dp[0] / bp[0], g[0]);
    for (std::size_t i = 1; i < n; ++i) out[i] = std::max((dp[i] - a[i] * out[i - 1]) / bp[i], g[i]);
    return out;
}

inline double american_put(double s0, double k, double t, double r, double q, double vol, std::size_t m,
                           std::size_t n_t, int rannacher = 2) {
    const std::vector<double> x = uniform_grid(s0, vol, t, m);
    const std::size_t n = x.size();
    std::vector<double> s(n), g(n), v(n);
    for (std::size_t i = 0; i < n; ++i) {
        s[i] = std::exp(x[i]);
        g[i] = std::max(k - s[i], 0.0);
        v[i] = g[i];
    }
    const Coefficients co = operator_coefficients(x, r, q, vol);
    const double dt = t / static_cast<double>(n_t);
    double tau = 0.0;
    std::size_t step = 0;
    int implicit_half = 2 * rannacher;
    const std::size_t ni = n - 2;
    std::vector<double> a(ni), b(ni), c(ni), rhs(ni), gi(g.begin() + 1, g.end() - 1);
    while (step < n_t) {
        double h = dt, theta = 0.5;
        if (implicit_half > 0) {
            h = 0.5 * dt;
            theta = 1.0;
            --implicit_half;
        }
        tau += h;
        for (std::size_t i = 0; i < ni; ++i) {
            rhs[i] = v[i + 1] + (1 - theta) * h * (co.lo[i] * v[i] + co.di[i] * v[i + 1] + co.up[i] * v[i + 2]);
            a[i] = -theta * h * co.lo[i];
            b[i] = 1 - theta * h * co.di[i];
            c[i] = -theta * h * co.up[i];
        }
        const double vl = k - s[0], vu = 0.0;
        rhs[0] -= a[0] * vl;
        rhs[ni - 1] -= c[ni - 1] * vu;
        a[0] = 0.0;
        c[ni - 1] = 0.0;
        const std::vector<double> inner = brennan_schwartz(a, b, c, rhs, gi);
        v[0] = vl;
        v[n - 1] = vu;
        for (std::size_t i = 0; i < ni; ++i) v[i + 1] = inner[i];
        for (std::size_t i = 0; i < n; ++i) v[i] = std::max(v[i], g[i]);
        if (std::fabs(tau - static_cast<double>(step + 1) * dt) < 1e-12 * std::max(1.0, t)) ++step;
    }
    // value at s0: quadratic through the three nodes around it
    const double x0 = std::log(s0);
    std::size_t i = static_cast<std::size_t>(std::lower_bound(x.begin(), x.end(), x0) - x.begin());
    i = std::clamp<std::size_t>(i, 1, n - 2);
    const double x1 = x[i - 1], x2 = x[i], x3 = x[i + 1];
    return v[i - 1] * (x0 - x2) * (x0 - x3) / ((x1 - x2) * (x1 - x3)) +
           v[i] * (x0 - x1) * (x0 - x3) / ((x2 - x1) * (x2 - x3)) +
           v[i + 1] * (x0 - x1) * (x0 - x2) / ((x3 - x1) * (x3 - x2));
}

}  // namespace firm::fdpricer
