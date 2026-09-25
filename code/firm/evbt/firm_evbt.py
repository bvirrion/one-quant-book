"""firm.evbt -- the level-2 (event-driven) backtester on bars (build of One Quant Book 7, chapter 17).

One instrument, a simulated clock and a priority queue of events: the close of each bar, order submissions and their
acknowledgement after an order-entry latency, cancellations (also delayed), and corporate actions (splits). A
strategy reacts to bars and fills through a context that submits and cancels orders; an order manager keeps each
order's lifecycle; a pluggable fill model decides, bar by bar, whether and how much of each working order fills. The
run is deterministic: events are ordered by time and then by sequence number, and nothing is random unless a fill
model is given a seeded generator. The result is a firm.vecbt.BacktestResult (one name) plus the orders and fills.

API (stable):
    Order        oid, side (+1 buy, -1 sell), qty, kind ('market' or 'limit'), price, submitted, active (time it
                 can first fill), status ('pending', 'working', 'partial', 'filled', 'cancelled'), filled, avg_price,
                 history [(time, status)]
    Fill         oid, t, qty (signed), price, fee
    TouchFill()                          a limit order fills in full when the bar trades at its price
    PenetrationFill(ticks)               ... only when the bar trades `ticks` beyond its price
    VolumeCapFill(inner, participation)  the inner model's fill, capped at a share of the bar's volume
    Strategy     on_bar(ctx, i, bar) and on_fill(ctx, fill); ctx.submit(side, qty, kind, price), ctx.cancel(oid),
                 ctx.position, ctx.cash, ctx.working(), ctx.now
    Engine(bars, strategy, fill_model, latency, fee, capital, splits, policy).run() -> (BacktestResult, orders, fills)
    policy: 'conservative' (an order fills in a bar only if it was live for the whole bar) or 'optimistic' (if it was
    live at any moment of the bar): a bar hides when, within it, the price reached the order
    bars: a firm.bars.Bars (start, end, open, high, low, close, volume), prices as traded; splits: [(time, ratio)]
    multiply the position and the working orders' quantities by the ratio and divide their prices by it
"""
from __future__ import annotations

import heapq
import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vecbt"))
from firm_vecbt import BacktestResult  # noqa: E402

BAR, SUBMIT, ACK, CANCEL, SPLIT = 0, 1, 2, 3, 4          # at equal times: bars first, then order events


@dataclass
class Order:
    oid: int
    side: int
    qty: float
    kind: str
    price: float | None
    submitted: float
    active: float = float("inf")
    cancelled_at: float = float("inf")
    status: str = "pending"
    filled: float = 0.0
    avg_price: float = 0.0
    history: list = field(default_factory=list)

    @property
    def remaining(self) -> float:
        return self.qty - self.filled


@dataclass
class Fill:
    oid: int
    t: float
    qty: float
    price: float
    fee: float


class TouchFill:
    """Limit: fills in full at its price if the bar's range reaches it. Market: fills at the bar's open."""

    def fill(self, order: Order, bar: dict, used: float = 0.0):
        if order.kind == "market":
            return order.remaining, bar["open"]
        if order.side > 0 and bar["low"] <= order.price or order.side < 0 and bar["high"] >= order.price:
            return order.remaining, order.price
        return None


class PenetrationFill(TouchFill):
    def __init__(self, ticks: float = 1.0):
        self.ticks = ticks

    def fill(self, order: Order, bar: dict, used: float = 0.0):
        if order.kind == "market":
            return order.remaining, bar["open"]
        k = self.ticks
        if order.side > 0 and bar["low"] <= order.price - k or order.side < 0 and bar["high"] >= order.price + k:
            return order.remaining, order.price
        return None


class VolumeCapFill:
    def __init__(self, inner, participation: float = 0.1):
        self.inner, self.participation = inner, participation

    def fill(self, order: Order, bar: dict, used: float = 0.0):
        f = self.inner.fill(order, bar)
        if f is None:
            return None
        room = self.participation * bar["volume"] - used
        q = min(f[0], max(room, 0.0))
        return (q, f[1]) if q > 0 else None


class Strategy:
    def on_bar(self, ctx, i: int, bar: dict) -> None:
        pass

    def on_fill(self, ctx, fill: Fill) -> None:
        pass


class Engine:
    def __init__(self, bars, strategy: Strategy, fill_model=None, latency: float = 0.0, fee: float = 0.0,
                 capital: float = 1.0, splits=(), policy: str = "conservative"):
        self.bars, self.strategy = bars, strategy
        self.fill_model = fill_model or TouchFill()
        self.latency, self.fee, self.capital = latency, fee, capital
        self.splits, self.policy = list(splits), policy
        self.orders: dict[int, Order] = {}
        self.fills: list[Fill] = []
        self.position, self.cash, self.now = 0.0, capital, 0.0
        self._q: list = []
        self._seq = 0

    # --------------------------------------------------------------------------------------- context for strategies
    def _push(self, t: float, kind: int, payload) -> None:
        heapq.heappush(self._q, (t, kind, self._seq, payload))
        self._seq += 1

    def submit(self, side: int, qty: float, kind: str = "limit", price: float | None = None) -> int:
        oid = len(self.orders)
        o = Order(oid, side, qty, kind, price, self.now, history=[(self.now, "pending")])
        self.orders[oid] = o
        self._push(self.now + self.latency, ACK, oid)
        return oid

    def cancel(self, oid: int) -> None:
        self._push(self.now + self.latency, CANCEL, oid)

    def working(self) -> list[Order]:
        return [o for o in self.orders.values() if o.status in ("pending", "working", "partial")]

    # --------------------------------------------------------------------------------------- the loop
    def _status(self, o: Order, s: str, t: float) -> None:
        o.status = s
        o.history.append((t, s))

    def _live(self, o: Order, bar: dict) -> bool:
        if self.policy == "conservative":
            return o.active <= bar["start"] and o.cancelled_at >= bar["end"] and o.status != "cancelled"
        return o.active < bar["end"] and o.cancelled_at > bar["start"]

    def _match(self, i: int, bar: dict) -> None:
        used = 0.0
        cand = [o for o in self.orders.values() if o.remaining > 1e-12 and o.status not in ("filled", "pending")]
        for o in sorted(cand, key=lambda o: o.oid):
            if not self._live(o, bar):
                continue
            f = self.fill_model.fill(o, bar, used)
            if f is None:
                continue
            q, px = f
            used += q
            o.avg_price = (o.avg_price * o.filled + px * q) / (o.filled + q)
            o.filled += q
            self._status(o, "filled" if o.remaining <= 1e-12 else "partial", bar["end"])
            fee = self.fee * q
            self.position += o.side * q
            self.cash -= o.side * q * px + fee
            fl = Fill(o.oid, bar["end"], o.side * q, px, fee)
            self.fills.append(fl)
            self.strategy.on_fill(self, fl)

    def run(self):
        b = self.bars
        n = len(b.close)
        for i in range(n):
            self._push(float(b.end[i]), BAR, i)
        for t, ratio in self.splits:
            self._push(float(t), SPLIT, ratio)
        equity, pos, fees, trades = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
        while self._q:
            t, kind, _, payload = heapq.heappop(self._q)
            self.now = t
            if kind == ACK:
                o = self.orders[payload]
                if o.status == "pending":
                    o.active = t
                    self._status(o, "working", t)
            elif kind == CANCEL:
                o = self.orders[payload]
                if o.status in ("pending", "working", "partial"):
                    o.cancelled_at = t
                    self._status(o, "cancelled", t)
            elif kind == SPLIT:
                self.position *= payload
                for o in self.working():
                    o.qty *= payload
                    o.filled *= payload
                    if o.price is not None:
                        o.price /= payload
            else:
                i = payload
                bar = {"start": float(b.start[i]), "end": float(b.end[i]), "open": float(b.open[i]),
                       "high": float(b.high[i]), "low": float(b.low[i]), "close": float(b.close[i]),
                       "volume": float(b.volume[i])}                  # as traded: a split shows in the prices
                before = len(self.fills)
                self._match(i, bar)
                new = self.fills[before:]
                fees[i] = sum(f.fee for f in new)
                trades[i] = sum(f.qty * f.price for f in new)
                equity[i] = self.cash + self.position * bar["close"]
                pos[i] = self.position * bar["close"]
                self.strategy.on_bar(self, i, bar)
        prev = np.r_[self.capital, equity[:-1]]
        net = equity / prev - 1.0
        cost = fees / prev
        res = BacktestResult(np.asarray(b.end), np.array([0]), (pos / equity)[:, None], (trades / prev)[:, None],
                             net + cost, {"trading": cost, "borrow": np.zeros(n), "financing": np.zeros(n)}, net,
                             equity / self.capital, {"level": 2, "latency": self.latency,
                                                     "fill_model": type(self.fill_model).__name__})
        return res, list(self.orders.values()), self.fills
