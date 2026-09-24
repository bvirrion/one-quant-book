"""Treasury futures delivery analytics (build of Book 2, Chapter 6): conversion factors (CBOT
formula), invoice price, gross and net basis, implied repo, cheapest-to-deliver.

Prices per 100 of face; rates decimal; money-market conventions actual/360. The conversion factor
follows the exchange's published formula: the price of 1 of par at a 6% yield, with the time to
maturity from the first day of the delivery month in whole months, rounded down to a quarter
for the 10-year and bond contracts (to a month for the 2-, 3- and 5-year), and the coupon rounded
to the nearest eighth.
"""
import datetime as dt
import math
from dataclasses import dataclass


def whole_months(start: dt.date, end: dt.date) -> int:
    """Complete one-month increments from start to end."""
    m = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        m -= 1
    return m


def conversion_factor(coupon: float, first_day_of_delivery_month: dt.date, maturity: dt.date,
                      quarter_rounding: bool = True) -> float:
    """CBOT conversion factor, rounded to four decimals. coupon in decimals (0.0375)."""
    cpn = math.floor(coupon * 800 + 0.5) / 800                   # nearest 1/8 of a percent, ties up
    months = whole_months(first_day_of_delivery_month, maturity)
    n, z = divmod(months, 12)
    if quarter_rounding:
        z -= z % 3
    v = z if z < 7 else (3 if quarter_rounding else z - 6)
    a = 1.0 / 1.03 ** (v / 6)
    b = cpn / 2 * (6 - v) / 6
    c = 1.0 / 1.03 ** (2 * n) if z < 7 else 1.0 / 1.03 ** (2 * n + 1)
    d = cpn / 0.06 * (1 - c)
    return round(a * (cpn / 2 + c + d) - b, 4)


def invoice_price(futures: float, cf: float, accrued_at_delivery: float) -> float:
    return futures * cf + accrued_at_delivery


@dataclass(frozen=True)
class Deliverable:
    name: str
    clean: float              # today
    accrued_now: float
    accrued_delivery: float
    cf: float
    coupon_income: float = 0.0   # coupons received before delivery, per 100


def gross_basis(d: Deliverable, futures: float) -> float:
    return d.clean - futures * d.cf


def carry_to_delivery(d: Deliverable, repo: float, days: int) -> float:
    """Coupon income over the period less financing of the dirty price, per 100."""
    accrual = d.accrued_delivery - d.accrued_now + d.coupon_income
    return accrual - (d.clean + d.accrued_now) * repo * days / 360.0


def net_basis(d: Deliverable, futures: float, repo: float, days: int) -> float:
    return gross_basis(d, futures) - carry_to_delivery(d, repo, days)


def implied_repo(d: Deliverable, futures: float, days: int) -> float:
    """The financing rate that makes buying the bond and delivering it into the future break even."""
    cost = d.clean + d.accrued_now
    proceeds = invoice_price(futures, d.cf, d.accrued_delivery) + d.coupon_income
    return (proceeds - cost) / cost * 360.0 / days


def cheapest_to_deliver(basket: list[Deliverable], futures: float, days: int) -> Deliverable:
    """The deliverable with the highest implied repo rate (equivalently, lowest net basis)."""
    return max(basket, key=lambda d: implied_repo(d, futures, days))
