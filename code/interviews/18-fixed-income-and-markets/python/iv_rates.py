"""Book 18, chapter 18: bond arithmetic with annual coupons (price per 100, yields as decimals)."""
from math import exp


def price(coupon: float, y: float, years: int, face: float = 100.0) -> float:
    return sum(face * coupon / (1 + y) ** t for t in range(1, years + 1)) + face / (1 + y) ** years


def modified_duration(coupon, y, years):
    p = price(coupon, y, years)
    mac = sum(t * 100 * coupon / (1 + y) ** t for t in range(1, years + 1)) + years * 100 / (1 + y) ** years
    return mac / p / (1 + y)


def convexity(coupon, y, years):
    p = price(coupon, y, years)
    s = sum(t * (t + 1) * 100 * coupon / (1 + y) ** (t + 2) for t in range(1, years + 1))
    s += years * (years + 1) * 100 / (1 + y) ** (years + 2)
    return s / p


def dv01(notional, clean_price, dmod):
    return notional * clean_price / 100 * dmod * 1e-4


def forward_rate(z1, t1, z2, t2):
    return ((1 + z2) ** t2 / (1 + z1) ** t1) ** (1 / (t2 - t1)) - 1


def curve(t: float) -> float:
    """The chapter's synthetic curve (Nelson-Siegel form): long-run 4.2%, short end 2.8%."""
    beta0, beta1, lam = 0.042, -0.014, 2.0
    if t == 0:
        return beta0 + beta1
    x = t / lam
    return beta0 + beta1 * (1 - exp(-x)) / x


def roll_down_return(coupon, years, repo, horizon: int = 1):
    """One-year total return of a bond bought at the curve's yield and sold a year later at the (unchanged)
    curve's yield for the shorter maturity, financed at `repo`: (price change + coupon - financing) / price."""
    p0 = price(coupon, curve(years), years)
    p1 = price(coupon, curve(years - horizon), years - horizon)
    carry = 100 * coupon - p0 * repo
    return (p1 - p0 + carry) / p0, (p1 - p0) / p0, carry / p0


def cip_forward(spot, r_quote, r_base, t=1.0):
    return spot * (1 + r_quote * t) / (1 + r_base * t)
