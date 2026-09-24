"""Structured-product term sheets (build of Book 5, Chapter 19): decomposition of a note into a zero-coupon bond at
the issuer's funding rate and option legs, the participation and margin solvers, a reverse convertible's coupon,
and the calculators of volatility-target and decrement indices.

Conventions: amounts per 100 of notional; continuously compounded rates; the issuer's zero-coupon bond is
discounted at the risk-free rate plus the issuer's funding spread.
"""
import math
import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import bs  # noqa: E402


@dataclass(frozen=True)
class Leg:
    kind: str                 # "zero", "call", "put"
    quantity: float           # per 100 of notional (calls and puts: on 100 of underlying)
    strike: float = 0.0       # relative to the initial level


@dataclass(frozen=True)
class Note:
    maturity: float
    legs: tuple[Leg, ...] = field(default_factory=tuple)


def zero_coupon(t: float, r: float, spread: float) -> float:
    """Value of 100 paid by the issuer at t."""
    return 100.0 * math.exp(-(r + spread) * t)


def value(note: Note, r: float, spread: float, q: float, vol_of_k) -> float:
    """Value of the note's legs to the investor (options at the smile volatility of their strikes)."""
    out = 0.0
    for leg in note.legs:
        if leg.kind == "zero":
            out += leg.quantity / 100.0 * zero_coupon(note.maturity, r, spread)
        else:
            right = "C" if leg.kind == "call" else "P"
            out += leg.quantity * bs(1.0, leg.strike, note.maturity, r, q, vol_of_k(leg.strike), right)
    return out


def protected_note(t: float, participation: float, protection: float = 1.0, cap: float | None = None) -> Note:
    """protection x 100 at maturity plus participation x 100 x (performance - 1)^+, capped at cap - 1 if given."""
    legs = [Leg("zero", 100.0 * protection), Leg("call", 100.0 * participation, 1.0)]
    if cap is not None:
        legs.append(Leg("call", -100.0 * participation, cap))
    return Note(t, tuple(legs))


def max_participation(t: float, r: float, spread: float, q: float, vol_of_k, margin: float,
                      protection: float = 1.0, cap: float | None = None) -> float:
    """The participation that leaves the issuer exactly its margin: the option budget is the issue price (100) less
    the protected amount's zero-coupon value less the margin, divided by the price of one unit of the option leg."""
    budget = 100.0 - protection * zero_coupon(t, r, spread) - margin
    unit = value(protected_note(t, 1.0, 0.0, cap), r, spread, q, vol_of_k)
    return budget / unit


def spread_for_participation(target: float, t: float, r: float, q: float, vol_of_k, margin: float,
                             protection: float = 1.0, cap: float | None = None) -> float:
    """The issuer funding spread at which the note can offer `target` participation after `margin` (closed form:
    the zero-coupon value must equal 100 - margin - target x option)."""
    unit = value(protected_note(t, 1.0, 0.0, cap), r, 0.0, q, vol_of_k)
    zc = (100.0 - margin - target * unit) / protection
    return -math.log(zc / 100.0) / t - r


def reverse_convertible_coupon(t: float, r: float, spread: float, q: float, vol_of_k, strike: float,
                               margin: float) -> float:
    """Annual coupon (paid at maturity, simple) of a note repaying 100 unless the underlying ends below strike, in
    which case it repays 100 x performance / strike (the investor is short 100 / strike puts): the coupon is funded
    by the funding benefit, the put premium and nothing else, after the margin."""
    put = 100.0 / strike * bs(1.0, strike, t, r, q, vol_of_k(strike), "P")
    budget = 100.0 - zero_coupon(t, r, spread) + put - margin
    return budget / (t * math.exp(-(r + spread) * t) * 100.0) * 100.0


# ---------------------------------------------------------------- strategy indices
def ewma_vol(returns: np.ndarray, lam: float = 0.94, dt: float = 1 / 252, start: float = 0.2) -> np.ndarray:
    """Exponentially weighted volatility estimate known at the start of each day (lagged), per path.
    returns has shape (n_paths, n_days)."""
    var = np.full(returns.shape[0], start * start)
    out = np.empty_like(returns)
    for i in range(returns.shape[1]):
        out[:, i] = np.sqrt(var)
        var = lam * var + (1 - lam) * returns[:, i] ** 2 / dt
    return out


def vol_target_index(returns: np.ndarray, target: float, rate: float = 0.0, lam: float = 0.94, max_lev: float = 1.5,
                     dt: float = 1 / 252, fee: float = 0.0) -> np.ndarray:
    """Index levels (start 1) of a strategy holding target / sigma_hat of the underlying (capped at max_lev) and the
    rest in cash at `rate`, less a running fee. returns are the underlying's simple daily excess-of-nothing returns."""
    exposure = np.minimum(target / ewma_vol(returns, lam, dt), max_lev)
    daily = exposure * returns + (1 - exposure) * rate * dt - fee * dt
    return np.hstack([np.ones((returns.shape[0], 1)), np.cumprod(1 + daily, axis=1)])


def decrement_index(total_return: np.ndarray, decrement: float, dt: float = 1 / 252, points: float | None = None,
                    base: float = 100.0) -> np.ndarray:
    """A decrement index built on a total-return index: each day it earns the total return and pays a fixed
    decrement, either as a percentage a year (decrement) or in index points a year (points, on the base scale)."""
    tr = np.asarray(total_return, float)
    ret = tr[..., 1:] / tr[..., :-1] - 1
    level = np.empty_like(tr)
    level[..., 0] = base
    for i in range(ret.shape[-1]):
        prev = level[..., i]
        cut = points * dt if points is not None else prev * decrement * dt
        level[..., i + 1] = prev * (1 + ret[..., i]) - cut
    return level
