"""firm.macrobook -- one macro view, several ways to express it (build of One Quant Book 9, chapter 17).

A manager expects a rate to fall over a horizon. The rate's true drift over the horizon is drawn around the view (the
view is right on average but by a varying amount), and the rate follows it with daily normal noise. The same view is
expressed as a futures position with or without a stop-loss, an at-the-money or out-of-the-money option on the rate
(a receiver: it pays when the rate ends below the strike) and an option spread, each sized to the same risk budget:
the premium paid for options, the stop distance for futures with a stop, and a two-standard-deviation loss for a
futures position without one. Options are priced by the normal (Bachelier) model at the path's volatility times a
premium. The simulator reports each expression's payoff per unit of risk budget, and how often a correct view (the
rate ends lower) was stopped out before it could pay. NumPy only.

API (stable):
    ViewConfig(...)                            parameters (seed 149)
    rate_paths(cfg)                            (n, days + 1) rate paths in basis points, starting at 0
    bachelier_receiver(strike, vol, tau)       normal-model price of a receiver (pays max(strike - rate, 0)), bp
    expressions(paths, cfg, stops)             dict name -> per-path payoff per unit of risk budget
    stopped_correct(paths, cfg, stop)          share of correct views whose futures position was stopped out
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ViewConfig:
    n: int = 20000
    days: int = 126               # the view's horizon: six months
    seed: int = 149
    view_bp: float = -50.0        # the manager's expected change of the rate over the horizon
    view_sd: float = 50.0         # dispersion of the true drift around the view
    vol_bp: float = 90.0          # annual normal volatility of the rate
    vol_premium: float = 1.1      # implied over realised volatility
    otm_bp: float = 25.0          # the out-of-the-money strike, below today's rate
    spread_bp: float = 50.0       # the option spread's width


def rate_paths(cfg: ViewConfig | None = None) -> np.ndarray:
    cfg = cfg or ViewConfig()
    rng = np.random.default_rng(cfg.seed)
    drift = cfg.view_bp + cfg.view_sd * rng.standard_normal(cfg.n)
    daily = cfg.vol_bp / math.sqrt(252) * rng.standard_normal((cfg.n, cfg.days))
    steps = drift[:, None] / cfg.days + daily
    return np.concatenate([np.zeros((cfg.n, 1)), np.cumsum(steps, axis=1)], axis=1)


def _ncdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def bachelier_receiver(strike: float, vol: float, tau: float) -> float:
    """Price (bp) of a claim paying max(strike - R_T, 0) with R_0 = 0 and R_T normal with sd vol sqrt(tau)."""
    sd = vol * math.sqrt(tau)
    d = strike / sd
    return strike * _ncdf(d) + sd * math.exp(-0.5 * d * d) / math.sqrt(2 * math.pi)


def expressions(paths, cfg: ViewConfig | None = None, stops=(25.0, 50.0)) -> dict:
    cfg = cfg or ViewConfig()
    end = paths[:, -1]
    tau = cfg.days / 252
    vol = cfg.vol_bp * cfg.vol_premium
    sd_h = cfg.vol_bp * math.sqrt(tau)
    out = {"futures": -end / (2 * sd_h)}                                 # budget: a two-sd loss over the horizon
    for s in stops:                                                      # budget: the stop distance
        hit = (paths >= s).any(axis=1)
        out[f"futures, stop {s:.0f}"] = np.where(hit, -1.0, -end / s)
    for name, k in (("option at the money", 0.0), ("option out of the money", -cfg.otm_bp)):
        prem = bachelier_receiver(k, vol, tau)
        out[name] = np.maximum(k - end, 0.0) / prem - 1.0                 # budget: the premium
    lo = -cfg.spread_bp
    prem = bachelier_receiver(0.0, vol, tau) - bachelier_receiver(lo, vol, tau)
    out["option spread"] = (np.maximum(-end, 0.0) - np.maximum(lo - end, 0.0)) / prem - 1.0
    return out


def stopped_correct(paths, cfg: ViewConfig | None = None, stop: float = 25.0) -> float:
    right = paths[:, -1] < 0
    hit = (paths >= stop).any(axis=1)
    return float((hit & right).sum() / right.sum())
