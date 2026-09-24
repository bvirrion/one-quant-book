"""Crude oil toolkit (build of Book 3, Chapter 2): quality, the most-competitive-grade rule of a
basket benchmark, the WTI futures last trading day, calendar-month averages and the storage bound.

Prices in dollars per barrel. Dates are datetime.date; business days are weekdays not in `holidays`.
"""
import datetime as dt


def api_gravity(sg: float) -> float:
    """Degrees API from specific gravity at 60 F: 141.5 / sg - 131.5."""
    return 141.5 / sg - 131.5


def specific_gravity(api: float) -> float:
    return 141.5 / (api + 131.5)


def quality_adjusted(price: float, api: float, sulphur: float, ref_api: float, ref_sulphur: float,
                     per_api: float, per_tenth_sulphur: float) -> float:
    """Price of a grade after linear quality escalators against a reference grade: + per_api for
    each degree API above the reference, - per_tenth_sulphur for each 0.1 % of sulphur above it."""
    return price + per_api * (api - ref_api) - per_tenth_sulphur * (sulphur - ref_sulphur) / 0.1


def basket_benchmark(grade_prices: dict[str, float], premiums: dict[str, float]) -> tuple[str, float]:
    """Most-competitive-grade rule: each grade's price is net of its quality premium (a de-escalator
    for grades better than the base) and the benchmark is the lowest net price."""
    net = {g: p - premiums.get(g, 0.0) for g, p in grade_prices.items()}
    grade = min(net, key=lambda g: (net[g], g))
    return grade, net[grade]


def is_business_day(d: dt.date, holidays: frozenset[dt.date] = frozenset()) -> bool:
    return d.weekday() < 5 and d not in holidays


def shift_business_days(d: dt.date, n: int, holidays: frozenset[dt.date] = frozenset()) -> dt.date:
    """The n-th business day before d (n > 0), not counting d itself."""
    while n > 0:
        d -= dt.timedelta(days=1)
        if is_business_day(d, holidays):
            n -= 1
    return d


def cl_last_trading_day(year: int, month: int, holidays: frozenset[dt.date] = frozenset()) -> dt.date:
    """Last trading day of the WTI futures for delivery month (year, month): three business days
    before the 25th calendar day of the preceding month; if the 25th is not a business day, three
    business days before the last business day preceding it."""
    y, m = (year, month - 1) if month > 1 else (year - 1, 12)
    d = dt.date(y, m, 25)
    while not is_business_day(d, holidays):
        d -= dt.timedelta(days=1)
    return shift_business_days(d, 3, holidays)


def calendar_month_average(settles: dict[dt.date, float], year: int, month: int) -> float:
    """Average of the daily settlements dated in the calendar month (days with a settlement only)."""
    xs = [p for d, p in settles.items() if d.year == year and d.month == month]
    if not xs:
        raise ValueError("no settlement in the month")
    return sum(xs) / len(xs)


def storage_floor(far: float, storage_per_month: float, months: float, rate: float = 0.0) -> float:
    """No-arbitrage floor on the near futures price when storage is available: buying the near
    contract, storing and delivering into the far one must not earn a riskless profit, so
    near >= (far - storage cost) / (1 + rate * months / 12)."""
    return (far - storage_per_month * months) / (1.0 + rate * months / 12.0)


def implied_storage_cost(near: float, far: float, months: float = 1.0) -> float:
    """Storage cost per barrel-month at which the near-far spread is exactly the carry (no financing)."""
    return (far - near) / months
