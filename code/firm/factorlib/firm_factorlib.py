"""firm.factorlib -- the equity factor canon (build of One Quant Book 8, chapter 6).

Factor portfolios from characteristics known point in time: sorts into long-short quantile books (equal or value
weights), characteristic-weighted books (weights proportional to demeaned ranks), composites of several
characteristics, betting against beta (low-beta stocks levered to a beta of one against high-beta stocks delevered to
one), and the two ways of timing book-to-price: with the current price (the book as last filed, divided by today's
price) or with the price of the book's own date (the Fama-French convention). NumPy only.

API (stable):
    sort_book(signal, universe, q, cap)           +0.5 over the top q, -0.5 over the bottom q; value weights if cap
    char_book(signal, universe)                   weights proportional to demeaned cross-sectional ranks, gross 1
    composite(*signals)                           mean of cross-sectional z-scores, NaN only where all are NaN
    bab_book(beta, universe, q)                   long the lowest q scaled to beta 1, short the highest q scaled to 1
    book_to_price(anchor_log_bp, cum, listed, current)
                                                  log book-to-price from anchors log(B / P) + cum at each anchor day
                                                  (NaN elsewhere): with the current price (current) or held fixed
"""
from __future__ import annotations

import numpy as np


def _rank(x):
    out = np.full(x.shape, np.nan)
    ok = np.isfinite(x)
    out[ok] = np.argsort(np.argsort(x[ok], kind="stable"), kind="stable")
    return out


def sort_book(signal, universe, q: float = 0.1, cap=None):
    s = np.where(universe, np.asarray(signal, float), np.nan)
    W = np.zeros(s.shape)
    for t in range(s.shape[0]):
        ok = np.isfinite(s[t])
        n = int(ok.sum() * q)
        if n < 2:
            continue
        idx = np.flatnonzero(ok)
        order = idx[np.argsort(s[t, ok], kind="stable")]
        for side, names in ((0.5, order[-n:]), (-0.5, order[:n])):
            v = np.ones(n) if cap is None else np.nan_to_num(np.asarray(cap, float)[t, names])
            W[t, names] = side * v / v.sum()
    return W


def char_book(signal, universe):
    s = np.where(universe, np.asarray(signal, float), np.nan)
    W = np.zeros(s.shape)
    for t in range(s.shape[0]):
        r = _rank(s[t])
        ok = np.isfinite(r)
        if ok.sum() < 2:
            continue
        d = r[ok] - r[ok].mean()
        W[t, ok] = d / np.abs(d).sum()
    return W


def composite(*signals):
    zs = []
    for s in signals:
        s = np.asarray(s, float)
        m, sd = np.nanmean(s, axis=1, keepdims=True), np.nanstd(s, axis=1, keepdims=True)
        zs.append((s - m) / np.where(sd > 0, sd, np.nan))
    Z = np.stack(zs)
    n = np.isfinite(Z).sum(axis=0)
    return np.where(n > 0, np.nansum(Z, axis=0) / np.maximum(n, 1), np.nan)


def bab_book(beta, universe, q: float = 0.2):
    b = np.where(universe, np.asarray(beta, float), np.nan)
    W = np.zeros(b.shape)
    for t in range(b.shape[0]):
        ok = np.isfinite(b[t]) & (b[t] > 0)
        n = int(ok.sum() * q)
        if n < 2:
            continue
        idx = np.flatnonzero(ok)
        order = idx[np.argsort(b[t, ok], kind="stable")]
        lo, hi = order[:n], order[-n:]
        W[t, lo] = 1.0 / n / b[t, lo].mean()
        W[t, hi] = -1.0 / n / b[t, hi].mean()
    return W


def book_to_price(anchor, cum, listed, current: bool = True):
    """anchor[t, i] = log(B / P) at the anchor day plus cum[t, i] (the log price index then), NaN elsewhere. With the
    current price the signal is the latest anchor minus today's cum; held fixed it is the latest log(B / P) itself."""
    anchor, cum = np.asarray(anchor, float), np.asarray(cum, float)
    T, M = anchor.shape
    idx = np.where(np.isfinite(anchor), np.arange(T)[:, None], 0)
    idx = np.maximum.accumulate(idx, axis=0)
    last = anchor[idx, np.arange(M)[None, :]]
    base = cum[idx, np.arange(M)[None, :]]
    out = last - cum if current else last - base
    return np.where(listed & np.isfinite(last), out, np.nan)
