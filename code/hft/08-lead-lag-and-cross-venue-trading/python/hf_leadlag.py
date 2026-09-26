"""Lead-lag and cross-venue trading (One Quant Book 11, chapter 8).

firm.tape pairs on one efficient price: A leads, B follows LAG seconds later, independent order flows (the index
future and its fund; the primary venue and a secondary one). The markets are made responsive (informed traders four
times as active and stale quotes pulled faster than Book 7's defaults), so that each mid follows its efficient price
within a fraction of a second and a sub-second lead is visible. For several planted lags: the lead estimated from the
two mids on asynchronous ticks (Hayashi-Yoshida), the price-discovery shares of A from a VECM on a 0.1-second grid,
and the edge of trading the lead in B -- a one-lot taker acting `latency` seconds after A has moved and B has not --
as a function of the trader's latency (firm.xvenue).
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
for dep in ("xvenue", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_tape as ft  # noqa: E402
import firm_xvenue as xv  # noqa: E402

SESSION = 1200.0
LAGS = (0.05, 0.2, 0.5, 1.0)
SEEDS = (121, 122)
LATENCIES = (0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0)
FEE = 0.1            # ticks per share (a taker fee of 0.1 cent with a one-cent tick)


INFORMED, STALE = 4.0, 10.0     # a responsive market: quotes follow the efficient price within a fraction of a second


def cfg(seed: int) -> ft.TapeConfig:
    return replace(ft.TapeConfig(), seed=seed, seconds=SESSION, news_at=None, informed=INFORMED, stale=STALE)


@functools.cache
def pair(lag: float, seed: int):
    a, b = ft.simulate_pair(cfg(seed), lag, seed_b=seed + 11)
    out = []
    for tp in (a, b):
        top = tp.top[tp.n_open - 1:]
        out.append((top["t"].astype(float), top["bid"].astype(float), top["ask"].astype(float)))
    return out


def mids(lag: float, seed: int):
    (ta, ba, aa), (tb, bb, ab) = pair(lag, seed)
    return ta, 0.5 * (ba + aa), tb, 0.5 * (bb + ab)


GRID_LAGS = np.round(np.arange(-60, 61) * 0.025, 3)


@functools.cache
def estimate(lag: float, seed: int) -> dict:
    ta, ma, tb, mb = mids(lag, seed)
    # the mids change only when the book does: keep the change points
    ka, kb = np.r_[0, np.flatnonzero(np.diff(ma)) + 1], np.r_[0, np.flatnonzero(np.diff(mb)) + 1]
    est, ccf = xv.lead(ta[ka], ma[ka], tb[kb], mb[kb], GRID_LAGS)
    grid = np.arange(0.0, SESSION, 0.1)
    s = xv.shares(xv.sample(ta, ma, grid), xv.sample(tb, mb, grid), lags=10)
    return {"lead": est, "ccf": ccf, "is_low": s["is_low"], "is_high": s["is_high"], "component": s["component"]}


def table() -> dict:
    out = {}
    for lag in LAGS:
        rows = [estimate(lag, s) for s in SEEDS]
        out[lag] = {"lead": [r["lead"] for r in rows], "is_low": float(np.mean([r["is_low"] for r in rows])),
                    "is_high": float(np.mean([r["is_high"] for r in rows])),
                    "component": float(np.mean([r["component"] for r in rows]))}
    return out


@functools.cache
def edge(lag: float, latency: float) -> dict:
    tr, e, se2 = 0, 0.0, 0.0
    for s in SEEDS:
        (ta, ba, aa), (tb, bb, ab) = pair(lag, s)
        r = xv.lead_edge(ta, 0.5 * (ba + aa), tb, bb, ab, latency, move=1.0, window=1.0, H=5.0, fee=FEE)
        tr += r["trades"]
        e += r["edge"] * r["trades"]
        se2 += (r["se"] * r["trades"]) ** 2
    return {"trades": tr, "edge": e / tr, "se": float(np.sqrt(se2) / tr)}


def edge_curve(lag: float = 0.5) -> dict:
    return {lat: edge(lag, lat) for lat in LATENCIES}
