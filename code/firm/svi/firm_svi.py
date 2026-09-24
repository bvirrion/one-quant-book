"""SVI and SSVI parametrisations of the smile, fitted to bid and ask (build of Book 5, Chapter 8).

Raw SVI slice: w(k) = a + b (rho (k - m) + sqrt((k - m)^2 + s^2)), s the parameter written
varsigma in the book. With y = (k - m)/s it is linear in (a, d, c) = (a, b rho s, b s):
w = a + d y + c sqrt(y^2 + 1), so for fixed (m, s) the best (a, d, c) is a weighted least-squares
problem (the quasi-explicit method); (m, s) are found by a Nelder-Mead search on top.
SSVI (Gatheral-Jacquier): w(k, theta) = theta/2 (1 + rho phi k + sqrt((phi k + rho)^2 + 1 - rho^2)),
power law phi(theta) = eta theta^(-gamma).
"""
import math

import numpy as np


def svi(k, a: float, b: float, rho: float, m: float, s: float):
    k = np.asarray(k, float)
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + s * s))


def svi_check(a: float, b: float, rho: float, m: float, s: float) -> dict[str, bool]:
    """Necessary conditions: positive variance, a valid correlation, wings within Lee's bound 2."""
    return {"b>=0": b >= 0, "|rho|<1": abs(rho) < 1, "s>0": s > 0,
            "min w>=0": a + b * s * math.sqrt(1 - rho * rho) >= 0,
            "wings<=2": b * (1 + abs(rho)) <= 2}


def nelder_mead(f, x0, step, tol: float = 1e-10, max_iter: int = 2000):
    """Derivative-free minimisation (Nelder-Mead simplex with standard coefficients)."""
    n = len(x0)
    pts = [np.asarray(x0, float)] + [np.asarray(x0, float) + np.eye(n)[i] * step[i] for i in range(n)]
    vals = [f(p) for p in pts]
    for _ in range(max_iter):
        order = np.argsort(vals)
        pts, vals = [pts[i] for i in order], [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < tol * (1 + abs(vals[0])):
            break
        centre = np.mean(pts[:-1], axis=0)
        xr = centre + (centre - pts[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = centre + 2 * (centre - pts[-1])
            fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = centre + 0.5 * (pts[-1] - centre)
            fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0] + 0.5 * (p - pts[0]) for p in pts]
                vals = [f(p) for p in pts]
    i = int(np.argmin(vals))
    return pts[i], vals[i]


def _inner(k, w, wts, m: float, s: float):
    """Best (a, d, c) for fixed (m, s): weighted least squares, then projected on the domain
    0 <= c <= 2s, |d| <= c, |d| <= 2s - c (Lee's bound b(1 + |rho|) <= 2), a >= 0, refitting a."""
    y = (k - m) / s
    x = np.column_stack([np.ones_like(y), y, np.sqrt(y * y + 1)])
    sw = np.sqrt(wts)
    coef, *_ = np.linalg.lstsq(x * sw[:, None], w * sw, rcond=None)
    a, d, c = coef
    c = min(max(c, 0.0), 2 * s)
    d = max(-min(c, 2 * s - c), min(d, min(c, 2 * s - c)))
    a = max(float(np.sum(wts * (w - d * y - c * np.sqrt(y * y + 1))) / np.sum(wts)), 0.0)
    return a, d, c


def fit_svi(k, w_mid, w_bid=None, w_ask=None, weights=None) -> tuple[tuple[float, ...], float]:
    """Fit raw SVI to one slice. With bid and ask, the objective counts only the distance by which the
    model leaves the [bid, ask] band, plus a small pull to the mid. Returns (a, b, rho, m, s) and the
    root-mean-square error to the mids."""
    k, w_mid = np.asarray(k, float), np.asarray(w_mid, float)
    wts = np.ones_like(k) if weights is None else np.asarray(weights, float)

    def params(z):
        m, s = z[0], abs(z[1]) + 1e-6
        a, d, c = _inner(k, w_mid, wts, m, s)
        b = c / s
        rho = d / c if c > 0 else 0.0
        return a, b, rho, m, s

    def obj(z):
        w = svi(k, *params(z))
        if w_bid is None:
            return float(np.sum(wts * (w - w_mid) ** 2))
        out = np.maximum(w - np.asarray(w_ask), 0) + np.maximum(np.asarray(w_bid) - w, 0)
        return float(np.sum(wts * out ** 2) + 1e-3 * np.sum(wts * (w - w_mid) ** 2))
    best = None
    for m0 in (-0.1, 0.0, 0.1):
        for s0 in (0.05, 0.2):
            z, v = nelder_mead(obj, [m0, s0], [0.05, 0.05])
            if best is None or v < best[1]:
                best = (z, v)
    p = params(best[0])
    rmse = float(np.sqrt(np.mean((svi(k, *p) - w_mid) ** 2)))
    return p, rmse


def ssvi(k, theta, rho: float, eta: float, gamma: float):
    phi = eta * np.power(theta, -gamma)
    k = np.asarray(k, float)
    return theta / 2 * (1 + rho * phi * k + np.sqrt((phi * k + rho) ** 2 + 1 - rho * rho))


def ssvi_check(thetas, rho: float, eta: float, gamma: float) -> dict[str, bool]:
    """Sufficient no-arbitrage conditions: calendar (0 < gamma < 1 with the power law and increasing
    theta) and butterfly (theta phi (1+|rho|) < 4 and theta phi^2 (1+|rho|) <= 4)."""
    th = np.asarray(thetas, float)
    phi = eta * th ** (-gamma)
    return {"theta increasing": bool(np.all(np.diff(th) >= 0)), "0<gamma<1": 0 < gamma < 1,
            "butterfly 1": bool(np.all(th * phi * (1 + abs(rho)) < 4)),
            "butterfly 2": bool(np.all(th * phi * phi * (1 + abs(rho)) <= 4))}


def fit_ssvi(slices: list[tuple[np.ndarray, np.ndarray, float]]) -> tuple[tuple[float, float, float], float]:
    """Fit (rho, eta, gamma) to slices (k, w, theta) with theta the at-the-money total variance of the
    slice. Returns the parameters and the RMSE in total variance."""
    def obj(z):
        rho, eta, gamma = math.tanh(z[0]), math.exp(z[1]), 1 / (1 + math.exp(-z[2]))
        return sum(float(np.sum((ssvi(k, th, rho, eta, gamma) - w) ** 2)) for k, w, th in slices)
    z, v = nelder_mead(obj, [-0.5, 0.0, 0.0], [0.3, 0.3, 0.3])
    n = sum(len(k) for k, _, _ in slices)
    return (math.tanh(z[0]), math.exp(z[1]), 1 / (1 + math.exp(-z[2]))), math.sqrt(v / n)


def event_variance(w_before: float, t_before: float, w_after: float, t_after: float) -> float:
    """Variance of a scheduled jump between two expiries, assuming the diffusive variance rate of the
    earlier expiry continues: w_after - (w_before / t_before) t_after."""
    return w_after - w_before / t_before * t_after


def implied_move(event_var: float) -> tuple[float, float]:
    """(standard deviation, expected absolute size) of a normally distributed log-jump."""
    sd = math.sqrt(max(event_var, 0.0))
    return sd, sd * math.sqrt(2 / math.pi)
