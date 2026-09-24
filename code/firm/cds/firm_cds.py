"""Credit default swaps with a flat hazard rate, and the settlement auction (build of Book 2,
Chapter 23).

A CDS of maturity T years pays a running coupon c a year on the notional, quarterly, while the
reference entity survives; on default it pays (1 - R). With a flat hazard rate lam the survival
probability is exp(-lam t); a default in a period is settled at the period's end, and the coupon
accrued to default is counted as half a period. Rates are continuously compounded, amounts per unit
notional. The auction replays the two-stage method used since 2005 (prices per 100 of par).
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Cds:
    maturity: float
    coupon: float                 # 0.01 or 0.05 for standard contracts
    recovery: float = 0.40
    freq: int = 4


def legs(cds: Cds, lam: float, r: float) -> tuple[float, float]:
    """(risky annuity: value of 1 a year of coupon, protection leg value)."""
    dt, annuity, protection = 1.0 / cds.freq, 0.0, 0.0
    for k in range(1, round(cds.maturity * cds.freq) + 1):
        q0, q1 = math.exp(-lam * (k - 1) * dt), math.exp(-lam * k * dt)
        df = math.exp(-r * k * dt)
        annuity += dt * df * (q1 + 0.5 * (q0 - q1))
        protection += (1.0 - cds.recovery) * df * (q0 - q1)
    return annuity, protection


def par_spread(cds: Cds, lam: float, r: float) -> float:
    a, p = legs(cds, lam, r)
    return p / a


def upfront(cds: Cds, lam: float, r: float) -> float:
    """Paid by the protection buyer at the start (negative: received), per unit notional."""
    a, p = legs(cds, lam, r)
    return p - cds.coupon * a


def hazard_from_spread(cds: Cds, spread: float, r: float) -> float:
    lo, hi = 1e-9, 5.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if par_spread(cds, mid, r) < spread else (lo, mid)
    return 0.5 * (lo + hi)


def upfront_from_spread(cds: Cds, spread: float, r: float) -> float:
    return upfront(cds, hazard_from_spread(cds, spread, r), r)


# ---- the settlement auction ---------------------------------------------------------------------

def inside_market_midpoint(bids: list[float], offers: list[float]) -> float:
    """Remove crossing bid/offer pairs, average the better half of the remaining bids and offers,
    round to the nearest 1/8."""
    b, o = sorted(bids, reverse=True), sorted(offers)
    while b and o and b[0] >= o[0]:
        b.pop(0)
        o.pop(0)
    h = math.ceil(len(b) / 2)
    return round((sum(b[:h]) + sum(o[:h])) / (2 * h) * 8) / 8


def open_interest(requests: list[tuple[str, float]]) -> float:
    """Net physical settlement requests: positive to sell bonds, negative to buy."""
    return sum(size if side == "sell" else -size for side, size in requests)


def final_price(imm: float, oi: float, orders: list[tuple[float, float]]) -> float:
    """Second stage: limit orders (price, size) fill the open interest, best price first; the last
    order filled sets the price, which may not move more than 1 point past the midpoint."""
    if oi == 0:
        return imm
    if oi > 0:                                   # sellers: bids to buy, highest first, cap imm + 1
        filled, price = 0.0, imm
        for p, size in sorted(orders, key=lambda x: -x[0]):
            filled, price = filled + size, p
            if filled >= oi:
                break
        return min(price, imm + 1.0)
    filled, price = 0.0, imm                     # buyers: offers to sell, lowest first, floor imm - 1
    for p, size in sorted(orders):
        filled, price = filled + size, p
        if filled >= -oi:
            break
    return max(price, imm - 1.0)


def cash_settlement(notional: float, price: float) -> float:
    """Paid by the protection seller to the buyer: (100 - price)% of notional."""
    return notional * (100.0 - price) / 100.0
