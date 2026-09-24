"""Uniform-price Treasury auction analyser (build of Book 2, Chapter 4).

Competitive bids are (bidder, yield, amount); noncompetitive bids are awarded in full first. The
remaining amount goes to competitive bids in increasing order of yield; the highest yield
accepted is the stop-out (high) yield, which every winner pays; bids at the stop-out are
allotted pro rata, the percentage rounded up to the next hundredth of a percent (31 CFR 356.20).
A bidder's recognised amount is capped at 35% of the offering. Amounts are in the same unit
throughout (e.g. USD million); yields are decimals.
"""
import math
from collections import defaultdict
from dataclasses import dataclass

MAX_SHARE = 0.35


@dataclass(frozen=True)
class Bid:
    bidder: str
    yld: float
    amount: float


@dataclass(frozen=True)
class Result:
    stop: float                      # high yield
    allotment_at_stop: float         # fraction of bids at the stop-out that is filled
    awards: dict[str, float]         # competitive awards by bidder
    competitive_tendered: float
    bid_to_cover: float              # (competitive + noncompetitive tendered) / offering


def cap_bids(bids: list[Bid], offering: float, max_share: float = MAX_SHARE) -> list[Bid]:
    """Recognise each bidder's bids from the lowest yield up to max_share of the offering."""
    left: dict[str, float] = defaultdict(lambda: max_share * offering)
    out = []
    for b in sorted(bids, key=lambda b: b.yld):
        amt = min(b.amount, left[b.bidder])
        if amt > 0:
            out.append(Bid(b.bidder, b.yld, amt))
            left[b.bidder] -= amt
    return out


def run_auction(offering: float, noncompetitive: float, bids: list[Bid]) -> Result:
    capacity = offering - noncompetitive
    book = cap_bids(bids, offering)
    tendered = sum(b.amount for b in book)
    if tendered < capacity:
        raise ValueError("auction not covered")
    levels = sorted({b.yld for b in book})
    filled = 0.0
    for y in levels:
        at = sum(b.amount for b in book if b.yld == y)
        if filled + at >= capacity:
            stop, pct = y, math.ceil((capacity - filled) / at * 1e4 - 1e-9) / 1e4
            break
        filled += at
    awards: dict[str, float] = defaultdict(float)
    for b in book:
        if b.yld < stop:
            awards[b.bidder] += b.amount
        elif b.yld == stop:
            awards[b.bidder] += b.amount * pct
    return Result(stop, pct, dict(awards), tendered, (tendered + noncompetitive) / offering)


def tail_bp(stop: float, when_issued: float) -> float:
    """Positive: the auction cleared at a higher yield (cheaper) than the market at the bid deadline."""
    return (stop - when_issued) * 1e4


def cumulative_demand(bids: list[Bid], offering: float) -> list[tuple[float, float]]:
    """(yield, amount bid at or below that yield) for the recognised book: the demand curve."""
    book = cap_bids(bids, offering)
    out, cum = [], 0.0
    for y in sorted({b.yld for b in book}):
        cum += sum(b.amount for b in book if b.yld == y)
        out.append((y, cum))
    return out


def coupon_from_high_yield(high_yield: float) -> float:
    """Coupon of a new note (percent): the multiple of 1/8 giving the price closest to, but not
    above, par at the high yield, i.e. the high yield rounded down to an eighth (minimum 1/8)."""
    return max(0.125, math.floor(high_yield * 100 * 8 + 1e-9) / 8)
