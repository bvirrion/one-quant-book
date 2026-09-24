"""Chapter 6 of Book 2: bond futures. A synthetic deliverable basket for a December 2026 ten-year
note future (remaining maturities 6.5 to 8 years), its conversion factors, basis and implied
repo, and the yield at which the cheapest-to-deliver switches."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/ctd"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/bond"))
from firm_bond import Bond
from firm_ctd import Deliverable, conversion_factor, gross_basis, implied_repo, net_basis

TODAY = dt.date(2026, 9, 25)
FIRST_DAY = dt.date(2026, 12, 1)
DELIVERY = dt.date(2026, 12, 31)          # last business day of the delivery month
DAYS = (DELIVERY - TODAY).days
REPO = 0.0390

# (name, coupon %, maturity, yield today): illustrative notes, not claimed to be outstanding
NOTES = [
    ("3 7/8 Aug-33", 3.875, dt.date(2033, 8, 15), 0.04020),
    ("4 1/8 Nov-33", 4.125, dt.date(2033, 11, 15), 0.04035),
    ("4 1/4 Feb-34", 4.250, dt.date(2034, 2, 15), 0.04050),
    ("4 5/8 May-34", 4.625, dt.date(2034, 5, 15), 0.04065),
    ("4 Aug-34", 4.000, dt.date(2034, 8, 15), 0.04080),
]
OPTION_TICKS = 1        # futures trade this many 1/64ths under the CTD's forward-implied price (illustrative)


def bonds() -> list[tuple[str, Bond, float, float]]:
    """(name, bond, yield, conversion factor)."""
    return [(n, Bond(c, m), y, conversion_factor(c / 100, FIRST_DAY, m)) for n, c, m, y in NOTES]


def deliverables(shift: float = 0.0) -> list[Deliverable]:
    out = []
    for n, b, y, cf in bonds():
        prev, nxt = b.coupon_dates(TODAY)
        paid = sum(b.coupon / 2 for d in nxt if TODAY < d <= DELIVERY)
        acc_del = b.accrued(DELIVERY)
        out.append(Deliverable(n, b.clean_price(y + shift, TODAY), b.accrued(TODAY), acc_del, cf, paid))
    return out


def forward_clean(d: Deliverable, repo: float = REPO, days: int = DAYS) -> float:
    """Clean price at delivery that makes buy-and-finance break even."""
    return (d.clean + d.accrued_now) * (1 + repo * days / 360) - d.coupon_income - d.accrued_delivery


def fair_futures(shift: float = 0.0) -> float:
    """Futures price: the lowest forward clean price per conversion factor, less a small option
    value, rounded to the contract's tick of half a 32nd."""
    raw = min(forward_clean(d) / d.cf for d in deliverables(shift)) - OPTION_TICKS / 64
    return round(raw * 64) / 64


def table(shift: float = 0.0) -> list[dict[str, float | str]]:
    f = fair_futures(shift)
    rows = []
    for d in deliverables(shift):
        rows.append({"name": d.name, "clean": d.clean, "cf": d.cf, "gross": gross_basis(d, f),
                     "net": net_basis(d, f, REPO, DAYS), "irr": implied_repo(d, f, DAYS)})
    return rows


def delivery_value_per_cf(shift: float) -> list[tuple[str, float]]:
    """At delivery, with all yields shifted, each note's clean price divided by its factor: the
    short delivers the lowest."""
    out = []
    for n, b, y, cf in bonds():
        out.append((n, b.clean_price(y + shift, DELIVERY) / cf))
    return out


def ctd_at(shift: float) -> str:
    return min(delivery_value_per_cf(shift), key=lambda t: t[1])[0]


def switch_shift(lo: float = -0.03, hi: float = 0.04, step: float = 0.0001) -> list[tuple[float, str, str]]:
    """Yield shifts at which the cheapest-to-deliver changes."""
    out, prev = [], ctd_at(lo)
    k = 0
    while lo + k * step <= hi:
        s = lo + k * step
        cur = ctd_at(s)
        if cur != prev:
            out.append((s, prev, cur))
            prev = cur
        k += 1
    return out


def min_value(shift: float) -> float:
    return min(v for _, v in delivery_value_per_cf(shift))


def _normal_expectation(fn, sd: float, points: int = 801) -> float:
    """E[fn(s)] for s ~ N(0, sd^2), trapezoidal rule on +-6 sd."""
    lo, hi = -6 * sd, 6 * sd
    h = (hi - lo) / (points - 1)
    acc = 0.0
    for k in range(points):
        s = lo + k * h
        w = 0.5 if k in (0, points - 1) else 1.0
        acc += w * math.exp(-0.5 * (s / sd) ** 2) * fn(s)
    return acc * h / (sd * math.sqrt(2 * math.pi))


def switch_option_value(sd: float) -> float:
    """Value, in futures price points, of the short's right to deliver whichever note is cheapest
    at delivery rather than today's cheapest-to-deliver, under a normal parallel yield shift of
    standard deviation sd."""
    today = ctd_at(0.0)
    stick = _normal_expectation(lambda s: dict(delivery_value_per_cf(s))[today], sd)
    choose = _normal_expectation(min_value, sd)
    return stick - choose
