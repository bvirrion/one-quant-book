"""Options allocation rules (build of Book 1, Chapter 24; extends firm_match of Chapter 19).

Two mechanisms of US options exchanges, in the generic form their rulebooks share:
customer priority with a market-maker entitlement and pro rata for the rest; and the
price-improvement auction, in which the firm that brings a customer order guarantees it a price
and keeps a share of it. Percentages and minimums are per exchange and per class.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    oid: str
    qty: int
    capacity: str                   # 'customer', 'mm' or 'firm'
    designated: bool = False        # the class's designated / lead market maker


def _give(fills: dict[str, int], q: Quote, want: int, left: int) -> int:
    got = max(0, min(want, q.qty - fills.get(q.oid, 0), left))
    if got:
        fills[q.oid] = fills.get(q.oid, 0) + got
    return left - got


def customer_priority_pro_rata(book: list[Quote], qty: int, entitlement_pct: int = 0) -> dict[str, int]:
    """`book` is the best price level in time priority.
    1. Priority customers, in time order, in full.
    2. The designated market maker: the larger of its entitlement and its pro-rata share of what is left.
    3. The other professionals pro rata on size over the remainder; leftovers by time."""
    fills: dict[str, int] = {}
    left = min(qty, sum(q.qty for q in book))
    for q in book:
        if q.capacity == "customer":
            left = _give(fills, q, q.qty, left)
    pros = [q for q in book if q.capacity != "customer"]
    total = sum(q.qty for q in pros)
    if left <= 0 or total <= 0:
        return fills
    pool = left
    for q in pros:                                             # the designated maker is served first
        if q.designated:
            share = max(pool * q.qty // total, pool * entitlement_pct // 100)
            left = _give(fills, q, share, left)
    others = [q for q in pros if not q.designated] if any(q.designated for q in pros) else pros
    rest, size = left, sum(q.qty for q in others)
    for q in others:
        left = _give(fills, q, rest * q.qty // size if size else 0, left)
    for q in pros:
        left = _give(fills, q, q.qty, left)
    return fills


@dataclass(frozen=True)
class AuctionResult:
    price: int
    fills: dict[str, int]
    initiator_qty: int
    improved: bool


def price_improvement_auction(agency_qty: int, stop_price: int, side: int, responses: list[tuple[str, int, int]],
                              book_customers: int = 0, one_other_pct: int = 50,
                              many_others_pct: int = 40) -> AuctionResult:
    """A customer order to buy (side=+1) or sell (side=-1) `agency_qty` is guaranteed `stop_price` by the
    initiating firm. `responses` are (participant, price, qty) received during the auction; a response
    is better than the stop if it is lower (customer buying) or higher (customer selling).

    Responses at better prices fill first, best price first, pro rata within a price. At the stop price:
    priority customers resting on the book first, then the initiator up to 50% of the ORIGINAL order if
    one other participant is at that price and 40% if several, then the others pro rata, and whatever
    is left goes back to the initiator, who guaranteed the whole order."""
    fills: dict[str, int] = {}
    left = agency_qty
    better = sorted({p for _, p, _ in responses if (stop_price - p) * side > 0}, key=lambda p: p * side)
    last_price = stop_price
    for price in better:
        level = [(who, q) for who, p, q in responses if p == price]
        total = sum(q for _, q in level)
        pool = min(left, total)
        if pool <= 0:
            break
        given = 0
        for who, q in level:
            share = pool * q // total
            fills[who] = fills.get(who, 0) + share
            given += share
        for who, q in level:                                   # rounding leftovers, in arrival order
            if given >= pool:
                break
            if fills[who] < q:
                fills[who] += 1
                given += 1
        left -= pool
        last_price = price
    improved = left < agency_qty
    initiator = 0
    if left > 0:
        last_price = stop_price
        cust = min(book_customers, left)
        if cust:
            fills["book customers"] = cust
            left -= cust
        at_stop = [(who, q) for who, p, q in responses if p == stop_price]
        others = len(at_stop) + (1 if cust else 0)
        if others == 0:
            initiator, left = left, 0
        else:
            pct = one_other_pct if others == 1 else many_others_pct
            initiator = min(left, agency_qty * pct // 100)
            left -= initiator
            total = sum(q for _, q in at_stop)
            pool = min(left, total)
            for who, q in at_stop:
                share = pool * q // total if total else 0
                fills[who] = fills.get(who, 0) + share
                left -= share
            initiator += left                                   # the guarantee: the initiator takes the rest
            left = 0
    return AuctionResult(last_price, fills, initiator, improved)
