"""Prediction and sports market making (One Quant Book 11, chapter 26).

Football matches with Poisson goals (1.5 home, 1.1 away a match); a market maker quotes the home-win contract at its
fair probability plus or minus one point, 1,000 units a side; courtsiders at the ground act half a second after a goal,
the maker's feed reports it after three (both lognormal with a log standard deviation of 0.3); the exchange holds each
in-play order for the bet delay; recreational bettors stake 50 twice a minute at the quote.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "sportsmm"))
import firm_sportsmm as sm  # noqa: E402

DELAYS = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0)
N = 2000


@functools.cache
def by_delay() -> dict:
    return {d: sm.season(N, d) for d in DELAYS}


def negligible(threshold: float = 0.01) -> float:
    """The shortest delay whose loss per goal is below `threshold` of the no-delay loss."""
    b = by_delay()
    base = b[0.0]["loss_per_goal"]
    return min(d for d in DELAYS if b[d]["loss_per_goal"] < threshold * base)


def caps() -> dict:
    return {c: sm.season(N, 0.0, cap=c) for c in (50.0, 100.0, 300.0)}


def match_path(seed: int = 7) -> list:
    """The home-win probability minute by minute through one simulated match."""
    m = sm.Match(seed=seed)
    out, diff, gi = [], 0, 0
    for minute in range(91):
        while gi < len(m.times) and m.times[gi] <= minute:
            diff += int(m.sides[gi])
            gi += 1
        out.append((minute, sm.home_win(m.lh, m.la, (90 - minute) / 90.0, diff)))
    return out, list(zip(m.times, m.sides, strict=True))


def faster_feed(mm_lat: float = 1.5) -> dict:
    """Exercise 7: a feed twice as fast; the loss per goal by delay and the negligible delay."""
    base = sm.season(N, 0.0, mm_lat=mm_lat)["loss_per_goal"]
    rows = {d: sm.season(N, d, mm_lat=mm_lat)["loss_per_goal"] for d in DELAYS}
    return {"rows": rows, "negligible": min(d for d in DELAYS if rows[d] < 0.01 * base)}
