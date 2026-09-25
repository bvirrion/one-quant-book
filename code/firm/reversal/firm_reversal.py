"""firm.reversal -- the short-term reversal family and a cost-aware daily book (build of One Quant Book 8, chapter 2).

Signals are computed at a close from that day's returns and are positive where the price is expected to rise: raw
reversal (minus the return), industry-adjusted (minus the return in excess of its industry's equal-weighted mean),
residual (minus the residual of a cross-sectional regression on factor exposures), overnight (minus the return from
the previous close to the open) and intraday (minus the return from the open to the close). The daily book maximises
expected return less a diagonal risk penalty and the trading cost (half spread plus square-root impact), dollar
neutral; with a diagonal risk the problem separates by name, so each name's trade is a closed-form proximal step and
neutrality to a few exposures is a small dual problem solved by Newton's method. NumPy only.

API (stable):
    raw(r)                                          -r
    industry_adjusted(r, industry, listed)          -(r - industry mean), NaN where not listed
    residual(r, X, w=None, listed=None)             -(r - X b), b the (weighted) least-squares fit over listed names
    overnight(open_, prev_close)                    -(open / prev_close - 1)
    intraday(close, open_)                          -(close / open - 1)
    forecast(z, ic, sigma)                          Grinold's rule: alpha = ic * sigma * z
    book(alpha, var, w0, gamma, aum, sigma, adv, half_spread, eta, costs=True, round_trip=1.0, X=None)
                                                    the day's dollar-neutral weights (fractions of capital); the
                                                    cost is multiplied by round_trip (2: a one-day forecast pays to
                                                    enter and again to leave); X'w = 0 for the exposures X (dollar
                                                    neutral if X is None)
"""
from __future__ import annotations

import numpy as np
from firm_tcost import prox_cost


def raw(r):
    return -np.asarray(r, float)


def industry_adjusted(r, industry, listed):
    r, industry, listed = np.asarray(r, float), np.asarray(industry), np.asarray(listed, bool)
    ok = listed & np.isfinite(r)
    k = int(industry.max()) + 1
    s = np.bincount(industry[ok], weights=r[ok], minlength=k)
    n = np.bincount(industry[ok], minlength=k)
    mean = s / np.maximum(n, 1)
    return np.where(ok, -(r - mean[industry]), np.nan)


def residual(r, X, w=None, listed=None):
    r, X = np.asarray(r, float), np.asarray(X, float)
    ok = np.isfinite(r) & (np.ones(len(r), bool) if listed is None else np.asarray(listed, bool))
    sw = np.sqrt(np.ones(len(r)) if w is None else np.asarray(w, float))
    b = np.linalg.lstsq(X[ok] * sw[ok, None], r[ok] * sw[ok], rcond=None)[0]
    return np.where(ok, -(r - X @ b), np.nan)


def overnight(open_, prev_close):
    return -(np.asarray(open_, float) / np.asarray(prev_close, float) - 1.0)


def intraday(close, open_):
    return -(np.asarray(close, float) / np.asarray(open_, float) - 1.0)


def forecast(z, ic: float, sigma):
    return ic * np.asarray(sigma, float) * np.asarray(z, float)


def book(alpha, var, w0, gamma: float, aum: float, sigma, adv, half_spread, eta: float, costs: bool = True,
         round_trip: float = 1.0, X=None):
    """Maximise (alpha - X mu)'w - gamma/2 sum var w^2 - cost(w - w0) with X'w = 0 (X: a column of ones, dollar
    neutral, if None). Per name, in d = w - w0 and divided by gamma var: (d - u)^2 / 2 + s|d| + c|d|^(3/2) with
    u = (alpha - X mu) / (gamma var) - w0, a proximal step; mu by Newton's method on the dual, damped."""
    alpha, var, w0 = (np.asarray(a, float) for a in (alpha, var, w0))
    X = np.ones((len(alpha), 1)) if X is None else np.asarray(X, float)
    h = gamma * var
    s = (round_trip * np.asarray(half_spread, float) / h) if costs else np.zeros(len(alpha))
    c = (round_trip * eta * np.asarray(sigma, float) * np.sqrt(aum / np.asarray(adv, float)) / h) if costs \
        else np.zeros(len(alpha))

    def weights(mu):
        u = (alpha - X @ mu) / h - w0
        d = prox_cost(u, s, c)
        y = np.sqrt(np.abs(d))
        slope = np.where(np.abs(u) > s, 2 * y / np.maximum(2 * y + 1.5 * c, 1e-300), 0.0) / h   # -dw/d(X mu)
        return w0 + d, slope

    mu = np.zeros(X.shape[1])
    w, slope = weights(mu)
    for _ in range(100):
        g = X.T @ w
        if np.abs(g).max() < 1e-12:
            break
        H = X.T @ (X * slope[:, None]) + 1e-12 * np.eye(X.shape[1])
        step, t = np.linalg.solve(H, g), 1.0
        while t > 1e-6:
            w_new, slope_new = weights(mu + t * step)
            if np.abs(X.T @ w_new).sum() < np.abs(g).sum():
                break
            t /= 2
        mu, w, slope = mu + t * step, w_new, slope_new
    return w
