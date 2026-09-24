"""Chapter 12 of Book 2: mortgages and agencies. A pass-through's cash flows under the PSA ramp,
the price-yield curve of a pass-through whose prepayments follow a refinancing S-curve, its
effective duration and convexity, the hedge a duration-neutral holder must trade after a rally,
and a dollar roll. Pool terms, the S-curve and the roll prices are illustrative."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/prepay"))
from firm_prepay import cash_flows, effective_risk, price, psa_cpr, refi_cpr, roll_financing_rate, wal

DATA = pathlib.Path(__file__).resolve().parents[4] / "data/markets-2"
FACE = 100_000_000.0
WAC, COUPON, TERM = 0.065, 0.060, 360     # 6.5% loans in a 6% pass-through, 30 years
AGE = 36                                  # seasoned: past the 30-month ramp
SPREAD = 0.005                            # primary mortgage rate over the discount yield
Y0 = 0.060                                # discount yield at which the pool is at the money


def speed_at(y: float) -> float:
    return refi_cpr(WAC - (y + SPREAD))


def mbs_price(y: float) -> float:
    """Price when the refinancing speed responds to the rate y."""
    c = speed_at(y)
    return price(cash_flows(FACE, WAC, COUPON, TERM, AGE, lambda a: c), y, FACE)


def static_price(y: float, cpr: float | None = None) -> float:
    """Price with the speed frozen at its at-the-money value: an ordinary amortising bond."""
    c = speed_at(Y0) if cpr is None else cpr
    return price(cash_flows(FACE, WAC, COUPON, TERM, AGE, lambda a: c), y, FACE)


def psa_curves() -> list[tuple[int, float, float, float]]:
    return [(a, 100 * psa_cpr(a, 0.5), 100 * psa_cpr(a, 1.0), 100 * psa_cpr(a, 2.0)) for a in range(0, 61)]


def new_pool(speed: float = 1.0):
    return cash_flows(FACE, WAC, COUPON, TERM, 0, lambda a: psa_cpr(a, speed))


def wal_table() -> dict[float, float]:
    return {s: wal(new_pool(s), FACE) for s in (0.0, 0.5, 1.0, 2.0, 3.0)}


def price_yield() -> list[tuple[float, float, float]]:
    """(yield %, pass-through price, static price) for shifts of -200 to +200 bp."""
    return [(100 * (Y0 + k * 0.0025), mbs_price(Y0 + k * 0.0025), static_price(Y0 + k * 0.0025)) for k in range(-8, 9)]


def risk_table() -> dict[float, dict[str, float]]:
    return {y: effective_risk(mbs_price, y) | {"cpr": speed_at(y)} for y in (0.055, 0.060, 0.065)}


def swap_dv01(notional: float, rate: float = Y0, years: int = 10) -> float:
    return notional * sum((1 + rate) ** -k for k in range(1, years + 1)) * 1e-4


def convexity_hedge(portfolio: float = 10e9) -> dict[str, float]:
    """A holder of `portfolio` face, hedged to zero duration at the money, after a 50 bp rally."""
    r0, r1 = effective_risk(mbs_price, Y0), effective_risk(mbs_price, Y0 - 0.005)
    dv0 = portfolio * r0["price"] / 100 * r0["duration"] * 1e-4
    dv1 = portfolio * r1["price"] / 100 * r1["duration"] * 1e-4
    per = swap_dv01(100e6)
    return {"d0": r0["duration"], "d1": r1["duration"], "p1": r1["price"], "dv0": dv0, "dv1": dv1,
            "lost": dv0 - dv1, "swap_dv01_100m": per, "receive": (dv0 - dv1) / per * 100e6,
            "market_2003": 289e9}


def roll_example() -> dict[float, float]:
    """6% coupon, front 100-16 (100.50), back 100-08 (100.25); a month's paydown at the
    at-the-money speed of the seasoned pool."""
    first = cash_flows(FACE, WAC, COUPON, TERM, AGE, lambda a: speed_at(Y0))[0]
    paydown = (first.scheduled + first.prepaid) / FACE
    return {"paydown": paydown, "rate": roll_financing_rate(100.50, 100.25, COUPON, paydown),
            "rate_no_drop": roll_financing_rate(100.50, 100.50, COUPON, paydown),
            "drop_at_repo": breakeven_drop(0.04, paydown)}


def breakeven_drop(repo: float, paydown: float, front: float = 100.50, days: int = 30) -> float:
    """Drop (front minus back price) at which the roll finances at `repo`."""
    target = front * (1 + repo * days / 360)
    back = (target - 100.0 * paydown - 100.0 * COUPON / 12.0) / (1.0 - paydown)
    return front - back


def load_fed_mbs() -> list[tuple[str, float]]:
    with open(DATA / "fed_mbs_monthly.csv") as f:
        return [(r["date"], float(r["mbs_bn"])) for r in csv.DictReader(f)]
