"""Reserve calculator for an exotic book (build of Book 5, Chapter 27): bid-offer reserves by risk bucket, a model
reserve from a set of models, a parameter reserve from the plausible range of an unobservable input, their
aggregation, the day-one P&L split and its release schedule, and a stress grid.

Sign convention: values are the book's value to the firm (a short note has a negative value); a reserve is a
positive amount that lowers the book's value (it is what the firm holds back).
"""
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np


def bid_offer_reserve(exposures: Mapping[str, float], half_spreads: Mapping[str, float]) -> dict[str, float]:
    """Cost of closing the net exposure of each risk bucket at the half bid-offer spread: |exposure| x half-spread.
    Exposures and spreads share units per bucket (e.g. vega per point and points, delta in currency and a fraction)."""
    out = {k: abs(exposures[k]) * half_spreads[k] for k in exposures}
    out["total"] = sum(out.values())
    return out


def prudent_point(values: Sequence[float], confidence: float = 0.9, weights: Sequence[float] | None = None) -> float:
    """The point of a range of plausible values of the book at which the firm is `confidence` sure it could exit at that
    value or better: the (1 - confidence) quantile of the plausible values (weighted, by linear interpolation)."""
    v = np.asarray(values, float)
    w = np.full(len(v), 1.0 / len(v)) if weights is None else np.asarray(weights, float) / np.sum(weights)
    order = np.argsort(v)
    v, w = v[order], w[order]
    cum = np.cumsum(w) - 0.5 * w                                     # mid-point plotting positions
    return float(np.interp(1 - confidence, cum, v))


def model_reserve(values_by_model: Mapping[str, float], booked: str, confidence: float = 0.9) -> float:
    """Model reserve: booked model's value minus the prudent point of the values under the model set (at least 0)."""
    return max(values_by_model[booked] - prudent_point(list(values_by_model.values()), confidence), 0.0)


def parameter_reserve(value_of: Callable[[float], float], mid: float, lo: float, hi: float, confidence: float = 0.9,
                      n: int = 41) -> dict[str, float]:
    """Parameter bid-offer for one unobservable input spread uniformly over [lo, hi]: the book's value at the prudent
    point of the values over the range, against its value at the booked input `mid`."""
    grid = np.linspace(lo, hi, n)
    values = [value_of(x) for x in grid]
    prudent = prudent_point(values, confidence)
    booked = value_of(mid)
    return {"booked": booked, "prudent": prudent, "reserve": max(booked - prudent, 0.0),
            "worst": float(min(values)), "best": float(max(values))}


def aggregate(reserves: Sequence[float], diversification: float = 0.5) -> float:
    """Category-level total after the aggregation benefit: diversification x the sum (Method 1 of the EU
    prudent-valuation standard applies 50 % to the market-price, close-out and model-risk categories)."""
    return diversification * float(np.sum(reserves))


@dataclass(frozen=True)
class DayOne:
    margin: float          # transaction price minus the booked mid value (the trade's economic margin)
    charged: float         # observable reserves at inception (bid-offer): part of fair value, not a deferral
    deferred: float        # reserves on unobservable inputs (model, parameter): held back, released later
    recognised: float      # margin - charged - deferred


def day_one(price_received: float, booked_value_of_liability: float, observable_reserve: float,
            unobservable_reserve: float) -> DayOne:
    """Split a sale's margin: the part left after the observable reserves and the reserves on unobservable inputs is
    recognised at inception; the unobservable part is deferred."""
    margin = price_received - booked_value_of_liability
    recognised = margin - observable_reserve - unobservable_reserve
    return DayOne(margin, observable_reserve, unobservable_reserve, recognised)


def release_schedule(deferred_by_date: Sequence[tuple[float, float]]) -> list[tuple[float, float, float]]:
    """Release of a deferred amount as its reserve falls: from (time, deferred balance) pairs, the list of (time,
    balance, amount released since the previous date); a rise is a new deferral (negative release)."""
    out = []
    prev = None
    for t, bal in deferred_by_date:
        out.append((t, bal, 0.0 if prev is None else prev - bal))
        prev = bal
    return out


def stress_grid(value_of: Callable[[float, float], float], spot_shocks: Sequence[float],
                vol_shocks: Sequence[float], hedge_delta: float = 0.0) -> np.ndarray:
    """P&L of the book (plus `hedge_delta` units of the underlying per unit relative shock) under joint relative spot
    shocks and absolute volatility shocks: rows follow vol_shocks, columns spot_shocks."""
    base = value_of(0.0, 0.0)
    return np.array([[value_of(ds, dv) - base + hedge_delta * ds for ds in spot_shocks] for dv in vol_shocks])


def concentration_days(position: float, daily_volume: float, participation: float = 0.1) -> float:
    """Days needed to exit a position trading `participation` of the daily volume: a prudent exit period above ten
    days calls for a concentration adjustment."""
    return abs(position) / (participation * daily_volume)
