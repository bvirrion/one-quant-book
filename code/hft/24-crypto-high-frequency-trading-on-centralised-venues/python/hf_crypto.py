"""Crypto high-frequency trading on centralised venues (One Quant Book 11, chapter 24).

One simulated week of a coin at 60,000 dollars (3% daily volatility): a maker quotes the perpetual on one venue at
2 bp either side of the fair price shown by another venue's spot book, hedges every fill on spot by taking (1 bp fee,
0.5 bp half-spread), is paid funding every eight hours, and meets a liquidation cascade on day 4 at noon (the
perpetual 80 bp below spot, $50,000 a second of forced sells for five minutes). Its request budget decides how often
it can move its quotes.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "cryptohft"))
import firm_cryptohft as ch  # noqa: E402

BASE = {"requote_per_s": 1.0, "absorb": True, "absorb_limit": 5e6, "absorb_from_bp": 40.0}
RATES = (1.0, 0.5, 0.25, 0.2, 0.1)


@functools.cache
def week() -> ch.Week:
    return ch.Week(seed=1)


@functools.cache
def base() -> dict:
    return ch.run(week(), **BASE)


@functools.cache
def budget() -> dict:
    return {r: ch.run(week(), **(BASE | {"requote_per_s": r})) for r in RATES}


@functools.cache
def absorption() -> dict:
    out = {"pull": ch.run(week(), **(BASE | {"absorb": False}))}
    for fr in (0.0, 20.0, 40.0, 60.0):
        out[fr] = ch.run(week(), **(BASE | {"absorb_from_bp": fr}))
    return out


def governor_budget() -> dict:
    g = ch.rl.binance_like
    return {n: ch.budget_from(g(), n) for n in (1, 2, 5)}


def early_small() -> dict:
    """Exercise 7: a $2 million limit from the first second of the cascade."""
    return ch.run(week(), **(BASE | {"absorb_limit": 2e6, "absorb_from_bp": 0.0}))
