"""firm.linreg -- linear regression under stress (One Quant Book 4, chapter 16).

Least squares with classical, heteroskedasticity-robust, HAC and clustered standard errors; variance
inflation factors; ridge through the SVD; lasso and elastic net by coordinate descent; a time-ordered
cross-validation splitter with a purge gap; Fama-MacBeth; total least squares. NumPy only.

API (stable):
    ols(X, y, cov="classical"|"hc"|"hac"|"cluster", lags=None, groups=None)  dict(beta, se, resid, leverage)
    vif(X)                                   variance inflation factor of each column
    ridge(X, y, lam)                         (X'X + lam I)^-1 X'y via the SVD
    elastic_net(X, y, lam, alpha=1.0, beta0=None, tol, max_iter)
                                             minimises |y - Xb|^2 / (2n) + lam (alpha |b|_1 + (1 - alpha) |b|^2 / 2)
    time_series_folds(n, n_folds, purge)     list of (train, test) index arrays, training strictly before testing
    fama_macbeth(ys, Xs, lags=0)             dict(beta, se, se_nw, slopes)
    tls(x, y)                                total least squares slope of y on x (errors in both)
Columns of X are used as given: add a constant column when an intercept is wanted.
"""
from __future__ import annotations

import math

import numpy as np


def _bartlett_lrv(s: np.ndarray, lags: int) -> np.ndarray:
    """Newey-West long-run covariance of the rows of s (n x k)."""
    n = s.shape[0]
    omega = s.T @ s / n
    for L in range(1, lags + 1):
        g = s[L:].T @ s[:-L] / n
        omega += (1 - L / (lags + 1)) * (g + g.T)
    return omega


def ols(X, y, cov: str = "classical", lags: int | None = None, groups=None) -> dict:
    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    n, k = X.shape
    q, r = np.linalg.qr(X)
    beta = np.linalg.solve(r, q.T @ y)
    e = y - X @ beta
    xtx_inv = np.linalg.inv(X.T @ X)
    leverage = np.sum(q * q, axis=1)
    if cov == "classical":
        v = xtx_inv * float(e @ e) / (n - k)
    elif cov == "hc":
        meat = (X * e[:, None]).T @ (X * e[:, None])
        v = xtx_inv @ meat @ xtx_inv
    elif cov == "hac":
        lags = int(math.floor(4 * (n / 100) ** (2 / 9))) if lags is None else lags
        v = xtx_inv @ (n * _bartlett_lrv(X * e[:, None], lags)) @ xtx_inv
    elif cov == "cluster":
        g = np.asarray(groups)
        meat = np.zeros((k, k))
        for gid in np.unique(g):
            s = (X[g == gid] * e[g == gid, None]).sum(axis=0)
            meat += np.outer(s, s)
        v = xtx_inv @ meat @ xtx_inv
    else:
        raise ValueError(cov)
    return {"beta": beta, "se": np.sqrt(np.diag(v)), "cov": v, "resid": e, "leverage": leverage}


def vif(X) -> np.ndarray:
    """1 / (1 - R_j^2), R_j^2 from regressing column j on the others (with a constant)."""
    X = np.asarray(X, dtype=float)
    out = np.empty(X.shape[1])
    for j in range(X.shape[1]):
        others = np.column_stack([np.ones(X.shape[0]), np.delete(X, j, axis=1)])
        b = np.linalg.lstsq(others, X[:, j], rcond=None)[0]
        res = X[:, j] - others @ b
        r2 = 1 - float(res @ res) / float(np.sum((X[:, j] - X[:, j].mean()) ** 2))
        out[j] = 1.0 / (1.0 - r2)
    return out


def ridge(X, y, lam: float) -> np.ndarray:
    """Each singular direction's least-squares coefficient multiplied by d^2 / (d^2 + lam)."""
    u, d, vt = np.linalg.svd(np.asarray(X, dtype=float), full_matrices=False)
    return vt.T @ ((d / (d * d + lam)) * (u.T @ np.asarray(y, dtype=float)))


def elastic_net(X, y, lam: float, alpha: float = 1.0, beta0=None, tol: float = 1e-9,
                max_iter: int = 10_000) -> np.ndarray:
    """Cyclic coordinate descent with soft thresholding (alpha = 1: lasso; alpha = 0: ridge)."""
    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    n, k = X.shape
    b = np.zeros(k) if beta0 is None else np.array(beta0, dtype=float)
    col_sq = np.sum(X * X, axis=0) / n
    r = y - X @ b
    for _ in range(max_iter):
        delta = 0.0
        for j in range(k):
            if col_sq[j] == 0:
                continue
            old = b[j]
            rho = X[:, j] @ r / n + col_sq[j] * old
            new = math.copysign(max(abs(rho) - lam * alpha, 0.0), rho) / (col_sq[j] + lam * (1 - alpha))
            if new != old:
                r -= X[:, j] * (new - old)
                b[j] = new
                delta = max(delta, abs(new - old))
        if delta < tol:
            break
    return b


def time_series_folds(n: int, n_folds: int, purge: int = 0, min_train: int | None = None) -> list:
    """Expanding-window folds: the data are cut into n_folds + 1 blocks; fold f trains on blocks 0..f
    (minus the last `purge` observations) and tests on block f + 1."""
    edges = np.linspace(0, n, n_folds + 2).astype(int)
    folds = []
    for f in range(n_folds):
        train_end = edges[f + 1] - purge
        if min_train is not None and train_end < min_train:
            continue
        folds.append((np.arange(0, max(train_end, 0)), np.arange(edges[f + 1], edges[f + 2])))
    return folds


def fama_macbeth(ys, Xs, lags: int = 0) -> dict:
    """One cross-sectional OLS per period; the estimate is the mean slope, its standard error the standard
    deviation of the slopes over sqrt(T), and with lags > 0 a Newey-West version."""
    slopes = np.array([np.linalg.lstsq(np.asarray(X, float), np.asarray(y, float), rcond=None)[0]
                       for y, X in zip(ys, Xs, strict=True)])
    t = slopes.shape[0]
    mean = slopes.mean(axis=0)
    se = slopes.std(axis=0, ddof=1) / math.sqrt(t)
    d = slopes - mean
    lrv = np.diag(_bartlett_lrv(d, lags)) if lags > 0 else np.diag(d.T @ d / t)
    return {"beta": mean, "se": se, "se_nw": np.sqrt(lrv / t), "slopes": slopes}


def tls(x, y) -> float:
    """Slope of the first principal axis of the centred (x, y) cloud: equal error variances in x and y."""
    x, y = np.asarray(x, float) - np.mean(x), np.asarray(y, float) - np.mean(y)
    sxx, syy, sxy = x @ x, y @ y, x @ y
    return float((syy - sxx + math.sqrt((syy - sxx) ** 2 + 4 * sxy * sxy)) / (2 * sxy))
