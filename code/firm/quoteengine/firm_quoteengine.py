"""firm.quoteengine -- from target quotes to orders (One Quant Book 11, chapter 10).

A quoting policy says where it wants to be: on each side a ladder of (price, size) levels. The engine turns each new
target into the fewest messages that get there, under the venue's priority rules and a message budget, and keeps
the state of every order it has sent. Python reference; cpp/firm_quoteengine.hpp and rust/src/lib.rs implement the
same algorithm and produce the same action log on data/fixture_*.csv.

Rules of update(t, side, targets), for one side, targets a list of (price, qty) in ticks and shares:
  1. Working orders are visited in price priority (best first), then by order id. Orders waiting for an
     acknowledgement are left alone.
  2. An order whose price is a target price covers that target: if it holds at least `min_size` more than the target,
     it is amended down (a size decrease keeps its queue priority); if it holds at least `min_size` less, a new
     order is sent at that price for the difference (increasing an order's size would lose its priority).
  3. An order at no target price is kept, and covers the nearest uncovered target, if it is within `min_move - 1`
     ticks of it (hysteresis); otherwise it is cancelled.
  4. Every target not covered gets a new order.
  5. Actions are issued cancels first, then amendments, then new orders, each taking one token from a token bucket
     of `rate` tokens a second and depth `burst`; when the bucket is empty the rest are dropped and re-derived at the
     next update (the target, not the queue of old actions, is what matters).
Order states: 'pending_new' -> ack -> 'live'; amend -> 'pending_amend' -> ack -> 'live'; cancel -> 'pending_cancel'
-> ack -> gone; a fill reduces the leaves and removes the order at zero, in any state (a fill that arrives while the
cancel is in flight is a cancel--fill race, counted).

API (stable):
    TokenBucket(rate, burst).take(t) -> bool
    QuoteEngine(min_move=1, min_size=1, rate=inf, burst=inf)
        .update(t, side, targets) -> list of actions ('new', oid, side, price, qty) | ('amend', oid, qty) |
                                     ('cancel', oid)
        .ack(oid), .fill(oid, qty), .orders (dict), .stats (dict: new, amend, cancel, dropped, fills, races)
"""
from __future__ import annotations

import math
from dataclasses import dataclass


class TokenBucket:
    def __init__(self, rate: float = math.inf, burst: float = math.inf):
        self.rate, self.burst = rate, burst
        self.tokens, self.t = burst, None

    def take(self, t: float) -> bool:
        if math.isinf(self.rate):
            return True
        if self.t is not None:
            self.tokens = min(self.burst, self.tokens + self.rate * (t - self.t))
        self.t = t
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


@dataclass
class Order:
    oid: int
    side: int
    price: int
    leaves: int
    state: str


class QuoteEngine:
    def __init__(self, min_move: int = 1, min_size: int = 1, rate: float = math.inf, burst: float = math.inf):
        self.min_move, self.min_size = min_move, min_size
        self.bucket = TokenBucket(rate, burst)
        self.orders: dict[int, Order] = {}
        self.next_oid = 0
        self.stats = {"new": 0, "amend": 0, "cancel": 0, "dropped": 0, "fills": 0, "races": 0}

    def update(self, t: float, side: int, targets) -> list:
        targets = [(int(p), int(q)) for p, q in targets if q > 0]
        covered = [False] * len(targets)
        cancels, amends, news = [], [], []
        mine = sorted((o for o in self.orders.values() if o.side == side),
                      key=lambda o: (-side * o.price, o.oid))
        for o in mine:
            if o.state != "live":
                if o.state != "pending_cancel":                      # in flight: it still covers its price
                    for k, (p, _) in enumerate(targets):
                        if not covered[k] and p == o.price:
                            covered[k] = True
                            break
                continue
            k = next((k for k, (p, _) in enumerate(targets) if not covered[k] and p == o.price), None)
            if k is not None:
                covered[k] = True
                q = targets[k][1]
                if o.leaves - q >= self.min_size:
                    amends.append(("amend", o.oid, q))
                elif q - o.leaves >= self.min_size:
                    news.append((side, o.price, q - o.leaves))
                continue
            near = [k for k, (p, _) in enumerate(targets) if not covered[k] and abs(p - o.price) < self.min_move]
            if near:
                k = min(near, key=lambda k: (abs(targets[k][0] - o.price), k))
                covered[k] = True
                continue
            cancels.append(("cancel", o.oid))
        for k, (p, q) in enumerate(targets):
            if not covered[k]:
                news.append((side, p, q))
        out = []
        for a in cancels + amends:
            if not self.bucket.take(t):
                self.stats["dropped"] += 1
                continue
            o = self.orders[a[1]]
            if a[0] == "cancel":
                o.state = "pending_cancel"
                self.stats["cancel"] += 1
            else:
                o.state, o.leaves = "pending_amend", a[2]
                self.stats["amend"] += 1
            out.append(a)
        for sd, p, q in news:
            if not self.bucket.take(t):
                self.stats["dropped"] += 1
                continue
            self.next_oid += 1
            self.orders[self.next_oid] = Order(self.next_oid, sd, p, q, "pending_new")
            self.stats["new"] += 1
            out.append(("new", self.next_oid, sd, p, q))
        return out

    def ack(self, oid: int) -> None:
        o = self.orders.get(oid)
        if o is None:
            return
        if o.state == "pending_cancel":
            del self.orders[oid]
        else:
            o.state = "live"

    def fill(self, oid: int, qty: int) -> None:
        o = self.orders.get(oid)
        if o is None:
            return
        self.stats["fills"] += 1
        if o.state == "pending_cancel":
            self.stats["races"] += 1
        o.leaves -= qty
        if o.leaves <= 0:
            del self.orders[oid]
