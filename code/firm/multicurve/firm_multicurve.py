"""Discount and projection curves (build of One Quant Book 6, chapter 2).

A projection curve per floating-rate index (e.g. six-month Euribor) is calibrated on a fixed
discount curve (the overnight-rate curve of the collateral currency, built with `firm_curvebuild`),
so that interbank-index swaps reprice. Adds: tenor-basis-swap spreads, collateral discounting with
a choice of collateral (effective forward = pointwise maximum of the eligible collateral rates in
the trade currency), and a shift of the discount curve such as a clearing house's discounting switch.

Conventions (teaching): fixed legs annual ACT/360; floating legs pay the simple forward of the
index over each period, ACT/360; no business-day adjustment; ACT/365 times.
"""
import datetime as dt
import math
import pathlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "curvebuild"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "curve"))
from firm_curve import add_years  # noqa: E402
from firm_curvebuild import ZeroCurve  # noqa: E402


def add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(y, m, day)
        except ValueError:
            continue
    raise ValueError(d)


def simple_forward(curve, s: dt.date, e: dt.date) -> float:
    return (curve.df(s) / curve.df(e) - 1) / ((e - s).days / 360)


def annuity(disc, start: dt.date, years: int) -> float:
    d = [add_years(start, k) for k in range(years + 1)]
    return sum((b - a).days / 360 * disc.df(b) for a, b in zip(d, d[1:], strict=False))


def float_leg(proj, disc, start: dt.date, years: int, months: int, spread: float = 0.0) -> float:
    """Value per unit notional of a floating leg paying the projected index (+ spread)."""
    d = [add_months(start, k * months) for k in range(12 * years // months + 1)]
    return sum((simple_forward(proj, a, b) + spread) * (b - a).days / 360 * disc.df(b)
               for a, b in zip(d, d[1:], strict=False))


@dataclass(frozen=True)
class IborSwap:
    """Par swap: annual fixed (ACT/360) against an interbank index paid every `months` months."""
    start: dt.date
    years: int
    rate: float
    months: int = 6
    label: str = ""

    @property
    def maturity(self) -> dt.date:
        return add_years(self.start, self.years)

    def quote(self) -> float:
        return self.rate

    def model(self, proj, disc) -> float:
        return float_leg(proj, disc, self.start, self.years, self.months) / annuity(disc, self.start, self.years)


@dataclass(frozen=True)
class Fixing:
    """The index fixing for its own tenor from spot: pins the projection curve's first pillar."""
    start: dt.date
    end: dt.date
    rate: float
    label: str = ""

    @property
    def maturity(self) -> dt.date:
        return self.end

    def quote(self) -> float:
        return self.rate

    def model(self, proj, disc) -> float:
        return simple_forward(proj, self.start, self.end)


def calibrate_projection(spot: dt.date, disc, instruments: Sequence, kind: str = "monotone_convex",
                         tol: float = 1e-12, max_iter: int = 30) -> ZeroCurve:
    """Solve the projection curve's pillar zero rates with the discount curve held fixed."""
    times = [(i.maturity - spot).days / 365.0 for i in instruments]
    labels = [i.label or f"P{k}" for k, i in enumerate(instruments)]
    q = np.array([i.quote() for i in instruments])
    z = q.copy()

    def resid(zv):
        c = ZeroCurve(spot, times, list(zv), kind, labels)
        return np.array([i.model(c, disc) for i in instruments]) - q
    r = resid(z)
    for _ in range(max_iter):
        if np.max(np.abs(r)) < tol:
            break
        jac = np.empty((len(z), len(z)))
        for j in range(len(z)):
            e = z.copy()
            e[j] += 1e-7
            jac[:, j] = (resid(e) - r) / 1e-7
        z = z - np.linalg.solve(jac, r)
        r = resid(z)
    return ZeroCurve(spot, times, list(z), kind, labels)


def ibor_swap_pv(proj, disc, start: dt.date, years: int, fixed: float, notional: float, months: int = 6,
                 payer: bool = True) -> float:
    v = notional * (float_leg(proj, disc, start, years, months) - fixed * annuity(disc, start, years))
    return v if payer else -v


def tenor_basis(proj, disc, start: dt.date, years: int, months: int = 6) -> float:
    """Par spread over the overnight rate (compounded, annual, ACT/360) that equates an overnight
    leg with the index leg: the tenor-basis-swap spread."""
    ann = annuity(disc, start, years)
    ois_leg = disc.df(start) - disc.df(add_years(start, years))
    return (float_leg(proj, disc, start, years, months) - ois_leg) / ann


class ShiftedCurve:
    """A discount curve whose instantaneous forwards are shifted by a constant (e.g. EONIA = ESTR + 8.5 bp)."""

    def __init__(self, base, shift: float):
        self.base, self.shift, self.spot = base, shift, base.spot

    def t(self, d: dt.date) -> float:
        return self.base.t(d)

    def df(self, d: dt.date) -> float:
        return self.base.df(d) * math.exp(-self.shift * self.base.t(d))


class CollateralChoiceCurve:
    """Discounting with a choice of collateral: the poster chooses the eligible collateral with the
    highest rate in the trade currency, so the effective forward is max_i (f_i(t) + s_i(t)). With
    deterministic rates this is the option's intrinsic value only."""

    def __init__(self, base, spreads: Sequence, step: float = 1 / 365):
        self.base, self.spreads, self.spot, self.step = base, list(spreads), base.spot, step

    def t(self, d: dt.date) -> float:
        return self.base.t(d)

    def fwd_t(self, t: float) -> float:
        f = self.base.fwd_t(t)
        return max(f + s(t) for s in self.spreads)

    def df_t(self, t: float) -> float:
        n = max(1, int(math.ceil(t / self.step)))
        h = t / n
        integral = sum(max(s((k + 0.5) * h) for s in self.spreads) for k in range(n)) * h
        return self.base.df_t(t) * math.exp(-integral)

    def df(self, d: dt.date) -> float:
        return self.df_t(self.t(d))
