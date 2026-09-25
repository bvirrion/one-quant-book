"""firm.riskmodel -- an equity factor risk model (build of One Quant Book 7, chapter 24).

A fundamental (cross-sectional) factor model in the style described publicly for commercial equity models: each
day, stock returns are regressed on known exposures (a country factor, industry dummies, style scores) by weighted
least squares with square-root-of-capitalisation weights and the constraint that the cap-weighted industry factor
returns sum to zero; the factor covariance is an exponentially weighted estimate, optionally with Newey-West terms
and a volatility-regime adjustment (the factor variances scaled by an exponentially weighted average of the
day's cross-sectional bias statistic); specific variances are exponentially weighted squared residuals, shrunk
towards the mean of their size group. A statistical model by principal components; portfolio risk and its
decomposition; bias statistics. NumPy only. Forecasts made at the close of day t use data up to day t.

API (stable):
    cs_regression(r, X, w, C)          one day's factor returns f and residuals: min sum w (r - X f)^2 s.t. C f = 0
    factor_returns(R, exposures, W, C) (T, K) factor returns and (T, M) residuals; exposures(t) -> (X_t (M, K))
    ewma_cov(F, half_life, nw_lags)    (T, K, K): the forecast for day t + 1 made at the close of day t
    vra(F, covs, half_life)            (T,) lambda^2: EWMA of the cross-sectional bias B_t^2 = mean_k f_kt^2 / var_k
    specific_var(E, half_life, groups, shrink)   (T, M) forecasts of specific variance, shrunk within groups
    portfolio_risk(w, X, Fcov, spec)   {'total', 'factor', 'specific', 'contrib' (K,)} variances; contrib sums to factor
    pca_model(R, k)                    (B (M, k), Fcov (k, k), spec (M,)) from a (T, M) window without NaN
    bias_stat(r, sigma)                std of r / sigma (1 for a correct forecast)
    bias_band(T)                       the 95% band 1 +- sqrt(2 / T) under normality
"""
from __future__ import annotations

import math

import numpy as np


def cs_regression(r, X, w, C=None):
    """Weighted least squares with linear equality constraints C f = 0, by the KKT system. Rows with NaN return or
    zero weight are ignored; residuals are NaN there."""
    r, X, w = np.asarray(r, float), np.asarray(X, float), np.asarray(w, float)
    ok = np.isfinite(r) & (w > 0) & np.all(np.isfinite(X), axis=1)
    Xo, ro, wo = X[ok], r[ok], w[ok]
    A = Xo.T @ (wo[:, None] * Xo)
    b = Xo.T @ (wo * ro)
    K = X.shape[1]
    if C is None or len(C) == 0:
        f = np.linalg.lstsq(A, b, rcond=None)[0]
    else:
        C = np.atleast_2d(np.asarray(C, float))
        kkt = np.block([[A, C.T], [C, np.zeros((len(C), len(C)))]])
        f = np.linalg.lstsq(kkt, np.r_[b, np.zeros(len(C))], rcond=None)[0][:K]
    e = np.full(len(r), np.nan)
    e[ok] = ro - Xo @ f
    return f, e


def factor_returns(R, exposures, W, C=None):
    """R (T, M) returns with NaN where not listed; exposures(t) -> X_t (M, K); W (T, M) weights; C(t) or a fixed
    matrix or None."""
    T, M = R.shape
    F, E = None, np.full((T, M), np.nan)
    for t in range(T):
        X = exposures(t)
        Ct = C(t) if callable(C) else C
        f, e = cs_regression(R[t], X, W[t], Ct)
        if F is None:
            F = np.zeros((T, len(f)))
        F[t], E[t] = f, e
    return F, E


def ewma_cov(F, half_life: float = 90.0, nw_lags: int = 0, start=None):
    """EWMA covariance of the rows of F (zero mean assumed), recursively; with nw_lags > 0 the lagged
    cross-covariances enter with Bartlett weights (for multi-day horizons, scaled per day)."""
    F = np.asarray(F, float)
    T, K = F.shape
    lam = 0.5 ** (1.0 / half_life)
    S = np.cov(F[: max(20, K + 1)].T) if start is None else np.asarray(start, float)
    G = [np.zeros((K, K)) for _ in range(nw_lags)]
    out = np.empty((T, K, K))
    for t in range(T):
        f = F[t]
        S = lam * S + (1 - lam) * np.outer(f, f)
        for j in range(nw_lags):
            if t > j:
                G[j] = lam * G[j] + (1 - lam) * np.outer(f, F[t - j - 1])
        adj = S.copy()
        for j in range(nw_lags):
            adj += (1 - (j + 1) / (nw_lags + 1)) * (G[j] + G[j].T)
        out[t] = adj
    return out


def vra(F, covs, half_life: float = 42.0):
    """lambda_t^2 = EWMA over s <= t of B_s^2, B_s^2 = mean_k f_ks^2 / var_k(forecast made at s - 1): scale the factor
    covariance forecast made at t by lambda_t^2 (volatility regime adjustment)."""
    F = np.asarray(F, float)
    T, _ = F.shape
    lam = 0.5 ** (1.0 / half_life)
    out, x = np.ones(T), 1.0
    for t in range(1, T):
        b2 = float(np.mean(F[t] ** 2 / np.diag(covs[t - 1])))
        x = lam * x + (1 - lam) * b2
        out[t] = x
    return out


def specific_var(E, half_life: float = 90.0, groups=None, shrink: float = 0.0, warm: int = 21):
    """EWMA of squared residuals per stock (NaN until `warm` observations); with shrink q > 0, each forecast's
    volatility is pulled towards the mean volatility of its group on that day: sigma = q mean + (1 - q) sigma."""
    E = np.asarray(E, float)
    T, M = E.shape
    lam = 0.5 ** (1.0 / half_life)
    v = np.full(M, np.nan)
    n = np.zeros(M)
    out = np.full((T, M), np.nan)
    for t in range(T):
        e = E[t]
        ok = np.isfinite(e)
        v = np.where(ok & np.isnan(v), e * e, v)
        v = np.where(ok, lam * v + (1 - lam) * np.where(ok, e * e, 0.0), v)
        n = np.where(ok, n + 1, n)
        cur = np.where(n >= warm, v, np.nan)
        if shrink > 0 and groups is not None:
            g = groups[t] if np.ndim(groups) == 2 else groups
            s = np.sqrt(cur)
            for k in np.unique(g[np.isfinite(s)]):
                m = (g == k) & np.isfinite(s)
                s[m] = shrink * s[m].mean() + (1 - shrink) * s[m]
            cur = s * s
        out[t] = cur
    return out


def portfolio_risk(w, X, Fcov, spec):
    w, X, Fcov, spec = (np.asarray(a, float) for a in (w, X, Fcov, spec))
    x = X.T @ w
    contrib = x * (Fcov @ x)
    fac = float(contrib.sum())
    sp = float(np.nansum(w * w * spec))
    return {"total": fac + sp, "factor": fac, "specific": sp, "contrib": contrib, "exposure": x}


def pca_model(R, k: int):
    R = np.asarray(R, float)
    D = R - R.mean(axis=0)
    U, s, Vt = np.linalg.svd(D, full_matrices=False)
    B = Vt[:k].T                                                       # (M, k) orthonormal loadings
    fac = D @ B                                                         # factor returns
    Fcov = np.cov(fac.T, ddof=1).reshape(k, k)
    resid = D - fac @ B.T
    return B, Fcov, resid.var(axis=0, ddof=1)


def bias_stat(r, sigma) -> float:
    z = np.asarray(r, float) / np.asarray(sigma, float)
    return float(np.std(z[np.isfinite(z)], ddof=1))


def bias_band(T: int) -> tuple[float, float]:
    return 1 - math.sqrt(2 / T), 1 + math.sqrt(2 / T)
