"""Hedging structured products (One Quant Book 9, chapter 28).

Synthetic: firm.sphedge's book of five-year autocallables sold on two indices (400 and 300 million on each alone,
300 million worst-of both; 20% volatility, a local-volatility skew, 3% dividends, correlation 0.7), priced with Book
5's autocallable engine; the issuer's exposures to volatility, skew, dividends and correlation; one note's vega and
delta against the index level; and the implied-volatility move and costs of recycling the book's vega into markets
of three depths. NumPy.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "sphedge"))
from firm_sphedge import BOOK, BUMPS, book_exposures, recycling_impact, spot_profile  # noqa: E402

SPOTS = tuple(round(0.40 + 0.05 * k, 2) for k in range(17))
DEPTHS = (5e6, 10e6, 20e6)


@functools.lru_cache(maxsize=1)
def exposures() -> dict:
    return book_exposures()


def margin() -> dict:
    """The bank's margin: 100 less each note's value, per 100 and in currency."""
    v = exposures()["value"]
    return {n.name: {"per100": 100 - v[n.name], "money": (100 - v[n.name]) / 100 * n.notional} for n in BOOK} | {
        "total": sum((100 - v[n.name]) / 100 * n.notional for n in BOOK)}


@functools.lru_cache(maxsize=1)
def profile() -> dict:
    return spot_profile(BOOK[0], SPOTS)


def recycling() -> dict:
    vega = exposures()["vega"]["total"]
    return {d: recycling_impact(vega, d) for d in DEPTHS} | {"vega": vega}


def table() -> dict:
    e = exposures()
    return {k: {"total": e[k]["total"], "by_note": e[k]["by_note"], "bump": BUMPS[k][1]} for k in BUMPS}
