"""firm.spreaddecomp -- decomposing the spread (build of One Quant Book 10, chapter 5).

Trades are arrays (t, price, sign, qty) with sign +1 for buyer-initiated; quotes are a mid-price path (times, mids).
Half-spreads are signed from the aggressor's side: effective eps (p - m_t), realised eps (p - m_{t+h}), price impact
eps (m_{t+h} - m_t); effective = realised + impact holds trade by trade.

API (stable):
    mid_at(times, mids, t)                         the mid in force at each time t (step function)
    quoted_spread(times, bids, asks, end)          time-weighted mean quoted spread
    decompose(trades, times, mids, h)              share-weighted mean effective, realised and impact half-spreads
    glosten_harris(prices, signs, sizes)          p = m + eps (c0 + c1 v), m moves eps (z0 + z1 v): c0, c1, z0, z1
    huang_stoll(prices, signs)                     basic model dP_t = (S/2) dQ_t + lam (S/2) Q_{t-1} + e: S, lam
    mrr(prices, signs)                             Madhavan-Richardson-Roomans: theta (information), phi (cost),
                                                   rho, and
                                                   the information share theta / (theta + phi)
    hasbrouck_var(r, x, lags, steps)               bivariate VAR of mid changes r and trade signs x: cumulative
                                                   response of the mid to one trade (permanent impact) and the IRF
    corwin_schultz(high, low)                      spread (relative) from consecutive high-low ranges, negatives at 0
    abdi_ranaldo(close, high, low)                 spread (relative) from close and mid-range
"""
from __future__ import annotations

import math

import numpy as np


def mid_at(times, mids, t) -> np.ndarray:
    times = np.asarray(times)
    i = np.searchsorted(times, np.asarray(t), side="right") - 1
    return np.asarray(mids)[np.clip(i, 0, len(times) - 1)]


def quoted_spread(times, bids, asks, end: float) -> float:
    t = np.asarray(times, float)
    s = np.asarray(asks, float) - np.asarray(bids, float)
    dt = np.diff(np.concatenate([t, [end]]))
    return float((s * dt).sum() / dt.sum())


def decompose(trades, times, mids, h: float) -> dict:
    t, p, eps, q = trades["t"], trades["price"].astype(float), trades["sign"].astype(float), trades["qty"].astype(float)
    m0 = mid_at(times, mids, t - 1e-9)
    mh = mid_at(times, mids, t + h)
    eff, real, imp = eps * (p - m0), eps * (p - mh), eps * (mh - m0)
    w = q / q.sum()
    return {"effective": float(w @ eff), "realised": float(w @ real), "impact": float(w @ imp),
            "impact_share": float((w @ imp) / (w @ eff))}


def _ols(y, X):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def huang_stoll(prices, signs) -> dict:
    p = np.asarray(prices, float)
    q = np.asarray(signs, float)
    dp, dq, q1 = np.diff(p), np.diff(q), q[:-1]
    a, b = _ols(dp, np.column_stack([dq, q1]))
    return {"spread": float(2 * a), "lam": float(b / a)}


def glosten_harris(prices, signs, sizes) -> dict:
    """dp_t = c0 d(eps_t) + c1 d(eps_t v_t) + z0 eps_t + z1 eps_t v_t + noise, by least squares."""
    p, e, v = np.asarray(prices, float), np.asarray(signs, float), np.asarray(sizes, float)
    ev = e * v
    c0, c1, z0, z1 = _ols(np.diff(p), np.column_stack([np.diff(e), np.diff(ev), e[1:], ev[1:]]))
    return {"c0": float(c0), "c1": float(c1), "z0": float(z0), "z1": float(z1)}


def mrr(prices, signs) -> dict:
    """dp_t = (phi + theta) x_t - (phi + rho theta) x_{t-1} + noise, with rho the first-order autocorrelation of the
    signs (the surprise in x_t is x_t - rho x_{t-1}); estimated by least squares with rho from the signs."""
    p = np.asarray(prices, float)
    x = np.asarray(signs, float)
    rho = float(np.corrcoef(x[1:], x[:-1])[0, 1])
    a, b = _ols(np.diff(p), np.column_stack([x[1:], -x[:-1]]))
    theta = (a - b) / (1 - rho)
    phi = a - theta
    return {"theta": float(theta), "phi": float(phi), "rho": rho, "info_share": float(theta / (theta + phi))}


def hasbrouck_var(r, x, lags: int = 5, steps: int = 20) -> dict:
    """r_t: mid change from before trade t to before trade t+1; x_t: sign of trade t. Equations
    r_t = sum a_i r_{t-i} + sum b_i x_{t-i} (i >= 0 for x) and x_t = sum c_i r_{t-i} + sum d_i x_{t-i} (i >= 1).
    Returns the cumulative response of the mid to a unit trade shock and the step responses."""
    r, x = np.asarray(r, float), np.asarray(x, float)
    n = len(r)
    rows = range(lags, n)
    Xr = np.array([[r[t - i] for i in range(1, lags + 1)] + [x[t - i] for i in range(0, lags + 1)] for t in rows])
    Xx = np.array([[r[t - i] for i in range(1, lags + 1)] + [x[t - i] for i in range(1, lags + 1)] for t in rows])
    br = _ols(r[lags:], Xr)
    bx = _ols(x[lags:], Xx)
    a, b = br[:lags], br[lags:]
    c, d = bx[:lags], bx[lags:]
    rr, xx = [], []
    for s in range(steps):
        xs = 1.0 if s == 0 else sum(c[i - 1] * rr[s - i] for i in range(1, min(s, lags) + 1)) + \
            sum(d[i - 1] * xx[s - i] for i in range(1, min(s, lags) + 1))
        xx.append(xs)
        rs = b[0] * xs + sum(a[i - 1] * rr[s - i] + b[i] * xx[s - i] for i in range(1, min(s, lags) + 1))
        rr.append(rs)
    return {"permanent": float(np.sum(rr)), "irf": np.cumsum(rr)}


def corwin_schultz(high, low) -> float:
    h, lo = np.log(np.asarray(high, float)), np.log(np.asarray(low, float))
    beta = (h[:-1] - lo[:-1]) ** 2 + (h[1:] - lo[1:]) ** 2
    gamma = (np.maximum(h[:-1], h[1:]) - np.minimum(lo[:-1], lo[1:])) ** 2
    k = 3 - 2 * math.sqrt(2)
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    s = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    return float(np.mean(np.maximum(s, 0.0)))


def abdi_ranaldo(close, high, low) -> float:
    c = np.log(np.asarray(close, float))
    eta = 0.5 * (np.log(np.asarray(high, float)) + np.log(np.asarray(low, float)))
    s2 = 4 * np.mean((c[:-1] - eta[:-1]) * (c[:-1] - eta[1:]))
    return float(math.sqrt(max(s2, 0.0)))
