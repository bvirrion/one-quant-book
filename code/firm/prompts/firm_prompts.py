"""LME-style prompt-date calendar, carries and margin (build of Book 3, Chapter 8).

Prompt dates: every business day from tom (next business day) to the three-month date, then every
Wednesday up to the end of the sixth month after the trade date's month, then the third Wednesday
of each month up to `months` months ahead. A prompt date on a non-business day moves to the next
business day, except that a Saturday moves back to a business-day Friday (LME Trading Regulation
8.4.1(a)); a three-month date pushed into the fourth month after the trade month falls instead on
the last business day of the third (8.4.2). Good Friday and Christmas exceptions are left to the
holiday list. Prices in USD per tonne.
"""
import datetime as dt

Holidays = frozenset[dt.date]


def is_business(d: dt.date, holidays: Holidays = frozenset()) -> bool:
    return d.weekday() < 5 and d not in holidays


def next_business(d: dt.date, holidays: Holidays = frozenset()) -> dt.date:
    d += dt.timedelta(days=1)
    while not is_business(d, holidays):
        d += dt.timedelta(days=1)
    return d


def add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    last = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).day
    return dt.date(y, m, min(d.day, last))


def lme_roll(d: dt.date, holidays: Holidays = frozenset()) -> dt.date:
    """A prompt date on a non-business day: back to Friday from a Saturday, else forward."""
    if is_business(d, holidays):
        return d
    friday = d - dt.timedelta(days=1)
    if d.weekday() == 5 and is_business(friday, holidays):
        return friday
    return next_business(d, holidays)


def three_month_date(trade: dt.date, holidays: Holidays = frozenset()) -> dt.date:
    x = lme_roll(add_months(trade, 3), holidays)
    if x > add_months(dt.date(trade.year, trade.month, 1), 4) - dt.timedelta(days=1):
        x = add_months(dt.date(trade.year, trade.month, 1), 4)
        x = x - dt.timedelta(days=1)
        while not is_business(x, holidays):
            x -= dt.timedelta(days=1)
    return x


def third_wednesday(y: int, m: int) -> dt.date:
    d = dt.date(y, m, 1)
    return d + dt.timedelta(days=(2 - d.weekday()) % 7 + 14)


def prompt_dates(trade: dt.date, months: int = 27, holidays: Holidays = frozenset()) -> dict[str, list[dt.date]]:
    """Daily, weekly and monthly prompt dates for a trade date."""
    tom = next_business(trade, holidays)
    three_m = three_month_date(trade, holidays)
    daily, d = [], tom
    while d <= three_m:
        daily.append(d)
        d = next_business(d, holidays)
    end_weekly = add_months(dt.date(trade.year, trade.month, 1), 7) - dt.timedelta(days=1)
    weekly, d = [], three_m + dt.timedelta(days=1)
    while d <= end_weekly:
        if d.weekday() == 2 and is_business(d, holidays):
            weekly.append(d)
        d += dt.timedelta(days=1)
    monthly = []
    for k in range(7, months + 1):
        f = add_months(dt.date(trade.year, trade.month, 1), k)
        w = third_wednesday(f.year, f.month)
        if w > end_weekly:
            monthly.append(lme_roll(w, holidays))
    return {"daily": daily, "weekly": weekly, "monthly": monthly, "cash": [daily[1]], "three_month": [three_m]}


def carry(near: float, far: float) -> float:
    """Far minus near: positive is contango, negative is backwardation (per tonne)."""
    return far - near


def variation_margin(position_tonnes: float, old: float, new: float) -> float:
    """Cash owed (negative) or received (positive) on a position marked from `old` to `new`."""
    return position_tonnes * (new - old)
