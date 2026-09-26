"""News and event trading (One Quant Book 11, chapter 18).

A scheduled release moves a future by 3 ticks per standard deviation of surprise; ten levels of 50 stale lots
from other providers who update after 20 ms, plus our market maker's 20 lots at each of the first three levels; four
latency tiers (0.05, 1, 5 and 50 ms), 200 lots each. Then the market maker's re-entry into the post-release flow.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "newsrace"))
import firm_newsrace as nr  # noqa: E402

N = 20000
TICK_USD = 12.5


@functools.cache
def base(stale_ms: float = 20.0) -> dict:
    return nr.simulate(n=N, seed=1, stale_ms=stale_ms)


def reentry_curve() -> dict:
    return {t: nr.reentry(t) for t in (0.0, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 30, 40, 60)}


def protocol() -> dict:
    b = base()
    re = reentry_curve()
    stay = re[0.0] - b["mm_loss_per_release"]
    return {"loss_if_stays": b["mm_loss_per_release"], "stay_total": stay, "protocol_total": re[b["best_reentry"]],
            "best_reentry": b["best_reentry"], "reenter_at_half_second": re[0.5]}


def headline(p_wrong: float = 0.02, capture: float = 2.0, loss: float = 10.0) -> float:
    return nr.misparse(p_wrong, capture, loss)
