"""Pass-through cash flows, prepayment and effective duration (build of Book 2, Chapter 12).

A pass-through collects the level payments of a pool of fixed-rate mortgages (rate `wac`) and
passes them to investors at the lower net coupon, less servicing and guarantee fees. Each month a
fraction SMM of the balance left after scheduled principal is prepaid. Prepayment speeds are
annual CPRs, from the PSA ramp or from a refinancing S-curve in the rate incentive. Rates are
decimals; the model is static (one rate path), as in the chapter.
"""
import math
from collections.abc import Callable
from dataclasses import dataclass


def psa_cpr(age: int, speed: float = 1.0) -> float:
    """PSA benchmark: 0.2% CPR in month 1, +0.2% a month to 6% at month 30, flat after; `speed`
    scales it (2.0 = 200% PSA)."""
    return speed * 0.06 * min(age, 30) / 30.0


def smm(cpr: float) -> float:
    """Single monthly mortality equivalent to an annual CPR."""
    return 1.0 - (1.0 - cpr) ** (1.0 / 12.0)


def level_payment(balance: float, monthly_rate: float, months: int) -> float:
    return balance * monthly_rate / (1.0 - (1.0 + monthly_rate) ** -months)


@dataclass(frozen=True)
class Flow:
    month: int
    interest: float           # to investors, at the net coupon
    scheduled: float
    prepaid: float
    balance: float            # after this month's principal


def cash_flows(balance: float, wac: float, coupon: float, term: int, age: int,
               cpr: Callable[[int], float]) -> list[Flow]:
    """Monthly flows of a pass-through; cpr(loan_age) gives the annual prepayment rate."""
    out, r = [], wac / 12.0
    for k in range(1, term - age + 1):
        if balance <= 1e-9:
            break
        pay = level_payment(balance, r, term - age - k + 1)
        sched = pay - balance * r
        pre = (balance - sched) * smm(cpr(age + k))
        interest = balance * coupon / 12.0
        balance -= sched + pre
        out.append(Flow(k, interest, sched, pre, balance))
    return out


def price(flows: list[Flow], y: float, face: float) -> float:
    """Price per 100 of face, discounting at the monthly-compounded yield y."""
    pv = sum((f.interest + f.scheduled + f.prepaid) / (1.0 + y / 12.0) ** f.month for f in flows)
    return 100.0 * pv / face


def wal(flows: list[Flow], face: float) -> float:
    """Weighted average life in years."""
    return sum(f.month / 12.0 * (f.scheduled + f.prepaid) for f in flows) / face


def refi_cpr(incentive: float, base: float = 0.06, top: float = 0.50, slope: float = 250.0,
             centre: float = 0.0075) -> float:
    """Refinancing S-curve: annual CPR as a function of the rate incentive (WAC minus the current
    mortgage rate), from `base` deep out of the money to `top` deep in it."""
    return base + (top - base) / (1.0 + math.exp(-slope * (incentive - centre)))


def effective_risk(p: Callable[[float], float], y: float, dy: float = 0.0025) -> dict[str, float]:
    """Effective duration and convexity from prices at y - dy, y and y + dy, the prepayment
    model being re-run at each rate."""
    down, mid, up = p(y - dy), p(y), p(y + dy)
    return {"price": mid, "down": down, "up": up, "duration": (down - up) / (2.0 * mid * dy),
            "convexity": (down + up - 2.0 * mid) / (mid * dy * dy)}


def roll_financing_rate(front: float, back: float, coupon: float, paydown: float, days: int = 30) -> float:
    """Implied financing rate of a dollar roll: selling the front month at `front` and buying the
    back month at `back` gives up the month's coupon and the paydown returned at par."""
    end_value = (1.0 - paydown) * back + 100.0 * paydown + 100.0 * coupon / 12.0
    return (end_value / front - 1.0) * 360.0 / days
