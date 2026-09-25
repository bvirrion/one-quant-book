"""firm.fxflows -- month-end hedge-rebalancing flows and the fix window (build of One Quant Book 9, chapter 15).

A currency pair and two equity markets, monthly. Foreign investors hold home-country equities hedged back to their
own currency at a hedge ratio; when the home market rises over the month, their hedges fall short and at month-end
they sell the home currency for the difference; home investors hedging foreign holdings do the reverse. The net flow
(in units of the currency's market depth) moves the exchange rate over the last days before the fix, and part of the
move reverses in the days after. A trader estimates the flow from the two markets' returns with noisy guesses of the
holdings and hedge ratios, and trades ahead of it. In the fix window itself the flow pushes the rate and part of the
push reverses within the half hour after, which a liquidity provider can take the other side of. NumPy only.

API (stable):
    FlowFXConfig(...)                           parameters (seed 137)
    simulate_months(cfg)                        dict of monthly equity returns, true and estimated flows, and the
                                                exchange-rate moves before and after month-end and in the fix window
    flow_trade(sim, cfg, scale)                 per-month P&L (bp) of trading ahead of the estimated flow
    fix_liquidity(sim, cfg)                     per-month P&L (bp) of taking the other side of the fix-window push
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FlowFXConfig:
    months: int = 360
    seed: int = 137
    eq_vol: float = 0.045         # monthly vol of each equity market
    eq_corr: float = 0.7
    hold_home: float = 1.0        # foreign holdings of home equities (units of market depth)
    hold_foreign: float = 0.6     # home holdings of foreign equities
    hedge_home: float = 0.5       # hedge ratios
    hedge_foreign: float = 0.3
    impact: float = 0.065         # exchange-rate move (log) per unit of flow over the last days
    reversal: float = 0.5         # share of it reversed in the days after month-end
    fx_vol: float = 0.004         # vol of the rate over the last days, from everything else
    est_error: float = 0.3        # lognormal error of the trader's holdings and hedge-ratio guesses
    fix_share: float = 0.3        # share of the month-end move that happens in the fix window
    fix_reversal: float = 0.4     # share of the window's push reversed within half an hour
    fix_noise: float = 0.0005     # noise over the half hour after the fix window
    cost_bp: float = 1.0          # round-trip cost of the flow trade (bp)
    fix_cost_bp: float = 0.5


def simulate_months(cfg: FlowFXConfig | None = None) -> dict:
    cfg = cfg or FlowFXConfig()
    rng = np.random.default_rng(cfg.seed)
    n = cfg.months
    z = rng.standard_normal((n, 2))
    home = cfg.eq_vol * z[:, 0]
    foreign = cfg.eq_vol * (cfg.eq_corr * z[:, 0] + np.sqrt(1 - cfg.eq_corr**2) * z[:, 1])
    # foreign holders' hedges are short the home currency: a rise in home equities needs more of it sold
    flow = -cfg.hold_home * cfg.hedge_home * home + cfg.hold_foreign * cfg.hedge_foreign * foreign
    g = np.exp(cfg.est_error * rng.standard_normal((n, 2)) - 0.5 * cfg.est_error**2)
    est = -cfg.hold_home * cfg.hedge_home * g[:, 0] * home + cfg.hold_foreign * cfg.hedge_foreign * g[:, 1] * foreign
    push = cfg.impact * flow
    before = push + cfg.fx_vol * rng.standard_normal(n)
    after = -cfg.reversal * push + cfg.fx_vol * rng.standard_normal(n)
    fix_push = cfg.fix_share * push
    fix_after = -cfg.fix_reversal * fix_push + cfg.fix_noise * rng.standard_normal(n)
    return {"home": home, "foreign": foreign, "flow": flow, "est": est, "before": before, "after": after,
            "fix_push": fix_push, "fix_after": fix_after}


def flow_trade(sim: dict, cfg: FlowFXConfig | None = None, scale: float | None = None) -> np.ndarray:
    """Hold the home currency in proportion to the estimated flow (sign if scale is None) over the last days; bp."""
    cfg = cfg or FlowFXConfig()
    pos = np.sign(sim["est"]) if scale is None else sim["est"] / scale
    return 1e4 * pos * sim["before"] - np.abs(pos) * cfg.cost_bp


def fix_liquidity(sim: dict, cfg: FlowFXConfig | None = None) -> np.ndarray:
    """Take the other side of the fix-window push, one unit, and close half an hour later; bp."""
    cfg = cfg or FlowFXConfig()
    return 1e4 * -np.sign(sim["fix_push"]) * sim["fix_after"] - cfg.fix_cost_bp
