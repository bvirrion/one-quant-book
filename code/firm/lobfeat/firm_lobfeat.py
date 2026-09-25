"""firm.lobfeat -- streaming order-book features (build of One Quant Book 7, chapter 8).

A book rebuilt order by order from firm.tape messages (add, cancel, execute), and after every message the features
of chapter 8: the best quotes and sizes, queue imbalance at the touch, depth imbalance over the first L levels, the
order-flow imbalance increment of Cont, Kukanov and Stoikov and its running sum, the weighted mid, and a microprice
(the mid plus an adjustment looked up by imbalance bucket, estimated beforehand). This Python module is the
reference; cpp/firm_lobfeat.hpp and rust/src/lib.rs implement the same engine and are checked against the same
fixture (data/fixture_msgs.csv, data/fixture_expected.csv), row by row.

Prices are integer ticks and sizes integer shares; the features are double precision with the same operation order
in all three languages.

API (stable):
    Engine(levels=5, g=None)                 g: microprice adjustments (ticks) for `len(g)` imbalance buckets
    Engine.on(kind, oid, side, price, qty)   apply one message; returns the Features after it
    Features: bid, ask, bid_qty, ask_qty, imbalance, depth_imbalance, ofi (increment), ofi_cum, wmid, micro
    run(msgs, levels=5, g=None) -> dict      numpy arrays of every feature over a Tape.msgs array
    bucket(imbalance, n)                     bucket index of an imbalance in [-1, 1] for n equal buckets
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Features:
    bid: int
    ask: int
    bid_qty: int
    ask_qty: int
    imbalance: float
    depth_imbalance: float
    ofi: int
    ofi_cum: int
    wmid: float
    micro: float


def bucket(imbalance: float, n: int) -> int:
    return min(n - 1, int((imbalance + 1.0) / 2.0 * n))


class Engine:
    def __init__(self, levels: int = 5, g=None):
        self.levels = levels
        self.g = list(g) if g is not None else []
        self.orders: dict[int, list] = {}              # oid -> [side, price, qty]
        self.book = {1: {}, -1: {}}                    # side -> price -> total qty
        self.prev = None                               # (bid, bid_qty, ask, ask_qty) before the message
        self.ofi_cum = 0

    def _top(self):
        b, a = self.book[1], self.book[-1]
        if not b or not a:
            return None
        bb, ba = max(b), min(a)
        return bb, b[bb], ba, a[ba]

    def _depth(self, side: int) -> int:
        lv = self.book[side]
        prices = sorted(lv, reverse=(side == 1))[: self.levels]
        return sum(lv[p] for p in prices)

    def on(self, kind: str, oid: int, side: int, price: int, qty: int):
        lv = self.book[side]
        if kind == "A":
            self.orders[oid] = [side, price, qty]
            lv[price] = lv.get(price, 0) + qty
        else:
            o = self.orders[oid]
            o[2] -= qty
            lv[price] -= qty
            if o[2] == 0:
                del self.orders[oid]
            if lv[price] == 0:
                del lv[price]
        top = self._top()
        if top is None:
            return None
        bb, qb, ba, qa = top
        e = 0
        if self.prev is not None:
            pb, pqb, pa, pqa = self.prev
            e = ((qb if bb >= pb else 0) - (pqb if bb <= pb else 0)
                 - (qa if ba <= pa else 0) + (pqa if ba >= pa else 0))
        self.prev = top
        self.ofi_cum += e
        imb = (qb - qa) / (qb + qa)
        db, da = self._depth(1), self._depth(-1)
        dimb = (db - da) / (db + da)
        mid = 0.5 * (bb + ba)
        wmid = (ba * qb + bb * qa) / (qb + qa)
        micro = mid + (self.g[bucket(imb, len(self.g))] if self.g and ba - bb == 1 else 0.0)
        return Features(bb, ba, qb, qa, imb, dimb, e, self.ofi_cum, wmid, micro)


FIELDS = ("bid", "ask", "bid_qty", "ask_qty", "imbalance", "depth_imbalance", "ofi", "ofi_cum", "wmid", "micro")


def run(msgs, levels: int = 5, g=None) -> dict:
    eng = Engine(levels, g)
    rows = []
    for m in msgs:
        f = eng.on(m["kind"].decode() if isinstance(m["kind"], bytes) else str(m["kind"]), int(m["oid"]),
                   int(m["side"]), int(m["price"]), int(m["qty"]))
        rows.append(None if f is None else tuple(getattr(f, k) for k in FIELDS))
    out = {k: np.full(len(rows), np.nan) for k in FIELDS}
    for i, r in enumerate(rows):
        if r is not None:
            for k, v in zip(FIELDS, r, strict=True):
                out[k][i] = v
    return out
