"""firm.lob -- the reference limit order book (build of One Quant Book 10, chapter 1).

A limit order book is a set of resting orders keyed by an order reference. Each side is a map from price to a
price level; a level holds two FIFO queues in time priority: the displayed orders first, then the non-displayed
ones (the priority most venues publish: at one price, displayed before hidden, then time). An order's `qty` is
what can execute at its level now (for an iceberg, its displayed slice; the reserve lives with the owner).

Prices are integers (1/10,000 currency unit in the exchange simulator, or ticks); sides are +1 (bid) and -1
(ask). The book never matches: it stores, removes and reduces. Matching is the engine's job (firm.exchsim).

API (stable):
    Order(ref, side, price, qty, visible=True, seq=0, owner=None)   a resting order (__slots__, mutable qty)
    LimitOrderBook()                     the book: add(order), remove(ref), reduce(ref, q), get(ref),
                                         best(side), top() -> (bid, bid_qty, ask, ask_qty), depth(side, n),
                                         level_orders(side, price) (displayed then hidden, time order),
                                         prices(side) (best first), visible_qty(side, price), check()
    MessageBook()                        the public view rebuilt from a market-by-order stream: apply(kind, ...)
                                         for A (add), X (partial cancel), D (delete), E/C (execute), U (replace)
    ArrayBook(lo, hi, tick)              the same view on a price-indexed array (chapter 1's comparison):
                                         O(1) level access, a moving best pointer
    apply_tape(book, msgs)               replay firm.tape messages (t, kind A/X/E, oid, side, price, qty) into
                                         a MessageBook or ArrayBook, yielding the level-2 state after each
    l2_lines(book, n)                    the canonical text of the n best levels, the fixture format the C++20
                                         and Rust twins reproduce
"""
from __future__ import annotations

import bisect
from collections import deque


class Order:
    __slots__ = ("ref", "side", "price", "qty", "visible", "seq", "owner")

    def __init__(self, ref: int, side: int, price: int, qty: int, visible: bool = True, seq: int = 0, owner=None):
        self.ref, self.side, self.price, self.qty = ref, side, price, qty
        self.visible, self.seq, self.owner = visible, seq, owner

    def __repr__(self) -> str:
        return f"Order(ref={self.ref}, side={self.side}, price={self.price}, qty={self.qty}, visible={self.visible})"


class _Level:
    __slots__ = ("vis", "hid")

    def __init__(self):
        self.vis: deque[Order] = deque()
        self.hid: deque[Order] = deque()


class LimitOrderBook:
    """Levels per side (dict price -> _Level) plus a sorted price list per side; orders by reference."""

    def __init__(self):
        self.levels: dict[int, dict[int, _Level]] = {1: {}, -1: {}}
        self._px: dict[int, list[int]] = {1: [], -1: []}          # ascending
        self.orders: dict[int, Order] = {}

    # -- storage ----------------------------------------------------------------------------------------------
    def add(self, o: Order) -> None:
        if o.ref in self.orders:
            raise KeyError(f"duplicate order reference {o.ref}")
        lv = self.levels[o.side].get(o.price)
        if lv is None:
            lv = self.levels[o.side][o.price] = _Level()
            bisect.insort(self._px[o.side], o.price)
        (lv.vis if o.visible else lv.hid).append(o)
        self.orders[o.ref] = o

    def get(self, ref: int) -> Order | None:
        return self.orders.get(ref)

    def remove(self, ref: int) -> Order:
        o = self.orders.pop(ref)
        lv = self.levels[o.side][o.price]
        (lv.vis if o.visible else lv.hid).remove(o)
        if not lv.vis and not lv.hid:
            del self.levels[o.side][o.price]
            px = self._px[o.side]
            del px[bisect.bisect_left(px, o.price)]
        return o

    def reduce(self, ref: int, q: int) -> Order:
        """Take q off the order's executable quantity; remove it when nothing is left."""
        o = self.orders[ref]
        if q > o.qty or q <= 0:
            raise ValueError(f"reduce {q} from {o.qty}")
        o.qty -= q
        if o.qty == 0:
            self.remove(ref)
        return o

    # -- views ------------------------------------------------------------------------------------------------
    def best(self, side: int) -> int | None:
        px = self._px[side]
        if not px:
            return None
        return px[-1] if side == 1 else px[0]

    def prices(self, side: int) -> list[int]:
        px = self._px[side]
        return px[::-1] if side == 1 else list(px)

    def level_orders(self, side: int, price: int) -> list[Order]:
        lv = self.levels[side].get(price)
        return [] if lv is None else [*lv.vis, *lv.hid]

    def visible_qty(self, side: int, price: int) -> int:
        lv = self.levels[side].get(price)
        return 0 if lv is None else sum(o.qty for o in lv.vis)

    def best_visible(self, side: int) -> int | None:
        for p in reversed(self._px[side]) if side == 1 else self._px[side]:
            if self.levels[side][p].vis:
                return p
        return None

    def top(self) -> tuple[int | None, int, int | None, int]:
        """Best displayed bid and ask with their displayed sizes (hidden orders are not quoted)."""
        b, a = self.best_visible(1), self.best_visible(-1)
        return (b, self.visible_qty(1, b) if b is not None else 0, a, self.visible_qty(-1, a) if a is not None else 0)

    def depth(self, side: int, n: int) -> list[tuple[int, int]]:
        out = []
        for p in self.prices(side):
            q = self.visible_qty(side, p)
            if q:
                out.append((p, q))
                if len(out) == n:
                    break
        return out

    def check(self) -> None:
        """Invariants: every stored order is in exactly its level; price lists match the levels."""
        seen = 0
        for side in (1, -1):
            assert self._px[side] == sorted(self.levels[side]), "price list out of sync"
            for p, lv in self.levels[side].items():
                assert lv.vis or lv.hid, "empty level kept"
                for o in (*lv.vis, *lv.hid):
                    assert self.orders.get(o.ref) is o and o.price == p and o.side == side and o.qty > 0
                    seen += 1
        assert seen == len(self.orders), "orders missing from their levels"


class MessageBook:
    """The public book a feed describes: orders by reference, displayed only (level 3 in, level 2 out)."""

    def __init__(self):
        self.book = LimitOrderBook()

    def apply(self, kind: str, ref: int, side: int = 0, price: int = 0, qty: int = 0, new_ref: int = 0) -> None:
        b = self.book
        if kind == "A":
            b.add(Order(ref, side, price, qty))
        elif kind in ("X", "E", "C"):
            b.reduce(ref, qty)
        elif kind == "D":
            b.remove(ref)
        elif kind == "U":
            old = b.remove(ref)
            b.add(Order(new_ref, old.side, price, qty))
        else:
            raise ValueError(f"unknown message kind {kind!r}")

    def top(self):
        return self.book.top()

    def depth(self, side: int, n: int):
        return self.book.depth(side, n)


class ArrayBook:
    """Level sizes in a price-indexed array between lo and hi (inclusive, multiples of tick): the structure of
    most production books for liquid instruments. Orders by reference in a dict; best prices tracked by pointers
    that move only as far as the next non-empty level."""

    def __init__(self, lo: int, hi: int, tick: int = 1):
        self.lo, self.tick = lo, tick
        n = (hi - lo) // tick + 1
        self.size = {1: [0] * n, -1: [0] * n}
        self.orders: dict[int, tuple[int, int, int]] = {}      # ref -> (side, index, qty)
        self.bid, self.ask = -1, n                               # indices of the best levels (sentinels)
        self.n = n

    def _i(self, price: int) -> int:
        i = (price - self.lo) // self.tick
        if not 0 <= i < self.n or (price - self.lo) % self.tick:
            raise ValueError(f"price {price} outside the array or off the grid")
        return i

    def apply(self, kind: str, ref: int, side: int = 0, price: int = 0, qty: int = 0, new_ref: int = 0) -> None:
        if kind == "A":
            i = self._i(price)
            self.orders[ref] = (side, i, qty)
            self.size[side][i] += qty
            if side == 1 and i > self.bid:
                self.bid = i
            if side == -1 and i < self.ask:
                self.ask = i
            return
        if kind == "U":
            side0 = self.orders[ref][0]
            self.apply("D", ref)
            self.apply("A", new_ref, side0, price, qty)
            return
        s, i, q = self.orders[ref]
        take = q if kind == "D" else qty
        if take > q:
            raise ValueError("reduce beyond the order's size")
        self.size[s][i] -= take
        if q == take:
            del self.orders[ref]
        else:
            self.orders[ref] = (s, i, q - take)
        if s == 1:
            while self.bid >= 0 and self.size[1][self.bid] == 0:
                self.bid -= 1
        else:
            while self.ask < self.n and self.size[-1][self.ask] == 0:
                self.ask += 1

    def top(self):
        b = None if self.bid < 0 else self.lo + self.bid * self.tick
        a = None if self.ask >= self.n else self.lo + self.ask * self.tick
        return (b, self.size[1][self.bid] if b is not None else 0, a, self.size[-1][self.ask] if a is not None else 0)

    def depth(self, side: int, n: int):
        out, i = [], self.bid if side == 1 else self.ask
        step = -1 if side == 1 else 1
        while 0 <= i < self.n and len(out) < n:
            if self.size[side][i]:
                out.append((self.lo + i * self.tick, self.size[side][i]))
            i += step
        return out


def apply_tape(book, msgs):
    """Replay firm.tape messages into `book` (MessageBook or ArrayBook), yielding after each message."""
    for m in msgs:
        kind = m["kind"].decode()
        if kind == "A":
            book.apply("A", int(m["oid"]), int(m["side"]), int(m["price"]), int(m["qty"]))
        else:
            book.apply("E" if kind == "E" else "X", int(m["oid"]), qty=int(m["qty"]))
        yield book


def l2_lines(book, n: int = 5) -> str:
    """One text line per side: 'B p:q p:q ...' then 'S p:q ...' (best first)."""
    return "B " + " ".join(f"{p}:{q}" for p, q in book.depth(1, n)) + "\nS " + " ".join(
        f"{p}:{q}" for p, q in book.depth(-1, n))
