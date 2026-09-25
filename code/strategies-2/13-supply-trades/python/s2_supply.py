"""Supply trades (One Quant Book 9, chapter 13).

Synthetic: firm.supplytrade's twenty years of a benchmark yield with monthly auctions of $20-45 billion, a concession
of 0.07 bp per $ billion at average dealer capacity (capacity lognormal, dispersion 0.4) built over the five days
before and 70% given back over the five days after, 5.5 bp a day of noise, and 0.1 bp a leg of cost; the supply
trade per auction, its legs, and its dependence on size. Real: Treasury yields around 2010-2026 coupon auctions
(TreasuryDirect and FRED), as derived statistics. NumPy.
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
sys.path.insert(0, str(ROOT / "firm" / "supplytrade"))
from firm_supplytrade import SupplyConfig, simulate_auctions, supply_trade  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"


@functools.lru_cache(maxsize=1)
def market():
    cfg = SupplyConfig()
    return cfg, simulate_auctions(cfg)


def results():
    """Per auction (bp of yield): mean, t, Sharpe a year (12 auctions) for both legs and each alone; by third of size;
    the slope of the P&L on size, and on size over capacity (which a trader does not see)."""
    cfg, sim = market()
    out = {}
    for name, pre, post in (("both", True, True), ("before", True, False), ("after", False, True)):
        p = supply_trade(sim, cfg, pre, post)["pnl"]
        out[name] = {"mean": float(p.mean()), "t": float(p.mean() / p.std(ddof=1) * math.sqrt(len(p))),
                     "sr": float(p.mean() / p.std(ddof=1) * math.sqrt(12)), "n": len(p)}
    p = supply_trade(sim, cfg)["pnl"]
    q = np.quantile(sim["size"], [1 / 3, 2 / 3])
    groups = (sim["size"] <= q[0], (sim["size"] > q[0]) & (sim["size"] <= q[1]), sim["size"] > q[1])
    out["terciles"] = [{"size": float(sim["size"][m].mean()), "mean": float(p[m].mean())} for m in groups]
    out["slope_size"] = float(np.polyfit(sim["size"], p, 1)[0])
    out["slope_pressure"] = float(np.polyfit(sim["size"] / sim["capacity"], p, 1)[0])
    out["concession_mean"] = float(sim["concession"].mean())
    return out


def real():
    with open(DATA / "auctions_summary.csv") as fh:
        out = {}
        for r in csv.DictReader(fh):
            out.setdefault(r["bench"], {})[r["stat"]] = float(r["value"])
        return out


def no_giveback():
    """Exercise 7: the same market with no giveback after the auction: each leg's mean per auction (bp)."""
    cfg = SupplyConfig(giveback=0.0)
    sim = simulate_auctions(cfg)
    return {name: float(supply_trade(sim, cfg, pre, post)["pnl"].mean())
            for name, pre, post in (("both", True, True), ("before", True, False), ("after", False, True))}
