"""Queue-reactive models and large-tick assets (One Quant Book 11, chapter 5).

(1) The simulated market (firm.tape) as a large-tick asset: how often the spread is one tick, and the queue-reactive
intensities of its best queues (firm.qreactive.estimate). (2) The value of a place in the bid queue in the fitted
queue-reactive model, at the front and at the back, by the sizes of the two best queues (firm.qreactive.order_value).
(3) Rules to join and to leave a queue, tested on the simulated market through firm.mmharness: a one-lot Quoter that
rests on a side only while that side's share of the two best queues (others' orders only) is at least theta, and, for
the exit rule, keeps a resting order it is near the front of.
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
for dep in ("mmharness", "qreactive", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_mmharness as mh  # noqa: E402
import firm_qreactive as qr  # noqa: E402
import firm_tape as ft  # noqa: E402

LOT = 100
EST_SEED = 61
SESSION = 1200.0
SEEDS = (71, 72, 73, 74, 75, 76)


def cfg(seed: int, seconds: float = SESSION) -> ft.TapeConfig:
    return replace(ft.TapeConfig(), seed=seed, seconds=seconds, news_at=None)


@functools.cache
def fitted() -> dict:
    tp = ft.simulate(cfg(EST_SEED, 3600.0))
    est = qr.estimate(tp.msgs, tp.top, LOT, 30, tp.n_open)
    top = tp.top[tp.n_open:]
    spread = top["ask"] - top["bid"]
    dt = np.diff(top["t"].astype(float), append=float(tp.cfg.seconds))
    est["one_tick"] = float(dt[spread == 1].sum() / dt.sum())
    q = np.concatenate([top["bid_qty"], top["ask_qty"]]) / LOT
    w = np.concatenate([dt, dt])
    est["median_queue"] = float(np.median(np.repeat(q, np.maximum((w * 10).astype(int), 0))))
    return est


def model() -> qr.QRModel:
    e = fitted()
    return qr.QRModel(e["L"], e["C"], e["M"], e["regen"])


QS = (2, 5, 10, 20)


@functools.cache
def values() -> dict:
    return qr.value_table(model(), QS, H=10.0, tmax=60.0, paths=4000, seed=5)


class QueueQuoter:
    """One lot per side at the others' best price. Queue-join rule: post on a side only if its share of the two best
    queues (others' orders) is at least theta. Queue-exit rule, by mode: 'stay' keeps a resting order whatever the
    share; 'leave' cancels it when the share falls below theta; 'front' cancels it then unless fewer than `front` lots
    are ahead of it. An order whose price is no longer the best is always cancelled."""

    wants_queue_position = True

    def __init__(self, theta: float, mode: str = "leave", front: int = 2, limit: int = 5):
        self.theta, self.mode, self.front, self.limit = theta, mode, front, limit

    def on_start(self, ctx):
        pass

    def on_market(self, ctx, t, top):
        x = ctx.external(top)
        qb, qa = max(int(x["bid_qty"]), 0), max(int(x["ask_qty"]), 0)
        share = {1: qb / (qb + qa) if qb + qa else 0.5}
        share[-1] = 1.0 - share[1]
        best = {1: int(x["bid"]), -1: int(x["ask"])}
        room = {1: ctx.position < self.limit * LOT, -1: ctx.position > -self.limit * LOT}
        want = {s: share[s] >= self.theta and room[s] for s in (1, -1)}
        for cid, w in ctx.working().items():
            if w.price != best[w.side] or want[w.side] or not room[w.side]:
                continue
            a = ctx.ahead(cid)
            if self.mode == "stay" or (self.mode == "front" and a is not None and a < self.front * LOT):
                want[w.side] = True
        ctx.quote(best[1], LOT if want[1] else 0, best[-1], LOT if want[-1] else 0)

    def on_fill(self, ctx, fill):
        pass


RULES = {"always": (0.0, "leave"), "join 0.3, stay": (0.3, "stay"), "join 0.3, leave": (0.3, "leave"),
         "join 0.3, leave unless front": (0.3, "front")}


@functools.cache
def run(rule: str, seed: int) -> mh.Result:
    theta, mode = RULES[rule]
    return mh.run_tape(QueueQuoter(theta, mode), cfg(seed))


def compare() -> dict:
    out = {}
    for rule in RULES:
        rs = [run(rule, s) for s in SEEDS]
        vol = sum(r.volume() for r in rs)
        mo = np.concatenate([r.markouts([10.0])[:, 0] * r.fills["qty"] for r in rs if len(r.fills)])
        pnl = [r.pnl() for r in rs]
        out[rule] = {"pnl": float(np.mean(pnl)), "sd": float(np.std(pnl, ddof=1)), "shares": vol / len(rs),
                     "markout10": float(mo.sum() / vol), "edge10": float(mo.sum() / len(rs) * 0.01),
                     "messages": float(np.mean([r.messages for r in rs]))}
    return out


THETAS = (0.0, 0.2, 0.3, 0.4, 0.5)


@functools.cache
def sweep_run(theta: float, seed: int) -> mh.Result:
    return mh.run_tape(QueueQuoter(theta, "leave"), cfg(seed))


def sweep() -> dict:
    """The join-and-leave rule for several thresholds: shares a session, ten-second mark-out per share (ticks) and
    ten-second edge a session ($)."""
    out = {}
    for th in THETAS:
        rs = [sweep_run(th, s) for s in SEEDS]
        vol = sum(r.volume() for r in rs)
        mo = sum(float((r.markouts([10.0])[:, 0] * r.fills["qty"]).sum()) for r in rs if len(r.fills))
        out[th] = {"shares": vol / len(rs), "markout10": mo / vol, "edge10": mo / len(rs) * 0.01}
    return out
