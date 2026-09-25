"""firm.momstrat -- momentum signals and crash management (build of One Quant Book 8, chapter 5).

Signals on a (T, N) panel, row t known at the close of t: total-return momentum over a lookback skipping the most recent
month, residual momentum (the sum of factor-model residuals over the same window divided by their standard deviation),
industry momentum (each stock gets its industry's cap-weighted past return); the decile long-short book; volatility
scaling of a strategy's returns to a target from its own trailing volatility; a market-state flag (bear markets, when
momentum crashes are more likely). NumPy only.

API (stable):
    total_mom(ret, lookback, skip)                 past return over [t - lookback + 1, t - skip]
    residual_mom(E, lookback, skip)                sum of residuals over the window / their standard deviation
    industry_mom(ret, industry, cap, lookback, skip)
    decile_book(signal, universe, q)               weights: +0.5 spread over the top q, -0.5 over the bottom q
    vol_scale(r, target, window, periods)          weights w_t = target / (trailing vol up to t - 1), NaN before
    bear(mkt, window)                              True where the market's return over the last window days is negative
"""
from __future__ import annotations

import math

import numpy as np


def _roll(x, w):
    x = np.asarray(x, float)
    c = np.concatenate([np.zeros((1,) + x.shape[1:]), np.cumsum(np.nan_to_num(x), axis=0)])
    n = np.concatenate([np.zeros((1,) + x.shape[1:]), np.cumsum(np.isfinite(x), axis=0)])
    out = np.full(x.shape, np.nan)
    out[w - 1:] = c[w:] - c[:-w]
    full = np.zeros(x.shape, bool)
    full[w - 1:] = (n[w:] - n[:-w]) == w
    return np.where(full, out, np.nan)


def _shift(x, k):
    out = np.full(np.shape(x), np.nan)
    out[k:] = np.asarray(x, float)[: len(out) - k] if k else x
    return out


def total_mom(ret, lookback: int = 252, skip: int = 21):
    return np.expm1(_shift(_roll(np.log1p(np.asarray(ret, float)), lookback - skip), skip))


def residual_mom(E, lookback: int = 252, skip: int = 21):
    w = lookback - skip
    s1, s2 = _roll(E, w), _roll(np.asarray(E, float) ** 2, w)
    sd = np.sqrt(np.maximum(s2 / w - (s1 / w) ** 2, 1e-300))
    return _shift(s1 / (sd * math.sqrt(w)), skip)


def industry_mom(ret, industry, cap, lookback: int = 252, skip: int = 21):
    ret, cap, industry = np.asarray(ret, float), np.asarray(cap, float), np.asarray(industry)
    K = int(industry.max()) + 1
    cprev = np.vstack([cap[:1], cap[:-1]])
    ind = np.zeros((ret.shape[0], K))
    for k in range(K):
        m = industry == k
        w = np.nan_to_num(cprev[:, m])
        ind[:, k] = (w * np.nan_to_num(ret[:, m])).sum(axis=1) / np.maximum(w.sum(axis=1), 1e-300)
    return total_mom(ind, lookback, skip)[:, industry]


def decile_book(signal, universe, q: float = 0.1):
    s = np.where(universe, np.asarray(signal, float), np.nan)
    W = np.zeros(s.shape)
    for t in range(s.shape[0]):
        ok = np.isfinite(s[t])
        n = int(ok.sum() * q)
        if n < 2:
            continue
        idx = np.flatnonzero(ok)
        order = idx[np.argsort(s[t, ok], kind="stable")]
        W[t, order[-n:]] = 0.5 / n
        W[t, order[:n]] = -0.5 / n
    return W


def vol_scale(r, target: float, window: int, periods: int = 252):
    r = np.asarray(r, float)
    out = np.full(len(r), np.nan)
    for t in range(window, len(r)):
        out[t] = target / (r[t - window:t].std(ddof=1) * math.sqrt(periods))
    return out


def bear(mkt, window: int = 504):
    lr = np.log1p(np.asarray(mkt, float))
    c = np.concatenate([[0.0], np.cumsum(lr)])
    out = np.zeros(len(lr), bool)
    out[window - 1:] = (c[window:] - c[:-window]) < 0
    return out
