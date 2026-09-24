"""Allocation algorithms and implied prices (build of Book 1, Chapter 19).

An allocation algorithm answers one question: an aggressor of `qty` lots arrives at a price level
holding these resting orders; who gets what? Orders are given in time priority (oldest first).
The variants follow the families exchanges publish; parameters are per product in real life.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Resting:
    oid: str
    qty: int
    lmm: bool = False              # lead market maker order
    top: bool = False              # the order that established this price level


def _take(fills: dict[str, int], order: Resting, want: int, left: int) -> int:
    got = min(want, order.qty - fills.get(order.oid, 0), left)
    if got > 0:
        fills[order.oid] = fills.get(order.oid, 0) + got
    return left - max(got, 0)


def fifo(book: list[Resting], qty: int) -> dict[str, int]:
    fills: dict[str, int] = {}
    left = qty
    for o in book:
        left = _take(fills, o, o.qty, left)
    return fills


def pro_rata(book: list[Resting], qty: int, min_alloc: int = 1) -> dict[str, int]:
    """Floor of qty * size / total; allocations below `min_alloc` are dropped; leftovers go FIFO."""
    return _pro_rata_into({}, book, qty, min_alloc)


def _pro_rata_into(fills: dict[str, int], book: list[Resting], qty: int, min_alloc: int) -> dict[str, int]:
    open_qty = {o.oid: o.qty - fills.get(o.oid, 0) for o in book}
    total = sum(open_qty.values())
    left = min(qty, total)
    if left <= 0:
        return fills
    target = left
    for o in book:
        share = target * open_qty[o.oid] // total
        if share >= min_alloc:
            left = _take(fills, o, share, left)
    for o in book:                                      # residual from rounding: time priority
        left = _take(fills, o, o.qty, left)
    return fills


def configurable(book: list[Resting], qty: int, top_pct: int = 0, lmm_pct: int = 0, fifo_pct: int = 0,
                 min_alloc: int = 1) -> dict[str, int]:
    """Top order first (up to top_pct of the aggressor), then lead market makers (lmm_pct, shared in
    time priority), then fifo_pct of what remains by time, then the rest pro rata, leftovers by time."""
    fills: dict[str, int] = {}
    left = min(qty, sum(o.qty for o in book))
    for o in book:
        if o.top:
            left = _take(fills, o, qty * top_pct // 100, left)
            break
    budget = qty * lmm_pct // 100
    for o in book:
        if o.lmm and budget > 0:
            before = left
            left = _take(fills, o, budget, left)
            budget -= before - left
    by_time = left * fifo_pct // 100
    for o in book:
        if by_time <= 0:
            break
        before = left
        left = _take(fills, o, by_time, left)
        by_time -= before - left
    return _pro_rata_into(fills, book, left, min_alloc)


@dataclass(frozen=True)
class Quote:
    bid: int | None
    bid_qty: int
    ask: int | None
    ask_qty: int


def implied_in(front: Quote, back: Quote) -> Quote:
    """Spread (front minus back) implied by the two outright books."""
    bid = front.bid - back.ask if front.bid is not None and back.ask is not None else None
    ask = front.ask - back.bid if front.ask is not None and back.bid is not None else None
    return Quote(bid, min(front.bid_qty, back.ask_qty) if bid is not None else 0,
                 ask, min(front.ask_qty, back.bid_qty) if ask is not None else 0)


def implied_out_front(spread: Quote, back: Quote) -> Quote:
    """Front-month outright implied by the spread book and the back month."""
    bid = spread.bid + back.bid if spread.bid is not None and back.bid is not None else None
    ask = spread.ask + back.ask if spread.ask is not None and back.ask is not None else None
    return Quote(bid, min(spread.bid_qty, back.bid_qty) if bid is not None else 0,
                 ask, min(spread.ask_qty, back.ask_qty) if ask is not None else 0)


def best_of(direct: Quote, implied: Quote) -> Quote:
    """The book a trader sees: the better of direct and implied on each side (sizes add at equal prices)."""
    def side(dp, dq, ip, iq, better):
        if dp is None:
            return ip, iq
        if ip is None:
            return dp, dq
        if dp == ip:
            return dp, dq + iq
        return (dp, dq) if better(dp, ip) else (ip, iq)
    b = side(direct.bid, direct.bid_qty, implied.bid, implied.bid_qty, lambda x, y: x > y)
    a = side(direct.ask, direct.ask_qty, implied.ask, implied.ask_qty, lambda x, y: x < y)
    return Quote(b[0], b[1], a[0], a[1])
