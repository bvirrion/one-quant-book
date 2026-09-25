"""Convertible arbitrage (One Quant Book 9, chapter 8).

Synthetic: thirty convertibles, one on each of firm.synthvol's members, bought at issue on day 1,000 of the synthetic
market (the share at the conversion price, 40), five years to maturity, priced by Book 5's convertible pricer with
an equity-to-credit hazard; firm.convarb's book is long each bond and short its delta, with or without credit
protection, levered three to one. A forced-selling episode begins 500 days in, with the first planted crash: the
bonds cheapen from 1% to 6% below model value, the hazard doubles and the borrow fee rises to 5% for three months,
and the cheapness comes back over the following six months. NumPy.
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
for p in ("synthvol", "convertible", "convarb"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_convarb import YEAR, ArbConfig, delta, mark, run_book, value_tables  # noqa: E402
from firm_convertible import Convertible, bond_floor  # noqa: E402
from firm_synthvol import VolConfig, simulate_vol  # noqa: E402

START, LEVERAGE = 1000, 3.0
BUCKETS = ("bond", "hedge", "cheapness", "credit", "credit_hedge", "coupon", "borrow")


@functools.lru_cache(maxsize=2)
def books(credit_hedge: bool = False):
    """Average daily P&L buckets per bond across the thirty members, and the average purchase price."""
    sim = simulate_vol(VolConfig())
    cfg = ArbConfig()
    n = int(cfg.maturity * YEAR)
    runs = [run_book(np.exp(np.cumsum(np.concatenate([[0.0], sim["R"][START:START + n, i]]))), cfg, credit_hedge)
            for i in range(sim["R"].shape[1])]
    out = {k: np.mean([x[k] for x in runs], axis=0) for k in BUCKETS + ("total",)}
    out["price0"] = float(np.mean([x["price0"] for x in runs]))
    out["per_bond_total"] = np.array([x["total"].sum() for x in runs])
    return cfg, out


def summary(credit_hedge: bool = False):
    """Returns on capital (bond price / leverage): annual carry outside the episode and its recovery, the episode's
    loss by bucket, the recovery's gain, and the whole five years."""
    cfg, b = books(credit_hedge)
    capital = b["price0"] / LEVERAGE
    a, e = cfg.stress_start - 1, cfg.stress_start + cfg.stress_len - 1
    rec = e + cfg.recovery_days
    days = len(b["total"])
    calm = np.ones(days, bool)
    calm[a:rec] = False
    ep = {k: float(b[k][a:e].sum() / capital) for k in BUCKETS + ("total",)}
    return {"carry": float(b["total"][calm].sum() / capital / (calm.sum() / YEAR)), "episode": ep,
            "recovery": float(b["total"][e:rec].sum() / capital), "total": float(b["total"].sum() / capital),
            "years": days / YEAR, "price0": b["price0"],
            "buckets": {k: float(b[k].sum() / capital) for k in BUCKETS}}


def profile(spots=(15.0, 25.0, 40.0, 60.0, 80.0)):
    """At issue: model value, conversion value, delta and the straight bond (at the hazard's spread at 40) by share
    price; and the full curve for the chapter's figure."""
    cfg = ArbConfig()
    tables = value_tables(cfg)
    floor = bond_floor(Convertible(ratio=100 / cfg.s0), cfg.r, cfg.lam0 * 0.6)
    rows = {s: {"value": mark(tables, cfg.maturity, s), "conversion": 100 / cfg.s0 * s,
                "delta": delta(tables, cfg.maturity, s)} for s in spots}
    grid = np.linspace(8, 100, 93)
    curve = np.array([mark(tables, cfg.maturity, s) for s in grid])
    return {"rows": rows, "floor": floor, "grid": grid, "curve": curve}


def cumulative(credit_hedge: bool = False):
    """Cumulative returns on capital of the total and of four groups of buckets, day by day."""
    _, b = books(credit_hedge)
    capital = b["price0"] / LEVERAGE
    groups = {"total": b["total"], "cheapness": b["cheapness"], "credit": b["credit"] + b["credit_hedge"],
              "gamma": b["bond"] + b["hedge"], "carry": b["coupon"] + b["borrow"]}
    return {k: np.cumsum(v) / capital for k, v in groups.items()}
