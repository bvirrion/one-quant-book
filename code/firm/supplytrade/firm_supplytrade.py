"""firm.supplytrade -- auction concessions and the trade around them (build of One Quant Book 9, chapter 13).

A benchmark yield with daily noise and a monthly auction calendar: each auction's size is drawn, and dealers'
capacity to absorb it varies from auction to auction; in the five days before an auction the yield rises by a
concession proportional to size over capacity, and in the five days after it gives back a share of it. The supply
trade is short duration from five days before the auction to its close and long from the close to five days after,
at a cost per leg; results per auction are in basis points of yield (multiply by DV01 for money). NumPy only.

API (stable):
    SupplyConfig(...)                          parameters (seed 127)
    simulate_auctions(cfg)                     dict of daily yields (bp), auction days, sizes, capacities, concessions
    supply_trade(sim, cfg, pre, post)          per-auction P&L (bp) of the short-before and long-after legs, net of cost
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

YEAR = 252


@dataclass(frozen=True)
class SupplyConfig:
    years: int = 20
    seed: int = 127
    every: int = 21               # an auction every so many trading days
    size_lo: float = 20.0         # auction size ($ billion), drawn uniformly ...
    size_hi: float = 45.0
    capacity_sd: float = 0.4      # lognormal dispersion of dealers' capacity
    beta: float = 0.07            # concession (bp) per $ billion at average capacity
    giveback: float = 0.7         # share of the concession reversed in the five days after
    window: int = 5
    daily_vol: float = 5.5        # bp a day
    cost: float = 0.1             # bp of yield per leg traded (futures)


def simulate_auctions(cfg: SupplyConfig | None = None) -> dict:
    cfg = cfg or SupplyConfig()
    rng = np.random.default_rng(cfg.seed)
    T = cfg.years * YEAR
    days = np.arange(cfg.every, T - cfg.window - 1, cfg.every)
    size = rng.uniform(cfg.size_lo, cfg.size_hi, len(days))
    capacity = np.exp(cfg.capacity_sd * rng.standard_normal(len(days)) - 0.5 * cfg.capacity_sd**2)
    concession = cfg.beta * size / capacity
    drift = np.zeros(T)
    for d, c in zip(days, concession, strict=True):
        drift[d - cfg.window + 1:d + 1] += c / cfg.window
        drift[d + 1:d + 1 + cfg.window] -= cfg.giveback * c / cfg.window
    y = 400.0 + np.cumsum(drift + cfg.daily_vol * rng.standard_normal(T))
    return {"y": y, "days": days, "size": size, "capacity": capacity, "concession": concession}


def supply_trade(sim: dict, cfg: SupplyConfig | None = None, pre: bool = True, post: bool = True) -> dict:
    """Per auction: short duration over the window before (gains when yields rise), long over the window after."""
    cfg = cfg or SupplyConfig()
    y, w = sim["y"], cfg.window
    before = np.array([y[d] - y[d - w] for d in sim["days"]])
    after = np.array([y[d] - y[d + w] for d in sim["days"]])
    legs = (2 if pre else 0) + (2 if post else 0)
    pnl = (before if pre else 0.0) + (after if post else 0.0) - legs * cfg.cost
    return {"before": before, "after": after, "pnl": pnl}
