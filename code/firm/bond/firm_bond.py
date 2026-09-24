"""Fixed-coupon government bonds (build of Book 2, Chapter 3): schedules, day counts, accrued
interest, price and yield, duration, DV01, convexity. Prices per 100 of face value; the coupon
is annual, in percent, paid `freq` times a year; yields are decimals compounded `freq` times a
year. Reference implementation; the C++20 and Rust twins live in cpp/ and rust/.

Two conventions for a settlement date between coupons, w = fraction of the current period still
to run: the market's (street) convention discounts every flow by (1 + y/f)^(k + w); the US
Treasury's auction convention (31 CFR 356, App. B) discounts the fractional period by simple
interest, (1 + w y/f). They agree on coupon dates.
"""
import calendar
import datetime as dt
from dataclasses import dataclass

# ---- dates and day counts ---------------------------------------------------------------------

def add_months(d: dt.date, months: int, eom: bool) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    last = calendar.monthrange(y, m)[1]
    return dt.date(y, m, last if eom else min(d.day, last))


def is_month_end(d: dt.date) -> bool:
    return d.day == calendar.monthrange(d.year, d.month)[1]


def act_360(a: dt.date, b: dt.date) -> float:
    return (b - a).days / 360.0


def act_365f(a: dt.date, b: dt.date) -> float:
    return (b - a).days / 365.0


def thirty_360(a: dt.date, b: dt.date) -> float:
    """30/360 (US bond basis): day 31 becomes 30; day 31 of b becomes 30 only if a's day is 30 or 31."""
    d1 = min(a.day, 30)
    d2 = 30 if (b.day == 31 and d1 == 30) else b.day
    return (360 * (b.year - a.year) + 30 * (b.month - a.month) + (d2 - d1)) / 360.0


# ---- the bond ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class Bond:
    coupon: float              # annual, percent of face (4.25 means 4.25%)
    maturity: dt.date
    freq: int = 2

    def coupon_dates(self, settle: dt.date) -> tuple[dt.date, list[dt.date]]:
        """(previous coupon date, remaining coupon dates after settle), generated back from maturity."""
        eom = is_month_end(self.maturity)
        step = 12 // self.freq
        dates, k = [], 0
        d = self.maturity
        while d > settle:
            dates.append(d)
            k += 1
            d = add_months(self.maturity, -step * k, eom)
        return d, dates[::-1]

    def period_fraction(self, settle: dt.date) -> tuple[float, int]:
        """w = days from settle to the next coupon / days in the current period; n = coupons left."""
        prev, nxt = self.coupon_dates(settle)
        return (nxt[0] - settle).days / (nxt[0] - prev).days, len(nxt)

    def accrued(self, settle: dt.date) -> float:
        """Actual/actual (ICMA): the period's coupon times the fraction of its days elapsed."""
        w, _ = self.period_fraction(settle)
        return self.coupon / self.freq * (1.0 - w)

    def dirty_price(self, y: float, settle: dt.date, treasury: bool = False) -> float:
        w, n = self.period_fraction(settle)
        c, f = self.coupon / self.freq, self.freq
        v = 1.0 / (1.0 + y / f)
        at_next = c * sum(v ** k for k in range(n)) + 100.0 * v ** (n - 1)   # value at the next coupon date
        return at_next / (1.0 + w * y / f) if treasury else at_next * v ** w

    def clean_price(self, y: float, settle: dt.date, treasury: bool = False) -> float:
        return self.dirty_price(y, settle, treasury) - self.accrued(settle)

    def yield_from_clean(self, clean: float, settle: dt.date, tol: float = 1e-12) -> float:
        """Newton on the street-convention price, started at the coupon rate."""
        y = self.coupon / 100.0
        for _ in range(100):
            p = self.clean_price(y, settle) - clean
            h = 1e-7
            dp = (self.clean_price(y + h, settle) - self.clean_price(y - h, settle)) / (2 * h)
            step = p / dp
            y -= step
            if abs(step) < tol:
                break
        return y

    def risk(self, y: float, settle: dt.date) -> dict[str, float]:
        """Street convention, per 100 face: dirty price, Macaulay and modified duration (years),
        DV01 (price change for a one-basis-point fall in yield) and convexity (years^2)."""
        w, n = self.period_fraction(settle)
        c, f = self.coupon / self.freq, self.freq
        v = 1.0 / (1.0 + y / f)
        flows = [(k + w, c + (100.0 if k == n - 1 else 0.0)) for k in range(n)]   # (periods, cash)
        pv = [(t, cf * v ** t) for t, cf in flows]
        p = sum(x for _, x in pv)
        mac = sum(t * x for t, x in pv) / p / f
        mod = mac / (1.0 + y / f)
        conv = sum(t * (t + 1) * x for t, x in pv) / p / (f * f) / (1.0 + y / f) ** 2
        return {"dirty": p, "macaulay": mac, "modified": mod, "dv01": p * mod * 1e-4, "convexity": conv}


def zero_price(zero_rate: float, years: float, freq: int = 2) -> float:
    """Price per 100 of a zero-coupon strip at a zero rate compounded freq times a year."""
    return 100.0 / (1.0 + zero_rate / freq) ** (freq * years)


def bootstrap_par(par_yields: list[float], freq: int = 2) -> list[float]:
    """Discount factors at 1/freq, 2/freq, ... years from par yields at those maturities."""
    dfs: list[float] = []
    for y in par_yields:
        c = y / freq
        dfs.append((1.0 - c * sum(dfs)) / (1.0 + c))
    return dfs


def par_yield(dfs: list[float], freq: int = 2) -> float:
    """The coupon that prices a bond at par on these discount factors: (1 - P(T)) / sum(delta P)."""
    return freq * (1.0 - dfs[-1]) / sum(dfs)
