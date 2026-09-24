// firm.pde (C++20): the one-dimensional finite-difference kernel of the miniature firm. One Quant Book 4, ch. 27.
// u_tau = a u_xx + b u_x - c u on a (possibly non-uniform) grid, theta scheme with Rannacher start-up and zero-gamma
// (linear) boundaries; the same operations in the same order as firm_pde.py and the Rust crate.
#pragma once
#include <cstddef>
#include <vector>

namespace firm::pde {

struct Tridiag {
    std::vector<double> lo, di, up;
};

// coefficients of L at the interior nodes 1..n-1: (L u)_i = lo u_{i-1} + di u_i + up u_{i+1}
inline Tridiag operator_1d(const std::vector<double>& x, double a, double b, double c) {
    const std::size_t m = x.size() - 2;
    Tridiag L{std::vector<double>(m), std::vector<double>(m), std::vector<double>(m)};
    for (std::size_t k = 0; k < m; ++k) {
        const double hm = x[k + 1] - x[k], hp = x[k + 2] - x[k + 1];
        const double lo = 2 * a / (hm * (hm + hp)), up = 2 * a / (hp * (hm + hp));
        L.lo[k] = lo + (-b * hp) / (hm * (hm + hp));
        L.up[k] = up + b * hm / (hp * (hm + hp));
        L.di[k] = (-lo - up - c) + b * (hp - hm) / (hm * hp);
    }
    return L;
}

// Thomas algorithm; the matrix is overwritten only in the scratch vectors
inline std::vector<double> thomas(const std::vector<double>& lo, const std::vector<double>& di,
                                  const std::vector<double>& up, const std::vector<double>& rhs) {
    const std::size_t n = di.size();
    std::vector<double> cp(n), dp(n), out(n);
    cp[0] = up[0] / di[0];
    dp[0] = rhs[0] / di[0];
    for (std::size_t i = 1; i < n; ++i) {
        const double m = di[i] - lo[i] * cp[i - 1];
        cp[i] = i < n - 1 ? up[i] / m : 0.0;
        dp[i] = (rhs[i] - lo[i] * dp[i - 1]) / m;
    }
    out[n - 1] = dp[n - 1];
    for (std::size_t i = n - 1; i-- > 0;) out[i] = dp[i] - cp[i] * out[i + 1];
    return out;
}

// one theta step (I - theta dt L) u' = (I + (1 - theta) dt L) u with linear extrapolation at both ends
inline std::vector<double> theta_step(const std::vector<double>& x, const std::vector<double>& u, const Tridiag& L,
                                      double dt, double theta) {
    const std::size_t m = x.size() - 2;
    std::vector<double> rhs(m), alo(m), adi(m), aup(m);
    for (std::size_t k = 0; k < m; ++k) {
        rhs[k] = u[k + 1] + (1 - theta) * dt * (L.lo[k] * u[k] + L.di[k] * u[k + 1] + L.up[k] * u[k + 2]);
        alo[k] = -theta * dt * L.lo[k];
        adi[k] = 1 - theta * dt * L.di[k];
        aup[k] = -theta * dt * L.up[k];
    }
    const std::size_t n = x.size() - 1;
    const double l0 = x[1] - x[0], l1 = x[2] - x[1], r0 = x[n] - x[n - 1], r1 = x[n - 1] - x[n - 2];
    adi[0] += alo[0] * (1 + l0 / l1);
    aup[0] += alo[0] * (-l0 / l1);
    adi[m - 1] += aup[m - 1] * (1 + r0 / r1);
    alo[m - 1] += aup[m - 1] * (-r0 / r1);
    const auto inner = thomas(alo, adi, aup, rhs);
    std::vector<double> out(n + 1);
    for (std::size_t k = 0; k < m; ++k) out[k + 1] = inner[k];
    out[0] = out[1] - (out[2] - out[1]) * l0 / l1;
    out[n] = out[n - 1] + (out[n - 1] - out[n - 2]) * r0 / r1;
    return out;
}

// march from the payoff to tau: `rannacher` implicit half steps replace the first rannacher / 2 steps
inline std::vector<double> solve_1d(const std::vector<double>& x, std::vector<double> u, double a, double b, double c,
                                    double tau, int n_steps, double theta, int rannacher) {
    const Tridiag L = operator_1d(x, a, b, c);
    const double dt = tau / n_steps;
    for (int k = 0; k < rannacher; ++k) u = theta_step(x, u, L, dt / 2, 1.0);
    for (int k = 0; k < n_steps - rannacher / 2; ++k) u = theta_step(x, u, L, dt, theta);
    return u;
}

}  // namespace firm::pde
