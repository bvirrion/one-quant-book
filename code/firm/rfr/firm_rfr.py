"""Overnight-rate compounding in arrears (build of Book 2, Chapter 1).

An interest period [start, end) accrues one overnight fixing per business day, each weighted by
the calendar days until the next business day (a Friday fixing counts three days). Rates are
decimals, simple, actual/basis. Three conventions let the payment be known before the period
ends: a lookback (rates observed p business days earlier, weights from the interest period), an
observation shift (rates and weights both from the shifted period) and a lockout (the last k
fixings frozen at the one before them).
"""
import datetime as dt
from dataclasses import dataclass

ONE_DAY = dt.timedelta(days=1)


@dataclass(frozen=True)
class Calendar:
    holidays: frozenset[dt.date] = frozenset()

    def is_business_day(self, d: dt.date) -> bool:
        return d.weekday() < 5 and d not in self.holidays

    def add(self, d: dt.date, n: int) -> dt.date:
        """Move n business days forward (n > 0) or back (n < 0) from d."""
        step = ONE_DAY if n >= 0 else -ONE_DAY
        for _ in range(abs(n)):
            d += step
            while not self.is_business_day(d):
                d += step
        return d

    def business_days(self, start: dt.date, end: dt.date) -> list[dt.date]:
        """Business days d with start <= d < end."""
        out, d = [], start
        while d < end:
            if self.is_business_day(d):
                out.append(d)
            d += ONE_DAY
        return out


def weights(cal: Calendar, days: list[dt.date], end: dt.date) -> list[int]:
    """Calendar days each fixing accrues for: to the next business day, capped at the period end."""
    nxt = days[1:] + [end]
    return [(b - a).days for a, b in zip(days, nxt, strict=True)]


@dataclass(frozen=True)
class Convention:
    lookback: int = 0        # business days
    shift: bool = False      # observation shift: weights from the observation period too
    lockout: int = 0         # last business days frozen at the fixing before them
    basis: int = 360


PLAIN = Convention()


def observations(cal: Calendar, start: dt.date, end: dt.date, conv: Convention) -> list[tuple[dt.date, int]]:
    """(fixing date, weight in days) for each accrual step of the interest period."""
    days = cal.business_days(start, end)
    if conv.shift:
        o_start, o_end = cal.add(start, -conv.lookback), cal.add(end, -conv.lookback)
        obs = cal.business_days(o_start, o_end)
        w = weights(cal, obs, o_end)
    else:
        obs = [cal.add(d, -conv.lookback) for d in days]
        w = weights(cal, days, end)
    if conv.lockout:
        frozen = obs[-conv.lockout - 1]
        obs = obs[:-conv.lockout] + [frozen] * conv.lockout
    return list(zip(obs, w, strict=True))


def compound_in_arrears(fixings: dict[dt.date, float], cal: Calendar, start: dt.date, end: dt.date,
                        conv: Convention = PLAIN) -> float:
    """Annualised compounded rate for the period: (prod(1 + r_i n_i / B) - 1) * B / N."""
    growth, n_total = 1.0, 0
    for d, n in observations(cal, start, end, conv):
        growth *= 1.0 + fixings[d] * n / conv.basis
        n_total += n
    return (growth - 1.0) * conv.basis / n_total


def simple_average(fixings: dict[dt.date, float], cal: Calendar, start: dt.date, end: dt.date,
                   conv: Convention = PLAIN) -> float:
    """Day-weighted arithmetic average of the same fixings: no interest on interest."""
    obs = observations(cal, start, end, conv)
    return sum(fixings[d] * n for d, n in obs) / sum(n for _, n in obs)


def interest(notional: float, rate: float, start: dt.date, end: dt.date, basis: int = 360) -> float:
    return notional * rate * (end - start).days / basis


def rate_from_index(index_start: float, index_end: float, start: dt.date, end: dt.date, basis: int = 360) -> float:
    """Compounded rate from a published compounded-rate index (value at start and at end)."""
    return (index_end / index_start - 1.0) * basis / (end - start).days
