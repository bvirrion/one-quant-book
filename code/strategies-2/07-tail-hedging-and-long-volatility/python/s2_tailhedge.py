"""Tail hedging and long volatility (One Quant Book 9, chapter 7).

Synthetic: firm.synthvol's index (twenty years, three planted crashes of 20% to 30% in ten days), options priced on a
steeper smile (skew -0.3, curvature 0.03) than chapter 1's; firm.tailhedge's put programmes by strike, tenor and
monetisation, a static mix of index and cash, and the index with a trend overlay, each judged by growth, volatility
and drawdown; a hedge's bleed in years without a crash and its payoff in crash years. Real: Cboe's put-protection
(PPUT) and zero-cost collar (CLLZ) indices against the S&P 500, 1986-2026, as derived statistics. NumPy.
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
for p in ("synthvol", "tailhedge"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_synthvol import YEAR, VolConfig, simulate_vol  # noqa: E402
from firm_tailhedge import evaluate, put_programme, static_mix, trend_overlay  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"
PROGRAMMES = (("5% monthly", 0.05, 21, None), ("10% monthly", 0.10, 21, None), ("10% quarterly", 0.10, 63, None),
              ("20% quarterly", 0.20, 63, None), ("10% quarterly, monetised at 3x", 0.10, 63, 3.0),
              ("20% half-yearly", 0.20, 126, None))


@functools.lru_cache(maxsize=1)
def market():
    cfg = VolConfig(skew=-0.25, curv=0.02)
    return cfg, simulate_vol(cfg)


@functools.lru_cache(maxsize=1)
def portfolios():
    cfg, sim = market()
    r, v = sim["r"], sim["v"]
    out = {"index": {"nav": np.concatenate([[1.0], np.exp(np.cumsum(r))]), "hedge_pnl": None}}
    for name, otm, tenor, mon in PROGRAMMES:
        p = put_programme(r, v, cfg, otm, tenor, mon)
        out[name] = {"nav": p["nav"], "hedge_pnl": p["hedge_pnl"], "monetised": p["monetised"]}
    out["70% index, 30% cash"] = {"nav": static_mix(r, 0.7), "hedge_pnl": None}
    out["index + trend overlay"] = {"nav": trend_overlay(r, 0.5), "hedge_pnl": None}
    return out


def table():
    return {k: evaluate(v["nav"]) for k, v in portfolios().items()}


def bleed():
    """Each programme's hedge P&L (per unit of starting value, summed by year of 252 days): mean in years without a
    crash start and the sum over the crash years."""
    _, sim = market()
    starts = [s for s, _ in sim["crashes"]]
    n = len(sim["r"]) // YEAR
    crash_years = {s // YEAR for s in starts}
    out = {}
    for name, p in portfolios().items():
        if p["hedge_pnl"] is None:
            continue
        nav = p["nav"]
        yearly = [p["hedge_pnl"][y * YEAR:(y + 1) * YEAR].sum() / nav[y * YEAR] for y in range(n)]
        calm = [x for y, x in enumerate(yearly) if y not in crash_years]
        out[name] = {"bleed": float(np.mean(calm)), "crash_years": [float(yearly[y]) for y in sorted(crash_years)]}
    return out


def curves(step: int = 5):
    p = portfolios()
    idx = np.arange(0, len(p["index"]["nav"]), step)
    return {"day": idx, **{k: p[k]["nav"][idx] for k in ("index", "5% monthly", "70% index, 30% cash",
                                                         "index + trend overlay")}}


def real():
    with open(DATA / "protect_summary.csv") as fh:
        return {r["index"]: r for r in csv.DictReader(fh)}


def crash_windows(name: str = "5% monthly", after: int = 15):
    """The programme's hedge P&L from the day before each crash to `after` days in, as a share of the portfolio, and
    the index's vol the day before."""
    _, sim = market()
    p = portfolios()[name]
    return [{"pnl": float(p["hedge_pnl"][s - 1:s + after].sum() / p["nav"][s - 1]),
             "vol_before": float(np.sqrt(sim["v"][s - 1]))} for s, _ in sim["crashes"]]


def slow_bear(start: int = 2016, days: int = 252, fall: float = 0.4):
    """Exercise 7: add a steady decline of `fall` (in log terms) over a year and compare the year's loss of the 5%
    monthly programme, the static mix and the index."""
    cfg, sim = market()
    r = sim["r"].copy()
    r[start:start + days] += math.log(1 - fall) / days
    puts = put_programme(r, sim["v"], cfg, 0.05, 21)["nav"]
    static = static_mix(r, 0.7)
    index = np.concatenate([[1.0], np.exp(np.cumsum(r))])
    span = lambda x: float(x[start + days] / x[start] - 1)                 # noqa: E731
    return {"puts": span(puts), "static": span(static), "index": span(index)}
