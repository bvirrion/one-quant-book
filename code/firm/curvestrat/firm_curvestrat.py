"""firm.curvestrat -- calendar spreads and curve trades (build of One Quant Book 8, chapter 21).

Generic futures series (contract 1 = the nearby, 2 = the next, ...) change identity at each expiry. This module tracks
contracts by identity: m[t] is the serial number of the nearby on day t (it increases the day after each expiry), so
contract a on day t is generic series a - m[t] + 1. A calendar spread is long the nearer contract of a pair and short
the farther; the pair traded on day t is the nearest one clear of expiry (it moves one contract out `days_before`
trading days before the nearby expires), and its P&L from t to t + 1 follows the same two contracts through a roll of
the generic series. Mean-reversion signals are z-scores of the log spread against its rolling mean; a regime filter
blocks positions that bet on a very steep contango narrowing. NumPy only.

API (stable):
    serials(expiry)                               m (T,) serial number of the nearby contract
    pair_pnl(C, m, near, days_before, expiry)     (T,) dollar P&L of +1 near / -1 far held from t - 1 to t, and
                                                  (T,) the log spread ln(F_near / F_far) of the pair held at t
    zscore(x, window)                             (x - rolling mean) / rolling sd, from data up to t
    positions(z, vol, target, cap, block)         -z scaled to target / vol, capped; `block` (bool) forbids long spreads
    band(z, vol, enter, leave, target, block)     enter against |z| > enter at target / vol, hold until |z| < leave or z
                                                  changes sign; `block` forbids (and closes) long spreads
    spread_carry(log_spread, days)                annual carry implied by a log spread of contracts `days` apart
"""
from __future__ import annotations

import numpy as np


def serials(expiry):
    e = np.asarray(expiry, bool)
    m = np.zeros(len(e), int)
    m[1:] = np.cumsum(e[:-1])
    return m


def _price(C, t, serial, m):
    j = serial - m[t]
    return C[t, j] if 0 <= j < C.shape[1] else np.nan


def pair_pnl(C, m, near: int = 0, days_before: int = 5, expiry=None):
    """C (T, K) generic settlements. near = 0: contracts 1-2 (2-3 within `days_before` of the nearby's expiry)."""
    C = np.asarray(C, float)
    T = len(C)
    exp_days = np.flatnonzero(np.asarray(expiry, bool)) if expiry is not None else np.array([], int)
    held = np.zeros(T, int)                       # serial number of the near leg chosen at the close of t
    for t in range(T):
        nxt = exp_days[exp_days >= t]
        roll = len(nxt) > 0 and nxt[0] - t < days_before
        held[t] = m[t] + near + (1 if roll else 0)
    pnl = np.zeros(T)
    spread = np.full(T, np.nan)
    for t in range(T):
        a = held[t]
        fn, ff = _price(C, t, a, m), _price(C, t, a + 1, m)
        if fn > 0 and ff > 0:
            spread[t] = np.log(fn / ff)
        if t > 0:
            b = held[t - 1]
            leg = [_price(C, t, k, m) - _price(C, t - 1, k, m) for k in (b, b + 1)]
            pnl[t] = leg[0] - leg[1]
    return np.nan_to_num(pnl), spread


def zscore(x, window: int = 60):
    x = np.asarray(x, float)
    z = np.full(len(x), np.nan)
    for t in range(window, len(x)):
        w = x[t - window + 1:t + 1]
        w = w[~np.isnan(w)]
        if len(w) > window // 2 and w.std() > 0 and not np.isnan(x[t]):
            z[t] = (x[t] - w.mean()) / w.std()
    return z


def positions(z, vol, target: float = 1.0, cap: float = 2.0, block=None):
    p = -np.clip(np.nan_to_num(np.asarray(z, float)), -cap, cap) * target / np.maximum(np.asarray(vol, float), 1e-9)
    if block is not None:
        p = np.where(np.asarray(block, bool) & (p > 0), 0.0, p)
    return p


def spread_carry(log_spread, days: float = 21.0):
    return np.asarray(log_spread, float) * 252.0 / days


def band(z, vol, enter: float = 1.5, leave: float = 0.5, target: float = 0.10, block=None):
    z, vol = np.asarray(z, float), np.asarray(vol, float)
    p = np.zeros(len(z))
    cur = 0.0
    for t in range(len(z)):
        if not np.isnan(z[t]):
            if cur == 0.0 and abs(z[t]) > enter:
                cur = -np.sign(z[t]) * target / max(vol[t], 1e-9)
            elif cur != 0.0 and (abs(z[t]) < leave or np.sign(z[t]) == np.sign(cur)):
                cur = 0.0
        if block is not None and block[t] and cur > 0:
            cur = 0.0
        p[t] = cur
    return p
