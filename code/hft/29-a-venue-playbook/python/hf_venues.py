"""A venue playbook (One Quant Book 11, chapter 29).

Eleven venue profiles (firm.venueprofile.standard(), eight of them simulated) and one quoting strategy written once.
Validate each profile with the home venue's quoting parameters to see which rules they break, then run the strategy
on every simulated venue with the home parameters and with the venue's own, over the same market: Book 7's tape flow,
a jump of the efficient price every 20 seconds on average that a fast arbitrageur hears of first, three seeds of 20
minutes each.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys
from dataclasses import replace

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "venueprofile"))
import firm_venueprofile as vp  # noqa: E402

REG = vp.standard()
SEEDS = (7, 8, 9)
SECONDS = 1200
KEYS = ("fills", "volume", "edge", "picked", "takes", "messages", "orders", "rejects", "fees_ticks", "pnl_ticks")


def home_errors() -> dict:
    """What the home venue's quoting parameters break, profile by profile (empty: nothing)."""
    return {p.name: vp.validate(replace(p, quoting=vp.HOME)) for p in REG}


def _mean(p, q, seconds, seeds) -> dict:
    runs = [vp.run(p, q, seconds=seconds, seed=s) for s in seeds]
    return {k: sum(r[k] for r in runs) / len(runs) for k in KEYS}


@functools.cache
def playbook(seconds: int = SECONDS, seeds: tuple = SEEDS) -> dict:
    out = {}
    for p in REG.simulated():
        home = _mean(p, vp.HOME, seconds, seeds)
        own = home if p.quoting == vp.HOME else _mean(p, p.quoting, seconds, seeds)
        out[p.name] = {"home": home, "own": own}
    return out


@functools.cache
def budget_curve(gaps=(0, 2, 4, 8, 16, 32), seconds: int = SECONDS, seeds: tuple = SEEDS) -> list:
    """The crypto venue: the minimum gap between requotes against the order budget."""
    p = REG.get("crypto")
    return [dict(gap=g, **_mean(p, replace(vp.HOME, gap_ns=g * 10**9), seconds, seeds)) for g in gaps]
