"""firm.powergas -- day-ahead against intraday power, forecast-error trades and battery optimisation (Book 9, ch. 23).

Day-ahead prices are given (the chapter uses Germany's, 2024-2025). Intraday prices for the same hours are simulated:
the day-ahead auction cleared on a wind forecast, and when more wind arrives than forecast the intraday price falls by
beta EUR/MWh per GW of the error; the error is autocorrelated through the day; other intraday noise is added. A
trader who forecasts part of the error sells day-ahead and buys back intraday when expecting more wind, and the reverse.
A battery (power, energy, round-trip efficiency, cycles a day) is scheduled by dynamic programming on each day's
day-ahead prices, then may re-optimise against intraday prices, paying a half-spread on every MWh it changes.
NumPy only.

API (stable):
    PowerConfig(...)                             parameters (seed 173)
    intraday(da, cfg)                            (intraday prices, wind forecast errors in GW), both (days, 24)
    forecast_trade(da, idp, err, cfg)            per-hour P&L (EUR per MWh traded) of trading a partial error forecast
    battery(prices, cfg, committed=None)         best daily schedules (grid MWh, + buys) and cash; against a committed
                                                 schedule, deviations are paid at `prices` plus the half-spread
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PowerConfig:
    seed: int = 173
    beta: float = 3.05            # EUR/MWh per GW of unexpected wind (the chapter's residual-load slope)
    err_sd: float = 2.0           # GW, sd of the day-ahead wind forecast error in an hour ...
    err_phi: float = 0.9          # ... autocorrelated hour to hour
    id_noise: float = 6.0         # EUR/MWh, other intraday price noise
    skill: float = 0.5            # correlation of the trader's error forecast with the error
    threshold: float = 0.5        # trade when the forecast exceeds this many sds
    id_cost: float = 1.0          # EUR/MWh half-spread paid on intraday trades
    power: int = 1                # MW (one step of the state of charge per hour)
    energy: int = 2               # MWh
    eff: float = 0.88             # round-trip efficiency
    cycles: int = 1               # full cycles a day


def intraday(da: np.ndarray, cfg: PowerConfig | None = None) -> tuple[np.ndarray, np.ndarray]:
    cfg = cfg or PowerConfig()
    rng = np.random.default_rng(cfg.seed)
    days = da.shape[0]
    err = np.empty((days, 24))
    err[:, 0] = cfg.err_sd * rng.standard_normal(days)
    step = cfg.err_sd * math.sqrt(1 - cfg.err_phi ** 2)
    for h in range(1, 24):
        err[:, h] = cfg.err_phi * err[:, h - 1] + step * rng.standard_normal(days)
    idp = da - cfg.beta * err + cfg.id_noise * rng.standard_normal((days, 24))
    return idp, err


def forecast_trade(da: np.ndarray, idp: np.ndarray, err: np.ndarray, cfg: PowerConfig | None = None) -> dict:
    """Sell 1 MWh day-ahead and buy it back intraday when the forecast says more wind than the auction assumed; the
    reverse when less; nothing when the forecast is small. P&L per hour in EUR."""
    cfg = cfg or PowerConfig()
    rng = np.random.default_rng(cfg.seed + 1)
    signal = cfg.skill * err / cfg.err_sd + math.sqrt(1 - cfg.skill ** 2) * rng.standard_normal(err.shape)
    pos = np.where(signal > cfg.threshold, -1.0, np.where(signal < -cfg.threshold, 1.0, 0.0))   # + buys day-ahead
    pnl = pos * (idp - da) - cfg.id_cost * np.abs(pos)
    return {"pnl": pnl, "pos": pos, "ic": float(np.corrcoef(signal.ravel(), (da - idp).ravel())[0, 1])}


def battery(prices: np.ndarray, cfg: PowerConfig | None = None, committed: np.ndarray | None = None) -> dict:
    """Schedule each day by dynamic programming over (state of charge, energy charged so far). Charging one MWh into
    the battery buys 1/sqrt(eff) MWh from the grid; discharging one sells sqrt(eff). Without `committed`, cash is
    -price x grid MWh. With `committed` (a schedule already sold day-ahead), cash is the cost of changing it at these
    prices: -price x (new - committed) - id_cost x |new - committed|."""
    cfg = cfg or PowerConfig()
    days = prices.shape[0]
    e, cmax = cfg.energy, cfg.energy * cfg.cycles
    grid = {1: 1 / math.sqrt(cfg.eff), 0: 0.0, -1: -math.sqrt(cfg.eff)}          # grid MWh per step of charge
    old = np.zeros_like(prices) if committed is None else committed
    cost = 0.0 if committed is None else cfg.id_cost
    V = np.full((days, e + 1, cmax + 1), -np.inf)
    V[:, 0, :] = 0.0                                                          # end empty
    policy = []
    for h in range(23, -1, -1):
        W, A = np.full_like(V, -np.inf), np.zeros(V.shape, int)
        for s in range(e + 1):
            for c in range(cmax + 1):
                for a in (-1, 0, 1):
                    s2, c2 = s + a * cfg.power, c + max(a, 0) * cfg.power
                    if not (0 <= s2 <= e and c2 <= cmax):
                        continue
                    g = grid[a] * cfg.power
                    v = -prices[:, h] * (g - old[:, h]) - cost * np.abs(g - old[:, h]) + V[:, s2, c2]
                    better = v > W[:, s, c]
                    W[:, s, c], A[:, s, c] = np.where(better, v, W[:, s, c]), np.where(better, a, A[:, s, c])
        V = W
        policy.append(A)
    policy.reverse()
    sched = np.zeros_like(prices)
    s, c, idx = np.zeros(days, int), np.zeros(days, int), np.arange(days)
    for h in range(24):
        a = policy[h][idx, s, c]
        sched[:, h] = np.vectorize(grid.get)(a) * cfg.power
        s, c = s + a * cfg.power, c + np.maximum(a, 0) * cfg.power
    return {"grid": sched, "cash": V[:, 0, 0]}
