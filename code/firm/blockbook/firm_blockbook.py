"""Block-batched order book (build of Book 3, Chapter 21).

Actions arrive during a block; at the end of the block they are sorted by an in-block priority rule and
applied to a price-time-priority book, deterministically. Rules: "arrival" keeps arrival order;
"cancels_first" applies, as one venue documents, first the actions that send no GTC or IOC order (such
as post-only orders), then cancels, then actions sending GTC or IOC orders, each class in arrival order.
Post-only orders that would cross are rejected; an open-interest cap rejects orders that would take a
trader's position beyond it. Mark price: the median of three inputs.
"""
from dataclasses import dataclass, field
from statistics import median


@dataclass
class Action:
    kind: str            # "alo" (post-only), "gtc", "ioc", "cancel"
    trader: str
    side: str = ""       # "buy" or "sell"
    price: int = 0       # in ticks
    qty: int = 0
    oid: int = 0         # the order to cancel, or the id given to a new order


@dataclass
class Fill:
    maker: str
    taker: str
    price: int
    qty: int
    maker_oid: int


@dataclass
class Book:
    bids: list = field(default_factory=list)      # [price, oid, trader, qty], best first
    asks: list = field(default_factory=list)
    positions: dict = field(default_factory=dict)
    oi_cap: int | None = None

    def _pos_after(self, trader: str, side: str, qty: int) -> int:
        return self.positions.get(trader, 0) + (qty if side == "buy" else -qty)

    def _book_fill(self, m: list, taker: str, side: str, q: int) -> Fill:
        p, oid, trader, _ = m
        m[3] -= q
        self.positions[taker] = self._pos_after(taker, side, q)
        self.positions[trader] = self._pos_after(trader, "sell" if side == "buy" else "buy", q)
        return Fill(trader, taker, p, q, oid)

    def apply(self, a: Action) -> list[Fill]:
        if a.kind == "cancel":
            for lvl in (self.bids, self.asks):
                lvl[:] = [o for o in lvl if not (o[1] == a.oid and o[2] == a.trader)]
            return []
        if self.oi_cap is not None and abs(self._pos_after(a.trader, a.side, a.qty)) > self.oi_cap:
            return []
        opp, same = (self.asks, self.bids) if a.side == "buy" else (self.bids, self.asks)
        crosses = (lambda p: p <= a.price) if a.side == "buy" else (lambda p: p >= a.price)
        if a.kind == "alo":
            if opp and crosses(opp[0][0]):
                return []                                    # post-only would take: rejected
            self._rest(same, a)
            return []
        fills, left = [], a.qty
        while left and opp and crosses(opp[0][0]):
            q = min(left, opp[0][3])
            fills.append(self._book_fill(opp[0], a.trader, a.side, q))
            left -= q
            if opp[0][3] == 0:
                opp.pop(0)
        if left and a.kind == "gtc":
            self._rest(same, Action(a.kind, a.trader, a.side, a.price, left, a.oid))
        return fills

    def _rest(self, lvl: list, a: Action) -> None:
        lvl.append([a.price, a.oid, a.trader, a.qty])
        lvl.sort(key=lambda o: (-o[0] if a.side == "buy" else o[0]))    # stable: time priority kept

    def best(self) -> tuple[int | None, int | None]:
        return (self.bids[0][0] if self.bids else None, self.asks[0][0] if self.asks else None)


def order_block(actions: list[Action], rule: str) -> list[Action]:
    if rule == "arrival":
        return list(actions)
    if rule == "cancels_first":
        cls = {"alo": 0, "cancel": 1, "gtc": 2, "ioc": 2}
        return sorted(actions, key=lambda a: cls[a.kind])        # sort is stable: arrival order within a class
    raise ValueError(f"unknown in-block rule {rule}")


def run_block(book: Book, actions: list[Action], rule: str) -> list[Fill]:
    fills = []
    for a in order_block(actions, rule):
        fills += book.apply(a)
    return fills


def mark_price(oracle_plus_basis: float, book_mid_median: float, external_median: float) -> float:
    return median([oracle_plus_basis, book_mid_median, external_median])
