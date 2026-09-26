"""The quoting engine (One Quant Book 11, chapter 10).

A one-lot-per-level ladder on firm.tape driven through firm.quoteengine: the quoter's target is the others' best bid
and ask and, for a ladder of depth d, the d - 1 prices behind each; the engine turns targets into messages, with
hysteresis (min_move) and a token-bucket throttle. On the tape there is no modify message: an amendment is sent as a
cancel and a new order (firm.exchsim's replace message keeps priority on a size decrease). Acknowledgements are
simulated at the order-entry latency. Four configurations on four twenty-minute sessions: messages, fills, orders per
fill, cancel-fill races, queue places kept across price moves, ten-second mark-out and edge.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys
from dataclasses import replace

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for dep in ("mmharness", "quoteengine", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_mmharness as mh  # noqa: E402
import firm_quoteengine as qe  # noqa: E402
import firm_tape as ft  # noqa: E402

LOT = 100
SESSION = 1200.0
SEEDS = (141, 142, 143, 144)
ENTRY = 0.0005


class EngineQuoter:
    """A ladder of `depth` one-lot levels per side at and behind the others' best prices, through a QuoteEngine."""

    def __init__(self, depth: int = 1, min_move: int = 1, rate: float = float("inf"), burst: float = float("inf"),
                 limit: int = 5):
        self.depth, self.limit = depth, limit
        self.eng = qe.QuoteEngine(min_move=min_move, min_size=LOT, rate=rate, burst=burst)
        self.cid = {}                  # engine oid -> harness cid
        self.oid = {}                  # harness cid -> engine oid
        self.born = {}                 # engine oid -> time sent
        self.pending_ack: list = []    # (due, oid)
        self.fill_age: list = []

    def on_start(self, ctx):
        pass

    def _apply(self, ctx, acts, t):
        for a in acts:
            if a[0] == "new":
                _, oid, side, px, q = a
                c = ctx.send(side, px, q)
                self.cid[oid], self.oid[c], self.born[oid] = c, oid, t
            elif a[0] == "cancel":
                ctx.cancel(self.cid[a[1]])
            else:                                             # amend: cancel and resend on the tape
                oid, q = a[1], a[2]
                o = self.eng.orders[oid]
                ctx.cancel(self.cid[oid])
                c = ctx.send(o.side, o.price, q)
                self.cid[oid], self.oid[c] = c, oid
            self.pending_ack.append((t + ENTRY, a[1]))

    def on_market(self, ctx, t, top):
        due = [o for d, o in self.pending_ack if d <= t]
        self.pending_ack = [(d, o) for d, o in self.pending_ack if d > t]
        for o in due:
            self.eng.ack(o)
        x = ctx.external(top)
        pos = ctx.position // LOT
        bids = [(int(x["bid"]) - k, LOT) for k in range(self.depth)] if pos < self.limit else []
        asks = [(int(x["ask"]) + k, LOT) for k in range(self.depth)] if pos > -self.limit else []
        for side, tg in ((1, bids), (-1, asks)):
            self._apply(ctx, self.eng.update(t, side, tg), t)

    def on_fill(self, ctx, fill):
        oid = self.oid.get(fill.cid)
        if oid is not None:
            self.fill_age.append(fill.t - self.born.get(oid, fill.t))
            self.eng.fill(oid, fill.qty)


CONFIGS = {"one level": dict(depth=1), "three levels": dict(depth=3),
           "three levels, hysteresis": dict(depth=3, min_move=2),
           "three levels, throttle 2/s": dict(depth=3, rate=2.0, burst=5.0)}


def cfg(seed: int) -> ft.TapeConfig:
    return replace(ft.TapeConfig(), seed=seed, seconds=SESSION, news_at=None)


@functools.cache
def run(name: str, seed: int):
    q = EngineQuoter(**CONFIGS[name])
    r = mh.run_tape(q, cfg(seed), latency=mh.Latency(entry=ENTRY))
    return r, q


def compare() -> dict:
    out = {}
    for name in CONFIGS:
        rows = [run(name, s) for s in SEEDS]
        rs, qs = [x[0] for x in rows], [x[1] for x in rows]
        vol = sum(r.volume() for r in rs)
        fills = sum(len(r.fills) for r in rs)
        mo = sum(float(r.markouts([10.0])[:, 0] @ r.fills["qty"]) for r in rs)
        msgs = sum(r.messages for r in rs)
        ages = np.concatenate([np.array(q.fill_age) for q in qs])
        st = {k: sum(q.eng.stats[k] for q in qs) for k in ("new", "cancel", "amend", "dropped", "races")}
        per_hour = 3600.0 / (SESSION * len(SEEDS))
        out[name] = {"messages_h": msgs * per_hour, "fills_h": fills * per_hour, "orders_per_fill": msgs / fills,
                     "races_h": st["races"] * per_hour, "dropped_h": st["dropped"] * per_hour,
                     "markout": mo / vol, "edge_h": mo * 0.01 * per_hour,
                     "median_age": float(np.median(ages)), "old_share": float(np.mean(ages > 5.0))}
    return out


def fixture_stats(**params) -> dict:
    """Replay the component's 3,000-event fixture through an engine with other parameters (exercise 7)."""
    import csv
    p = {"min_move": 2, "min_size": 100, "rate": 20.0, "burst": 5.0} | params
    e = qe.QuoteEngine(**p)
    with open(ROOT / "firm" / "quoteengine" / "data" / "fixture_events.csv") as f:
        for r in csv.DictReader(f):
            if r["kind"] == "U":
                tg = [tuple(int(x) for x in s.split(":")) for s in r["targets"].split("|")] if r["targets"] else []
                e.update(float(r["t"]), int(r["side"]), tg)
            elif r["kind"] == "A":
                e.ack(int(r["oid"]))
            else:
                e.fill(int(r["oid"]), int(r["qty"]))
    return dict(e.stats)
