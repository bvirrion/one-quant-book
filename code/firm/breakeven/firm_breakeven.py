"""Breakevens, index ratios and linker carry (build of Book 2, Chapter 11).

An index-linked bond's principal is scaled by an index ratio: the reference index on the day over
the reference index on the bond's dated date. The reference index for the first day of a month is
the price index of three months earlier; other days interpolate linearly towards the next month's
value (the US rule for TIPS, and the rule of most linkers since the 2000s). Index values are keyed
by (year, month). Rates are decimals.
"""
import datetime as dt
import math
from calendar import monthrange

Index = dict[tuple[int, int], float]


def month_shift(year: int, month: int, k: int) -> tuple[int, int]:
    m = year * 12 + (month - 1) + k
    return m // 12, m % 12 + 1


def _five(x: float) -> float:
    """Truncate to six decimals, then round to five (the TIPS rule for Ref CPI and index ratios)."""
    return round(math.floor(x * 1e6) / 1e6, 5)


def ref_index(d: dt.date, index: Index, lag: int = 3) -> float:
    """Reference index for day d: index of month M-lag, interpolated towards month M-lag+1."""
    start = index[month_shift(d.year, d.month, -lag)]
    end = index[month_shift(d.year, d.month, 1 - lag)]
    days = monthrange(d.year, d.month)[1]
    return _five(start + (d.day - 1) / days * (end - start))


def index_ratio(d: dt.date, dated: dt.date, index: Index, lag: int = 3) -> float:
    return _five(ref_index(d, index, lag) / ref_index(dated, index, lag))


def monthly_accrual(year: int, month: int, index: Index, lag: int = 3) -> float:
    """Growth of the reference index over calendar month (year, month): known once month M-lag+1
    is published, which is about lag-1.5 months before the month starts."""
    return index[month_shift(year, month, 1 - lag)] / index[month_shift(year, month, -lag)] - 1.0


def breakeven(nominal: float, real: float) -> float:
    """Inflation rate that equates a nominal and a real yield of the same maturity (Fisher)."""
    return (1.0 + nominal) / (1.0 + real) - 1.0


def forward_index(base: float, zc_rate: float, years: float) -> float:
    """Index level the zero-coupon inflation swap of that maturity locks in."""
    return base * (1.0 + zc_rate) ** years


def zc_swap_payment(notional: float, base: float, final: float, zc_rate: float, years: float) -> float:
    """Net payment to the inflation receiver at maturity."""
    return notional * (final / base - (1.0 + zc_rate) ** years)


def seasonal_factors(index: Index) -> dict[int, float]:
    """Average excess log change of each calendar month over its year's mean monthly change, in
    percent; uses only complete calendar years whose twelve changes are all available."""
    excess: dict[int, list[float]] = {m: [] for m in range(1, 13)}
    for y in sorted({y for y, _ in index}):
        ch = []
        for m in range(1, 13):
            prev = month_shift(y, m, -1)
            if (y, m) not in index or prev not in index:
                break
            ch.append(math.log(index[(y, m)] / index[prev]))
        if len(ch) == 12:
            mean = sum(ch) / 12
            for m, c in enumerate(ch, start=1):
                excess[m].append(100.0 * (c - mean))
    return {m: sum(v) / len(v) for m, v in excess.items()}


def linker_carry(market_value: float, accrual: float, real_yield: float, repo: float, days: int) -> float:
    """Carry of a repo-financed linker over `days` if its real yield does not move: the index
    accrual and the real yield's pull, less the repo interest (actual/360)."""
    growth = (1.0 + accrual) * (1.0 + real_yield) ** (days / 365.0) - 1.0
    return market_value * (growth - repo * days / 360.0)


def contingency_index(last: float, year_before_last: float, missing: int = 1) -> float:
    """Substitute for an index not reported by the end of the following month (31 CFR 356,
    Appendix B): the last reported index grown at its twelve-month rate, for `missing` months."""
    return last * (last / year_before_last) ** (missing / 12)
