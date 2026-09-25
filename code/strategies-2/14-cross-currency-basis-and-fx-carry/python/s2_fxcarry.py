"""Cross-currency basis and FX carry (One Quant Book 9, chapter 14).

Synthetic: firm.synthfut's ten currencies over thirty years (carry premium, three planted crashes); firm.fxcarry's
basket long the three highest-carry and short the three lowest, monthly; a monthly put on the basket struck 1.5
standard deviations down and priced at 1.2 times trailing vol; a cross-currency basis of -20 bp a year with
quarter-end windows (-30 bp more, -60 at year-end), lent into with a 15 bp balance-sheet cost. Real: a G10 carry
basket from FRED exchange rates and OECD interbank rates, 2002-2025, as derived statistics. NumPy.
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
for p in ("synthfut", "fxcarry"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_fxcarry import BasisConfig, basis_trade, carry_basket, crash_hedge, simulate_basis  # noqa: E402
from firm_synthfut import FutConfig, simulate_futures  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"


def _stats(x, per_year):
    x = np.asarray(x, float)
    d = x - x.mean()
    return {"ann": float(x.mean() * per_year), "sr": float(x.mean() / x.std() * math.sqrt(per_year)),
            "skew": float((d**3).mean() / (d**2).mean() ** 1.5), "worst": float(x.min())}


@functools.lru_cache(maxsize=1)
def basket():
    F = simulate_futures(FutConfig())
    cur = F["cls"] == 2
    return F, carry_basket(F["r"][:, cur], F["carry"][:, cur], 3, 21)["r"]


def carry_results(strike_sd: float = 1.5, vol_mult: float = 1.2):
    F, b = basket()
    h = crash_hedge(b, 21, strike_sd, vol_mult)
    crashes = [float(np.prod(1 + b[s:e]) - 1) for s, e in F["crashes"]]
    hedged_crash = []
    for s, e in F["crashes"]:
        m = (h["start"] >= s - 21) & (h["start"] < e)
        hedged_crash.append((float(np.prod(1 + h["raw"][m]) - 1), float(np.prod(1 + h["hedged"][m]) - 1)))
    return {"raw": _stats(h["raw"], 12), "hedged": _stats(h["hedged"], 12), "cost": float(h["premium"].mean() * 12),
            "payoff": float(h["payoff"].mean() * 12), "crashes": crashes, "crash_months": hedged_crash,
            "periods": len(h["raw"])}


def basis_results():
    cfg = BasisConfig()
    b = simulate_basis(cfg)
    always = basis_trade(b, cfg)
    qe = basis_trade(b, cfg, b["quarter_end"])
    days = int(b["quarter_end"].sum())
    yrs = cfg.days / 252
    qe_only = b["quarter_end"] & ~b["year_end"]
    return {"mean_basis": float(b["basis"].mean()), "qe_basis": float(b["basis"][qe_only].mean()),
            "ye_basis": float(b["basis"][b["year_end"]].mean()), "always_bp": float(always.sum() / yrs),
            "qe_bp": float(qe.sum() / yrs), "qe_days_a_year": days / yrs,
            "qe_rate": float(qe[b["quarter_end"]].mean() * 252)}


def real():
    with open(DATA / "g10_summary.csv") as fh:
        return {r["stat"]: r["value"] for r in csv.DictReader(fh)}


def cumulative():
    """Cumulative log return, by period, of the basket unhedged and hedged."""
    _, b = basket()
    h = crash_hedge(b, 21, 1.5, 1.2)
    return {"start": h["start"], "raw": np.cumsum(np.log1p(h["raw"])), "hedged": np.cumsum(np.log1p(h["hedged"]))}
