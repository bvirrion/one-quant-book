"""firm.allocation -- allocation beyond plain mean-variance (build of One Quant Book 7, chapter 26).

Robust mean-variance with an ellipsoidal uncertainty set on the alpha (the second-order-cone problem solved by
majorisation-minimisation: a sequence of quadratic programmes on firm.portopt.qp, each majorising the square-root
term); the Black-Litterman posterior (He and Litterman's form); risk contributions, risk budgeting and the equal risk
contribution portfolio by Newton's method (Maillard, Roncalli and Teiletche); hierarchical risk parity (single-linkage
clustering of correlation distances, quasi-diagonalisation, recursive bisection; Lopez de Prado); and the aim
portfolio of Garleanu and Pedersen for quadratic trading costs and signals that decay at known rates. NumPy only.

API (stable):
    mean_variance(alpha, Sigma, gamma, lo, hi, budget)          long-only (or boxed) mean-variance by QP
    robust_mv(alpha, Sigma, Omega, kappa, gamma, lo, hi, budget, iters)
                                         max alpha'w - kappa sqrt(w'Omega w) - gamma/2 w'Sigma w over the same set
    implied_returns(Sigma, w_mkt, gamma) pi = gamma Sigma w_mkt
    black_litterman(pi, Sigma, P, q, Omega, tau)   (posterior mean, posterior covariance of returns)
    risk_contributions(w, Sigma)         w_i (Sigma w)_i / (w'Sigma w): shares that sum to one
    risk_budget(Sigma, b, tol)           long-only weights whose risk contributions are b (sum 1), Newton
    erc(Sigma)                           risk_budget with equal budgets
    hrp(Sigma)                           hierarchical risk parity weights
    gp_trade_rate(gamma, lam, rho)       a / lam: the share of the gap to the aim traded each period
    gp_aim(Sigma, signals, phis, gamma, a)   (gamma Sigma)^-1 sum_k B_k f_k / (1 + phi_k a / gamma)
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "portopt"))
from firm_portopt import qp  # noqa: E402


def _box_qp(P, q, lo, hi, budget):
    n = len(q)
    A = np.ones((1, n)) if budget is not None else None
    b = np.array([budget]) if budget is not None else None
    G = np.vstack([np.eye(n), -np.eye(n)])
    h = np.r_[np.broadcast_to(hi, (n,)), -np.broadcast_to(lo, (n,))]
    return qp(P, q, A, b, G, h, tol=1e-10)["x"]


def mean_variance(alpha, Sigma, gamma: float, lo=0.0, hi=1.0, budget=1.0):
    return _box_qp(gamma * np.asarray(Sigma, float), -np.asarray(alpha, float), lo, hi, budget)


def robust_mv(alpha, Sigma, Omega, kappa: float, gamma: float, lo=0.0, hi=1.0, budget=1.0, iters: int = 50):
    """sqrt(x) <= x / (2 s) + s / 2 with equality at x = s^2: each step maximises the minorant alpha'w -
    kappa w'Omega w / (2 s) - gamma/2 w'Sigma w, s = sqrt(w_prev' Omega w_prev); the objective rises monotonically."""
    alpha, Sigma, Omega = (np.asarray(a, float) for a in (alpha, Sigma, Omega))
    w = mean_variance(alpha, Sigma, gamma, lo, hi, budget)
    for _ in range(iters):
        s = max(math.sqrt(float(w @ Omega @ w)), 1e-12)
        new = _box_qp(gamma * Sigma + kappa / s * Omega, -alpha, lo, hi, budget)
        if np.abs(new - w).max() < 1e-10:
            return new
        w = new
    return w


def implied_returns(Sigma, w_mkt, gamma: float):
    return gamma * np.asarray(Sigma, float) @ np.asarray(w_mkt, float)


def black_litterman(pi, Sigma, P, q, Omega, tau: float = 0.05):
    """Posterior mean mu = [(tau S)^-1 + P' O^-1 P]^-1 [(tau S)^-1 pi + P' O^-1 q] and covariance S + M, M the
    posterior covariance of the mean."""
    pi, Sigma, P, q, Omega = (np.atleast_1d(np.asarray(a, float)) for a in (pi, Sigma, P, q, Omega))
    P = np.atleast_2d(P)
    Omega = np.atleast_2d(Omega)
    ti = np.linalg.inv(tau * Sigma)
    oi = np.linalg.inv(Omega)
    M = np.linalg.inv(ti + P.T @ oi @ P)
    mu = M @ (ti @ pi + P.T @ oi @ q)
    return mu, Sigma + M


def risk_contributions(w, Sigma):
    w = np.asarray(w, float)
    m = np.asarray(Sigma, float) @ w
    return w * m / float(w @ m)


def risk_budget(Sigma, b, tol: float = 1e-12, max_iter: int = 100):
    """Minimise y'Sigma y / 2 - sum b_i log y_i (strictly convex on y > 0) by Newton's method with backtracking;
    at the optimum y_i (Sigma y)_i = b_i, so w = y / sum y has risk contributions b."""
    S, b = np.asarray(Sigma, float), np.asarray(b, float)
    y = b / np.sqrt(np.diag(S))
    f = lambda v: 0.5 * v @ S @ v - b @ np.log(v)  # noqa: E731
    for _ in range(max_iter):
        g = S @ y - b / y
        H = S + np.diag(b / y**2)
        d = -np.linalg.solve(H, g)
        if -g @ d < tol:
            break
        t = 1.0
        while np.any(y + t * d <= 0) or f(y + t * d) > f(y) + 0.25 * t * (g @ d):
            t *= 0.5
        y = y + t * d
    return y / y.sum()


def erc(Sigma):
    n = len(Sigma)
    return risk_budget(Sigma, np.full(n, 1.0 / n))


def _linkage_order(dist):
    """Single-linkage agglomerative clustering; returns the leaf order of the dendrogram."""
    n = len(dist)
    clusters = {i: [i] for i in range(n)}
    D = dist.astype(float).copy()
    np.fill_diagonal(D, np.inf)
    active = list(range(n))
    while len(active) > 1:
        sub = D[np.ix_(active, active)]
        i, j = np.unravel_index(np.argmin(sub), sub.shape)
        a, b = active[i], active[j]
        clusters[a] = clusters[a] + clusters[b]
        D[a, :] = np.minimum(D[a, :], D[b, :])
        D[:, a] = D[a, :]
        D[a, a] = np.inf
        active.remove(b)
    return clusters[active[0]]


def hrp(Sigma):
    S = np.asarray(Sigma, float)
    sd = np.sqrt(np.diag(S))
    corr = S / np.outer(sd, sd)
    dist = np.sqrt(np.clip(0.5 * (1 - corr), 0, None))
    dd = np.sqrt(((dist[:, None, :] - dist[None, :, :]) ** 2).sum(axis=2))   # distance between distance columns
    order = _linkage_order(dd)
    w = np.ones(len(S))
    stack = [order]
    while stack:
        items = stack.pop()
        if len(items) < 2:
            continue
        half = len(items) // 2
        left, right = items[:half], items[half:]

        def cvar(idx):
            sub = S[np.ix_(idx, idx)]
            ivp = 1.0 / np.diag(sub)
            ivp /= ivp.sum()
            return float(ivp @ sub @ ivp)
        vl, vr = cvar(left), cvar(right)
        a = 1 - vl / (vl + vr)
        w[left] *= a
        w[right] *= 1 - a
        stack += [left, right]
    return w / w.sum()


def gp_trade_rate(gamma: float, lam: float, rho: float) -> float:
    """Garleanu-Pedersen: a solves a^2 (1-rho) + a (gamma (1-rho) + lam rho) - gamma lam (1-rho) = 0 (costs
    lam/2 dx'Sigma dx, risk gamma/2 x'Sigma x, discount 1 - rho); the book trades a/lam of the gap each period."""
    c = gamma * (1 - rho) + lam * rho
    a = (-c + math.sqrt(c * c + 4 * gamma * lam * (1 - rho) ** 2)) / (2 * (1 - rho))
    return a / lam


def gp_aim(Sigma, signals, phis, gamma: float, a: float):
    """The aim portfolio: the Markowitz portfolio of each signal's expected return, down-weighted by 1 + phi a /
    gamma for a signal whose predictive power decays at rate phi per period (signals: list of (n,) expected-return
    contributions, i.e. B_k f_k)."""
    total = sum(np.asarray(s, float) / (1 + phi * a / gamma) for s, phi in zip(signals, phis, strict=True))
    return np.linalg.solve(gamma * np.asarray(Sigma, float), total)
