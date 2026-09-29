"""Backtest-engine architecture (One Quant Book 15, chapter 11).

One quoting strategy (a lot at the best bid and the best ask, an inventory limit of three lots) is run by
firm.btengine at level 2 (Book 7's event-driven backtester on one-second bars, touch fills), level 3 (Book 7's
order-book replay, first-in first-out queue positions) and level 4 (Book 10's exchange simulator with the same
firm.tape session replayed as real orders: the reactive simulation). Every run goes to a results store with its
manifest. The ladder is the strategy's P&L an hour at each level over twenty one-hour sessions; the gap between
replay and the reactive simulation is decomposed by ten-second markouts into fills both runs share, fills only
the replay had, and fills that exist only because the strategy's orders were in the book. A daily trend rule runs
at levels 1 and 2 through the same engine.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/btengine"))
import firm_btengine as B  # noqa: E402

GEN = ROOT / "data/platforms/generated/btengine"
TICK = 0.01                                            # dollars per tick
HORIZON = 10.0                                         # markout horizon, seconds


class Quoter(B.QuoteStrategy):
    """A lot at the best bid and ask; requote when the touch moves; stop at the limit."""

    name = "quoter"

    def __init__(self, lots: int = 1, limit: int = 3):
        self.qty, self.limit, self.mine = 100 * lots, 100 * lots * limit, {}

    def on_market(self, ctx, t, snap):
        b, a = snap["bid"], snap["ask"]
        if b is None or a is None:
            return
        live = set(ctx.working())
        self.mine = {v: sp for v, sp in self.mine.items() if v in live}
        have = set()
        for v, (side, px) in list(self.mine.items()):
            if px != (b if side == 1 else a):               # the touch moved: cancel
                ctx.cancel(v)
                del self.mine[v]
            else:
                have.add(side)
        for side, px in ((1, b), (-1, a)):
            if side not in have and side * ctx.position < self.limit:
                self.mine[ctx.send(side, px, self.qty)] = (side, px)


class Trend(B.TargetStrategy):
    """Long (short) one unit of capital when the close is above (below) its level 50 days earlier."""

    def target(self, close, i):
        return 0.0 if i < 50 else float(np.sign(close[i] / close[i - 50] - 1.0))


def one_session(data: B.DataAccess, store: B.ResultsStore | None, seed: int, seconds: float,
                latency: float = 20e-6, limit: int = 3) -> dict:
    name = data.tape(seconds, seed)
    runs = {}
    for level in (2, 3, 4):
        cfg = {"dataset": name, "latency": latency, "seed": 1, "limit": limit}
        runs[level] = B.Engine(level, Quoter(limit=limit), data, cfg).run()
        if store is not None:
            store.save(runs[level])
    only4 = B.classify_fills(runs[4], runs[3])
    only3 = B.classify_fills(runs[3], runs[4])
    m3, m4 = B.markouts(runs[3], HORIZON), B.markouts(runs[4], HORIZON)
    per_hour = 3600.0 / seconds
    row = {"seed": seed}
    for level, r in runs.items():
        row[f"pnl{level}"] = r.pnl * TICK * per_hour
        row[f"fills{level}"] = len(r.fills)
    row.update(shared3=m3[~only3].sum() * TICK, only3=m3[only3].sum() * TICK,
               shared4=m4[~only4].sum() * TICK, only4=m4[only4].sum() * TICK,
               n_only3=int(only3.sum()), n_only4=int(only4.sum()))
    div = B.first_divergence(runs[3], runs[4])
    row["first_div"] = div[0] if div else -1
    row["first_div_t"] = min(div[1].t, div[2].t) if div and div[1] and div[2] else -1.0
    return row


def ladder(seeds=range(1, 21), seconds: float = 3600.0, root: pathlib.Path = GEN) -> list[dict]:
    data, store = B.DataAccess(root / "data"), B.ResultsStore(root / "runs")
    return [one_session(data, store, s, seconds) for s in seeds]


def summary(rows: list[dict]) -> dict:
    out = {}
    for k in ("pnl2", "pnl3", "pnl4", "shared3", "only3", "shared4", "only4", "fills2", "fills3", "fills4",
              "n_only3", "n_only4"):
        x = np.array([r[k] for r in rows], dtype=float)
        out[k] = (float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else 0.0)
    gap = np.array([r["pnl3"] - r["pnl4"] for r in rows])
    out["gap"] = (float(gap.mean()), float(gap.std(ddof=1) / np.sqrt(len(gap))) if len(gap) > 1 else 0.0)
    out["l4_below_l3"] = int(sum(r["pnl4"] < r["pnl3"] for r in rows))
    mgap = sum(r["shared3"] + r["only3"] - r["shared4"] - r["only4"] for r in rows)
    out["markout_gap"] = mgap / len(rows)
    out["share_only4"] = -sum(r["only4"] for r in rows) / mgap
    out["share_only3"] = sum(r["only3"] for r in rows) / mgap
    out["share_shared"] = sum(r["shared3"] - r["shared4"] for r in rows) / mgap
    return out


def trend_levels(root: pathlib.Path = GEN) -> dict:
    data = B.DataAccess(root / "data")
    name = data.daily()
    r1 = B.Engine(1, Trend(), data, {"dataset": name}).run()
    r2 = B.Engine(2, Trend(), data, {"dataset": name}).run()
    return {"level1": r1.pnl, "level2": r2.pnl, "trades1": len(r1.events), "trades2": len(r2.fills)}


def rerun_is_identical(root: pathlib.Path = GEN, seed: int = 1, seconds: float = 120.0) -> bool:
    """Same code, data, parameters and seed: the same run id and the same events."""
    data = B.DataAccess(root / "data")
    name = data.tape(seconds, seed)
    a = B.Engine(4, Quoter(), data, {"dataset": name, "latency": 20e-6, "seed": 1}).run()
    b = B.Engine(4, Quoter(), data, {"dataset": name, "latency": 20e-6, "seed": 1}).run()
    return a.run_id == b.run_id and [e.data for e in a.events] == [e.data for e in b.events]
