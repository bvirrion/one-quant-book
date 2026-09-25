"""The volatility-index complex (One Quant Book 9, chapter 5).

Synthetic: firm.synthvol's variance path (twenty years, three crashes; volatility of variance 0.25) gives a VIX-like
index; firm.vixetp prices futures expiring every 21 days with a term premium, a long constant-maturity index, a
short-futures book at several sizes, and long, inverse and twice-leveraged products with an acceleration clause at
20% of the previous close, with the futures the products must trade at each close. Real: Cboe's VIX futures
settlements from 2013, a constant 30-day index and its inverse built from them, and 5 February 2018, as derived
statistics. NumPy.
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
for p in ("synthvol", "vixetp"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_synthvol import VolConfig, simulate_vol  # noqa: E402
from firm_vixetp import curve_path, etp, flow  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"
PREMIUM = 0.5
XI = 0.25                      # a calmer volatility of variance than synthvol's default 0.5


@functools.lru_cache(maxsize=4)
def market(premium: float = PREMIUM):
    cfg = VolConfig(xi=XI)
    sim = simulate_vol(cfg)
    return cfg, sim, curve_path(sim["v"], cfg, premium)


def curve_stats(premium: float = PREMIUM):
    _, _, c = market(premium)
    r = c["cm"][1:]
    return {"vix_mean": float(c["vix"].mean()), "vix_median": float(np.median(c["vix"])),
            "premium_f1": float((c["f1"] - c["vix"]).mean()), "contango": float((c["f2"] > c["f1"]).mean()),
            "long_log": float(np.log1p(r).mean() * 252), "long_mean": float(r.mean() * 252),
            "long_vol": float(r.std() * math.sqrt(252))}


def short_book(size: float, premium: float = PREMIUM):
    """A book short `size` times its capital in the constant-maturity index, rebalanced daily (no acceleration)."""
    _, _, c = market(premium)
    p = etp(c["cm"][1:], -size, accel=0.0)
    v = p["value"]
    peak = np.maximum.accumulate(v)
    years = (len(v) - 1) / 252
    alive = bool(v[-1] > 0)
    return {"final": float(v[-1]), "ann": float(v[-1] ** (1 / years) - 1) if alive else -1.0,
            "max_dd": float((v / peak - 1).min()), "alive": alive}


def spike(premium: float = PREMIUM):
    """The first planted crash: index, daily index return and each product's fate and flows at that close."""
    _, sim, c = market(premium)
    s = sim["crashes"][0][0]
    r = c["cm"][1:]
    out = {"day": s, "vix_before": float(c["vix"][s - 1]), "vix_after": float(c["vix"][s]),
           "cm_return": float(r[s - 1])}
    for name, lev in (("inverse", -1.0), ("long", 1.0), ("double", 2.0)):
        p = etp(r, lev)
        f = flow(p, r, lev)
        out[name] = {"value_before": float(p["value"][s - 1]), "value_after": float(p["value"][s]),
                     "ended": bool(not p["alive"][s]), "flow": float(f[s - 1] / p["value"][s - 1])}
    return out


def paths(premium: float = PREMIUM, step: int = 5):
    """Every step-th day: the index, the inverse product and a short book of a quarter of capital, from day 0."""
    _, _, c = market(premium)
    r = c["cm"][1:]
    inv, quarter = etp(r, -1.0)["value"], etp(r, -0.25, accel=0.0)["value"]
    idx = np.arange(0, len(inv), step)
    return {"day": idx, "vix": c["vix"][idx], "inverse": inv[idx], "quarter": quarter[idx]}


def real():
    with open(DATA / "vx_summary.csv") as fh:
        s = {r["stat"]: r["value"] for r in csv.DictReader(fh)}
    with open(DATA / "vx_yearly.csv") as fh:
        y = list(csv.DictReader(fh))
    return s, y
