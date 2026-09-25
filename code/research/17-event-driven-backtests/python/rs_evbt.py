"""Event-driven backtests (One Quant Book 7, chapter 17).

A passive bar strategy on one-minute bars of firm.tape (four simulated days of 6.5 hours, seeds 17 to 20): at every
bar's close it cancels its orders and rests a buy limit one tick below the close and a sell limit one tick above,
within an inventory limit, marking its position to the close. Run in firm.evbt under three fill models (touch,
penetration by one tick, touch capped at a share of the bar's volume) and two order-entry latencies; compared with
the level-1 version of the same idea (buy after a down bar, sell after an up bar, at the close, paying a half-tick).
The mark-out of each fill (the close five bars later, in the fill's direction) measures adverse selection. NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("evbt", "bars", "tape", "vecbt"):
    sys.path.insert(0, str(ROOT / c))
from firm_bars import time_bars  # noqa: E402
from firm_evbt import Engine, PenetrationFill, Strategy, TouchFill, VolumeCapFill  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

SEEDS, DAY, WIDTH, LOT, MAX_LOTS = (17, 18, 19, 20), 23_400.0, 60.0, 100.0, 5


@functools.lru_cache(maxsize=4)
def day(seed: int):
    tp = simulate(TapeConfig(seconds=DAY, news_at=None, u_shape=1.5, seed=seed))
    tr = tp.trades
    return tp, time_bars(tr["t"], tr["price"].astype(float), tr["qty"].astype(float), WIDTH, 0.0, DAY)


class Quoter(Strategy):
    """Rest one lot one tick beyond the last close on each side (buy below, sell above), within the inventory limit."""

    def on_bar(self, ctx, i, bar):
        for o in ctx.working():
            ctx.cancel(o.oid)
        if ctx.position < MAX_LOTS * LOT:
            ctx.submit(+1, LOT, "limit", bar["close"] - 1.0)
        if ctx.position > -MAX_LOTS * LOT:
            ctx.submit(-1, LOT, "limit", bar["close"] + 1.0)


MODELS = {"touch": TouchFill, "penetration": lambda: PenetrationFill(1.0),
          "capped": lambda: VolumeCapFill(TouchFill(), 0.025)}


def run(model: str, latency: float = 0.0, policy: str = "conservative"):
    """Per day: orders placed, fills, P&L in dollars (prices are in cents), mean mark-out in ticks; totals."""
    out = []
    for seed in SEEDS:
        tp, bars = day(seed)
        eng = Engine(bars, Quoter(), MODELS[model](), latency=latency, capital=1e6, policy=policy)
        res, orders, fills = eng.run()
        close = bars.close
        idx = np.searchsorted(bars.end, [f.t for f in fills])
        later = close[np.minimum(idx + 5, len(close) - 1)]
        mo = [np.sign(f.qty) * (lt - f.price) for f, lt in zip(fills, later, strict=True)]
        pnl = (res.capital[-1] - 1.0) * 1e6 / 100.0                   # cents to dollars
        out.append({"orders": len(orders), "fills": len(fills), "filled_lots": sum(abs(f.qty) for f in fills) / LOT,
                    "pnl": float(pnl), "markout": float(np.mean(mo)) if mo else float("nan")})
    return out


def level1():
    """The same idea at level 1: after a down bar hold +1 lot, after an up bar -1 lot, traded at the close, paying
    half a tick per share traded. P&L in dollars per day."""
    out = []
    for seed in SEEDS:
        tp, bars = day(seed)
        c = bars.close
        pos = -np.sign(np.diff(c, prepend=c[0])) * LOT
        pnl = np.sum(pos[:-1] * np.diff(c)) - 0.5 * np.sum(np.abs(np.diff(pos, prepend=0.0)))
        out.append(float(pnl / 100.0))
    return out


def summary():
    """Mean per day for each fill model with no latency, and with a 5-second latency under both policies."""
    rows = {}
    for m in MODELS:
        for lat, pol in ((0.0, "conservative"), (5.0, "conservative"), (5.0, "optimistic")):
            r = run(m, lat, pol)
            rows[(m, lat, pol)] = {k: float(np.nanmean([d[k] for d in r])) for k in r[0]}
    return rows


class AtClose(Quoter):
    """Exercise 7: the same quoter with both orders at the close price itself."""

    def on_bar(self, ctx, i, bar):
        for o in ctx.working():
            ctx.cancel(o.oid)
        if ctx.position < MAX_LOTS * LOT:
            ctx.submit(+1, LOT, "limit", bar["close"])
        if ctx.position > -MAX_LOTS * LOT:
            ctx.submit(-1, LOT, "limit", bar["close"])


def at_close(model: str):
    rows = []
    for seed in SEEDS:
        tp, bars = day(seed)
        res, orders, fills = Engine(bars, AtClose(), MODELS[model](), capital=1e6).run()
        idx = np.searchsorted(bars.end, [f.t for f in fills])
        later = bars.close[np.minimum(idx + 5, len(bars.close) - 1)]
        mo = [np.sign(f.qty) * (lt - f.price) for f, lt in zip(fills, later, strict=True)]
        rows.append((len(fills) / len(orders), float(np.mean(mo)), (res.capital[-1] - 1.0) * 1e4))
    return tuple(float(np.mean([r[k] for r in rows])) for k in range(3))
