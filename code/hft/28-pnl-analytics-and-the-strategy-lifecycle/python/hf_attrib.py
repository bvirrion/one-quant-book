"""P&L analytics and the strategy lifecycle (One Quant Book 11, chapter 28).

A simulated year of a two-venue market maker (firm.mmattrib.Year, seed 1): the half-spread narrows 10% and market
volume rises 15% in month 9; a competitor arrives on venue B on day 175 (our share there -30%, capture ratio -15%);
from day 182 a parameter change is run as an experiment on randomised days (share +10%, adverse selection +0.10 cent a
share). Detect the competitor, estimate the parameter's effect, attribute month 9 against month 8, apply a retirement
rule.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "mmattrib"))
import firm_mmattrib as ma  # noqa: E402

SEEDS = (1, 2, 3)


@functools.cache
def year(seed: int = 1) -> ma.Year:
    return ma.Year(seed=seed)


def detect(seed: int = 1) -> dict:
    y = year(seed)
    at = ma.attribution(y)
    share_b, ratio_b = y.share[:, 1], at["capture_ratio_obs"][:, 1]
    cp = ma.cusum_down(share_b, 0.12, 0.005, 0.05)
    cp_ratio = ma.cusum_down(ratio_b, 0.8, 0.02, 0.1)
    days = np.arange(y.days)
    pre, post = days < cp, (days >= cp) & ~y.treated
    return {"day": cp, "day_ratio": cp_ratio, "comp_share": float(1 - share_b[post].mean() / share_b[pre].mean()),
            "comp_kappa": float(1 - ratio_b[post].mean() / ratio_b[pre].mean())}


def exp(seed: int = 1) -> dict:
    return ma.experiment(year(seed), 182, 251)


def month9(seed: int = 1) -> dict:
    y, d, e = year(seed), detect(seed), exp(seed)
    est = {"comp_share": d["comp_share"], "comp_kappa": d["comp_kappa"], "param_share_mult": e["share_mult"],
           "param_adverse_add": e["adverse_add"], "comp_day": d["day"]}
    return {"truth": ma.month_change(y, 7, 8), "estimate": ma.month_change(y, 7, 8, est)}


def daily(seed: int = 1) -> np.ndarray:
    return year(seed).pnl.sum(axis=1)


def retirement(seed: int = 1, cost_per_day: float = 12000.0, window: int = 60) -> int:
    return ma.retire_day(daily(seed), window, cost_per_day)


def cusum_path(seed: int = 1, target: float = 0.12, k: float = 0.005) -> np.ndarray:
    s, out = 0.0, []
    for v in year(seed).share[:, 1]:
        s = max(0.0, s + (target - v) - k)
        out.append(s)
    return np.array(out)
