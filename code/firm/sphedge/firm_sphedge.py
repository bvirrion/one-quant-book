"""firm.sphedge -- an autocallable book's exposures, recycling trades and their market impact (Book 9, chapter 28).

A bank has sold autocallables on two indices, singly and worst-of both (Book 5's `firm_autocall`: term sheets, paths
and cash flows). Its exposures are the notes' value changes, with the sign reversed, for bumps of volatility,
downside skew, dividend yield and the correlation between the indices, all with common random numbers. The book is
long volatility, long skew and long dividends, and short correlation; it recycles them by selling long-dated
volatility and dividends to hedge funds and buying correlation. A linear impact model says how far its selling moves
long-dated implied volatility, and what a hedge fund that buys the recycled vega earns if volatility returns. NumPy.

API (stable):
    Note(...), BOOK                            a term sheet with its notional and underlying(s); the chapter's book
    MarketState(...)                           volatility, skew slope, dividend yield, correlation, rate
    note_value(note, mkt, paths, seed)         value per 100 on monthly paths (exact for constant volatility)
    book_exposures(book, mkt, paths, seed)     the issuer's P&L for each bump, per note and in total
    spot_profile(note, spots, mkt)             the issuer's vega and delta of one note against the index level
    recycling_impact(vega, depth)              move of long-dated implied volatility (vol points), cost and gain
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, replace

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "autocall"))
from firm_autocall import TermSheet, cashflows, simulate  # noqa: E402


@dataclass(frozen=True)
class Note:
    name: str
    notional: float
    assets: tuple                 # indices of the underlyings: (0,), (1,) or (0, 1) for worst-of
    coupon: float = 7.0


@dataclass(frozen=True)
class MarketState:
    vol: float = 0.20
    skew: float = 0.10            # local volatility rises by this much per 100% fall of the index
    div: float = 0.03
    corr: float = 0.70
    rate: float = 0.03


BOOK = (Note("single A", 400e6, (0,), 7.0), Note("single B", 300e6, (1,), 7.0),
        Note("worst-of A, B", 300e6, (0, 1), 9.0))
BUMPS = {"vega": ("vol", 0.01), "skew": ("skew", 0.05), "dividends": ("div", 0.001), "correlation": ("corr", 0.05)}


def _sigma(mkt: MarketState):
    return lambda t, s: np.clip(mkt.vol + mkt.skew * (1.0 - s), 0.05, 1.0)


def note_value(note: Note, mkt: MarketState, paths: int = 20_000, seed: int = 197, spot: float = 1.0) -> float:
    """Five-year note, annual observations, autocall at 100%, Phoenix coupon at a 70% barrier with memory, 60%
    protection at maturity; value per 100 on monthly paths of the (worst-of the) underlyings, which start at `spot`
    times the strike."""
    ts = TermSheet(obs_times=(1.0, 2.0, 3.0, 4.0, 5.0), trigger=1.0, coupon=note.coupon, coupon_barrier=0.7,
                   protection=0.6)
    m = len(note.assets)
    corr = np.array([[1.0, mkt.corr], [mkt.corr, 1.0]]) if m == 2 else None
    times, perf = simulate(_sigma(mkt), np.ones(m), ts.maturity, mkt.rate, mkt.div, paths, seed, steps_per_year=12,
                           corr=corr)
    return float(cashflows(ts, times, spot * perf, mkt.rate)["pv"].mean())


def book_exposures(book=BOOK, mkt: MarketState | None = None, paths: int = 20_000, seed: int = 197) -> dict:
    """For each bump: the issuer's P&L (the notes' value falls are its gains), by note and in total, in currency."""
    mkt = mkt or MarketState()
    base = {n.name: note_value(n, mkt, paths, seed) for n in book}
    out = {"value": base}
    for key, (field, size) in BUMPS.items():
        bumped = replace(mkt, **{field: getattr(mkt, field) + size})
        by = {n.name: -(note_value(n, bumped, paths, seed) - base[n.name]) / 100 * n.notional
              for n in book if key != "correlation" or len(n.assets) == 2}
        out[key] = {"by_note": by, "total": sum(by.values()), "bump": size}
    return out


def spot_profile(note: Note, spots, mkt: MarketState | None = None, paths: int = 20_000, seed: int = 197) -> dict:
    """The issuer's vega (currency per vol point) and delta (currency of index per 1% move) of one note, at the start of
    its life, if the index opened at each level relative to the strike. Local volatility is left as a function of the
    level relative to today's, as a sticky-moneyness market would quote it after a move."""
    mkt = mkt or MarketState()
    out = {"spot": list(spots), "vega": [], "delta": []}
    for s in spots:
        v0 = note_value(note, mkt, paths, seed, s)
        vv = note_value(note, replace(mkt, vol=mkt.vol + 0.01), paths, seed, s)
        up, dn = note_value(note, mkt, paths, seed, s * 1.02), note_value(note, mkt, paths, seed, s * 0.98)
        out["vega"].append(-(vv - v0) / 100 * note.notional)
        out["delta"].append(-(up - dn) / 4 / 100 * note.notional)          # per 1% move, central difference over 2%
    return out


def recycling_impact(vega: float, depth: float) -> dict:
    """Selling `vega` (currency per vol point) into a market that gives `depth` of vega per vol point of price
    concession lowers long-dated implied volatility by vega / depth points; with a linear concession the seller pays
    half the move on average, and a buyer who holds until volatility returns earns the whole move."""
    move = vega / depth
    return {"move": -move, "seller_cost": vega * move / 2, "buyer_gain": vega * move}
