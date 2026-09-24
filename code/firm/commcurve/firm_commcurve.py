"""Commodity forward curves, convenience yield, roll yield and the index roll (build of Book 3,
Chapter 10).

Times in years, rates continuously compounded. Under the cost-of-carry relation with storage cost
u and convenience yield y_c, F(tau) = S exp((r + u - y_c) tau); between two futures,
F2 / F1 = exp((r + u - y_c)(tau2 - tau1)).
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ForwardCurve:
    taus: tuple[float, ...]
    prices: tuple[float, ...]

    def __post_init__(self) -> None:
        if list(self.taus) != sorted(self.taus) or len(self.taus) != len(self.prices) or min(self.prices) <= 0:
            raise ValueError("maturities must increase and prices be positive")

    def price(self, tau: float) -> float:
        """Log-linear interpolation, flat extrapolation."""
        t, p = self.taus, self.prices
        if tau <= t[0]:
            return p[0]
        if tau >= t[-1]:
            return p[-1]
        i = next(k for k in range(1, len(t)) if t[k] >= tau)
        w = (tau - t[i - 1]) / (t[i] - t[i - 1])
        return math.exp((1 - w) * math.log(p[i - 1]) + w * math.log(p[i]))

    def shape(self) -> str:
        return "contango" if self.prices[-1] > self.prices[0] else "backwardation"


def net_convenience_yield(f1: float, f2: float, dt: float, r: float) -> float:
    """y_c - u implied by two futures `dt` years apart and the rate r."""
    return r - math.log(f2 / f1) / dt


def full_carry_spread(f1: float, dt: float, r: float, u: float) -> float:
    """Far minus near price at full carry (convenience yield zero): the largest spread storage allows."""
    return f1 * (math.exp((r + u) * dt) - 1.0)


def roll_yield(f_near: float, f_far: float, dt: float) -> float:
    """Annualised return from rolling a long position from the far contract as it converges to the
    near one, all else equal: positive in backwardation."""
    return math.log(f_near / f_far) / dt


def roll_weights(business_day: int, start: int = 5, end: int = 9) -> float:
    """Share of an index position already moved to the next contract after the close of the
    `business_day`-th business day of the month, rolling equal parts on days start..end."""
    n = end - start + 1
    return min(max(business_day - start + 1, 0), n) / n


def decompose(excess_log: float, spot_log: float, collateral_log: float) -> dict[str, float]:
    """Split a total-return index's log return into spot, roll and collateral parts."""
    return {"spot": spot_log, "roll": excess_log - spot_log, "collateral": collateral_log,
            "total": excess_log + collateral_log}
