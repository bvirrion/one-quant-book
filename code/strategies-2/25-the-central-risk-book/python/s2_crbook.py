"""The central risk book (One Quant Book 9, chapter 25).

Synthetic: firm.crbook's five desks receiving client flows of $0.5 million per name a day (standard deviation) in 100
stocks over 500 days, 10% of the variance common to all desks; hedging desk by desk, pooled, and patiently with an
index-future overlay, with Book 7's cost model; the cost-risk frontier, the cheapest rate within a one-day 99% VaR
limit, and the pooling saving against the number of desks. NumPy.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "crbook"))
from firm_crbook import CRBConfig, central, desk_by_desk, pooled, simulate_desks  # noqa: E402

RATES = tuple(round(0.05 * k, 2) for k in range(1, 21))
Z99 = 2.326


@functools.lru_cache(maxsize=1)
def market():
    cfg = CRBConfig()
    return cfg, simulate_desks(cfg)


def pooling() -> dict:
    """Daily hedging cost ($) desk by desk and pooled, and the share of gross flow that crosses internally."""
    cfg, sim = market()
    d, p = desk_by_desk(sim, cfg), pooled(sim, cfg)
    fl = sim["flows"]
    return {"desks": float(d.mean()), "pooled": float(p.mean()), "saving": float(1 - p.mean() / d.mean()),
            "crossed": float(1 - np.abs(fl.sum(axis=0)).sum() / np.abs(fl).sum())}


@functools.cache
def frontier(futures: bool = True) -> dict:
    """For each rate: mean daily cost (stocks and futures, $) and the standard deviation of the daily P&L carried."""
    cfg, sim = market()
    out = {}
    for r in RATES:
        c = central(sim, cfg, r, futures)
        out[r] = {"cost": float((c["stock_cost"] + c["futures_cost"]).mean()), "sd": float(c["pnl"][1:].std()),
                  "futures": float(c["futures_cost"].mean())}
    return out


def pick(var_limit: float = 1e6) -> dict:
    """The cheapest rate whose one-day 99% VaR (2.326 sd) fits the limit, with futures."""
    f = frontier(True)
    ok = [r for r in RATES if Z99 * f[r]["sd"] <= var_limit]
    r = min(ok, key=lambda k: f[k]["cost"])
    return {"rate": r, "cost": f[r]["cost"], "sd": f[r]["sd"], "var": Z99 * f[r]["sd"]}


def by_desks(counts=(1, 2, 3, 4, 5, 6, 8, 10)) -> dict:
    """Pooling saving and share crossed against the number of desks, with and without a common flow component."""
    out = {}
    for n in counts:
        row = []
        for common in (0.1, 0.0):
            cfg = CRBConfig(desks=n, common=common)
            sim = simulate_desks(cfg)
            row.append(float(1 - pooled(sim, cfg).mean() / desk_by_desk(sim, cfg).mean()))
        out[n] = row
    return out
