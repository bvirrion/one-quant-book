"""firm.pairsel -- pair selection and pair trading rules (build of One Quant Book 8, chapter 4).

Selection by distance (the sum of squared differences of normalised price paths, Gatev, Goetzmann and Rouwenhorst),
by the Engle-Granger residual test vectorised over many pairs with p-values from a simulated null and Benjamini-Hochberg
control of the false discovery rate, and a Gaussian-copula mispricing index; the distance rule (open at k formation
standard deviations, close at the next crossing) on daily returns with drifting positions; synthetic-twin baskets by
ridge regression. NumPy only.

API (stable):
    normalise(P)                         (T, N) prices -> cumulative return index starting at 1
    top_pairs(N, k)                      the k pairs of distinct stocks with the smallest distances, greedy (no stock
                                         twice): list of (i, j, distance)
    eg_tau(y, x)                         (P,) Engle-Granger tau of log series y on x (T, P): OLS with constant, then a
                                         Dickey-Fuller regression of the residual's change on its lag
    eg_null(T, reps, seed)               sorted null taus of two independent random walks of length T
    pvalue(tau, null)                    left-tail p-values
    bh(p, q)                             Benjamini-Hochberg rejections at false discovery rate q
    trade_pair(ra, rb, spread, sd, k, cost)
                                         the distance rule on one pair: (daily P&L on $1 per leg, trades, opened,
                                         side still open at the end)
    copula_fit(ra, rb)                   {'rho', 'xa', 'xb'} normal-score correlation and sorted formation returns
    copula_h(fit, ra, rb)                P(U_a <= u_a | U_b = u_b) under the Gaussian copula
    twin(y, X, lam)                      ridge weights of y on the columns of X (no constant)
"""
from __future__ import annotations

import math

import numpy as np


def normalise(P):
    P = np.asarray(P, float)
    return P / P[0]


def top_pairs(N, k: int):
    N = np.asarray(N, float)
    sq = (N * N).sum(axis=0)
    D = sq[:, None] + sq[None, :] - 2 * N.T @ N
    i, j = np.triu_indices(N.shape[1], 1)
    order = np.argsort(D[i, j], kind="stable")
    used, out = set(), []
    for o in order:
        a, b = int(i[o]), int(j[o])
        if a in used or b in used:
            continue
        out.append((a, b, float(D[a, b])))
        used |= {a, b}
        if len(out) == k:
            break
    return out


def eg_tau(y, x):
    y, x = np.asarray(y, float), np.asarray(x, float)
    xm, ym = x.mean(axis=0), y.mean(axis=0)
    beta = ((x - xm) * (y - ym)).sum(axis=0) / ((x - xm) ** 2).sum(axis=0)
    u = y - ym - beta * (x - xm)
    du, lag = np.diff(u, axis=0), u[:-1]
    rho = (lag * du).sum(axis=0) / (lag * lag).sum(axis=0)
    e = du - rho * lag
    se = np.sqrt((e * e).sum(axis=0) / (len(du) - 1) / (lag * lag).sum(axis=0))
    return rho / se


def eg_null(T: int, reps: int = 20000, seed: int = 4):
    rng = np.random.default_rng(seed)
    y = np.cumsum(rng.standard_normal((T, reps)), axis=0)
    x = np.cumsum(rng.standard_normal((T, reps)), axis=0)
    return np.sort(eg_tau(y, x))


def pvalue(tau, null):
    return np.searchsorted(null, np.asarray(tau, float), side="right") / len(null)


def bh(p, q: float = 0.05):
    p = np.asarray(p, float)
    order = np.argsort(p)
    m = len(p)
    ok = p[order] <= q * np.arange(1, m + 1) / m
    out = np.zeros(m, bool)
    if ok.any():
        out[order[: np.flatnonzero(ok).max() + 1]] = True
    return out


def trade_pair(ra, rb, spread, sd: float, k: float = 2.0, cost: float = 0.0):
    """spread[t] known at the close of t; open when |spread| > k sd (long the lower leg, short the higher, $1 each),
    close at the next change of sign; positions drift with returns; P&L of day t + 1 from positions set at t."""
    ra, rb, spread = (np.nan_to_num(np.asarray(v, float)) for v in (ra, rb, spread))
    T = len(spread)
    pnl = np.zeros(T)
    wa = wb = 0.0
    side, trades, opened = 0, 0, 0
    for t in range(T - 1):
        new = side
        if side != 0 and np.sign(spread[t]) != side:
            new = 0
        if side == 0 and abs(spread[t]) > k * sd:
            new = int(np.sign(spread[t]))              # +1: a above b, so short a and buy b
        if new != side:
            traded = abs(wa) + abs(wb)
            if new != 0:
                wa, wb = -float(new), float(new)
                traded += 2.0
                opened += 1
            else:
                wa = wb = 0.0
            pnl[t] -= cost * traded
            trades += 1
            side = new
        pnl[t + 1] += wa * ra[t + 1] + wb * rb[t + 1]
        wa, wb = wa * (1 + ra[t + 1]), wb * (1 + rb[t + 1])
    return pnl, trades, opened, side


def _ncdf(z):
    return 0.5 * (1 + np.vectorize(math.erf)(np.asarray(z, float) / math.sqrt(2)))


def _ninv(u):
    """Inverse normal CDF (Acklam's rational approximation, relative error below 1.2e-9)."""
    u = np.clip(np.asarray(u, float), 1e-10, 1 - 1e-10)
    a = (-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.383577518672690e2, -3.066479806614716e1,
         2.506628277459239)
    b = (-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1)
    c = (-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968,
         2.938163982698783)
    d = (7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416)
    q = np.minimum(u, 1 - u)
    t = np.sqrt(-2 * np.log(q))
    tail = (((((c[0] * t + c[1]) * t + c[2]) * t + c[3]) * t + c[4]) * t + c[5]) / \
        ((((d[0] * t + d[1]) * t + d[2]) * t + d[3]) * t + 1)
    r = (u - 0.5) ** 2
    mid = (u - 0.5) * (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) / \
        (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    return np.where(q < 0.02425, np.where(u < 0.5, tail, -tail), mid)


def _ecdf(sorted_x, x):
    n = len(sorted_x)
    return (np.searchsorted(sorted_x, np.asarray(x, float), side="right") + 0.5) / (n + 1)


def copula_fit(ra, rb):
    xa, xb = np.sort(np.asarray(ra, float)), np.sort(np.asarray(rb, float))
    za, zb = _ninv(_ecdf(xa, ra)), _ninv(_ecdf(xb, rb))
    return {"rho": float(np.corrcoef(za, zb)[0, 1]), "xa": xa, "xb": xb}


def copula_h(fit, ra, rb):
    za, zb = _ninv(_ecdf(fit["xa"], ra)), _ninv(_ecdf(fit["xb"], rb))
    rho = fit["rho"]
    return _ncdf((za - rho * zb) / math.sqrt(1 - rho * rho))


def twin(y, X, lam: float):
    y, X = np.asarray(y, float), np.asarray(X, float)
    return np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ y)
