"""firm.venuefees -- fees, rebates and the choice of venue (build of One Quant Book 10, chapter 7).

Fees are per share in currency, positive when the member pays and negative for a rebate. A buyer's fee-adjusted price
is price + fee, a seller's price - fee: what the trade really costs or brings once the venue has been paid.

API (stable):
    fee_adjusted(price, side, fee)                 price + side * fee (side +1 buy, -1 sell)
    effective_tick(tick, fees)                     the smallest gap between fee-adjusted prices on the grid when
                                                   the same side can trade on venues with these fees
    route_take(quotes, side, qty)                  split a marketable order over (venue, price, qty, take_fee)
                                                   quotes in order of fee-adjusted price: [(venue, price, q)]
    passive_value(fill, capture, adverse, make)    value per posted share: fill share x (capture - adverse - make)
    indifference_make(fill_a, net_a, fill_b, net_b, make_b)   the make fee on venue a that equalises the two
                                                   values, given each venue's fill share and net (capture - adverse)
                                                   per filled share
    neutral_ask(ask, take, take_new, tick=None)    the ask that keeps a taker's fee-adjusted price when the take fee
                                                   changes: exact without a tick, rounded up to the grid with one
    tier_make_fee(schedule, adav, tcv)             the make fee of a firm.feesched schedule at a member's volume share
"""
from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "feesched"))
from firm_feesched import Schedule  # noqa: E402


def fee_adjusted(price: float, side: int, fee: float) -> float:
    return price + side * fee


def effective_tick(tick: float, fees) -> float:
    offsets = sorted({round(f % tick, 12) for f in fees})
    gaps = [b - a for a, b in zip(offsets, offsets[1:], strict=False)] + [tick - offsets[-1] + offsets[0]]
    return min(g for g in gaps if g > 1e-12) if len(offsets) > 1 else tick


def route_take(quotes, side: int, qty: int) -> list[tuple]:
    """quotes: (venue, price, displayed qty, take fee) on the side being taken (asks for a buy, bids for a sell)."""
    order = sorted(quotes, key=lambda q: fee_adjusted(q[1], side, q[3]) * side)
    out, left = [], qty
    for venue, price, avail, _ in order:
        if left <= 0:
            break
        q = min(avail, left)
        if q > 0:
            out.append((venue, price, q))
            left -= q
    return out


def passive_value(fill: float, capture: float, adverse: float, make: float) -> float:
    return fill * (capture - adverse - make)


def indifference_make(fill_a: float, net_a: float, fill_b: float, net_b: float, make_b: float) -> float:
    """fill_a (net_a - m) = fill_b (net_b - make_b), solved for m."""
    return net_a - fill_b * (net_b - make_b) / fill_a


def neutral_ask(ask: float, take: float, take_new: float, tick: float | None = None) -> float:
    a = ask + take - take_new
    return a if tick is None else math.ceil(round(a / tick, 9)) * tick


def tier_make_fee(schedule: Schedule, adav: float, tcv: float) -> float:
    return schedule.add_rate(adav, tcv)
