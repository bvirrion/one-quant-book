"""Latency arbitrage and its defence (One Quant Book 11, chapter 9).

(1) Races (firm.latrace.race): a liquidity provider with a median cancel latency of 50 microseconds against three
snipers with a median of 40, lognormal jitter 0.3, a one-tick jump against a half-tick quote; the probability of being
sniped and the latency-arbitrage tax per race under each venue design, and against the provider's own latency.
(2) Defence by speed on firm.tape (responsive markets as in chapter 8; the fund follows the future half a second
later): a one-lot quoter in the fund that withdraws the side the future's move makes stale (firm.latrace.LeadGuard),
reading the future with delays from 1 ms to 1 s, against no guard; informed share and mark-out of its fills.
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
for dep in ("mmharness", "latrace", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_latrace as lr  # noqa: E402
import firm_mmharness as mh  # noqa: E402
import firm_tape as ft  # noqa: E402

BASE = {"lp_median": 50.0, "sniper_median": 40.0, "snipers": 3, "jitter": 0.3, "jump": 1.0, "half": 0.5}
DESIGNS = (("continuous", {}), ("symmetric", {"d": 350.0}), ("asymmetric", {"d": 350.0}), ("batch", {"tau": 100.0}),
           ("batch", {"tau": 1000.0}))


def designs() -> dict:
    return {f"{d} {kw}": lr.race(d, **BASE | kw, seed=11) for d, kw in DESIGNS}


LP_MEDIANS = (10.0, 20.0, 30.0, 40.0, 50.0, 70.0, 100.0)


def by_lp_latency() -> dict:
    out = {}
    for m in LP_MEDIANS:
        kw = BASE | {"lp_median": m}
        out[m] = {"continuous": lr.race("continuous", **kw, seed=12)["p_sniped"],
                  "asymmetric": lr.race("asymmetric", **kw, d=50.0, seed=12)["p_sniped"]}
    return out


# --- defence by speed on the simulated market ------------------------------------------------------------------
LAG = 0.5
SESSION = 1200.0
SEEDS = (131, 132, 133, 134)
DELAYS = (None, 0.001, 0.1, 0.3, 0.6, 1.0)          # None: no guard


def cfg(seed: int) -> ft.TapeConfig:
    return replace(ft.TapeConfig(), seed=seed, seconds=SESSION, news_at=None, informed=4.0, stale=10.0)


@functools.cache
def pair(seed: int):
    c = cfg(seed)
    rng = np.random.default_rng(c.seed + 1000)
    act = ft.activity(c, rng)
    vt, v = ft.efficient_path(c, rng, act)
    a = ft.simulate(c, (vt, v, act))
    shifted = np.concatenate([[0.0], np.minimum(vt[1:] + LAG, c.seconds)])
    top = a.top[a.n_open - 1:]
    return top["t"].astype(float), 0.5 * (top["bid"] + top["ask"]).astype(float), (shifted, v, act)


@functools.cache
def run(delay, seed: int) -> mh.Result:
    lt, lm, bpath = pair(seed)
    q = lr.LeadGuard(lt, lm, lead_delay=delay if delay is not None else 0.0, guard=delay is not None)
    return mh.run_tape(q, replace(cfg(seed), seed=seed + 11), v_path=bpath)


def defence() -> dict:
    out = {}
    for delay in DELAYS:
        rs = [run(delay, s) for s in SEEDS]
        vol = sum(r.volume() for r in rs)
        inf = sum(float(r.fills["qty"][r.extra["informed"]].sum()) for r in rs)
        mo = sum(float(r.markouts([5.0])[:, 0] @ r.fills["qty"]) for r in rs)
        out[delay] = {"shares": vol / len(rs), "informed": inf / vol, "markout": mo / vol,
                      "messages": float(np.mean([r.messages for r in rs]))}
    return out
