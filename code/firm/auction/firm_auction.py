"""firm.auction -- call-auction uncrossing (build of Chapter 13, One Quant Book 1).

Prices are integer ticks. A price of None is a market order. Rules, in order:
  1. maximise the executable volume;
  2. among those prices, minimise the surplus (unexecuted quantity at that price);
  3. if the surplus is on the buy side at all remaining prices take the highest, if on the
     sell side take the lowest (market pressure);
  4. otherwise take the price closest to the reference price, the lower one on a tie.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AuctionOrder:
    order_id: str
    side: int                  # +1 buy, -1 sell
    quantity: int
    price: int | None          # None = market order
    seq: int                   # arrival sequence: time priority


@dataclass(frozen=True)
class Uncrossing:
    price: int | None
    volume: int
    surplus: int               # signed: + unexecuted buy interest at the price, - sell
    fills: tuple[tuple[str, int], ...]


def demand(orders, p: int) -> int:
    return sum(o.quantity for o in orders if o.side > 0 and (o.price is None or o.price >= p))


def supply(orders, p: int) -> int:
    return sum(o.quantity for o in orders if o.side < 0 and (o.price is None or o.price <= p))


def uncross(orders: list[AuctionOrder], reference: int) -> Uncrossing:
    prices = sorted({o.price for o in orders if o.price is not None} | {reference})
    table = [(p, demand(orders, p), supply(orders, p)) for p in prices]
    best = max(min(d, s) for _, d, s in table)
    if best == 0:
        return Uncrossing(None, 0, 0, ())
    cands = [(p, d, s) for p, d, s in table if min(d, s) == best]                 # rule 1
    least = min(abs(d - s) for _, d, s in cands)
    cands = [c for c in cands if abs(c[1] - c[2]) == least]                       # rule 2
    if all(d > s for _, d, s in cands):
        p, d, s = cands[-1]                                                       # rule 3: buy pressure
    elif all(d < s for _, d, s in cands):
        p, d, s = cands[0]                                                        # rule 3: sell pressure
    else:
        p, d, s = min(cands, key=lambda c: (abs(c[0] - reference), c[0]))         # rule 4
    return Uncrossing(p, best, d - s, tuple(_allocate(orders, p, best)))


def _allocate(orders, p: int, volume: int):
    """Market orders first, then better-priced limits, then time priority."""
    fills = []
    for side in (+1, -1):
        eligible = [o for o in orders if o.side == side and
                    (o.price is None or (o.price >= p if side > 0 else o.price <= p))]
        eligible.sort(key=lambda o: (o.price is not None, -side * (o.price or 0), o.seq))
        left = volume
        for o in eligible:
            q = min(left, o.quantity)
            if q:
                fills.append((o.order_id, q))
            left -= q
    return fills
