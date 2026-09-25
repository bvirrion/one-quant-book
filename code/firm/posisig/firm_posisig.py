"""firm.posisig -- positioning and sentiment signals (build of One Quant Book 8, chapter 24).

Positions are measured on a report day and published later (the CFTC's Commitments of Traders: Tuesday's positions,
Friday's release). This module turns a daily position series into what a trader knows each day under a reporting
schedule, simulates a futures market with hedging pressure (hedgers' net short position, an AR(1), earning
speculators a premium proportional to it) and speculators who absorb it and chase trends, and measures a signal's
rank IC with forward returns. NumPy only.

API (stable):
    published(x, every, offset, lag)                  (T, ...) value of the latest report known at each day's close
    hedging_market(r, vol, half_life, premium, chase, noise, rng)
                                                      dict: r (returns with the premium), hedge (hedgers' net short),
                                                      spec (speculators' net long), both in standard deviations
    forward(r, h)                                     (T, N) sum of returns over days t+1 .. t+h (NaN at the end)
    ic(signal, fwd, step, overlap)                    mean cross-sectional rank IC over days `step` apart, and its t
                                                      (divided by sqrt(overlap) for overlapping forward returns)
    zscore(x, window)                                 trailing z-score along axis 0 (window observations before t)
"""
from __future__ import annotations

import math

import numpy as np


def published(x, every: int = 5, offset: int = 1, lag: int = 3):
    x = np.asarray(x, float)
    T = len(x)
    out = np.full(x.shape, np.nan)
    last = None
    report_days = set(range(offset, T, every))
    pending = []
    for t in range(T):
        if t in report_days:
            pending.append((t + lag, x[t].copy()))
        while pending and pending[0][0] <= t:
            last = pending.pop(0)[1]
        if last is not None:
            out[t] = last
    return out


def hedging_market(r, vol, half_life: float = 20.0, premium: float = 0.3, chase: float = 0.5, noise: float = 0.5,
                   rng=None):
    rng = rng or np.random.default_rng(24)
    r = np.asarray(r, float)
    T, N = r.shape
    phi = math.exp(-math.log(2) / half_life)
    h = np.zeros((T, N))
    for t in range(1, T):
        h[t] = phi * h[t - 1] + math.sqrt(1 - phi**2) * rng.standard_normal(N)
    out = r.copy()
    out[1:] += premium * np.asarray(vol) * h[:-1] / 252.0          # hedgers short -> speculators long earn the premium
    c = np.cumsum(out, axis=0)
    trend = np.zeros((T, N))
    trend[60:] = (c[60:] - c[:-60]) / (np.asarray(vol) * math.sqrt(60 / 252))
    spec = h + chase * trend + noise * rng.standard_normal((T, N))
    return {"r": out, "hedge": h, "spec": spec}


def forward(r, h: int):
    c = np.vstack([np.zeros((1, np.asarray(r).shape[1])), np.cumsum(r, axis=0)])
    f = np.full(np.asarray(r).shape, np.nan)
    f[:-h] = c[1 + h:] - c[1:-h]
    return f


def ic(signal, fwd, step: int = 5, overlap: int = 1):
    vals = []
    for t in range(0, len(signal), step):
        m = ~np.isnan(signal[t]) & ~np.isnan(fwd[t])
        if m.sum() > 2:
            a, b = np.argsort(np.argsort(signal[t][m])), np.argsort(np.argsort(fwd[t][m]))
            vals.append(np.corrcoef(a, b)[0, 1])
    v = np.array(vals)
    return float(v.mean()), float(v.mean() / v.std(ddof=1) * math.sqrt(len(v) / overlap))


def zscore(x, window: int):
    x = np.asarray(x, float)
    z = np.full(x.shape, np.nan)
    for t in range(window, len(x)):
        w = x[t - window:t]
        z[t] = (x[t] - w.mean(0)) / w.std(0, ddof=1)
    return z
