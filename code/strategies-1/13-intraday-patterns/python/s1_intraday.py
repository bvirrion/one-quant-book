"""Intraday patterns (One Quant Book 8, chapter 13).

Twenty years (5,040 days) of an index traded in half-hour bars (firm.intraday): 16% volatility, a 7% expected return
spread in proportion to variance, a quarter of the variance arriving overnight, a U-shaped volume curve. Measured, with
and without dealers who hedge a short-gamma book in the last half hour (5% of the day's move so far, half of it reversed
the next day): the share of the cumulative return earned overnight; the regression of the last half hour's return on
the rest of the day's; a last-half-hour momentum trade (futures, 1 basis point a round trip); and a trade that fades the
closing auction's published imbalance from the close to the next open. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "intraday"))
from firm_intraday import DayConfig, last_half_hour, simulate_days  # noqa: E402

DAYS, YEAR, COST = 5040, 252, 0.0001


@functools.lru_cache(maxsize=4)
def days(gamma: float = 0.0):
    return simulate_days(DAYS, DayConfig(gamma=gamma), np.random.default_rng(13))


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


@functools.lru_cache(maxsize=4)
def summary(gamma: float = 0.0):
    d = days(gamma)
    on, bars = d["overnight"], d["bars"]
    day = bars.sum(axis=1)
    slope, t = last_half_hour(bars, on)
    rest = on + bars[:, :-1].sum(axis=1)
    mom = np.sign(rest) * bars[:, -1] - COST                        # the last half hour, in the day's direction
    fade = -np.sign(d["imbalance"][:-1]) * on[1:] - COST            # against the close imbalance, to the next open
    return {"on_share": float(on.sum() / (on.sum() + day.sum())), "on_ann": float(on.mean() * YEAR),
            "day_ann": float(day.mean() * YEAR), "slope": slope, "t": t, "mom_sr": sharpe(mom),
            "mom_ann": float(mom.mean() * YEAR), "fade_sr": sharpe(fade), "fade_ann": float(fade.mean() * YEAR),
            "hit": float((np.sign(rest) == np.sign(bars[:, -1])).mean()), "next_day": next_day(d)}


def next_day(d) -> float:
    """Slope of the next overnight return on the last half hour's return: the reversal of the hedging push."""
    x, y = d["bars"][:-1, -1], d["overnight"][1:]
    return float(np.polyfit(x, y, 1)[0])


def smile():
    return days()["volume"]
