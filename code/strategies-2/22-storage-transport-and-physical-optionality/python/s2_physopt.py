"""Storage, transport and physical optionality (One Quant Book 9, chapter 22).

Synthetic: Book 6's illustrative Henry Hub-like forward curve (April to March) and two-factor model (kappa 1.5,
short-end vol 60%, long-end 20%, correlation 0.3); a storage lease of 10 units of 100,000 MMBtu (inject 2 and withdraw
4 a month, 2 cents a unit each way) valued by intrinsic, spread-option pairs, rolling intrinsic and least-squares Monte
Carlo, and monetised by the intrinsic and rolling-intrinsic hedge programmes with re-hedging costs of 0, 0.5 and 2 cents
per unit; a transport strip from the hub to a market-area hub; an LNG cargo that can be diverted. Real: Henry Hub
winter-minus-summer spot spreads (s2_fetch_hh.py). NumPy.
"""
from __future__ import annotations

import csv
import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
DATA = ROOT.parent / "data" / "strategies-2"
for comp in ("physopt", "energymodel"):
    sys.path.insert(0, str(ROOT / "firm" / comp))
from firm_energymodel import lsm, spot_paths  # noqa: E402
from firm_physopt import (  # noqa: E402
    Facility,
    TwoFactor,
    diversion,
    hedge_programme,
    plans,
    spread_option_pairs,
    transport,
)

MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
F0 = [2.60, 2.62, 2.68, 2.74, 2.78, 2.80, 2.90, 3.20, 3.45, 3.50, 3.30, 3.00]
T = [k / 12 + 1 / 24 for k in range(12)]
MODEL = TwoFactor(1.5, 0.60, 0.20, 0.30)
FAC = Facility(capacity=10, max_inject=2, max_withdraw=4, cost_in=0.02, cost_out=0.02)
PATHS, UNIT = 2000, 100_000
COSTS = (0.0, 0.005, 0.02)
BASIS = [0.05, 0.05, 0.08, 0.12, 0.12, 0.06, 0.05, 0.25, 0.45, 0.60, 0.40, 0.15]    # market-area hub over the hub


@functools.lru_cache(maxsize=1)
def programmes() -> dict:
    """The intrinsic and rolling-intrinsic hedge programmes, per path, for each re-hedging cost ($/MMBtu per unit)."""
    out = {"static": hedge_programme(FAC, MODEL, F0, T, PATHS, 5, 0.0, roll=False)}
    for c in COSTS:
        out[c] = hedge_programme(FAC, MODEL, F0, T, PATHS, 5, c)
    return out


def storage() -> dict:
    """Value by method, per unit ($/MMBtu x units), and the intrinsic plan."""
    plan = plans(FAC, np.array([F0]), np.array([0]))[0]
    pairs = spread_option_pairs(FAC, F0, T, MODEL)
    p = programmes()
    return {"plan": [int(a) for a in plan], "intrinsic": p[0.0]["intrinsic"],
            "pairs": float(sum(x["option"] for x in pairs)), "pairs_n": len(pairs),
            "rolling": float(p[0.0]["pnl"].mean()), "lsm": lsm(FAC, spot_paths(MODEL, F0, T, PATHS, 5), [1.0] * 12)}


def hedging() -> dict:
    """Per re-hedging cost: the rolling programme's P&L less the static programme's at the same cost (which pays for
    its initial hedges too): mean, sd, 5% quantile, share of paths below; forward units traded beyond the static
    programme's; and the static programme's spread across paths."""
    p = programmes()
    out = {"static_sd": float(p["static"]["pnl"].std()), "static_units": float(p["static"]["traded"][0])}
    for c in COSTS:
        x = p[c]["pnl"] - (p[c]["intrinsic"] - c * out["static_units"])
        out[c] = {"mean": float(x.mean()), "sd": float(x.std()), "q05": float(np.quantile(x, 0.05)),
                  "below": float((x < -1e-9).mean()), "extra_units": float(p[c]["traded"].mean() - out["static_units"])}
    return out


def transport_strip(cost: float = 0.10, rho: float = 0.85) -> dict:
    FB = [f + b for f, b in zip(F0, BASIS, strict=True)]
    return transport(F0, FB, T, cost, 0.45, 0.55, rho)


def cargo(rho: float = 0.8) -> dict:
    """A cargo committed to Europe at $10.00 that may go to Asia at $10.50 for $0.80 more shipping, decided in three
    months."""
    return diversion(10.0, 10.5, 0.8, 0.25, 0.6, 0.6, rho)


def henry_hub() -> dict:
    with open(DATA / "hh_summary.csv") as fh:
        return {r["key"]: float(r["value"]) for r in csv.DictReader(fh)}


def gated(cost: float = 0.02) -> dict:
    """Rolling intrinsic that re-hedges only when the gain on the curve exceeds the cost of the trades, against the
    static programme at the same cost."""
    r = hedge_programme(FAC, MODEL, F0, T, PATHS, 5, cost, gate=True)
    units = float(np.abs(plans(FAC, np.array([F0]), np.array([0]))[0]).sum())
    x = r["pnl"] - (r["intrinsic"] - cost * units)
    return {"mean": float(x.mean()), "below": float((x < -1e-9).mean()),
            "extra_units": float(r["traded"].mean() - units)}
