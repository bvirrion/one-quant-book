"""firm.capacity -- capacity, decay and crowding (build of One Quant Book 7, chapter 28).

Capacity curves (net return, net Sharpe ratio and dollar profit against the size of the fund, from any backtest run at
each size), the profit-maximising size and the size at which the net Sharpe ratio falls to a fraction of its best;
crowding monitors (the average pairwise correlation of a set of stocks' returns, Lou and Polk's comomentum as its
average over a strategy's long and short legs, the overlap of two books); and an unwind simulator: funds hold
overlapping books, one sells a fraction of its book over some days, each day's net selling moves prices by a
square-root impact of which a share is permanent and the rest decays, and every fund marks its book. NumPy only.

API (stable):
    capacity_curve(sizes, net_returns, vols)    {'size', 'net', 'sr', 'profit'} arrays (profit = size * net return)
    profit_maximising(curve)                    the size with the largest dollar profit (on the grid)
    size_at_fraction(curve, frac, key)          the smallest size at which curve[key] falls below frac * its best,
                                                interpolated on log size (None if it never does)
    avg_pairwise_corr(R)                        mean off-diagonal correlation of the columns of R (periods x assets)
    comomentum(R_long, R_short)                 the average of the two legs' average pairwise correlations
    overlap(w1, w2)                             cosine similarity of two books
    unwind(books, capitals, seller, fraction, days, adv, sigma, eta, permanent, half_life, horizon)
                                                {'price' (horizon+1, n) log price moves, 'pnl' (horizon, funds) daily
                                                P&L as a fraction of each fund's capital, 'cum' (horizon, funds)}
"""
from __future__ import annotations

import math

import numpy as np


def capacity_curve(sizes, net_returns, vols) -> dict:
    s, n, v = (np.asarray(a, float) for a in (sizes, net_returns, vols))
    return {"size": s, "net": n, "sr": n / v, "profit": s * n}


def profit_maximising(curve: dict) -> float:
    return float(curve["size"][int(np.argmax(curve["profit"]))])


def size_at_fraction(curve: dict, frac: float = 0.5, key: str = "sr"):
    y, s = np.asarray(curve[key], float), np.log(np.asarray(curve["size"], float))
    target = frac * y.max()
    start = int(np.argmax(y))
    for i in range(start, len(y) - 1):
        if y[i + 1] < target <= y[i]:
            x = s[i] + (target - y[i]) / (y[i + 1] - y[i]) * (s[i + 1] - s[i])
            return float(math.exp(x))
    return None


def avg_pairwise_corr(R) -> float:
    C = np.corrcoef(np.asarray(R, float).T)
    n = len(C)
    return float((C.sum() - n) / (n * (n - 1)))


def comomentum(R_long, R_short) -> float:
    return 0.5 * (avg_pairwise_corr(R_long) + avg_pairwise_corr(R_short))


def overlap(w1, w2) -> float:
    a, b = np.asarray(w1, float), np.asarray(w2, float)
    return float(a @ b / math.sqrt((a @ a) * (b @ b)))


def unwind(books, capitals, seller: int, fraction: float, days: int, adv, sigma, eta: float = 0.7,
           permanent: float = 0.3, half_life: float = 1.0, horizon: int = 10) -> dict:
    """books (funds, n) weights; capitals (funds,) dollars. The seller trades fraction / days of its book each day for
    `days` days (selling longs, buying back shorts). Day t's impact on stock i is -sign(q) eta sigma_i sqrt(|q| /
    adv_i) for its net dollar trade q; a share `permanent` stays, the rest decays with the half-life (days). Every fund
    holds its book (the seller's shrinking) and marks it to the moved prices."""
    B, K = np.asarray(books, float), np.asarray(capitals, float)
    adv, sigma = np.asarray(adv, float), np.asarray(sigma, float)
    n = B.shape[1]
    decay = 0.5 ** (1.0 / half_life)
    temp, perm = np.zeros(n), np.zeros(n)
    level = np.zeros((horizon + 1, n))
    hold = B.copy()
    pnl = np.zeros((horizon, len(K)))
    for t in range(horizon):
        trade = -B[seller] * fraction / days if t < days else np.zeros(n)
        hold[seller] = hold[seller] + trade                              # trades at the open
        q = trade * K[seller]
        push = np.sign(q) * eta * sigma * np.sqrt(np.abs(q) / adv)
        temp = temp * decay + (1 - permanent) * push
        perm = perm + permanent * push
        level[t + 1] = temp + perm
        move = level[t + 1] - level[t]
        pnl[t] = (hold * move).sum(axis=1)
        pnl[t, seller] -= float(np.abs(trade) @ np.abs(push)) / 2          # it traded through its own move
    return {"price": level, "pnl": pnl, "cum": np.cumsum(pnl, axis=0)}
