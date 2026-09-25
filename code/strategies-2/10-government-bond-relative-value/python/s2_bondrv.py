"""Government-bond relative value (One Quant Book 9, chapter 10).

Synthetic: firm.bondrv's ten years of forty government bonds on a three-factor Nelson-Siegel curve, with pricing
errors in two parts (2 bp reverting with a half-life of 40 days, 2 bp over 250 days) seen through 0.5 bp of quote
noise; a weekly rich-cheap book, five bonds a side, unhedged (long the cheap only), DV01-neutral or neutral in the
three curve factors, at a cost of 0.25 bp of yield per unit of DV01 traded. Real: US Treasury constant-maturity
yields (FRED, 1994-2026): principal components of daily changes and the 2-5-10 butterfly, as derived statistics.
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
sys.path.insert(0, str(ROOT / "firm" / "bondrv"))
from firm_bondrv import BondConfig, book, simulate_market  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"
HEDGES = ("none", "dv01", "factors")


@functools.lru_cache(maxsize=4)
def market(cost: float = 0.25):
    cfg = BondConfig(cost=cost)
    sim = simulate_market(cfg)
    return cfg, sim, {h: book(sim, cfg, h) for h in HEDGES}


def table(cost: float = 0.25):
    """Per hedge: gross and net Sharpe ratios, mean and cost (bp of yield a year per unit of gross DV01), volatility."""
    _, _, books = market(cost)
    out = {}
    for h, b in books.items():
        g, n = b["pnl"][2:], b["net"][2:]
        out[h] = {"gross_sr": float(g.mean() / g.std() * math.sqrt(252)),
                  "net_sr": float(n.mean() / n.std() * math.sqrt(252)), "mean": float(g.mean() * 252),
                  "cost": float(b["cost"].sum() / 10), "vol": float(g.std() * math.sqrt(252)),
                  "turnover": float(b["turnover"].sum() / 10)}
    return out


def decay(horizons=(1, 5, 20, 60, 120)):
    """Share of a fitted residual still there after h days (the slope of res[t + h] on res[t], pooled over bonds and
    days, excluding reissues), against the planted mixture of two half-lives and the planted fast part alone."""
    cfg, sim, books = market()
    res = books["dv01"]["residuals"]
    T = res.shape[0]
    out = {}
    for h in horizons:
        a, b = res[:T - h].ravel(), res[h:].ravel()
        c = np.cumsum(sim["reissued"], axis=0)
        alive = c[h:] == c[:T - h]                                        # no reissue in between
        a, b = a[alive.ravel()], b[alive.ravel()]
        fast, slow = 0.5 ** (h / cfg.err_half_life), 0.5 ** (h / cfg.slow_half_life)
        planted = (cfg.err_sd**2 * fast + cfg.slow_sd**2 * slow) / (cfg.err_sd**2 + cfg.slow_sd**2)
        out[h] = {"slope": float((a * b).sum() / (a * a).sum()), "planted": float(planted), "fast": float(fast)}
    r1 = out[1]["slope"]
    return out | {"half_life_ar1": math.log(0.5) / math.log(r1)}


def real():
    with open(DATA / "ust_summary.csv") as fh:
        return {r["stat"]: r["value"] for r in csv.DictReader(fh)}
