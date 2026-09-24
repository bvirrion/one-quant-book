"""Money-market quote conversions (build of Book 2, Chapter 2).

Prices per 100 of face value. Treasury bills are quoted as a discount rate (bank discount basis,
360 days, on face value); the Treasury also publishes an investment rate (coupon-equivalent
yield, 365 or 366 days, on price, with a semiannual-compounding formula beyond half a year).
Money-market instruments (deposits, CDs, repo, commercial paper yields) are simple interest on
the amount invested, actual/360 in dollars and euros. Formulas follow 31 CFR 356, Appendix B.
"""
import datetime as dt
import math


def price_from_discount(d: float, days: int) -> float:
    """P = 100 (1 - d r / 360), rounded to six decimals as the Treasury does."""
    return round(100.0 * (1.0 - d * days / 360.0), 6)


def discount_from_price(p: float, days: int) -> float:
    return (100.0 - p) / 100.0 * 360.0 / days


def money_market_yield(p: float, days: int, basis: int = 360) -> float:
    """Simple interest on the amount paid: what a deposit of the same term would have to pay."""
    return (100.0 - p) / p * basis / days


def year_days(issue: dt.date) -> int:
    """366 if the year following the issue date contains 29 February, else 365."""
    try:
        ahead = issue.replace(year=issue.year + 1)
    except ValueError:                       # issued on 29 February
        ahead = dt.date(issue.year + 1, 3, 1)
    d = issue + dt.timedelta(days=1)
    while d <= ahead:
        if d.month == 2 and d.day == 29:
            return 366
        d += dt.timedelta(days=1)
    return 365


def investment_rate(p: float, days: int, y: int = 365) -> float:
    """Coupon-equivalent (bond-equivalent) yield of a bill. Up to half a year: simple interest on
    price over a y-day year. Beyond: solve P [1 + (r - y/2) i / y] (1 + i / 2) = 100."""
    if days <= y / 2:
        return (100.0 - p) / p * y / days
    a = days / (2.0 * y) - 0.25
    b = days / y
    c = (p - 100.0) / p
    return (-b + math.sqrt(b * b - 4.0 * a * c)) / (2.0 * a)


def term_proceeds(amount: float, rate: float, days: int, basis: int = 360) -> float:
    """Principal plus simple interest at maturity: a deposit, a CD, a term repo."""
    return amount * (1.0 + rate * days / basis)


def implied_turn(term_rate: float, term_days: int, normal_rate: float, normal_days: int, turn_days: int,
                 basis: int = 360) -> float:
    """Overnight rate over the turn implied by a term rate spanning it, when the other days of the
    term are assumed to earn normal_rate each day, compounded daily."""
    total = 1.0 + term_rate * term_days / basis
    normal = (1.0 + normal_rate / basis) ** normal_days
    return (total / normal - 1.0) * basis / turn_days
