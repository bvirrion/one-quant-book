"""firm.propagator -- transient impact: the propagator model and its no-manipulation conditions (build of One Quant
Book 10, chapter 12).

Discrete time is counted in trades: eps_t is the sign of trade t, p_t the mid just before it. The propagator model
writes p_t = sum_{s < t} G(t - s) eps_s + noise, so that dp_t = p_{t+1} - p_t = sum_{n >= 0} K(n) eps_{t-n} with
K(n) = G(n + 1) - G(n) (G(0) = 0).

API (stable):
    sign_acf(eps, maxlag)                  C(l) = E[eps_t eps_{t+l}], l = 0..maxlag
    response(eps, p, maxlag)               R(l) = E[eps_t (p_{t+l} - p_t)], l = 0..maxlag
    fit_kernel(eps, p, maxlag)             K from the Toeplitz system E[eps_{t-k} dp_t] = sum_n K(n) C(|k - n|),
                                           solved by Levinson recursion; returns (K, G) with G(l) = K(0) + ... + K(l-1)
    propagate(eps, G)                      model prices p_t = sum_{s<t} G(t - s) eps_s (G beyond its length: last value)
    impact_matrix(times, kernel)           Gamma_ij = kernel(|t_i - t_j|): the cost of trades x is x' Gamma x / 2
                                           (instantaneous impact kernel(0) on the diagonal)
    round_trip(Gamma)                      the most negative cost of a round trip (sum x = 0, |x| = 1): -lambda_min / 2
                                           of Gamma on the orthogonal of the ones (positive = a profitable round trip)
    optimal_liquidation(Gamma, X)          the trades that minimise the cost of selling X:
                                           Gamma^-1 1 X / (1' Gamma^-1 1); any trade of the other sign is a
                                           transaction-triggered manipulation
    obizhaeva_wang(X, rho, T)              the continuous-time optimum with exponential resilience rho: (first block,
                                           rate, last block) = X (1, rho, 1) / (rho T + 2)
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_toeplitz


def sign_acf(eps, maxlag: int) -> np.ndarray:
    e = np.asarray(eps, float)
    return np.array([1.0] + [float(np.mean(e[:-lag] * e[lag:])) for lag in range(1, maxlag + 1)])


def response(eps, p, maxlag: int) -> np.ndarray:
    e, p = np.asarray(eps, float), np.asarray(p, float)
    return np.array([0.0] + [float(np.mean(e[:-lag] * (p[lag:] - p[:-lag]))) for lag in range(1, maxlag + 1)])


def fit_kernel(eps, p, maxlag: int):
    e, p = np.asarray(eps, float), np.asarray(p, float)
    dp = np.diff(p)                                     # dp_t = p_{t+1} - p_t
    e = e[: len(dp)]
    c = sign_acf(e, maxlag)
    s = np.array([float(np.mean(e[: len(e) - k] * dp[k:])) if k else float(np.mean(e * dp))
                  for k in range(maxlag + 1)])
    k = solve_toeplitz(c, s)                            # Levinson recursion
    return k, np.concatenate([[0.0], np.cumsum(k)])


def propagate(eps, G) -> np.ndarray:
    e = np.asarray(eps, float)
    g = np.asarray(G, float)
    n = len(e)
    full = np.concatenate([g, np.full(max(0, n - len(g) + 1), g[-1])])[: n + 1]
    k = np.diff(full)                                   # K(l) for l = 0..n-1
    return np.concatenate([[0.0], np.cumsum(np.convolve(e, k)[:n])])[:n]


def impact_matrix(times, kernel) -> np.ndarray:
    t = np.asarray(times, float)
    return kernel(np.abs(t[:, None] - t[None, :]))


def round_trip(gamma) -> float:
    n = len(gamma)
    q, _ = np.linalg.qr(np.column_stack([np.ones(n), np.eye(n)[:, : n - 1]]))
    b = q[:, 1:]                                        # an orthonormal basis of sum x = 0
    lam = np.linalg.eigvalsh(b.T @ gamma @ b)
    return float(-lam[0] / 2)


def optimal_liquidation(gamma, x_total: float) -> np.ndarray:
    one = np.ones(len(gamma))
    w = np.linalg.solve(gamma, one)
    return w * x_total / (one @ w)


def obizhaeva_wang(x_total: float, rho: float, horizon: float) -> tuple[float, float, float]:
    d = rho * horizon + 2
    return x_total / d, rho * x_total / d, x_total / d
