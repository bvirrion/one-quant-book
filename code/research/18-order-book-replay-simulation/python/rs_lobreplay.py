"""Order-book replay simulation (One Quant Book 7, chapter 18).

Two strategies replayed through firm.lobreplay on firm.tape's market-by-order messages.
(1) A touch quoter on one-hour sessions (seeds 31 and 32): it keeps one lot (100 shares) on the best bid and one on
the best ask, moving an order when its price is no longer the best, within five lots of inventory; under the three
queue-position models and order-entry latencies from zero to five seconds (market-data latency equal to half of it).
(2) Chapter 17's bar quoter replayed at level 3 on the same four 6.5-hour days: at each minute's end it rests one lot
one tick below and one above the last trade, under the 'fifo' model, to locate the answer that chapter's fill models
bracket. P&L in dollars (prices are in cents), inventory marked at the last mid. NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("lobreplay", "tape"):
    sys.path.insert(0, str(ROOT / c))
from firm_lobreplay import Replay, Strategy  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

LOT, MAX_LOTS = 100, 5
HOUR_SEEDS, DAY_SEEDS = (31, 32), (17, 18, 19, 20)
LATENCIES = (0.0, 0.05, 0.2, 1.0, 5.0)


@functools.lru_cache(maxsize=8)
def tape(seed: int, seconds: float):
    if seconds == 23_400.0:
        return simulate(TapeConfig(seconds=seconds, news_at=None, u_shape=1.5, seed=seed))
    return simulate(TapeConfig(seconds=seconds, news_at=None, seed=seed))


class TouchQuoter(Strategy):
    def __init__(self):
        self.buy = self.sell = None

    def _keep(self, ctx, side: int, price, vid):
        if price is None:
            return vid
        allowed = ctx.position < MAX_LOTS * LOT if side > 0 else ctx.position > -MAX_LOTS * LOT
        sh = ctx.shadows[vid] if vid is not None else None
        live = sh is not None and sh.status in ("sent", "working") and sh.cancel_sent == float("inf")
        if live and (not allowed or ctx.shadows[vid].price != price):
            ctx.cancel(vid)
            live = False
        if not live and allowed:
            return ctx.send(side, price, LOT)
        return vid if live else None

    def on_market(self, ctx, t, snap):
        self.buy = self._keep(ctx, +1, snap["bid"], self.buy)
        self.sell = self._keep(ctx, -1, snap["ask"], self.sell)


class BarQuoter(Strategy):
    """Chapter 17's quoter: at each minute's end, cancel and rest one lot one tick either side of the last trade."""

    def __init__(self, trades):
        self.t, self.px = trades["t"], trades["price"]
        self.next = 60.0

    def on_market(self, ctx, t, snap):
        if t < self.next:
            return
        self.next += 60.0 * (1 + (t - self.next) // 60.0)
        k = np.searchsorted(self.t, t, side="right") - 1
        if k < 0:
            return
        last = int(self.px[k])
        for s in ctx.working():
            ctx.cancel(s.vid)
        if ctx.position < MAX_LOTS * LOT:
            ctx.send(+1, last - 1, LOT)
        if ctx.position > -MAX_LOTS * LOT:
            ctx.send(-1, last + 1, LOT)


def _stats(res, trades, horizon: float = 10.0):
    mt, mid = res.mid_t, res.mid
    mo = []
    for t, _, side, _q, px in res.fills:
        j = np.searchsorted(mt, t + horizon, side="right") - 1
        mo.append(side * (mid[j] - px))
    lots = sum(q for *_, q, _ in res.fills) / LOT
    at_px = trades["qty"].sum()
    return {"fills": len(res.fills), "lots": float(lots), "pnl": res.pnl() / 100.0,
            "markout": float(np.mean(mo)) if mo else float("nan"), "share": float(lots * LOT / at_px)}


def touch_grid(models=("front", "fifo", "prob"), latencies=LATENCIES):
    """Mean over the hour sessions of fills, lots, P&L, 10-second mark-out (ticks) and share of traded volume."""
    out = {}
    for model in models:
        for lat in latencies:
            rows = []
            for seed in HOUR_SEEDS:
                tp = tape(seed, 3600.0)
                res = Replay(tp.msgs, TouchQuoter(), model, entry_latency=lat, data_latency=lat / 2).run()
                rows.append(_stats(res, tp.trades))
            out[(model, lat)] = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
    return out


def bar_quoter_level3(model: str = "fifo"):
    """Chapter 17's quoter at level 3 on its four days: lots filled, orders sent, P&L and mark-out, per day."""
    rows = []
    for seed in DAY_SEEDS:
        tp = tape(seed, 23_400.0)
        res = Replay(tp.msgs, BarQuoter(tp.trades), model).run()
        st = _stats(res, tp.trades, horizon=300.0)
        st["orders"] = len(res.shadows)
        rows.append(st)
    return rows


def impact_bound(stats: dict, kyle_lambda: float = 0.10) -> float:
    """A bound on the P&L the shadow fills overstate: each lot we trade would, by Kyle's lambda (ticks per 100
    shares, chapter 9), have moved the price against us by lambda / 2 on average; in dollars per session."""
    return stats["lots"] * LOT * (kyle_lambda / 2) / 100.0


def see_or_act(latency: float = 1.0):
    """Exercise 7: the fifo touch quoter with only the order-entry latency, and with only the market-data latency."""
    out = {}
    for name, entry, data in (("act late", latency, 0.0), ("see late", 0.0, latency)):
        rows = []
        for seed in HOUR_SEEDS:
            tp = tape(seed, 3600.0)
            res = Replay(tp.msgs, TouchQuoter(), "fifo", entry_latency=entry, data_latency=data).run()
            rows.append(_stats(res, tp.trades))
        out[name] = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
    return out
