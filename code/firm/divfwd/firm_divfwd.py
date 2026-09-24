"""Equity forward curve: discrete dividends, borrow, and what put-call parity implies about both
(build of Book 5, Chapter 5).

Times are year fractions from today; rates continuously compounded.
    F(T) = (S - sum_{t_i <= T} D_i P(t_i)) * prod_{t_j <= T} (1 - y_j) * exp(-l T) / P(T)
with cash dividends D_i, proportional dividends y_j and a borrow fee l. From a chain, parity
C - P = P(T) (F - K) is linear in K: a regression across strikes returns P(T) and F(T) together.
"""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ForwardCurve:
    spot: float
    rate: float                                          # flat financing rate
    cash: tuple[tuple[float, float], ...] = ()           # (time, amount)
    proportional: tuple[tuple[float, float], ...] = ()   # (time, fraction of the share)
    borrow: float = 0.0

    def df(self, t: float) -> float:
        return math.exp(-self.rate * t)

    def pv_cash(self, t: float) -> float:
        return sum(d * self.df(ti) for ti, d in self.cash if 0.0 < ti <= t)

    def forward(self, t: float) -> float:
        prop = math.prod(1.0 - y for ti, y in self.proportional if 0.0 < ti <= t)
        return (self.spot - self.pv_cash(t)) * prop * math.exp(-self.borrow * t) / self.df(t)


def implied_forward(strikes, calls, puts) -> tuple[float, float]:
    """Least squares of C - P on K across strikes: slope -P(T), intercept P(T) F. Returns (F, P(T))."""
    k = np.asarray(strikes, float)
    y = np.asarray(calls, float) - np.asarray(puts, float)
    a = np.column_stack([np.ones_like(k), k])
    (intercept, slope), *_ = np.linalg.lstsq(a, y, rcond=None)
    df = -slope
    return float(intercept / df), float(df)


def implied_carry(spot: float, fwd: float, df: float) -> float:
    """PV of everything the forward removes from the spot: dividends plus the cost of borrow
    (Book 1, Chapter 25's D_imp)."""
    return spot - fwd * df


def implied_borrow(spot: float, fwd: float, df: float, t: float, pv_dividends: float = 0.0) -> float:
    """Borrow fee l such that F = (S - PV divs) exp(-l T) / P(T), given a dividend forecast."""
    return -math.log(fwd * df / (spot - pv_dividends)) / t


def strip_dividends(spot: float, expiries, forwards, dfs) -> list[float]:
    """PV (today) of the carry implied between consecutive expiries: the dividend term structure."""
    carry = [implied_carry(spot, f, d) for f, d in zip(forwards, dfs, strict=True)]
    return [carry[0]] + [b - a for a, b in zip(carry, carry[1:], strict=False)]
