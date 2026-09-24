"""Chapter 9 of Book 2: interest-rate swaps. An illustrative SOFR OIS par curve, the bootstrapped
discount and forward curves, bucketed DV01 of a par swap and a forward-starting swap, and the
corporate hedge of the weekend problem."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/curve"))
from firm_curve import add_years, annuity, bootstrap, bucket_dv01, par_rate, schedule, swap_pv

SPOT = dt.date(2026, 9, 29)                  # spot for a trade on Friday 25 September 2026
TENORS = [1, 2, 3, 5, 7, 10]
RATES = [0.0390, 0.0385, 0.0383, 0.0385, 0.0392, 0.0405]   # illustrative par OIS rates


def curve():
    return bootstrap(SPOT, TENORS, RATES)


def curve_table() -> list[tuple[float, float, float]]:
    """(years, zero rate %, one-year forward rate starting then %) at half-year steps."""
    c = curve()
    out = []
    for k in range(1, 21):
        years = k / 2
        d = SPOT + dt.timedelta(days=round(365 * years))
        d1 = SPOT + dt.timedelta(days=round(365 * (years - 0.5)))
        d2 = SPOT + dt.timedelta(days=round(365 * (years + 0.5)))
        fwd = (c.df(d1) / c.df(d2) - 1) / ((d2 - d1).days / 360)
        out.append((years, 100 * c.zero(d), 100 * fwd))
    return out


def ten_year() -> dict[str, float]:
    c = curve()
    dates = schedule(SPOT, 10)
    k = par_rate(c, dates)
    b = bucket_dv01(SPOT, TENORS, RATES, dates, k, 1e8)
    return {"par": k, "annuity": annuity(c, dates), "dv01_analytic": 1e8 * annuity(c, dates) * 1e-4,
            "buckets": b, "dv01": sum(b)}


def forward_5y5y() -> dict[str, float]:
    c = curve()
    dates = schedule(add_years(SPOT, 5), 5)
    k = par_rate(c, dates)
    b = bucket_dv01(SPOT, TENORS, RATES, dates, k, 1e8)
    return {"par": k, "buckets": b, "dv01": sum(b)}


# ---- the corporate hedge -------------------------------------------------------------------------
LOAN = 200_000_000.0
LOAN_MARGIN = 0.0150


def steepener(t: float) -> float:
    """-20 bp at one year rising linearly to +15 bp at ten years (flat outside)."""
    t = min(max(t, 1.0), 10.0)
    return (-20.0 + (t - 1.0) / 9.0 * 35.0) * 1e-4


def corporate_hedge() -> dict[str, float]:
    dates = schedule(SPOT, 10)
    k = par_rate(curve(), dates)
    parallel = bootstrap(SPOT, TENORS, [r + 1e-4 for r in RATES])
    steep = bootstrap(SPOT, TENORS, [r + steepener(t) for r, t in zip(RATES, TENORS, strict=True)])
    return {
        "fixed": k, "all_in": k + LOAN_MARGIN,
        "dv01": swap_pv(parallel, dates, k, LOAN) - swap_pv(curve(), dates, k, LOAN),
        "pnl_steep": swap_pv(steep, dates, k, LOAN),
        "pnl_up50": swap_pv(bootstrap(SPOT, TENORS, [r + 0.005 for r in RATES]), dates, k, LOAN),
        "pnl_dn50": swap_pv(bootstrap(SPOT, TENORS, [r - 0.005 for r in RATES]), dates, k, LOAN),
    }


def swap_spread(swap_rate: float, treasury_yield: float) -> float:
    return (swap_rate - treasury_yield) * 1e4


def first_period_interest(notional: float, rate: float, start: dt.date, end: dt.date) -> float:
    return notional * rate * (end - start).days / 360


__all__ = ["math"]
