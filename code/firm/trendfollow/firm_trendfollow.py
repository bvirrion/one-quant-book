"""firm.trendfollow -- trend-following signals and portfolios (build of One Quant Book 8, chapter 19).

Signal families on a (T, N) panel of daily excess returns, each using data up to the close of day t for a position
held over day t + 1: the sign of the past L-day return (time-series momentum), the sign of a short-over-long moving
average of the cumulative return, and a breakout rule (long at an L-day high, short at an L-day low, otherwise keep
the position). Positions are scaled by an exponentially weighted volatility forecast so that each market targets the
same volatility; speeds are blended by averaging positions; the portfolio can be scaled again to a volatility target.
Costs are charged per unit of notional traded. NumPy only.

API (stable):
    ewma_vol(r, com)                          (T, N) annualised volatility forecast known at each close
    tsmom(r, L)                               (T, N) sign of the past L-day return
    ma_cross(r, short, long)                  (T, N) sign of the short minus long moving average of cumulative r
    breakout(r, L)                            (T, N) +1 / -1 after an L-day high / low, held until the opposite
    positions(signal, vol, target, n)         notional per market: signal x target / (n x vol)
    run(r, pos, cost)                         daily P&L of positions set at t and held over t + 1, net of costs
    vol_target(pnl, target, com, cap)         P&L scaled by target / forecast portfolio volatility, leverage capped
"""
from __future__ import annotations

import numpy as np


def ewma_vol(r, com: float = 60.0):
    r = np.asarray(r, float)
    lam = com / (com + 1.0)
    v = np.empty_like(r)
    s = np.nanmean(r[:21] ** 2, axis=0)
    for t in range(len(r)):
        s = lam * s + (1 - lam) * r[t] ** 2
        v[t] = s
    return np.sqrt(252 * v)


def tsmom(r, L: int):
    c = np.cumsum(np.asarray(r, float), axis=0)
    out = np.zeros_like(c)
    out[L:] = np.sign(c[L:] - c[:-L])
    return out


def ma_cross(r, short: int, long: int):
    c = np.cumsum(np.asarray(r, float), axis=0)
    cs = np.cumsum(np.vstack([np.zeros((1, c.shape[1])), c]), axis=0)
    out = np.zeros_like(c)
    ms = (cs[long:] - cs[long - short:-short]) / short
    ml = (cs[long:] - cs[:-long]) / long
    out[long - 1:] = np.sign(ms - ml)
    return out


def breakout(r, L: int):
    c = np.cumsum(np.asarray(r, float), axis=0)
    out = np.zeros_like(c)
    state = np.zeros(c.shape[1])
    for t in range(L, len(c)):
        window = c[t - L:t]
        state = np.where(c[t] >= window.max(0), 1.0, np.where(c[t] <= window.min(0), -1.0, state))
        out[t] = state
    return out


def positions(signal, vol, target: float = 0.4, n: int | None = None):
    n = n or np.asarray(signal).shape[1]
    return np.asarray(signal) * target / (n * np.maximum(np.asarray(vol), 1e-4))


def run(r, pos, cost):
    """cost: per unit of notional traded, scalar or (N,)."""
    r, pos = np.asarray(r, float), np.asarray(pos, float)
    pnl = np.zeros(len(r))
    pnl[1:] = (pos[:-1] * r[1:]).sum(1)
    trade = np.abs(np.diff(pos, axis=0, prepend=np.zeros((1, pos.shape[1]))))
    pnl -= (trade * np.asarray(cost)).sum(1)
    return pnl


def vol_target(pnl, target: float = 0.10, com: float = 60.0, cap: float = 3.0):
    pnl = np.asarray(pnl, float)
    v = ewma_vol(pnl[:, None], com)[:, 0]
    lev = np.minimum(target / np.maximum(v, 1e-6), cap)
    out = np.zeros_like(pnl)
    out[1:] = lev[:-1] * pnl[1:]
    return out
