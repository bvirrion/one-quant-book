"""Basis over a contract's life, index arbitrage and roll yield (Chapter 21). Illustrative."""
import datetime as dt
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fairvalue"))
from firm_fairvalue import ArbCosts, Dividend, arbitrage_band, fair_value

TODAY, DEC, MAR = dt.date(2026, 9, 18), dt.date(2026, 12, 18), dt.date(2027, 3, 19)
DIVS = [Dividend(dt.date(y, m, d), pts) for y, m, d, pts in (
    (2026, 10, 15, 6.0), (2026, 11, 16, 9.5), (2026, 12, 10, 5.5),
    (2027, 1, 15, 6.0), (2027, 2, 15, 9.5), (2027, 3, 10, 5.5))]


def basis_path(spot: float, rate: float, start: dt.date, expiry: dt.date, divs: list[Dividend]):
    """Fair basis (future minus spot) on each calendar day with the index held constant:
    interest accrues away linearly and each dividend, once paid, stops being subtracted."""
    days = [start + dt.timedelta(days=k) for k in range((expiry - start).days + 1)]
    return days, [fair_value(spot, rate, d, expiry, divs) - spot for d in days]


def mispricing(n: int, lower: float, upper: float, vol: float, kappa: float, seed: int):
    """Future minus fair value: noise pulled back gently inside the band [lower, upper] and
    pushed back by arbitrageurs when it leaves it."""
    rng = np.random.default_rng(seed)
    x, out, hits = 0.0, [], {"upper": 0, "lower": 0}
    for _ in range(n):
        x += -kappa * x + rng.normal(0.0, vol)
        if x > upper:
            hits["upper"] += 1
            x = 0.6 * upper
        elif x < lower:
            hits["lower"] += 1
            x = 0.6 * lower
        out.append(x)
    return np.array(out), hits


def roll_yield(near: float, far: float, years_between: float) -> float:
    """Annualised return from rolling a long position down (or up) the curve, prices unchanged."""
    return (near / far - 1.0) / years_between


def rolled_index(curves: np.ndarray) -> np.ndarray:
    """Value of 1 invested in the front contract, rolled each period into the next one.
    curves[t] = (front, second) at the start of period t; at the end of the period the second
    has become the front. Excess return only (collateral interest ignored)."""
    value = [1.0]
    for t in range(len(curves) - 1):
        value.append(value[-1] * curves[t + 1][0] / curves[t][1])
    return np.array(value)


def example_band():
    return arbitrage_band(6000.0, 0.042, TODAY, DEC, DIVS, ArbCosts(3.0, 0.5, 40.0, 15.0))
