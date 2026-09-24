"""Gamma as expiry approaches, and what hedgers' flow does to the underlying (Chapter 26). Illustrative."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/gex"))
from firm_gex import YEAR_MINUTES, gamma


def atm_gamma_by_minutes(spot: float, vol: float, minutes: list[float]) -> list[float]:
    """Gamma of the at-the-money option, per 1% move and per 100 of notional, as expiry approaches."""
    return [gamma(spot, spot, m / YEAR_MINUTES, vol) * spot * 0.01 * spot / 100.0 for m in minutes]


def straddle_price(spot: float, vol: float, years: float) -> float:
    """At-the-money straddle, zero rates: 2 S (2 N(s/2) - 1), close to 0.8 S sigma sqrt(T)."""
    s = vol * math.sqrt(years)
    return 2.0 * spot * (2.0 * 0.5 * (1.0 + math.erf(s / 2.0 / math.sqrt(2.0))) - 1.0)


def simulate_with_hedgers(n: int, steps: int, step_vol: float, feedback: float, seed: int) -> float:
    """Realised volatility of a price whose hedgers trade `feedback` times the last move:
    feedback < 0 (hedgers long gamma) sells rallies; feedback > 0 (short gamma) buys them.
    Returns realised volatility relative to the volatility of the news alone."""
    rng = np.random.default_rng(seed)
    news = rng.normal(0.0, step_vol, (n, steps))
    r = np.zeros_like(news)
    r[:, 0] = news[:, 0]
    for t in range(1, steps):
        r[:, t] = news[:, t] + feedback * r[:, t - 1]
    return float(r.sum(axis=1).std() / news.sum(axis=1).std())
