"""Credit spread measures of a fixed-coupon bond (build of Book 2, Chapter 21).

Curves are given as (years, rate) points, linearly interpolated: par yields for the G- and I-spreads,
continuously compounded zero rates for the Z-spread and the asset-swap spread. A bond pays `coupon`
(percent of 100) `freq` times a year for `years` years; prices are per 100, dirty, on a coupon date.
"""
import math


def interp(curve: list[tuple[float, float]], t: float) -> float:
    if t <= curve[0][0]:
        return curve[0][1]
    for (t0, r0), (t1, r1) in zip(curve, curve[1:], strict=False):
        if t <= t1:
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return curve[-1][1]


def flows(coupon: float, years: float, freq: int = 2) -> list[tuple[float, float]]:
    n = round(years * freq)
    return [(k / freq, coupon / freq + (100.0 if k == n else 0.0)) for k in range(1, n + 1)]


def price_from_yield(coupon: float, years: float, y: float, freq: int = 2) -> float:
    return sum(cf / (1 + y / freq) ** (t * freq) for t, cf in flows(coupon, years, freq))


def yield_from_price(coupon: float, years: float, price: float, freq: int = 2) -> float:
    lo, hi = -0.05, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if price_from_yield(coupon, years, mid, freq) > price else (lo, mid)
    return 0.5 * (lo + hi)


def g_spread(y: float, years: float, govt_par: list[tuple[float, float]]) -> float:
    return y - interp(govt_par, years)


def i_spread(y: float, years: float, swap_par: list[tuple[float, float]]) -> float:
    return y - interp(swap_par, years)


def price_on_zero(coupon: float, years: float, zero: list[tuple[float, float]], z: float = 0.0, freq: int = 2) -> float:
    return sum(cf * math.exp(-(interp(zero, t) + z) * t) for t, cf in flows(coupon, years, freq))


def z_spread(coupon: float, years: float, price: float, zero: list[tuple[float, float]], freq: int = 2) -> float:
    """Constant spread over the zero curve that reprices the bond."""
    lo, hi = -0.05, 0.5
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if price_on_zero(coupon, years, zero, mid, freq) > price else (lo, mid)
    return 0.5 * (lo + hi)


def asset_swap_spread(coupon: float, years: float, price: float, zero: list[tuple[float, float]],
                      freq: int = 2) -> float:
    """Par-par asset-swap spread: (price on the swap curve - market price) / annuity of the floating leg."""
    annuity = sum(math.exp(-interp(zero, t) * t) / freq for t, _ in flows(coupon, years, freq))
    return (price_on_zero(coupon, years, zero, 0.0, freq) - price) / (100.0 * annuity)


def spread_price_impact(duration: float, widening: float, price: float = 100.0) -> float:
    """First-order price change of a bond of modified duration `duration` when its spread widens."""
    return -duration * widening * price
