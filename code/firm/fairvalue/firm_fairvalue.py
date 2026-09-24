"""Fair-value calculator for index futures (build of Book 1, Chapter 21).

Money-market conventions: simple interest, actual/360. Dividends are discrete, in index points,
each reinvested from its payment date to expiry. Everything a desk quotes around a future comes
from these few functions: fair value, basis, implied financing rate, arbitrage band, roll.
"""
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Dividend:
    pay_date: dt.date
    points: float


def _frac(a: dt.date, b: dt.date, day_count: int = 360) -> float:
    return (b - a).days / day_count


def dividends_to_expiry(divs: list[Dividend], today: dt.date, expiry: dt.date, rate: float) -> float:
    """Value at expiry of the dividends paid in (today, expiry]."""
    return sum(d.points * (1.0 + rate * _frac(d.pay_date, expiry)) for d in divs if today < d.pay_date <= expiry)


def fair_value(spot: float, rate: float, today: dt.date, expiry: dt.date, divs: list[Dividend]) -> float:
    return spot * (1.0 + rate * _frac(today, expiry)) - dividends_to_expiry(divs, today, expiry, rate)


def implied_rate(future: float, spot: float, today: dt.date, expiry: dt.date, divs: list[Dividend],
                 tol: float = 1e-12) -> float:
    """The financing rate at which the market price is fair (bisection: dividends depend on it too)."""
    lo, hi = -0.5, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if fair_value(spot, mid, today, expiry, divs) < future:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


@dataclass(frozen=True)
class ArbCosts:
    stock_bp: float                 # one-way cost of trading the basket, bp of value
    future_bp: float                # one-way cost of trading the future
    borrow_bp_annual: float         # stock-borrow fee, paid only when the basket is sold short
    funding_spread_bp_annual: float  # the arbitrageur's financing above the benchmark, when long the basket


def arbitrage_band(spot: float, rate: float, today: dt.date, expiry: dt.date, divs: list[Dividend],
                   costs: ArbCosts) -> tuple[float, float]:
    """Futures prices outside (lower, upper) pay: above, buy the basket and sell the future;
    below, short the basket and buy the future. Round-trip trading costs on both legs."""
    fv = fair_value(spot, rate, today, expiry, divs)
    t = _frac(today, expiry)
    trading = 2.0 * (costs.stock_bp + costs.future_bp) * 1e-4 * spot
    upper = fv + trading + costs.funding_spread_bp_annual * 1e-4 * t * spot
    lower = fv - trading - costs.borrow_bp_annual * 1e-4 * t * spot
    return lower, upper


def roll_richness_bp(spread_market: float, spot: float, rate: float, today: dt.date, near: dt.date,
                     far: dt.date, divs: list[Dividend]) -> float:
    """Market calendar spread (far minus near) less its fair value, annualised over the period
    between the two expiries, in basis points of the index. Positive = the roll is rich: longs pay."""
    fair = fair_value(spot, rate, today, far, divs) - fair_value(spot, rate, today, near, divs)
    return (spread_market - fair) / spot / _frac(near, far) * 1e4
