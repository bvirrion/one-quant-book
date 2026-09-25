"""firm.multistrat -- running many strategies in one firm (build of One Quant Book 8, chapter 28).

A firm of pods: each pod's daily P&L at unit capital is its own edge and noise plus loadings on a few shared
factors that are quiet most of the time and crash together in rare episodes (the same trade under different names).
One pod's edge dies halfway. The firm allocates by risk budgets (inverse trailing volatility), optionally capping
each shared factor's total exposure using the pods' reported factor loadings (overlap detection), applies drawdown
limits to pods, and nets pods' trades in common instruments. NumPy only.

API (stable):
    PodConfig(...), simulate_pods(cfg, rng)     dict: pnl (T, P), factors (T, K), load (P, K), sr (P,), dead (pod, day)
    allocate(pnl, load, t, window, factor_cap)  (P,) weights at day t: inverse trailing volatility, each factor's
                                                total |loading x weight| capped at factor_cap (None: no cap), gross 1
    run_firm(S, rebalance, factor_cap, limit)   firm daily P&L (weights summing to one) and the (pod, day) stops of a
                                                drawdown limit on each pod's own P&L; stopped pods restart each year
    stop_rate(sr, vol, limit, years, n, rng)    share of pods with Sharpe ratio sr hitting a drawdown `limit` within
                                                `years`, at annual volatility vol
    netting(trades)                             share of gross traded volume saved by netting across pods
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PodConfig:
    pods: int = 10
    days: int = 252 * 20
    vol: float = 0.10                                   # each pod's annual volatility at unit capital
    sr: tuple = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.6, 0.7, 0.8, 0.9)
    load: tuple = ((0.4, 0, 0), (0.4, 0, 0), (0.4, 0, 0), (0, 0.4, 0), (0, 0.4, 0),
                   (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))
    crash_days: tuple = ((1500, 10), (3600, 10), (4400, 10))     # (start, length) of each shared-factor crash
    crash_size: float = 6.0                             # factor fall over a crash, in pod annual volatilities
    dead_pod: int = 9
    dead_day: int = 2520
    dead_sr: float = -0.3


def simulate_pods(cfg: PodConfig | None = None, rng=None):
    cfg = cfg or PodConfig()
    rng = rng or np.random.default_rng(28)
    T, P = cfg.days, cfg.pods
    L = np.array(cfg.load, float)
    K = L.shape[1]
    d = cfg.vol / math.sqrt(252)
    f = d * rng.standard_normal((T, K))
    for s, n in cfg.crash_days:
        f[s:s + n] -= cfg.crash_size * cfg.vol / n
    own = np.sqrt(1 - (L**2).sum(1))
    sr = np.tile(np.array(cfg.sr, float), (T, 1))
    sr[cfg.dead_day:, cfg.dead_pod] = cfg.dead_sr
    pnl = sr * d / math.sqrt(252) + f @ L.T + own * d * rng.standard_normal((T, P))
    return {"pnl": pnl, "factors": f, "load": L, "sr": np.array(cfg.sr, float), "dead": (cfg.dead_pod, cfg.dead_day)}


def allocate(pnl, load, t: int, window: int = 252, factor_cap: float | None = None):
    vol = pnl[max(0, t - window):t].std(0)
    w = 1 / np.maximum(vol, 1e-12)
    w /= w.sum()
    if factor_cap is not None:
        for k in range(load.shape[1]):
            expo = np.abs(load[:, k] * w * len(w)).sum()      # in units of one equal-weight pod
            if expo > factor_cap:
                on = load[:, k] != 0
                w[on] *= factor_cap / expo
        w /= w.sum()
    return w


def run_firm(S, rebalance: int = 21, factor_cap: float | None = None, limit: float | None = None):
    pnl, load = S["pnl"], S["load"]
    T, P = pnl.shape
    firm = np.zeros(T)
    alive = np.ones(P, bool)
    peak, eq = np.zeros(P), np.zeros(P)
    stops = []
    w = np.full(P, 1 / P)
    for t in range(252, T):
        if (t - 252) % rebalance == 0:
            w = allocate(pnl, load, t, 252, factor_cap)
        firm[t] = (w * alive * pnl[t]).sum()
        eq += pnl[t] * alive
        peak = np.maximum(peak, eq)
        if limit is not None:
            hit = alive & (peak - eq > limit)
            for i in np.flatnonzero(hit):
                stops.append((i, t))
            alive &= ~hit
            eq[hit] = peak[hit] = 0.0
            if (t - 252) % 252 == 0:                           # stopped pods restart at the start of each year
                alive[:] = True
    return firm, stops


def stop_rate(sr: float, vol: float, limit: float, years: float = 1.0, n: int = 20_000, rng=None):
    rng = rng or np.random.default_rng(1)
    days = int(252 * years)
    d = vol / math.sqrt(252)
    x = np.cumsum(sr * d / math.sqrt(252) + d * rng.standard_normal((n, days)), axis=1)
    dd = np.maximum.accumulate(np.maximum(x, 0), axis=1) - x
    return float((dd.max(1) > limit).mean())


def netting(trades):
    trades = np.asarray(trades, float)
    gross = np.abs(trades).sum()
    return float(1 - np.abs(trades.sum(0)).sum() / gross)
