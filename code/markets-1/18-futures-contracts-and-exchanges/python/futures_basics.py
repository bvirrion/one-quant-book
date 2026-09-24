"""Contract arithmetic: notional, tick value, leverage and hedge sizing (Chapter 18). Illustrative prices."""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Spec:
    root: str
    multiplier: float            # currency per full price point
    tick: float
    currency: str
    ref_price: float             # an illustrative price, not a quote

    @property
    def tick_value(self) -> float:
        return self.multiplier * self.tick

    @property
    def notional(self) -> float:
        return self.multiplier * self.ref_price

    @property
    def tick_bp(self) -> float:
        """One tick as basis points of the contract's value."""
        return self.tick / self.ref_price * 1e4


SPECS = (
    Spec("ES", 50.0, 0.25, "USD", 6000.0),
    Spec("FESX", 10.0, 1.0, "EUR", 5400.0),
    Spec("ZN", 1000.0, 1 / 64, "USD", 112.0),
    Spec("FGBL", 1000.0, 0.01, "EUR", 128.0),
    Spec("CL", 1000.0, 0.01, "USD", 70.0),
    Spec("B", 1000.0, 0.01, "USD", 74.0),
)


def leverage(spec: Spec, margin: float) -> float:
    return spec.notional / margin


def hedge(portfolio_value: float, beta: float, spec: Spec) -> tuple[int, float]:
    """Contracts to sell (nearest integer) and the residual exposure left, in currency."""
    exact = beta * portfolio_value / spec.notional
    n = math.floor(exact + 0.5)
    return n, beta * portfolio_value - n * spec.notional


def roll_open_interest(days: int, roll_day: int, width: float, total: float, seed: int):
    """Open interest of the front and next contract around a roll: a logistic hand-over plus noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(days)
    share = 1.0 / (1.0 + np.exp((t - roll_day) / width))
    noise = 1.0 + rng.normal(0.0, 0.01, days)
    return total * share * noise, total * (1.0 - share) * noise
