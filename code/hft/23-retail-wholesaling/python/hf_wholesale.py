"""Retail wholesaling (One Quant Book 11, chapter 23).

A day of 20,000 retail market orders (median 50 shares, herding sentiment, 0.1 cent of information a share) in a stock
quoted 2 to 3 cents wide, filled by a wholesaler with price improvement of a share of the half-spread, 0.1 cent a share
paid for the flow, a 10,000-share inventory limit beyond which it hedges on an exchange. The same terms applied to
institutional flow (median 2,000 shares, 1.5 cents of information) show what segmentation is worth.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "wholesale"))
import firm_wholesale as fw  # noqa: E402

PIS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
SEEDS = tuple(range(20))


@functools.cache
def retail(seed: int = 1, herd: float = 0.995) -> fw.Flow:
    return fw.Flow("retail", seed=seed, herd=herd)


@functools.cache
def institutional() -> fw.Flow:
    return fw.Flow("institutional", seed=2, rate=0.05, n=1000)


def by_pi() -> dict:
    return {p: {"retail": fw.wholesale(retail(), p), "inst": fw.wholesale(institutional(), p)} for p in PIS}


def break_even() -> float:
    """Price-improvement share at which the retail business stops paying (before inventory P&L), by bisection."""
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if fw.wholesale(retail(), mid)["net_ex_inventory"] > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def limits(values=(1000.0, 2000.0, 5000.0, 10000.0, 20000.0, 50000.0)) -> dict:
    """Mean and standard deviation of the day's net over 20 days (same flow model, other seeds) by inventory limit."""
    out = {}
    for lim in values:
        nets = [fw.wholesale(retail(s), 0.3, limit=lim, seed=s + 100)["net"] for s in SEEDS]
        hedge = [fw.wholesale(retail(s), 0.3, limit=lim, seed=s + 100)["hedge"] for s in SEEDS]
        out[lim] = {"mean": float(np.mean(nets)), "sd": float(np.std(nets)), "hedge": float(np.mean(hedge))}
    return out


def herding() -> dict:
    return {h: fw.wholesale(retail(1, h), 0.3)["hedged_share"] for h in (0.0, 0.9, 0.99, 0.995)}


def rule605() -> dict:
    return fw.rule605(retail(), 0.3)


def best_limits() -> dict:
    lim = limits()
    return {"mean": max(lim, key=lambda k: lim[k]["mean"]),
            "mean_less_sd": max(lim, key=lambda k: lim[k]["mean"] - lim[k]["sd"])}
