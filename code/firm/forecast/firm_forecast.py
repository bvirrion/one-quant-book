"""firm.forecast -- from a score to an expected return, and what the forecast is worth (build of Book 7, chapter 15).

Calibrators turn a standardised score into an expected return: the alpha scaling rule (IC x volatility x score), bin
means, and isotonic regression by pool-adjacent-violators. Evaluation: the Mincer-Zarnowitz regression of realised on
forecast returns, the calibration curve, the IC's mean and dispersion. The fundamental law and its corrections:
effective breadth from the average correlation of the bets, the transfer coefficient of a constrained portfolio, and
the information ratio implied by a noisy IC (Qian and Hua; Ding and Martin). NumPy only.

API (stable):
    scale_rule(z, ic, vol)                     expected return = ic * vol * z
    binned(score, realised, bins)              (bin centres, mean score, mean realised) by score quantile
    isotonic(x, y, w)                          non-decreasing least-squares fit of y on x (pool adjacent violators)
    mincer_zarnowitz(forecast, realised)       (intercept, slope, R^2) of realised on forecast
    effective_breadth(n, rho)                  n / (1 + (n - 1) rho)
    transfer_coefficient(w, alpha, vol)        corr(w * vol, alpha / vol): risk-adjusted weights against forecasts
    law_ir(ic, breadth, tc)                    tc * ic * sqrt(breadth)
    qian_hua_ir(mu_ic, sd_ic)                  mu_ic / sd_ic (per period)
    ding_martin_ir(mu_ic, sd_ic, n)            mu_ic / sqrt(sd_ic^2 + (1 - mu_ic^2 - sd_ic^2) / n) (per period)
    information_ratio(pnl, periods)            annualised mean / standard deviation
"""
from __future__ import annotations

import math

import numpy as np


def scale_rule(z, ic, vol):
    return np.asarray(ic) * np.asarray(vol) * np.asarray(z)


def binned(score, realised, bins: int = 10):
    s, r = np.asarray(score, float).ravel(), np.asarray(realised, float).ravel()
    ok = ~np.isnan(s) & ~np.isnan(r)
    s, r = s[ok], r[ok]
    edges = np.quantile(s, np.linspace(0, 1, bins + 1))
    k = np.clip(np.searchsorted(edges, s, side="right") - 1, 0, bins - 1)
    return (np.arange(bins), np.array([s[k == b].mean() for b in range(bins)]),
            np.array([r[k == b].mean() for b in range(bins)]))


def isotonic(x, y, w=None) -> np.ndarray:
    """Pool adjacent violators: sort by x, merge neighbouring blocks whose means decrease, return the fit at each
    original point (Ayer, Brunk, Ewing, Reid and Silverman, 1955)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    w = np.ones(len(y)) if w is None else np.asarray(w, float)
    order = np.argsort(x, kind="stable")
    means, weights, sizes = [], [], []
    for yi, wi in zip(y[order], w[order], strict=True):
        means.append(yi)
        weights.append(wi)
        sizes.append(1)
        while len(means) > 1 and means[-2] > means[-1]:
            m2, w2, n2 = means.pop(), weights.pop(), sizes.pop()
            m1, w1, n1 = means.pop(), weights.pop(), sizes.pop()
            means.append((m1 * w1 + m2 * w2) / (w1 + w2))
            weights.append(w1 + w2)
            sizes.append(n1 + n2)
    fit = np.repeat(means, sizes)
    out = np.empty(len(y))
    out[order] = fit
    return out


def mincer_zarnowitz(forecast, realised) -> tuple[float, float, float]:
    f, r = np.asarray(forecast, float).ravel(), np.asarray(realised, float).ravel()
    ok = ~np.isnan(f) & ~np.isnan(r)
    b, a = np.polyfit(f[ok], r[ok], 1)
    res = r[ok] - (a + b * f[ok])
    return float(a), float(b), float(1.0 - res.var() / r[ok].var())


def effective_breadth(n: float, rho: float) -> float:
    return float(n / (1.0 + (n - 1.0) * rho))


def transfer_coefficient(w, alpha, vol) -> float:
    w, alpha, vol = (np.asarray(a, float) for a in (w, alpha, vol))
    return float(np.corrcoef(w * vol, alpha / vol)[0, 1])


def law_ir(ic: float, breadth: float, tc: float = 1.0) -> float:
    return float(tc * ic * math.sqrt(breadth))


def qian_hua_ir(mu_ic: float, sd_ic: float) -> float:
    return float(mu_ic / sd_ic)


def ding_martin_ir(mu_ic: float, sd_ic: float, n: int) -> float:
    return float(mu_ic / math.sqrt(sd_ic ** 2 + (1.0 - mu_ic ** 2 - sd_ic ** 2) / n))


def information_ratio(pnl, periods: int = 12) -> float:
    p = np.asarray(pnl, float)
    return float(p.mean() / p.std(ddof=1) * math.sqrt(periods))
