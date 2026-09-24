"""Degree days, burn analysis and freight settlement (build of Book 3, Chapter 11).

Temperatures in degrees Fahrenheit; the degree-day base is 65 F. A degree-day contract pays a tick
(dollars per degree day) times the index's distance from a strike. A forward freight agreement
settles on the average of a daily route index over its month.
"""
import math

BASE_F = 65.0


def c10_to_f(tenths_celsius: int) -> float:
    """GHCN-Daily stores temperatures in tenths of a degree Celsius."""
    return tenths_celsius / 10 * 9 / 5 + 32


def daily_average(tmax_f: float, tmin_f: float) -> float:
    return (tmax_f + tmin_f) / 2


def hdd(tavg_f: float, base: float = BASE_F) -> float:
    """Heating degree days of one day: how far the day's average falls below the base."""
    return max(0.0, base - tavg_f)


def cdd(tavg_f: float, base: float = BASE_F) -> float:
    return max(0.0, tavg_f - base)


def swap_payoff(index: float, strike: float, tick: float) -> float:
    """Paid to the buyer of a degree-day swap (long the index)."""
    return tick * (index - strike)


def put_payoff(index: float, strike: float, tick: float, cap: float = math.inf) -> float:
    """Paid to the buyer of a degree-day put, capped."""
    return min(tick * max(strike - index, 0.0), cap)


def burn(history: list[float], payoff) -> dict[str, float]:  # noqa: ANN001
    """Burn analysis: apply a payoff to each historical season's index; the fair price is the mean
    payout, and the distribution of payouts measures the risk."""
    pays = sorted(payoff(x) for x in history)
    n = len(pays)
    return {"mean": sum(pays) / n, "max": pays[-1], "p90": pays[min(n - 1, math.ceil(0.9 * n) - 1)],
            "freq": sum(1 for p in pays if p > 0) / n}


def detrend(history: list[float], years: list[float], target_year: float) -> list[float]:
    """Remove a least-squares linear trend and re-centre every season on the trend's value in
    `target_year`."""
    n = len(history)
    my, mx = sum(history) / n, sum(years) / n
    b = sum((x - mx) * (y - my) for x, y in zip(years, history, strict=True)) / sum((x - mx) ** 2 for x in years)
    level = my + b * (target_year - mx)
    return [y - (my + b * (x - mx)) + level for x, y in zip(years, history, strict=True)]


def ffa_settlement(daily_index: list[float], fixed_rate: float, days: float, lots: float = 1.0) -> float:
    """Cash to the buyer of a time-charter FFA: (monthly average of the index - fixed rate) times the
    days covered times the number of lots."""
    avg = sum(daily_index) / len(daily_index)
    return (avg - fixed_rate) * days * lots
