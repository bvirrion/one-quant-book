"""firm.voltarget -- volatility targeting and its aggregate flow (build of One Quant Book 8, chapter 26).

Forecast variance from past returns (realised over a window, or exponentially weighted), size a position at a target
(inverse volatility, or inverse variance as in Moreira and Muir), cap the leverage, rebalance only outside a band,
and account for the P&L and turnover. Then add up many funds that target volatility on the same market: the change in
their exposure is a flow, which can be expressed as a share of the market's daily volume and fed back into the price
through a linear impact. NumPy only.

API (stable):
    realised_var(r, window)                   (T,) mean squared return over the previous `window` days, annualised
    ewma_var(r, com)                          (T,) exponentially weighted variance known at each close, annualised
    weights(var, target, cap, power)          target / sigma (power 1) or target^2 / sigma^2 (power 2), capped
    banded(w, band)                           weights rebalanced only when they drift more than `band` (relative)
    run(r, w, cost)                           daily P&L of weights set at t over t + 1, net of cost per unit traded
    spike_flows(base, share, turnover, impact, target, com, cap)
                                              returns with feedback, targeting funds' exposure and their daily flow as
                                              a share of the market's volume
"""
from __future__ import annotations

import math

import numpy as np


def realised_var(r, window: int = 21):
    r = np.asarray(r, float)
    c = np.concatenate([[0.0], np.cumsum(r**2)])
    v = np.full(len(r), np.nan)
    v[window:] = (c[window:-1] - c[:-window - 1]) / window * 252
    return v


def ewma_var(r, com: float = 20.0):
    r = np.asarray(r, float)
    lam = com / (com + 1)
    v = np.empty(len(r))
    s = np.mean(r[:21] ** 2)
    for t in range(len(r)):
        s = lam * s + (1 - lam) * r[t] ** 2
        v[t] = s * 252
    return v


def weights(var, target: float = 0.10, cap: float = 2.0, power: int = 1):
    var = np.asarray(var, float)
    w = (target / np.sqrt(var)) if power == 1 else (target**2 / var)
    return np.where(np.isnan(w), 0.0, np.minimum(w, cap))


def banded(w, band: float = 0.1):
    w = np.asarray(w, float)
    out = np.empty_like(w)
    cur = w[0]
    for t in range(len(w)):
        if abs(w[t] - cur) > band * max(abs(cur), 1e-12):
            cur = w[t]
        out[t] = cur
    return out


def run(r, w, cost: float = 0.0):
    r, w = np.asarray(r, float), np.asarray(w, float)
    pnl = np.zeros(len(r))
    pnl[1:] = w[:-1] * r[1:]
    pnl -= cost * np.abs(np.diff(w, prepend=0.0))
    return pnl


def spike_flows(base, share: float, turnover: float, impact: float, target: float = 0.10, com: float = 20.0,
                cap: float = 2.0):
    """base: the market's returns without the funds' trading. The funds hold `share` of the market's value at an
    exposure of one. On day t they trade toward target / volatility forecast at t - 1's close (capped); their net
    flow, a share of market value, divided by the daily `turnover` is a share of the day's volume, and moves that day's
    price by `impact` times that share. The forecast is updated with the realised return, impact included: the
    feedback loop."""
    base = np.asarray(base, float)
    T = len(base)
    lam = com / (com + 1)
    s = float(np.mean(base[:21] ** 2))
    w = min(cap, target / math.sqrt(s * 252))
    held = w
    r, exp_, flow = np.zeros(T), np.zeros(T), np.zeros(T)
    for t in range(T):
        new = min(cap, target / math.sqrt(s * 252))
        flow[t] = share * (new - held) / turnover
        r[t] = base[t] + impact * flow[t]
        s = lam * s + (1 - lam) * r[t] ** 2
        exp_[t] = new
        held = new * (1 + r[t])
    return {"r": r, "exposure": exp_, "flow": flow}
