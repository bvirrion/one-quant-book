"""firm.residarb -- residual stat arb with s-scores (build of One Quant Book 8, chapter 3).

Avellaneda and Lee's method: each day, regress every stock's last 60 daily returns on factor returns (a sector index,
or principal-component eigenportfolios of the last year's correlation matrix); treat the cumulative residual as an
Ornstein-Uhlenbeck process fitted by an AR(1) regression; standardise its distance from equilibrium into an s-score;
open a position when the s-score passes an entry threshold and close it when it comes back, only in names whose fitted
mean reversion is fast (the speed filter). Returns can first be put in trading time with volume. NumPy only.

API (stable):
    regress(R, F, per_name)            time-series OLS with intercept of each column of R (W, N) on F (W, K), or with
                                       per_name on its own factor column of F (W, N): (betas, residuals)
    eigenportfolios(R, k)              (Q (k, N) weights v_j / sigma_i, explained share of the top k eigenvalues)
    ou_fit(resid)                      AR(1) of the cumulative residual: {'a', 'b', 'var', 'kappa', 'm', 'sigma_eq'}
    s_score(fit, center=True)          -m / sigma_eq, with m centred across names (Avellaneda and Lee eq. 22)
    step(pos, s, ok, s_open, s_close_long, s_close_short)
                                       next positions (-1, 0, 1) from the current ones and today's s-scores
    speed_ok(kappa, min_kappa)         fast mean reversion: kappa > min_kappa (default 252 / 30)
    volume_adjust(R, V, avg)           returns in trading time: R * avg / V
"""
from __future__ import annotations

import numpy as np

YEAR = 252


def regress(R, F, per_name: bool = False):
    R, F = np.asarray(R, float), np.asarray(F, float)
    if per_name:                                             # one factor per name (its sector index), F (W, N)
        fm, rm = F - F.mean(axis=0), R - R.mean(axis=0)
        beta = (fm * rm).sum(axis=0) / np.maximum((fm * fm).sum(axis=0), 1e-300)
        return beta, rm - beta * fm
    X = np.column_stack([np.ones(len(F)), F])
    coef = np.linalg.lstsq(X, R, rcond=None)[0]
    return coef[1:], R - X @ coef


def eigenportfolios(R, k: int):
    R = np.asarray(R, float)
    sd = R.std(axis=0, ddof=1)
    Z = (R - R.mean(axis=0)) / sd
    C = Z.T @ Z / (len(R) - 1)
    lam, V = np.linalg.eigh(C)
    lam, V = lam[::-1], V[:, ::-1]
    return (V[:, :k] / sd[:, None]).T, float(lam[:k].sum() / lam.sum())


def ou_fit(resid):
    """resid (W, N): X_n = sum of the first n residuals, X_{n+1} = a + b X_n + zeta; kappa = -log(b) * 252,
    m = a / (1 - b), sigma_eq = sqrt(var(zeta) / (1 - b^2)); NaN where b is not in (0, 1)."""
    X = np.cumsum(np.asarray(resid, float), axis=0)
    x, y = X[:-1], X[1:]
    xm, ym = x.mean(axis=0), y.mean(axis=0)
    b = ((x - xm) * (y - ym)).sum(axis=0) / ((x - xm) ** 2).sum(axis=0)
    a = ym - b * xm
    var = ((y - a - b * x) ** 2).sum(axis=0) / (len(x) - 2)
    ok = (b > 0) & (b < 1)
    bb = np.where(ok, b, np.nan)
    return {"a": a, "b": b, "var": var, "kappa": -np.log(bb) * YEAR, "m": a / (1 - bb),
            "sigma_eq": np.sqrt(var / (1 - bb * bb))}


def s_score(fit, center: bool = True):
    m = fit["m"]
    if center:
        m = m - np.nanmean(m)
    return -m / fit["sigma_eq"]


def step(pos, s, ok, s_open: float = 1.25, s_close_long: float = 0.5, s_close_short: float = 0.75):
    """Buy to open below -s_open, sell to open above s_open; close longs above -s_close_long and shorts below
    s_close_short; names that are not ok (no fit, or too slow) are closed."""
    pos, s, ok = np.asarray(pos, int).copy(), np.asarray(s, float), np.asarray(ok, bool)
    good = ok & np.isfinite(s)
    pos[(pos == 1) & (~good | (s > -s_close_long))] = 0
    pos[(pos == -1) & (~good | (s < s_close_short))] = 0
    flat = pos == 0
    pos[flat & good & (s < -s_open)] = 1
    pos[flat & good & (s > s_open)] = -1
    return pos


def speed_ok(kappa, min_kappa: float = YEAR / 30):
    k = np.asarray(kappa, float)
    return np.isfinite(k) & (k > min_kappa)


def volume_adjust(R, V, avg):
    return np.asarray(R, float) * np.asarray(avg, float) / np.maximum(np.asarray(V, float), 1e-300)
