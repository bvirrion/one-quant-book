"""firm.lobreplay -- the level-3 backtester: order-book replay with queue positions and latency (Book 7, chapter 18).

A market-by-order message stream (firm.tape's msgs: t, kind A/X/E, oid, side, price, qty) rebuilds the book, and the
strategy's own orders are shadow orders: they sit at a place in the queue at their price, fill when the replayed
executions reach them, and do not change what the replay does next (no impact). Where a shadow order stands, and how
its place changes, is a queue-position model:
    'front'   it is first at its price as soon as it arrives (the touch fill of chapter 17)
    'fifo'    it joins behind every order resting at its price when it arrives, known by order id (market-by-order),
              moves up as those orders are executed or cancelled, and fills when an execution reaches an order behind it
    'prob'    only the level's total size is known (market-by-price): executions at the price consume the queue ahead
              first; a cancellation at the price removes size ahead of it in proportion to ahead / (ahead + behind)
Latency: the strategy sees each market event `data_latency` after it happens, and its orders and cancellations reach
the exchange `entry_latency` after it sends them. NumPy for the arrays; the loop is plain Python.

API (stable):
    Book                                   levels {side: {price: [ [oid, qty], ... ]}} in time priority; apply(msg)
    Shadow                                 vid, side, price, qty, sent, arrive, cancel_sent, cancel_arrive, ahead,
                                           behind, filled, fills [(t, qty)], status
    QueueTracker(model, seed)              join(book, shadow), on_message(book_before, msg, shadows) -> fills
    Replay(msgs, strategy, model, entry_latency, data_latency, seed).run() -> ReplayResult
    Strategy.on_market(ctx, t, snapshot) and on_fill(ctx, vid, t, qty, price); ctx.send(side, price, qty) -> vid,
        ctx.cancel(vid), ctx.position, ctx.working()
    ReplayResult: shadows, fills [(t, vid, side, qty, price)], position, cash, mid path (t, mid), pnl(mark)
    track_fifo(msgs, orders) -> fills       the 'fifo' model alone, for orders with known arrival and cancel times
                                           (the reference the C++20 and Rust cores reproduce)
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field

import numpy as np


class Book:
    def __init__(self):
        self.levels = {1: {}, -1: {}}
        self.where: dict[int, tuple[int, int]] = {}

    def apply(self, m) -> None:
        kind, oid, side, px, qty = m["kind"], int(m["oid"]), int(m["side"]), int(m["price"]), int(m["qty"])
        if kind == b"A":
            self.levels[side].setdefault(px, []).append([oid, qty])
            self.where[oid] = (side, px)
            return
        side, px = self.where[oid]
        q = self.levels[side][px]
        for i, (o, _) in enumerate(q):
            if o == oid:
                q[i][1] -= qty
                if q[i][1] <= 0:
                    q.pop(i)
                    del self.where[oid]
                break
        if not q:
            del self.levels[side][px]

    def best(self, side: int):
        lv = self.levels[side]
        if not lv:
            return None
        return max(lv) if side == 1 else min(lv)

    def size(self, side: int, px: int) -> int:
        return sum(n for _, n in self.levels[side].get(px, []))


@dataclass
class Shadow:
    vid: int
    side: int
    price: int
    qty: int
    sent: float
    arrive: float
    cancel_sent: float = float("inf")
    cancel_arrive: float = float("inf")
    ahead: float = 0.0
    behind: float = 0.0
    ahead_ids: dict = field(default_factory=dict)
    filled: int = 0
    fills: list = field(default_factory=list)
    status: str = "sent"                    # sent, working, filled, cancelled

    @property
    def remaining(self) -> int:
        return self.qty - self.filled


class QueueTracker:
    def __init__(self, model: str = "fifo", seed: int = 0):
        self.model = model
        self.rng = np.random.default_rng(seed)

    def join(self, book: Book, s: Shadow) -> None:
        s.status = "working"
        q = book.levels[s.side].get(s.price, [])
        if self.model == "front":
            s.ahead = 0.0
        elif self.model == "fifo":
            s.ahead_ids = {o: n for o, n in q}
            s.ahead = float(sum(s.ahead_ids.values()))
        else:
            s.ahead, s.behind = float(sum(n for _, n in q)), 0.0

    def on_message(self, book: Book, m, shadows) -> list:
        """Update the working shadows at the message's price and side, before the book applies it. Returns fills
        [(vid, qty)] caused by an execution that, in time priority, would have reached the shadow."""
        kind, oid, side, px, qty = m["kind"], int(m["oid"]), int(m["side"]), int(m["price"]), int(m["qty"])
        out = []
        for s in shadows:
            if s.status != "working" or s.side != side or s.price != px:
                continue
            if kind == b"A":
                if self.model == "prob":
                    s.behind += qty
                continue
            if self.model == "fifo":
                if oid in s.ahead_ids:
                    take = min(qty, s.ahead_ids[oid])
                    s.ahead_ids[oid] -= take
                    s.ahead -= take
                    if s.ahead_ids[oid] <= 0:
                        del s.ahead_ids[oid]
                elif kind == b"E":
                    out.append((s, min(s.remaining, qty)))
                continue
            if kind == b"E":
                if self.model == "front":
                    out.append((s, min(s.remaining, qty)))
                    continue
                take = min(qty, s.ahead)
                s.ahead -= take
                if qty - take > 0:
                    out.append((s, min(s.remaining, qty - take)))
                    s.behind = max(0.0, s.behind - max(0.0, qty - take - s.remaining))
                continue
            if self.model == "prob":                          # a cancellation at our price
                tot = s.ahead + s.behind
                share = s.ahead / tot if tot > 0 else 0.0
                s.ahead = max(0.0, s.ahead - qty * share)
                s.behind = max(0.0, s.behind - qty * (1.0 - share))
        return out


class Strategy:
    def on_market(self, ctx, t: float, snap: dict) -> None:
        pass

    def on_fill(self, ctx, vid: int, t: float, qty: int, price: int) -> None:
        pass


@dataclass
class ReplayResult:
    shadows: list
    fills: list
    position: int
    cash: float
    mid_t: np.ndarray
    mid: np.ndarray

    def pnl(self) -> float:
        """Cash plus the position marked at the last mid (in price units x shares)."""
        return float(self.cash + self.position * self.mid[-1])


MKT, ARRIVE, CANCEL, SEE = 0, 1, 2, 3


class Replay:
    def __init__(self, msgs, strategy: Strategy, model: str = "fifo", entry_latency: float = 0.0,
                 data_latency: float = 0.0, seed: int = 0):
        self.msgs, self.strategy = msgs, strategy
        self.tracker = QueueTracker(model, seed)
        self.entry, self.data = entry_latency, data_latency
        self.book = Book()
        self.shadows: list[Shadow] = []
        self.active: dict[int, Shadow] = {}
        self.fills: list = []
        self.position, self.cash, self.now = 0, 0.0, 0.0
        self._q: list = []
        self._seq = 0

    def _push(self, t, kind, payload):
        heapq.heappush(self._q, (t, kind, self._seq, payload))
        self._seq += 1

    # ------------------------------------------------------------------ context
    def send(self, side: int, price: int, qty: int) -> int:
        s = Shadow(len(self.shadows), side, int(price), int(qty), self.now, self.now + self.entry)
        self.shadows.append(s)
        self._push(s.arrive, ARRIVE, s.vid)
        return s.vid

    def cancel(self, vid: int) -> None:
        s = self.shadows[vid]
        if s.cancel_sent == float("inf"):
            s.cancel_sent, s.cancel_arrive = self.now, self.now + self.entry
            self._push(s.cancel_arrive, CANCEL, vid)

    def working(self) -> list[Shadow]:
        return [s for s in self.shadows if s.status in ("sent", "working") and s.cancel_sent == float("inf")]

    # ------------------------------------------------------------------ loop
    def _snapshot(self) -> dict:
        b = self.book
        bid, ask = b.best(1), b.best(-1)
        return {"bid": bid, "ask": ask, "bid_qty": b.size(1, bid) if bid is not None else 0,
                "ask_qty": b.size(-1, ask) if ask is not None else 0}

    def run(self) -> ReplayResult:
        m = self.msgs
        n = len(m)
        mid_t, mid = np.empty(n), np.empty(n)
        i = 0
        while i < n or self._q:
            t_next = float(m["t"][i]) if i < n else float("inf")
            if self._q and self._q[0][0] <= t_next:
                t, kind, _, payload = heapq.heappop(self._q)
                self.now = t
                if kind == ARRIVE:
                    s = self.shadows[payload]
                    if s.status == "sent":
                        self.tracker.join(self.book, s)
                        self.active[s.vid] = s
                elif kind == CANCEL:
                    s = self.shadows[payload]
                    if s.status in ("sent", "working"):
                        s.status = "cancelled"
                        self.active.pop(s.vid, None)
                else:
                    self.strategy.on_market(self, t, payload)
                continue
            msg = m[i]
            self.now = t_next
            for s, q in self.tracker.on_message(self.book, msg, list(self.active.values())):
                if q <= 0:
                    continue
                s.filled += q
                s.fills.append((t_next, q))
                if s.remaining <= 0:
                    s.status = "filled"
                    self.active.pop(s.vid, None)
                self.position += s.side * q
                self.cash -= s.side * q * s.price
                self.fills.append((t_next, s.vid, s.side, q, s.price))
                self.strategy.on_fill(self, s.vid, t_next, q, s.price)
            self.book.apply(msg)
            snap = self._snapshot()
            mid_t[i] = t_next
            both = snap["bid"] is not None and snap["ask"] is not None
            mid[i] = 0.5 * (snap["bid"] + snap["ask"]) if both else np.nan
            self._push(t_next + self.data, SEE, snap)
            i += 1
        ok = ~np.isnan(mid)
        return ReplayResult(self.shadows, self.fills, self.position, self.cash, mid_t[ok], mid[ok])


def track_fifo(msgs, orders) -> list[tuple[int, float, int]]:
    """orders: (vid, side, price, qty, arrive, cancel_arrive). Fills [(vid, t, qty)] under the 'fifo' model, with
    arrivals and cancellations taking effect before any market message at the same time."""
    book, tracker = Book(), QueueTracker("fifo")
    shadows = [Shadow(int(v), int(sd), int(p), int(q), a, a, cancel_arrive=c) for v, sd, p, q, a, c in orders]
    events = [(s.arrive, 0, s.vid) for s in shadows]
    events += [(s.cancel_arrive, 1, s.vid) for s in shadows if s.cancel_arrive < float("inf")]
    events.sort()
    out, j, active = [], 0, {}
    for msg in msgs:
        t = float(msg["t"])
        while j < len(events) and events[j][0] <= t:
            _, kind, vid = events[j]
            s = shadows[vid]
            if kind == 0 and s.status == "sent":
                tracker.join(book, s)
                active[vid] = s
            elif kind == 1 and s.status in ("sent", "working"):
                s.status = "cancelled"
                active.pop(vid, None)
            j += 1
        for s, q in tracker.on_message(book, msg, list(active.values())):
            if q > 0:
                s.filled += q
                if s.remaining <= 0:
                    s.status = "filled"
                    active.pop(s.vid, None)
                out.append((s.vid, t, q))
        book.apply(msg)
    return out
