"""Policy-path extraction from short-term interest-rate futures (build of Book 2, Chapter 8).

A one-month overnight-rate future settles at 100 minus the arithmetic average of the daily rate
over the calendar days of its month (a weekend or holiday day takes the previous business day's
rate). If the central bank meets on day m of the month and the new rate applies from the next day,
the month's average mixes the rate before and the rate after; chaining the months from a known
starting rate gives the rate the market expects after each meeting. Rates in percent.
"""
import calendar
import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class MonthContract:
    year: int
    month: int
    price: float                        # 100 - average rate
    meeting: dt.date | None = None      # decision day; the new rate applies from the next day
    turn_days: int = 0                  # calendar days of the month carrying a turn premium
    turn_bp: float = 0.0

    @property
    def days(self) -> int:
        return calendar.monthrange(self.year, self.month)[1]

    @property
    def average(self) -> float:
        return 100.0 - self.price


def rate_after(c: MonthContract, rate_before: float) -> float:
    """The post-meeting rate implied by the month's average (or the month's own rate if no meeting)."""
    turn = c.turn_days * c.turn_bp / 100.0
    if c.meeting is None:
        return (c.average * c.days - turn) / c.days
    before = c.meeting.day                   # days 1..m at the old rate
    after = c.days - before
    return (c.average * c.days - turn - before * rate_before) / after


def policy_path(contracts: list[MonthContract], start_rate: float) -> list[tuple[str, float]]:
    """[(label, rate expected after that month's meeting or over that month)] chained month by month."""
    out, r = [], start_rate
    for c in contracts:
        r = rate_after(c, r)
        out.append((f"{c.year}-{c.month:02d}", r))
    return out


def move_probability(rate_after_meeting: float, rate_before: float, step: float = 0.25) -> float:
    """Probability of a move of `step` implied by the expected change, if only 0 or `step` are possible."""
    return (rate_after_meeting - rate_before) / step


def strip_rate(rates: list[float], fractions: list[float]) -> float:
    """Term rate from a strip of consecutive period rates (percent), compounded: the rate of a
    deposit spanning them all."""
    growth = 1.0
    for r, d in zip(rates, fractions, strict=True):
        growth *= 1.0 + r / 100.0 * d
    return (growth - 1.0) / sum(fractions) * 100.0


def convexity_adjustment(sigma: float, t1: float, t2: float) -> float:
    """Futures rate minus forward rate in a Gaussian (Ho-Lee) model, decimals: sigma^2 t1 t2 / 2."""
    return 0.5 * sigma * sigma * t1 * t2
