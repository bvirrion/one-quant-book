"""firm.volfcst -- volatility forecasting (One Quant Book 4, chapter 18).

GARCH(1,1) and GJR-GARCH with Gaussian or Student-t innovations fitted by (quasi-)maximum likelihood with
sandwich standard errors, EWMA and rolling-window variances, the HAR model on realised variance, and forecast
evaluation (QLIKE and MSE losses, Mincer-Zarnowitz regression, Diebold-Mariano test). NumPy only.

API (stable):
    garch_filter(r, omega, alpha, beta, gamma=0.0, h0=None)   conditional variances h_t (h_t uses r up to t - 1)
    garch_fit(r, dist="normal"|"t", gjr=False)                dict(params, se, loglik, persistence, half_life, h, ...)
    garch_forecast(fit, horizon)                              variance forecasts 1..horizon days ahead
    ewma(r, lam=0.94, h0=None), rolling_var(r, window)        variance forecasts for day t from data to t - 1
    har_fit(rv), har_forecast(fit, rv)                        rv_{t+1} = b0 + b_d rv_t + b_w mean_5 + b_m mean_22
    qlike(proxy, h), mse(proxy, h)                            per-period losses (QLIKE as proxy / h + ln h)
    mincer_zarnowitz(proxy, h)                                (intercept, slope, R^2)
    diebold_mariano(loss1, loss2, lags=None)                  (statistic, two-sided normal p-value)
Returns are in any unit; variances are in that unit squared.
"""
from __future__ import annotations

import math

import numpy as np


def garch_filter(r, omega: float, alpha: float, beta: float, gamma: float = 0.0, h0: float | None = None) -> np.ndarray:
    r = np.asarray(r, dtype=float)
    h = np.empty(r.size + 1)
    h[0] = float(np.var(r)) if h0 is None else h0
    for t in range(r.size):
        h[t + 1] = omega + (alpha + gamma * (r[t] < 0)) * r[t] ** 2 + beta * h[t]
    return h


def _loglik_obs(r, h, dist, nu):
    if dist == "normal":
        return -0.5 * (math.log(2 * math.pi) + np.log(h) + r * r / h)
    c = math.lgamma((nu + 1) / 2) - math.lgamma(nu / 2) - 0.5 * math.log(math.pi * (nu - 2))
    return c - 0.5 * np.log(h) - (nu + 1) / 2 * np.log1p(r * r / ((nu - 2) * h))


def _unpack(th, dist, gjr):
    omega, alpha, beta = math.exp(th[0]), math.exp(th[1]), math.exp(th[2])
    gamma = math.exp(th[3]) if gjr else 0.0
    nu = 2.05 + math.exp(th[-1]) if dist == "t" else None
    return omega, alpha, beta, gamma, nu


def _obs(th, r, dist, gjr, h0):
    omega, alpha, beta, gamma, nu = _unpack(th, dist, gjr)
    if alpha + beta + gamma / 2 >= 1:
        return np.full(r.size, -1e10)
    h = garch_filter(r, omega, alpha, beta, gamma, h0)[:-1]
    return _loglik_obs(r, h, dist, nu)


def _nelder_mead(f, x0, step=0.3, tol=1e-10, max_iter=20_000):
    x0 = np.asarray(x0, dtype=float)
    n = x0.size
    pts = [x0] + [x0 + step * np.eye(n)[i] for i in range(n)]
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


def _natural(th, dist, gjr):
    omega, alpha, beta, gamma, nu = _unpack(th, dist, gjr)
    out = [omega, alpha, beta] + ([gamma] if gjr else []) + ([nu] if dist == "t" else [])
    return np.array(out)


def garch_fit(r, dist: str = "normal", gjr: bool = False) -> dict:
    """(Quasi-)maximum likelihood; the variance recursion starts at the sample variance. Standard errors of the
    natural parameters by the sandwich (Hessian and outer product of per-observation scores, delta method from the
    log parameterisation)."""
    r = np.asarray(r, dtype=float)
    h0 = float(np.var(r))
    x0 = [math.log(0.05 * h0), math.log(0.05), math.log(0.9)] + ([math.log(0.02)] if gjr else []) + \
         ([math.log(4.0)] if dist == "t" else [])

    def nll(th):
        return -float(np.sum(_obs(th, r, dist, gjr, h0)))
    th = _nelder_mead(nll, x0)
    th = _nelder_mead(nll, th, step=0.05)
    k = th.size
    eps = 1e-4
    scores = np.empty((r.size, k))
    for i in range(k):
        d = np.zeros(k)
        d[i] = eps
        scores[:, i] = (_obs(th + d, r, dist, gjr, h0) - _obs(th - d, r, dist, gjr, h0)) / (2 * eps)
    H = np.empty((k, k))
    for i in range(k):
        for j in range(k):
            di, dj = np.zeros(k), np.zeros(k)
            di[i], dj[j] = eps, eps
            H[i, j] = -(nll(th + di + dj) - nll(th + di - dj) - nll(th - di + dj) + nll(th - di - dj)) / (4 * eps * eps)
    Hinv = np.linalg.inv(H)
    cov_th = Hinv @ (scores.T @ scores) @ Hinv
    J = np.diag(_natural(th, dist, gjr))                   # d natural / d log parameter (nu: exp part only)
    if dist == "t":
        J[-1, -1] = _natural(th, dist, gjr)[-1] - 2.05
    cov = J @ cov_th @ J.T
    cov_h = -J @ Hinv @ J.T                                  # H is the Hessian of the log-likelihood
    omega, alpha, beta, gamma, nu = _unpack(th, dist, gjr)
    pers = alpha + beta + gamma / 2
    h = garch_filter(r, omega, alpha, beta, gamma, h0)
    return {"params": _natural(th, dist, gjr), "se": np.sqrt(np.diag(cov)), "se_hessian": np.sqrt(np.diag(cov_h)),
            "loglik": -nll(th),
            "omega": omega, "alpha": alpha, "beta": beta, "gamma": gamma, "nu": nu, "persistence": pers,
            "half_life": math.log(0.5) / math.log(pers), "uncond_var": omega / (1 - pers), "h": h, "r_last": r[-1],
            "dist": dist, "gjr": gjr}


def garch_forecast(fit: dict, horizon: int) -> np.ndarray:
    """E[h_{T+k}] for k = 1..horizon from the last filtered variance: mean reversion at rate persistence^k."""
    h1 = fit["h"][-1]
    p, v = fit["persistence"], fit["uncond_var"]
    return np.array([v + p ** (k - 1) * (h1 - v) for k in range(1, horizon + 1)])


def ewma(r, lam: float = 0.94, h0: float | None = None) -> np.ndarray:
    r = np.asarray(r, dtype=float)
    h = np.empty(r.size + 1)
    h[0] = float(np.mean(r[:20] ** 2)) if h0 is None else h0
    for t in range(r.size):
        h[t + 1] = lam * h[t] + (1 - lam) * r[t] ** 2
    return h


def rolling_var(r, window: int) -> np.ndarray:
    """Forecast for day t (t >= window): sample variance of r[t - window:t]; NaN before."""
    r = np.asarray(r, dtype=float)
    out = np.full(r.size + 1, np.nan)
    c1 = np.concatenate([[0.0], np.cumsum(r)])
    c2 = np.concatenate([[0.0], np.cumsum(r * r)])
    for t in range(window, r.size + 1):
        s1, s2 = c1[t] - c1[t - window], c2[t] - c2[t - window]
        out[t] = (s2 - s1 * s1 / window) / (window - 1)
    return out


def _har_design(rv):
    rv = np.asarray(rv, dtype=float)
    t = np.arange(21, rv.size)
    d = rv[t]
    w = np.array([rv[i - 4: i + 1].mean() for i in t])
    m = np.array([rv[i - 21: i + 1].mean() for i in t])
    return np.column_stack([np.ones(t.size), d, w, m]), t


def har_fit(rv) -> dict:
    rv = np.asarray(rv, dtype=float)
    X, t = _har_design(rv)
    X, y = X[:-1], rv[t[:-1] + 1]
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    return {"beta": b, "r2": 1 - float(e @ e) / float(np.sum((y - y.mean()) ** 2))}


def har_forecast(fit: dict, rv) -> np.ndarray:
    """Forecasts of rv_{t+1} for every t >= 21 (aligned with rv[22:] and one beyond)."""
    X, _ = _har_design(rv)
    return X @ fit["beta"]


def qlike(proxy, h) -> np.ndarray:
    """proxy / h + ln h: Patton's QLIKE up to terms free of h, so finite when the proxy is zero (a day without a
    price change); minimised in expectation by h = E[proxy]."""
    h = np.asarray(h, dtype=float)
    return np.asarray(proxy, dtype=float) / h + np.log(h)


def mse(proxy, h) -> np.ndarray:
    return (np.asarray(proxy, dtype=float) - np.asarray(h, dtype=float)) ** 2


def mincer_zarnowitz(proxy, h) -> tuple[float, float, float]:
    y, x = np.asarray(proxy, dtype=float), np.asarray(h, dtype=float)
    X = np.column_stack([np.ones(x.size), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    return float(b[0]), float(b[1]), 1 - float(e @ e) / float(np.sum((y - y.mean()) ** 2))


def diebold_mariano(loss1, loss2, lags: int | None = None) -> tuple[float, float]:
    """Mean loss difference over its Newey-West standard error; negative favours the first forecast."""
    d = np.asarray(loss1, dtype=float) - np.asarray(loss2, dtype=float)
    n = d.size
    lags = int(math.floor(4 * (n / 100) ** (2 / 9))) if lags is None else lags
    dc = d - d.mean()
    lrv = float(dc @ dc) / n
    for k in range(1, lags + 1):
        lrv += 2 * (1 - k / (lags + 1)) * float(dc[k:] @ dc[:-k]) / n
    stat = d.mean() / math.sqrt(lrv / n)
    return float(stat), float(math.erfc(abs(stat) / math.sqrt(2)))
