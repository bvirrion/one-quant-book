"""Gamma-exposure estimator (build of Book 1, Chapter 26).

Turns an options position (or, with a sign assumption, the market's open interest) into the
number of shares a delta-hedger must trade when the underlying moves. Zero rates and dividends:
for options that expire today or this week nothing else matters.
"""
import math
from dataclasses import dataclass

YEAR_MINUTES = 252 * 390.0          # trading time: 252 days of 390 minutes


def _pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def delta(spot: float, strike: float, years: float, vol: float, right: str) -> float:
    if years <= 0.0:
        itm = spot > strike if right == "C" else spot < strike
        return (1.0 if right == "C" else -1.0) if itm else 0.0
    s = vol * math.sqrt(years)
    d1 = math.log(spot / strike) / s + 0.5 * s
    return _cdf(d1) if right == "C" else _cdf(d1) - 1.0


def gamma(spot: float, strike: float, years: float, vol: float) -> float:
    """Change of delta per one unit of spot. The same for a call and a put."""
    if years <= 0.0:
        return 0.0
    s = vol * math.sqrt(years)
    d1 = math.log(spot / strike) / s + 0.5 * s
    return _pdf(d1) / (spot * s)


@dataclass(frozen=True)
class Holding:
    strike: float
    right: str
    years: float
    vol: float
    contracts: int                  # signed: + long, - short
    multiplier: int = 100


def net_delta_shares(book: list[Holding], spot: float) -> float:
    return sum(h.contracts * h.multiplier * delta(spot, h.strike, h.years, h.vol, h.right) for h in book)


def gamma_shares_per_pct(book: list[Holding], spot: float) -> float:
    """Shares the holder's delta changes by when spot rises 1%. A hedger trades the opposite:
    long gamma (positive) sells into a rise and buys into a fall; short gamma does the reverse."""
    return sum(h.contracts * h.multiplier * gamma(spot, h.strike, h.years, h.vol) for h in book) * spot * 0.01


def hedge_trade(book: list[Holding], spot_before: float, spot_after: float) -> float:
    """Exact shares a delta-neutral hedger must trade after the move (negative = sell)."""
    return -(net_delta_shares(book, spot_after) - net_delta_shares(book, spot_before))


def dealer_book_from_open_interest(open_interest: list[tuple[float, str, int]], years: float, vol: float,
                                   dealer_side: dict[str, int]) -> list[Holding]:
    """The market's open interest seen from the dealers' side under an ASSUMPTION about who is long:
    dealer_side = {'C': +1, 'P': -1} says dealers are long all calls and short all puts. The output
    is only as good as that assumption, which open-interest data cannot test."""
    return [Holding(k, r, years, vol, dealer_side[r] * oi) for k, r, oi in open_interest]
