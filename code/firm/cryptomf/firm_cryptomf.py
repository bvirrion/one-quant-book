"""firm.cryptomf -- crypto medium-frequency strategies (build of One Quant Book 8, chapter 27).

Carry accounting for a delta-neutral book (long spot, short a perpetual or dated future): the funding or basis
earned per year on the capital the book ties up (spot plus the future's margin), net of trading costs. A coin
universe simulator (a market factor, coin-specific shocks with fat tails, a planted persistent drift that makes
cross-sectional momentum pay, and exchange flows that lead returns a little) with a weekly momentum book and a flow
signal. Venue risk: books spread over venues that fail independently with a yearly probability and a loss given
failure, and the distribution of the book's yearly loss. NumPy only.

API (stable):
    carry_return(funding, margin, cost)          yearly return on capital of long spot / short future
    basis_carry(fut, spot, days)                 annualised basis of a dated future
    CoinConfig(...), simulate_coins(cfg, rng)    dict: r (days, coins) daily returns, flow (days, coins), drift (truth)
    momentum_book(r, lookback, hold, q, cost)    weekly long-short on past returns (top minus bottom quantile)
    flow_ic(flow, r, window)                     rank IC of the z-scored net inflow with the next day's return
    venue_losses(k, p, lgd, years, rng)          (years,) yearly loss as a share of capital spread evenly on k venues
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def carry_return(funding, margin: float = 0.2, cost: float = 0.002):
    return (np.asarray(funding, float) - cost) / (1.0 + margin)


def basis_carry(fut, spot, days: float):
    return (np.asarray(fut, float) / np.asarray(spot, float) - 1.0) * 365.0 / days


@dataclass(frozen=True)
class CoinConfig:
    coins: int = 50
    days: int = 2190                 # six years of 365 days
    mkt_vol: float = 0.60            # annual volatility of the crypto market factor
    spec_vol: float = 0.80           # annual coin-specific volatility
    t_df: float = 3.0
    drift_sd: float = 0.6            # annual sd of the planted persistent drift
    drift_half_life: float = 60.0    # days
    flow_skill: float = 0.03         # correlation of today's net inflow with tomorrow's specific return (negative)


def simulate_coins(cfg: CoinConfig | None = None, rng=None):
    cfg = cfg or CoinConfig()
    rng = rng or np.random.default_rng(27)
    T, N = cfg.days, cfg.coins
    t = lambda size: rng.standard_t(cfg.t_df, size) / math.sqrt(cfg.t_df / (cfg.t_df - 2))  # noqa: E731
    mkt = cfg.mkt_vol / math.sqrt(365) * t(T)
    spec = cfg.spec_vol / math.sqrt(365) * t((T, N))
    phi = math.exp(-math.log(2) / cfg.drift_half_life)
    a = np.zeros((T, N))
    a[0] = cfg.drift_sd * rng.standard_normal(N)
    for d in range(1, T):
        a[d] = phi * a[d - 1] + math.sqrt(1 - phi**2) * cfg.drift_sd * rng.standard_normal(N)
    r = mkt[:, None] + spec + a / 365
    z = spec / (cfg.spec_vol / math.sqrt(365))
    flow = np.zeros((T, N))
    flow[:-1] = -cfg.flow_skill * z[1:] + math.sqrt(1 - cfg.flow_skill**2) * rng.standard_normal((T - 1, N))
    return {"r": r, "flow": flow, "drift": a, "mkt": mkt}


def momentum_book(r, lookback: int = 21, hold: int = 7, q: float = 0.2, cost: float = 0.001):
    r = np.asarray(r, float)
    T, N = r.shape
    c = np.vstack([np.zeros((1, N)), np.cumsum(r, axis=0)])
    w = np.zeros((T, N))
    cur = np.zeros(N)
    for d in range(lookback, T):
        if (d - lookback) % hold == 0:
            past = c[d + 1] - c[d + 1 - lookback]
            k = max(1, int(q * N))
            order = np.argsort(past)
            cur = np.zeros(N)
            cur[order[-k:]], cur[order[:k]] = 0.5 / k, -0.5 / k
        w[d] = cur
    pnl = np.zeros(T)
    pnl[1:] = (w[:-1] * r[1:]).sum(1)
    pnl -= cost * np.abs(np.diff(w, axis=0, prepend=np.zeros((1, N)))).sum(1)
    return pnl


def flow_ic(flow, r, window: int = 30):
    flow, r = np.asarray(flow, float), np.asarray(r, float)
    ics = []
    for d in range(window, len(r) - 1):
        w = flow[d - window:d]
        z = (flow[d] - w.mean(0)) / w.std(0)
        a, b = np.argsort(np.argsort(z)), np.argsort(np.argsort(r[d + 1]))
        ics.append(np.corrcoef(a, b)[0, 1])
    v = np.array(ics)
    return float(v.mean()), float(v.mean() / v.std(ddof=1) * math.sqrt(len(v)))


def venue_losses(k: int, p: float, lgd: float, years: int = 100_000, rng=None):
    rng = rng or np.random.default_rng(28)
    fails = rng.random((years, k)) < p
    return fails.sum(1) * lgd / k
