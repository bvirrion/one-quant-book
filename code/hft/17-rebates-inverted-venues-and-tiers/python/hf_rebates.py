"""Rebates, inverted venues and tiers (One Quant Book 11, chapter 17).

Two venues show the same bid: a maker-taker venue that pays 0.30 cents a share to a passive fill, with 20,000 shares
queued, and an inverted venue that charges 0.10 cents, with 2,000. Takers reach them at 500 and 300 shares a second;
the level is swept on average every 30 seconds and abandoned every 20. Then a month's tier decision on a schedule
with a cliff at 0.20% of consolidated volume.
"""
from __future__ import annotations

import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "rebatemm"))
import firm_rebatemm as rm  # noqa: E402

fs = rm.fs
MU_THROUGH, MU_AWAY = 1 / 30, 1 / 20
VENUES = {"maker-taker": (20000, 500.0, -0.30), "inverted": (2000, 300.0, 0.10)}
TCV = 11e9
SCHEDULE = fs.Schedule("X", -0.20, 0.30, (fs.Tier("T1", 0.0020, -0.29), fs.Tier("T2", 0.0050, -0.32)))
LOSS = 0.6


def venues() -> dict:
    return {k: rm.queue_edge(q, lam, MU_THROUGH, MU_AWAY, fee) for k, (q, lam, fee) in VENUES.items()}


def by_queue(queues=(0, 1000, 2000, 5000, 10000, 20000, 40000)) -> dict:
    out = {}
    for name, (_, lam, fee) in VENUES.items():
        out[name] = {q: rm.queue_edge(q, lam, MU_THROUGH, MU_AWAY, fee)["edge_per_order"] for q in queues}
    return out


def tier() -> dict:
    nat = 18e6
    return {"marginal": {v: rm.marginal_fee(SCHEDULE, v, TCV, 100000) for v in (18e6, 21.9e6, 22e6)},
            "chase": rm.chase(SCHEDULE, nat, TCV, 21, 21, LOSS),
            "breakeven": fs.breakeven_natural_volume(0.20, 0.29, 0.0020 * TCV, LOSS),
            "last_day": rm.last_day_to_chase(SCHEDULE, nat, TCV, 21, LOSS, 0.001),
            "chase_14m": rm.chase(SCHEDULE, 14e6, TCV, 21, 21, LOSS)}


def zero_queue(lo: float = 5000.0, hi: float = 20000.0) -> float:
    """Exercise 7: the queue ahead (shares, to the nearest 100) at which the rebate venue's edge per order is zero."""
    q, lam, fee = VENUES["maker-taker"]
    while hi - lo > 100.0:
        mid = 0.5 * (lo + hi)
        if rm.queue_edge(mid, lam, MU_THROUGH, MU_AWAY, fee)["edge_per_order"] > 0:
            lo = mid
        else:
            hi = mid
    return round(0.5 * (lo + hi), -2)


def chase_curve(naturals=tuple(range(12, 22))) -> list:
    """The month's tier chase against natural volume (million shares a day): the tier's value, the padding's cost and
    the net, in dollars (the schedule's rates are in cents a share)."""
    out = []
    for n in naturals:
        c = rm.chase(SCHEDULE, n * 1e6, TCV, 21, 21, LOSS)
        out.append({"natural": n, "gain": c["gain"] / 100, "cost": c["cost"] / 100, "net": c.get("net", 0.0) / 100})
    return out
