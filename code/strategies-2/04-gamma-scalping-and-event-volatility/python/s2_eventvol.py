"""Gamma scalping and event volatility (One Quant Book 9, chapter 4).

Synthetic: firm.eventvol's 2,000 events on single stocks (diffusive vol around 30% with a 25% variance premium;
earnings gaps with a true move sd around 5%, priced with an implied event variance 30% too low on average and a
lognormal error). An at-the-money straddle with 21 days to expiry is bought at the close three days before the event
and sold at the event day's close, delta-hedged by several rules, with 2 bps on hedges and 2% of the premium on the
options. The same straddle bought for 20 days with no event is plain gamma scalping. Real: S&P 500 returns and
VIX9D and VIX changes on scheduled FOMC statement days, 2011-2026, as derived statistics. NumPy.
"""
from __future__ import annotations

import csv
import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("synthvol", "eventvol"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_eventvol import EventConfig, event_variance, implied_move, straddle_pnl, windows  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"
RULES = (("never", 0, 0.0), ("daily", 8, 0.0), ("twice a day", 4, 0.0), ("every two hours", 2, 0.0),
         ("hourly", 1, 0.0), ("band 0.05", 0, 0.05), ("band 0.10", 0, 0.10), ("band 0.20", 0, 0.20))
EVENTS_A_YEAR = 200            # fifty names, four reports each


@functools.lru_cache(maxsize=4)
def paths(event: bool = True, bias: float = -0.30):
    cfg = EventConfig(bias=bias)
    return cfg, windows(cfg, 3 if event else 20, event)


@functools.lru_cache(maxsize=8)
def hedging(event: bool = True, bias: float = -0.30):
    """Return on premium per window under each hedging rule: mean, sd, mean/sd, hedge cost, and a 200-a-year Sharpe."""
    cfg, w = paths(event, bias)
    out = {}
    for name, every, band in RULES:
        b = straddle_pnl(w, cfg, every, band)
        x = b["total"] / b["premium"]
        out[name] = {"mean": float(x.mean()), "sd": float(x.std(ddof=1)), "per_event": float(x.mean() / x.std(ddof=1)),
                     "hedge_cost": float((b["hedge_cost"] / b["premium"]).mean()),
                     "annual": float(x.mean() / x.std(ddof=1) * math.sqrt(EVENTS_A_YEAR))}
    return out


def by_error(rule: str = "daily", bins: int = 5):
    """Mean return by quintile of the implied move's error (log of implied over true move), with the quintile edges."""
    cfg, w = paths(True)
    _, every, band = next(r for r in RULES if r[0] == rule)
    b = straddle_pnl(w, cfg, every, band)
    x = b["total"] / b["premium"]
    err = np.log(implied_move(w["var_imp"]) / implied_move(w["sd_true"] ** 2))
    edges = np.quantile(err, np.linspace(0, 1, bins + 1)[1:-1])
    g = np.digitize(err, edges)
    return {"mean": [float(x[g == i].mean()) for i in range(bins)],
            "err": [float(err[g == i].mean()) for i in range(bins)],
            "corr": float(np.corrcoef(err, x)[0, 1]), "median_err": float(np.median(err))}


def crush():
    cfg, w = paths(True)
    b = straddle_pnl(w, cfg, 8)
    fall = 1 - b["iv_after"] / b["iv_before"]
    return {"iv_before": float(np.median(b["iv_before"])), "iv_after": float(np.median(b["iv_after"])),
            "fall": float(np.median(fall)), "gap_abs": float(np.abs(w["gap"]).mean()),
            "implied_abs": float(implied_move(w["var_imp"]).mean())}


def extraction():
    """The event variance recovered from two expiries after the event, for the first window."""
    cfg, w = paths(True)
    base = w["vol"][0] ** 2 * (1 + cfg.vrp)
    t1, t2 = 5 / 252, 21 / 252
    v1, v2 = math.sqrt(base + w["var_imp"][0] / t1), math.sqrt(base + w["var_imp"][0] / t2)
    return {"v1": v1, "v2": v2, "event_var": float(event_variance(v1, t1, v2, t2)), "true_imp": float(w["var_imp"][0])}


def real():
    with open(DATA / "fomc_summary.csv") as fh:
        return {r["stat"]: r["value"] for r in csv.DictReader(fh)}
