"""Swap-spread and asset-swap trades (One Quant Book 9, chapter 12).

Synthetic: firm.swapspread's ten years of a ten-year swap spread, +10 bp before a regulation that from year 3 phases
in a 45 bp balance-sheet cost over a year, with quarter-end dips (twice as deep at year-end) and a mean-reverting
noise; the long-swap-spread trade (long the Treasury in repo, pay fixed) before and after, with and without a
balance-sheet charge of 5% capital at a 10% hurdle; and a quarter-end trade that buys the dip and sells five days
later. Real: US dollar swap spreads at 2, 5, 10 and 30 years from FRED (2000-2016), as derived statistics. NumPy.
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
sys.path.insert(0, str(ROOT / "firm" / "swapspread"))
from firm_swapspread import YEAR, SwapConfig, long_spread, simulate_spread  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"


@functools.lru_cache(maxsize=1)
def market():
    cfg = SwapConfig()
    return cfg, simulate_spread(cfg)


def regimes():
    """The long-spread trade before the regulation and once the charge is fully phased in, with and without the
    balance-sheet charge: bp of notional a year, Sharpe ratio, and the parts."""
    cfg, s = market()
    out = {}
    for name, start, days in (("before", 0, cfg.regulation), ("after", cfg.regulation + cfg.ramp, None)):
        for charge in (False, True):
            r = long_spread(s, cfg, start, days, charge)
            yrs = len(r["total"]) / YEAR
            parts = {k: float(r[k].sum() / yrs * 1e4) for k in ("carry", "marks", "float_repo", "charge")}
            out[(name, charge)] = {"bp": float(r["total"].sum() / yrs * 1e4),
                                   "sr": float(r["total"].mean() / r["total"].std() * math.sqrt(YEAR)), **parts}
    return out


def spread_stats():
    cfg, s = market()
    sp = s["spread"]
    after = sp[cfg.regulation + cfg.ramp:]
    return {"before": float(sp[:cfg.regulation].mean()), "after": float(after.mean()), "min": float(sp.min()),
            "neg_share_after": float((after < 0).mean())}


def quarter_ends(hold: int = 5):
    """After the regulation: buy the spread at each quarter's last close, sell `hold` days later; the mean gain in bp
    of notional (DV01 times the change), for year-ends and for the other quarter-ends."""
    cfg, s = market()
    sp = s["spread"]
    q = YEAR // 4
    out = {"year_end": [], "other": []}
    for t in range(cfg.regulation + cfg.ramp + q - 1, len(sp) - hold, q):
        gain = cfg.dv01 * (sp[t + hold] - sp[t])
        out["year_end" if (t + 1) % YEAR == 0 else "other"].append(gain)
    return {k: {"n": len(v), "mean_bp": float(np.mean(v)), "min_bp": float(np.min(v))} for k, v in out.items()}


def real():
    with open(DATA / "swaps_summary.csv") as fh:
        out = {}
        for r in csv.DictReader(fh):
            out.setdefault(r["maturity"], {})[r["stat"]] = r["value"]
        return out


def whole_sample():
    """Exercise 7: the long-spread trade from day 0 to the end, no charge: bp a year and the parts."""
    cfg, s = market()
    r = long_spread(s, cfg, 0, None, False)
    yrs = len(r["total"]) / YEAR
    return {k: float(r[k].sum() / yrs * 1e4) for k in ("total", "carry", "marks")}
