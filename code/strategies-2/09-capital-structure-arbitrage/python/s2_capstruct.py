"""Capital-structure arbitrage (One Quant Book 9, chapter 9).

Synthetic: firm.capstruct's sixty firms over ten years, shares at 35% vol, debt of 40 a share, five-year CDS priced by
a first-passage model with each firm's own barrier (unknown to the trader) times a mean-reverting mispricing (sd 10%
in logs, half-life 34 days); leveraged buyouts double a firm's debt now and then, with a 20% jump in the share, and
the trader learns the new debt three months later. The trader enters when the market spread is 40% (in logs) away
from the equity-implied spread, hedges with shares, and exits on convergence or after 180 days. NumPy.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "capstruct"))
from firm_capstruct import YEAR, CapConfig, hedge_ratio, implied_spread, simulate_firms, trades  # noqa: E402


@functools.lru_cache(maxsize=8)
def run(shift_rate: float = 0.05):
    cfg = CapConfig(shift_rate=shift_rate)
    sim = simulate_firms(cfg)
    return cfg, sim, trades(sim, cfg)


def stats(shift_rate: float = 0.05):
    """Per trade (bp of notional) and for the book (daily P&L per average open trade, annualised)."""
    _, sim, res = run(shift_rate)
    p = np.array([x["pnl"] for x in res["trades"]])
    days = np.array([x["exit"] - x["entry"] for x in res["trades"]])
    d = res["daily"][YEAR:] / res["open"][YEAR:].mean()
    return {"trades": len(p), "mean_bp": float(p.mean() * 1e4), "lose": float((p < 0).mean()),
            "worst_bp": float(p.min() * 1e4), "days": float(days.mean()), "timeouts": float((days >= 180).mean()),
            "sr": float(d.mean() / d.std() * math.sqrt(YEAR)), "ann": float(d.mean() * YEAR),
            "open": float(res["open"][YEAR:].mean()), "shifts": len(sim["shifts"]),
            "cds_bp": float(np.mean([x["cds"] for x in res["trades"]]) * 1e4),
            "equity_bp": float(np.mean([x["equity"] for x in res["trades"]]) * 1e4)}


def through_shifts(shift_rate: float = 0.05):
    """Trades open when their firm's leverage shifted, by side: count, mean and worst P&L in bp of notional."""
    _, _, res = run(shift_rate)
    out = {}
    for side, name in ((1.0, "sold protection"), (-1.0, "bought protection")):
        p = np.array([x["pnl"] for x in res["trades"] if x["through_shift"] and x["side"] == side])
        out[name] = {"n": len(p), "mean_bp": float(p.mean() * 1e4), "worst_bp": float(p.min() * 1e4)}
    return out


def curve(debts=(40.0, 80.0)):
    """Equity-implied five-year spread (bp) and hedge ratio by share price, at two debt levels, at 35% vol."""
    cfg = CapConfig()
    E = np.linspace(10, 100, 91)
    return {"E": E, **{D: implied_spread(E, D, cfg.sigma_E, cfg) * 1e4 for D in debts},
            "at50": {D: (float(implied_spread(50.0, D, cfg.sigma_E, cfg) * 1e4),
                         float(hedge_ratio(50.0, D, cfg.sigma_E, cfg))) for D in debts},
            "lbo": float(implied_spread(60.0, 80.0, cfg.sigma_E, cfg) * 1e4)}


def cumulative():
    out = {}
    for rate in (0.05, 0.2):
        _, _, res = run(rate)
        out[rate] = np.cumsum(res["daily"]) / res["open"][YEAR:].mean()
    return out
