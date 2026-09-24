"""firm.estim -- estimation toolkit (One Quant Book 4, chapter 11).

Maximum likelihood with numerical derivatives, sandwich and Newey-West (HAC) covariances, the delta
method, and the Sharpe ratio with its standard errors. NumPy only; the minimiser is a Nelder-Mead
simplex (chapter 24 builds better ones).

API (stable):
    minimize(f, x0, step=0.1, tol=1e-10, max_iter=5000)          Nelder-Mead
    gradient(f, x, h=1e-5), hessian(f, x, h=1e-4)                central differences
    mle(loglik_obs, x0)             loglik_obs(theta) -> per-observation log-likelihoods (array)
                                    returns dict(theta, se_hessian, se_opg, se_sandwich, cov_*)
    long_run_variance(x, lags)      Newey-West with Bartlett weights
    nw_lags(n)                      floor(4 (n / 100)^(2/9))
    mean_se(x, kind)                standard error of the mean: "iid" or "hac"
    sharpe(x, periods)              annualised Sharpe ratio with iid (Lo 2002) and HAC standard errors
    delta_method(g, theta, cov)     standard error of g(theta)
"""
from __future__ import annotations

import math

import numpy as np


def minimize(f, x0, step: float = 0.1, tol: float = 1e-10, max_iter: int = 5000) -> tuple[np.ndarray, float]:
    x0 = np.atleast_1d(np.asarray(x0, dtype=float))
    n = x0.size
    simplex = [x0] + [x0 + step * np.eye(n)[i] * max(1.0, abs(x0[i])) for i in range(n)]
    vals = [f(x) for x in simplex]
    for _ in range(max_iter):
        order = np.argsort(vals)
        simplex, vals = [simplex[i] for i in order], [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) <= tol * (1 + abs(vals[0])):
            break
        cen = np.mean(simplex[:-1], axis=0)
        xr = 2 * cen - simplex[-1]
        fr = f(xr)
        if fr < vals[0]:
            xe = 3 * cen - 2 * simplex[-1]
            fe = f(xe)
            simplex[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            simplex[-1], vals[-1] = xr, fr
        else:
            xc = 0.5 * (cen + simplex[-1])
            fc = f(xc)
            if fc < vals[-1]:
                simplex[-1], vals[-1] = xc, fc
            else:
                simplex = [simplex[0]] + [0.5 * (simplex[0] + x) for x in simplex[1:]]
                vals = [vals[0]] + [f(x) for x in simplex[1:]]
    i = int(np.argmin(vals))
    return simplex[i], vals[i]


def gradient(f, x, h: float = 1e-5) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    g = []
    for i in range(x.size):
        e = np.zeros(x.size)
        e[i] = h * max(1.0, abs(x[i]))
        g.append((f(x + e) - f(x - e)) / (2 * e[i]))
    return np.array(g)


def hessian(f, x, h: float = 1e-4) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    n = x.size
    H = np.empty((n, n))
    steps = [h * max(1.0, abs(v)) for v in x]
    for i in range(n):
        for j in range(n):
            ei, ej = np.zeros(n), np.zeros(n)
            ei[i], ej[j] = steps[i], steps[j]
            H[i, j] = (f(x + ei + ej) - f(x + ei - ej) - f(x - ei + ej) + f(x - ei - ej)) / (4 * steps[i] * steps[j])
    return 0.5 * (H + H.T)


def mle(loglik_obs, x0) -> dict:
    """Maximise sum(loglik_obs(theta)). Covariances: inverse Hessian (A^-1), inverse outer product of
    per-observation scores (B^-1), and the sandwich A^-1 B A^-1, which stays right when the model is
    misspecified."""
    def neg(t):
        v = np.sum(loglik_obs(np.asarray(t, float)))
        return -v if np.isfinite(v) else 1e300

    theta, _ = minimize(neg, x0)
    A = hessian(lambda t: -np.sum(loglik_obs(t)), theta)            # observed information, sum over n
    n_par = theta.size
    scores = np.empty((np.asarray(loglik_obs(theta)).size, n_par))
    for i in range(n_par):
        e = np.zeros(n_par)
        e[i] = 1e-5 * max(1.0, abs(theta[i]))
        scores[:, i] = (loglik_obs(theta + e) - loglik_obs(theta - e)) / (2 * e[i])
    B = scores.T @ scores
    Ai = np.linalg.inv(A)
    cov_s = Ai @ B @ Ai
    return {"theta": theta, "cov_hessian": Ai, "cov_opg": np.linalg.inv(B), "cov_sandwich": cov_s,
            "se_hessian": np.sqrt(np.diag(Ai)), "se_opg": np.sqrt(np.diag(np.linalg.inv(B))),
            "se_sandwich": np.sqrt(np.diag(cov_s))}


def nw_lags(n: int) -> int:
    return int(math.floor(4 * (n / 100) ** (2 / 9)))


def long_run_variance(x, lags: int | None = None) -> float:
    """sum over |k| <= L of (1 - |k| / (L + 1)) gamma(k): Newey-West, always nonnegative."""
    x = np.asarray(x, dtype=float)
    n = x.size
    L = nw_lags(n) if lags is None else lags
    d = x - x.mean()
    lrv = d @ d / n
    for k in range(1, L + 1):
        lrv += 2 * (1 - k / (L + 1)) * (d[k:] @ d[:-k]) / n
    return float(lrv)


def mean_se(x, kind: str = "iid", lags: int | None = None) -> float:
    x = np.asarray(x, dtype=float)
    n = x.size
    if kind == "iid":
        return float(x.std(ddof=1) / math.sqrt(n))
    return float(math.sqrt(long_run_variance(x, lags) / n))


def sharpe(x, periods: int = 252, lags: int | None = None) -> dict:
    """Annualised Sharpe ratio sqrt(periods) mean / sd, its iid standard error sqrt((1 + SR_1^2 / 2) / n)
    (per period, Lo 2002, normal returns) scaled by sqrt(periods), and a HAC standard error by the
    delta method applied to the long-run covariance of (x, x^2)."""
    x = np.asarray(x, dtype=float)
    n = x.size
    m, s = x.mean(), x.std(ddof=1)
    sr1 = m / s
    se_iid = math.sqrt((1 + 0.5 * sr1**2) / n)
    z = np.column_stack([x - m, (x - m) ** 2 - s**2])
    L = nw_lags(n) if lags is None else lags
    S = z.T @ z / n
    for k in range(1, L + 1):
        g = z[k:].T @ z[:-k] / n
        S += (1 - k / (L + 1)) * (g + g.T)
    grad = np.array([1 / s, -m / (2 * s**3)])               # d SR / d (mean, variance)
    se_hac = math.sqrt(grad @ S @ grad / n)
    root = math.sqrt(periods)
    return {"sr": root * sr1, "se_iid": root * se_iid, "se_hac": root * se_hac}


def delta_method(g, theta, cov) -> float:
    """se(g(theta_hat)) = sqrt(grad g' cov grad g)."""
    grad = gradient(g, theta)
    return float(math.sqrt(grad @ np.asarray(cov) @ grad))
