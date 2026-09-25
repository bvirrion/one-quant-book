"""firm.eventvol -- event volatility and discrete delta hedging (build of One Quant Book 9, chapter 4).

Single stocks with a diffusive volatility and scheduled events (earnings) that gap the price at the open of the event
day, before anyone can hedge. Each event has a true move standard deviation drawn around a median; the market prices
an implied event variance equal to the true one times (1 + bias) times a lognormal error, so the implied move is
right on average only if bias is zero. Implied volatility for an expiry after the event adds the event variance to
the diffusive variance (which carries its own premium): sigma^2 tau = sigma_d^2 (1 + vrp) tau + event variance. After
the event only the diffusive part remains: the volatility crush. Paths are simulated in intraday steps over a
window; an event straddle is bought at the close `before` days ahead of the event and sold at the event day's
close, delta-hedged every `every` steps or when the delta leaves a band, with costs on the hedges and the options.
NumPy only.

API (stable):
    EventConfig(...)                           parameters (seed 97)
    event_variance(v1, t1, v2, t2)             event variance from two implied vols straddling the event
    implied_move(event_var)                    expected absolute event return, sqrt(2 / pi) x event sd
    windows(cfg, days, event)                  dict of paths (n, steps) and the true and implied event sds
    straddle_pnl(w, cfg, every, band)          dict of per-window P&L, premium, hedge cost and option cost
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "synthvol"))
from firm_synthvol import YEAR, bs_delta, bs_price  # noqa: E402


@dataclass(frozen=True)
class EventConfig:
    n: int = 2000                 # windows (events) simulated
    steps: int = 8                # hedging steps per day
    seed: int = 97
    vol: float = 0.30             # median diffusive annual vol
    vol_dispersion: float = 0.3   # lognormal dispersion of diffusive vol across names
    vrp: float = 0.25             # implied diffusive variance = vol^2 (1 + vrp)
    event_sd: float = 0.05        # median true event-day move sd
    event_dispersion: float = 0.4
    bias: float = -0.30           # implied event variance = true x (1 + bias) x lognormal error
    error: float = 0.35           # sd of the log error of the implied event variance
    expiry: int = 21              # trading days from purchase to expiry
    hedge_cost: float = 0.0002    # cost per unit of stock notional traded (2 bps)
    option_cost: float = 0.02     # round-trip cost as a share of the straddle premium


def event_variance(v1, t1, v2, t2):
    """Two implied vols with expiries t1 < t2 both after the event, and the same diffusive vol: solve for the event."""
    v1, v2 = np.asarray(v1, float), np.asarray(v2, float)
    diffusive = (v2**2 * t2 - v1**2 * t1) / (t2 - t1)
    return v1**2 * t1 - diffusive * t1


def implied_move(event_var):
    return math.sqrt(2 / math.pi) * np.sqrt(np.asarray(event_var, float))


def windows(cfg: EventConfig | None = None, days: int = 3, event: bool = True) -> dict:
    """Paths over `days` days after the purchase close; with an event, its gap opens the last day."""
    cfg = cfg or EventConfig()
    rng = np.random.default_rng(cfg.seed + (0 if event else 1))
    n, k = cfg.n, days * cfg.steps
    vol = cfg.vol * np.exp(cfg.vol_dispersion * rng.standard_normal(n) - 0.5 * cfg.vol_dispersion**2)
    sd_true = cfg.event_sd * np.exp(cfg.event_dispersion * rng.standard_normal(n)) if event else np.zeros(n)
    err = cfg.error * rng.standard_normal(n)
    var_imp = sd_true**2 * (1 + cfg.bias) * np.exp(err - 0.5 * cfg.error**2) if event else np.zeros(n)
    dt = 1 / (YEAR * cfg.steps)
    r = vol[:, None] * math.sqrt(dt) * rng.standard_normal((n, k)) - 0.5 * vol[:, None] ** 2 * dt
    gap_at = (days - 1) * cfg.steps                      # first step of the event day
    gap = sd_true * rng.standard_normal(n) - 0.5 * sd_true**2
    r[:, gap_at] += gap
    S = np.concatenate([np.ones((n, 1)), np.exp(np.cumsum(r, axis=1))], axis=1)
    return {"S": S, "vol": vol, "sd_true": sd_true, "var_imp": var_imp, "gap": gap, "gap_at": gap_at if event else -1,
            "days": days}


def _iv(w, cfg, j, tau):
    """Implied vol at step j (0 = purchase) for remaining maturity tau: event variance until the gap has happened."""
    base = w["vol"] ** 2 * (1 + cfg.vrp)
    before = j <= w["gap_at"]
    return np.sqrt(base + np.where(before, w["var_imp"], 0.0) / max(tau, 1e-8))


def straddle_pnl(w: dict, cfg: EventConfig | None = None, every: int = 0, band: float = 0.0) -> dict:
    """Long one at-the-money straddle per window, delta-hedged every `every` steps (0: never) or, if band > 0, whenever
    the position's delta has moved more than band since the last hedge; per unit of stock price at purchase."""
    cfg = cfg or EventConfig()
    S = w["S"]
    n, k = S.shape[0], S.shape[1] - 1
    dt = 1 / (YEAR * cfg.steps)
    tau0 = cfg.expiry / YEAR
    K = np.ones(n)
    v0 = _iv(w, cfg, 0, tau0)
    prem = bs_price(1.0, K, tau0, v0, "C") + bs_price(1.0, K, tau0, v0, "P")
    hedge = np.zeros(n)                                  # shares held short against the straddle's delta
    pnl_h, cost = np.zeros(n), np.zeros(n)
    for j in range(k):
        tau = tau0 - j * dt
        v = _iv(w, cfg, j, tau)
        d = bs_delta(S[:, j], K, tau, v, "C") + bs_delta(S[:, j], K, tau, v, "P")
        if band > 0:
            move = np.abs(d - hedge) > band
        else:
            move = np.full(n, every > 0 and j % every == 0)
        trade = np.where(move, d - hedge, 0.0)
        cost += cfg.hedge_cost * np.abs(trade) * S[:, j]
        hedge += trade
        pnl_h -= hedge * (S[:, j + 1] - S[:, j])
    tk = max(tau0 - k * dt, 1e-8)
    vk = _iv(w, cfg, k, tk)
    end = bs_price(S[:, k], K, tk, vk, "C") + bs_price(S[:, k], K, tk, vk, "P")
    opt_cost = cfg.option_cost * prem
    total = end - prem + pnl_h - cost - opt_cost
    return {"total": total, "premium": prem, "option": end - prem, "hedge": pnl_h, "hedge_cost": cost,
            "option_cost": opt_cost, "iv_before": v0, "iv_after": vk}
