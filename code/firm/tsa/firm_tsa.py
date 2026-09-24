"""firm.tsa -- linear time series (One Quant Book 4, chapter 17).

Autocorrelations with bands, the partial autocorrelation by Durbin-Levinson, Yule-Walker and conditional
least squares for ARMA models, the augmented Dickey-Fuller test with MacKinnon's response-surface critical
values, the AR(1) small-sample bias correction, the periodogram, fractional differencing and two Hurst
estimates. NumPy only.

API (stable):
    acf(x, nlags), pacf(x, nlags), band(n)            autocorrelations, partial autocorrelations, 2/sqrt(n)
    yule_walker(x, p)                                 AR(p) coefficients and innovation variance
    arma_css(x, p, q)                                 ARMA(p, q) by conditional sum of squares: (phi, theta, sigma2)
    ar1(x)                                            OLS AR(1) with intercept: dict(rho, se, half_life, ...)
    adf(x, lags=None, trend="c", max_lags=None)       dict(tau, lags, crit) with MacKinnon critical values
    mackinnon_crit(trend, n)                          1%, 5%, 10% Dickey-Fuller critical values for sample size n
    periodogram(x)                                    (frequencies, ordinates)
    frac_diff(x, d, k)                                (1 - L)^d x with k weights
    hurst_rs(x), hurst_gph(x)                         rescaled-range and log-periodogram estimates
"""
from __future__ import annotations

import math

import numpy as np

# MacKinnon (2010), Tables 2-3, N = 1: beta_inf, beta_1, beta_2, beta_3 for the 1%, 5% and 10% levels.
MACKINNON = {
    "n": [(-2.56574, -2.2358, -3.627, 0.0), (-1.94100, -0.2686, -3.365, 31.223), (-1.61682, 0.2656, -2.714, 25.364)],
    "c": [(-3.43035, -6.5393, -16.786, -79.433), (-2.86154, -2.8903, -4.234, -40.040),
          (-2.56677, -1.5384, -2.809, 0.0)],
    "ct": [(-3.95877, -9.0531, -28.428, -134.155), (-3.41049, -4.3904, -9.036, -45.374),
           (-3.12705, -2.5856, -3.925, -22.380)],
}


def acf(x, nlags: int) -> np.ndarray:
    x = np.asarray(x, dtype=float) - np.mean(x)
    n = x.size
    g0 = float(x @ x) / n
    return np.array([float(x[k:] @ x[: n - k]) / n / g0 for k in range(nlags + 1)])


def band(n: int) -> float:
    return 2.0 / math.sqrt(n)


def pacf(x, nlags: int) -> np.ndarray:
    """Durbin-Levinson recursion on the sample autocorrelations."""
    r = acf(x, nlags)
    out = np.zeros(nlags + 1)
    out[0] = 1.0
    phi = np.zeros(nlags + 1)
    v = 1.0
    for k in range(1, nlags + 1):
        a = (r[k] - phi[1:k] @ r[1:k][::-1]) / v
        new = phi.copy()
        new[k] = a
        new[1:k] = phi[1:k] - a * phi[1:k][::-1]
        phi = new
        v *= 1 - a * a
        out[k] = a
    return out


def yule_walker(x, p: int) -> tuple[np.ndarray, float]:
    x = np.asarray(x, dtype=float)
    r = acf(x, p)
    R = np.array([[r[abs(i - j)] for j in range(p)] for i in range(p)])
    phi = np.linalg.solve(R, r[1:])
    return phi, float(np.var(x) * (1 - phi @ r[1:]))


def _css(params, x, p, q):
    phi, theta = params[:p], params[p: p + q]
    e = np.zeros(x.size)
    for t in range(p, x.size):
        ar = phi @ x[t - p: t][::-1] if p else 0.0
        ma = sum(theta[j] * e[t - 1 - j] for j in range(q) if t - 1 - j >= p)
        e[t] = x[t] - ar - ma
    return e[p:]


def arma_css(x, p: int, q: int) -> tuple[np.ndarray, np.ndarray, float]:
    """Conditional sum of squares for x_t = sum phi_i x_{t-i} + e_t + sum vartheta_j e_{t-j} (x demeaned);
    Gauss-Newton with a numerical Jacobian, started from Yule-Walker."""
    x = np.asarray(x, dtype=float) - np.mean(x)
    th = np.concatenate([yule_walker(x, p)[0] if p else np.zeros(0), np.zeros(q)])
    for _ in range(100):
        e = _css(th, x, p, q)
        J = np.empty((e.size, th.size))
        for i in range(th.size):
            d = np.zeros(th.size)
            d[i] = 1e-6
            J[:, i] = (_css(th + d, x, p, q) - e) / 1e-6
        step = np.linalg.lstsq(J, -e, rcond=None)[0]
        th = th + step
        if np.max(np.abs(step)) < 1e-10:
            break
    e = _css(th, x, p, q)
    return th[:p], th[p:], float(e @ e / e.size)


def ar1(x) -> dict:
    """OLS of x_t on (1, x_{t-1}); half-life ln(1/2)/ln(rho); Kendall's correction rho + (1 + 3 rho)/n."""
    x = np.asarray(x, dtype=float)
    n = x.size
    X = np.column_stack([np.ones(n - 1), x[:-1]])
    b, *_ = np.linalg.lstsq(X, x[1:], rcond=None)
    e = x[1:] - X @ b
    s2 = float(e @ e) / (n - 3)
    xc = x[:-1] - x[:-1].mean()
    se = math.sqrt(s2 / float(xc @ xc))
    rho = float(b[1])
    rk = rho + (1 + 3 * rho) / n

    def hl(r):
        return math.log(0.5) / math.log(r) if 0 < r < 1 else math.inf
    return {"rho": rho, "se": se, "t_unit": (rho - 1) / se, "c": float(b[0]), "sigma": math.sqrt(s2),
            "half_life": hl(rho), "rho_kendall": rk, "half_life_kendall": hl(rk), "n": n}


def mackinnon_crit(trend: str, n: int) -> tuple[float, float, float]:
    return tuple(b0 + b1 / n + b2 / n**2 + b3 / n**3 for b0, b1, b2, b3 in MACKINNON[trend])


def _adf_reg(x, lags, trend):
    dx = np.diff(x)
    n = dx.size - lags
    cols = [x[lags:-1]]
    if trend in ("c", "ct"):
        cols.append(np.ones(n))
    if trend == "ct":
        cols.append(np.arange(n, dtype=float))
    for k in range(1, lags + 1):
        cols.append(dx[lags - k: dx.size - k])
    X = np.column_stack(cols)
    y = dx[lags:]
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    s2 = float(e @ e) / (n - X.shape[1])
    se = math.sqrt(s2 * np.linalg.inv(X.T @ X)[0, 0])
    return float(b[0]) / se, float(e @ e), n, X.shape[1]


def adf(x, lags: int | None = None, trend: str = "c", max_lags: int | None = None) -> dict:
    """Augmented Dickey-Fuller tau for Delta x_t = gamma x_{t-1} + deterministics + sum a_k Delta x_{t-k} + e_t.
    lags=None chooses them by AIC up to max_lags (default 12 (n/100)^(1/4)) on a common sample."""
    x = np.asarray(x, dtype=float)
    if lags is None:
        max_lags = int(12 * (x.size / 100) ** 0.25) if max_lags is None else max_lags
        best = None
        for k in range(max_lags + 1):
            _, ssr, n, m = _adf_reg(x[max_lags - k:], k, trend)
            aic = n * math.log(ssr / n) + 2 * m
            if best is None or aic < best[0]:
                best = (aic, k)
        lags = best[1]
    tau, _, n, _ = _adf_reg(x, lags, trend)
    return {"tau": tau, "lags": lags, "n": n, "crit": mackinnon_crit(trend, n)}


def periodogram(x) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float) - np.mean(x)
    n = x.size
    f = np.fft.rfft(x)
    freqs = 2 * math.pi * np.arange(f.size) / n
    return freqs[1:], (np.abs(f[1:]) ** 2) / (2 * math.pi * n)


def frac_diff(x, d: float, k: int = 500) -> np.ndarray:
    """(1 - L)^d x with weights w_0 = 1, w_j = w_{j-1} (j - 1 - d) / j, truncated at k lags."""
    w = np.empty(k + 1)
    w[0] = 1.0
    for j in range(1, k + 1):
        w[j] = w[j - 1] * (j - 1 - d) / j
    x = np.asarray(x, dtype=float)
    return np.convolve(x, w)[k: x.size]


def hurst_rs(x, sizes=None) -> float:
    """Slope of log(R/S) on log(block size)."""
    x = np.asarray(x, dtype=float)
    sizes = [int(s) for s in np.geomspace(16, x.size // 4, 12)] if sizes is None else sizes
    pts = []
    for s in sizes:
        rs = []
        for a in range(0, x.size - s + 1, s):
            b = x[a: a + s]
            z = np.cumsum(b - b.mean())
            sd = b.std()
            if sd > 0:
                rs.append((z.max() - z.min()) / sd)
        pts.append((math.log(s), math.log(np.mean(rs))))
    p = np.array(pts)
    return float(np.polyfit(p[:, 0], p[:, 1], 1)[0])


def hurst_gph(x, power: float = 0.5) -> float:
    """Geweke-Porter-Hudak: regress log I(w_j) on -2 log(2 sin(w_j / 2)) over the lowest n^power frequencies;
    the slope is d, and H = d + 1/2."""
    w, i = periodogram(x)
    m = int(np.asarray(x).size ** power)
    reg = -2 * np.log(2 * np.sin(w[:m] / 2))
    d = float(np.polyfit(reg, np.log(i[:m]), 1)[0])
    return d + 0.5
