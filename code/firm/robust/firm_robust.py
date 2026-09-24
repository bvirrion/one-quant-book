"""firm.robust -- robust statistics and tail estimation (One Quant Book 4, chapter 15).

Robust location and scale, winsorising and trimming, rank correlations and tail dependence, the Hill
estimator, and the generalised Pareto fit for peaks over a threshold with its tail quantiles.
NumPy only; the minimiser is a small Nelder-Mead so that the module stands alone.

API (stable):
    mad(x)                          median absolute deviation, scaled to the normal standard deviation
    qn_scale(x)                     Rousseeuw-Croux Qn, scaled to the normal standard deviation
    huber_location(x, c=1.345)      Huber M-estimate of location (scale fixed at the MAD)
    winsorize(x, p), trimmed_mean(x, p)
    spearman(x, y), kendall_tau(x, y), tail_dependence(x, y, q)
    hill(x, k)                      tail index from the k largest values: (alpha, se)
    gpd_fit(excess)                 generalised Pareto (xi, beta) by maximum likelihood
    gpd_quantile(u, xi, beta, p_u, p)   the level exceeded with probability 1 - p, given P(X > u) = p_u
"""
from __future__ import annotations

import math

import numpy as np

MAD_TO_SD = 1.482602218505602        # 1 / Phi^{-1}(3/4)
QN_TO_SD = 2.2219                    # Rousseeuw and Croux's consistency constant


def mad(x) -> float:
    x = np.asarray(x, dtype=float)
    return float(MAD_TO_SD * np.median(np.abs(x - np.median(x))))


def qn_scale(x) -> float:
    """k-th smallest of the |x_i - x_j|, i < j, with k = C(h, 2), h = n // 2 + 1; found by bisection on the
    value with an O(n log n) count, so no n^2 array is formed."""
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    h = n // 2 + 1
    k = h * (h - 1) // 2

    def count(t: float) -> int:
        return int(np.sum(np.searchsorted(x, x + t, side="right") - np.arange(1, n + 1)))

    lo, hi = 0.0, float(x[-1] - x[0])
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if count(mid) >= k:
            hi = mid
        else:
            lo = mid
        if hi - lo <= 1e-15 * max(1.0, hi):
            break
    return QN_TO_SD * hi


def huber_location(x, c: float = 1.345, tol: float = 1e-12) -> float:
    x = np.asarray(x, dtype=float)
    s = mad(x)
    mu = float(np.median(x))
    if s == 0:
        return mu
    for _ in range(200):
        r = (x - mu) / s
        w = np.minimum(1.0, c / np.maximum(np.abs(r), 1e-300))
        new = float(np.sum(w * x) / np.sum(w))
        if abs(new - mu) < tol * s:
            return new
        mu = new
    return mu


def winsorize(x, p: float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    lo, hi = np.quantile(x, [p, 1 - p])
    return np.clip(x, lo, hi)


def trimmed_mean(x, p: float) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    g = int(math.floor(p * x.size))
    return float(x[g: x.size - g].mean())


def _ranks(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="mergesort")
    r = np.empty(x.size)
    r[order] = np.arange(1, x.size + 1)
    xs = x[order]                                    # average ranks over ties
    i = 0
    while i < x.size:
        j = i
        while j + 1 < x.size and xs[j + 1] == xs[i]:
            j += 1
        if j > i:
            r[order[i: j + 1]] = 0.5 * (i + j) + 1
        i = j + 1
    return r


def spearman(x, y) -> float:
    return float(np.corrcoef(_ranks(x), _ranks(y))[0, 1])


def kendall_tau(x, y, block: int = 2000) -> float:
    """Kendall's tau-a by blocks of pairs (O(n^2) work, O(n * block) memory)."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    n = x.size
    s = 0.0
    for a in range(0, n, block):
        b = min(n, a + block)
        dx = np.sign(x[a:b, None] - x[None, :])
        dy = np.sign(y[a:b, None] - y[None, :])
        s += float(np.sum(dx * dy))
    return s / (n * (n - 1))


def tail_dependence(x, y, q: float) -> float:
    """Empirical lower-tail dependence at level q: P(F_Y(Y) <= q | F_X(X) <= q)."""
    u, v = _ranks(x) / (len(x) + 1), _ranks(y) / (len(y) + 1)
    both = np.sum((u <= q) & (v <= q))
    return float(both / max(1, np.sum(u <= q)))


def hill(x, k: int) -> tuple[float, float]:
    """Hill estimator of the tail index alpha from the k largest positive values: alpha_hat and its
    asymptotic standard error alpha_hat / sqrt(k)."""
    x = np.sort(np.asarray(x, dtype=float))[::-1]
    if k < 2 or x[k] <= 0:
        raise ValueError("need k >= 2 and the (k+1)-th largest value positive")
    gamma = float(np.mean(np.log(x[:k])) - math.log(x[k]))
    a = 1.0 / gamma
    return a, a / math.sqrt(k)


def _nelder_mead(f, x0, step: float = 0.1, tol: float = 1e-12, max_iter: int = 4000) -> np.ndarray:
    x0 = np.asarray(x0, dtype=float)
    n = x0.size
    pts = [x0] + [x0 + step * np.eye(n)[i] * max(1.0, abs(x0[i])) for i in range(n)]
    vals = [f(p) for p in pts]
    for _ in range(max_iter):
        order = np.argsort(vals)
        pts = [pts[i] for i in order]
        vals = [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) <= tol * (abs(vals[0]) + 1e-12):
            break
        c = np.mean(pts[:-1], axis=0)
        xr = c + (c - pts[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1])
            fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c)
            fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
    return pts[int(np.argmin(vals))]


def gpd_nll(xi: float, beta: float, y: np.ndarray) -> float:
    if beta <= 0:
        return math.inf
    if abs(xi) < 1e-9:
        return float(y.size * math.log(beta) + np.sum(y) / beta)
    z = 1 + xi * y / beta
    if np.any(z <= 0):
        return math.inf
    return float(y.size * math.log(beta) + (1 + 1 / xi) * np.sum(np.log(z)))


def gpd_fit(excess) -> tuple[float, float]:
    """Maximum likelihood (xi, beta) of the generalised Pareto law for threshold excesses y > 0."""
    y = np.asarray(excess, dtype=float)
    m, v = float(y.mean()), float(y.var())
    xi0 = 0.5 * (1 - m * m / v)                      # method of moments start
    beta0 = 0.5 * m * (m * m / v + 1)
    th = _nelder_mead(lambda t: gpd_nll(t[0], math.exp(t[1]), y), [xi0, math.log(max(beta0, 1e-12))])
    return float(th[0]), float(math.exp(th[1]))


def gpd_quantile(u: float, xi: float, beta: float, p_u: float, p: float) -> float:
    """VaR at level p: u + beta / xi ((p_u / (1 - p))^xi - 1), P(X > u) = p_u."""
    r = p_u / (1 - p)
    if abs(xi) < 1e-9:
        return u + beta * math.log(r)
    return u + beta / xi * (r**xi - 1)
