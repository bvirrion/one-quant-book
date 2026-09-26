"""Inventory models (One Quant Book 11, chapter 3).

Three steps. (1) Calibrate the model on firm.tape: the variance rate of the mid, and the fill intensity of a 100-share
order resting at each depth, from an exploring Quoter that moves its quotes at random between depths every few
seconds (firm.mmharness). (2) Solve and simulate the model (firm.invmm): Avellaneda-Stoikov's reservation price and
spread, Cartea-Jaimungal's optimal depths with a running inventory penalty, against symmetric quoting, on common random
numbers. (3) Take the policy back to the simulated market as a Quoter and compare it with the symmetric one there.
Prices in ticks, time in seconds.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys
from dataclasses import replace

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for dep in ("mmharness", "invmm", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_invmm as inv  # noqa: E402
import firm_mmharness as mh  # noqa: E402
import firm_tape as ft  # noqa: E402

DEPTHS = (0, 1, 2, 3)          # ticks behind the others' best price
HOLD = 5.0                     # seconds at one depth before a new draw
SIZE = 100


class Explorer:
    """Quote SIZE shares on each side at a depth drawn at random every HOLD seconds; record the time spent at each
    distance from the mid and the fills there. Inventory is kept small by skipping the side that would grow it
    beyond 500 shares."""

    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)
        self.until = -1.0
        self.d = (0, 0)
        self.time = {}
        self.fills = {}
        self.last = None
        self.cur = {}

    def on_start(self, ctx):
        pass

    def _account(self, t):
        if self.last is not None:
            for key in self.cur.values():
                self.time[key] = self.time.get(key, 0.0) + (t - self.last)
        self.last = t

    def on_market(self, ctx, t, top):
        self._account(t)
        if t >= self.until:
            self.d = (int(self.rng.choice(DEPTHS)), int(self.rng.choice(DEPTHS)))
            self.until = t + HOLD
        x = ctx.external(top)
        mid = 0.5 * (x["bid"] + x["ask"])
        bid, ask = int(x["bid"]) - self.d[0], int(x["ask"]) + self.d[1]
        bq = SIZE if ctx.position < 500 else 0
        aq = SIZE if ctx.position > -500 else 0
        ctx.quote(bid, bq, ask, aq)
        self.cur = {}
        for cid, w in ctx.working().items():
            self.cur[cid] = (w.side, round(abs(w.price - mid) * 2) / 2)

    def on_fill(self, ctx, fill):
        key = self.cur.get(fill.cid)
        if key is not None:
            self.fills[key] = self.fills.get(key, 0) + fill.qty / SIZE


def tape_cfg(seed: int, seconds: float = 3600.0) -> ft.TapeConfig:
    return replace(ft.TapeConfig(), seed=seed, seconds=seconds, news_at=None)


@functools.cache
def explore(seed: int = 41) -> dict:
    e = Explorer(seed)
    res = mh.run_tape(e, tape_cfg(seed, 3600.0))
    return {"time": dict(e.time), "fills": dict(e.fills), "res": res}


def calibration(seed: int = 41) -> dict:
    """Mid variance rate (ticks^2 per second) and the fill intensity per side, pooled over both sides, by depth from
    the mid (ticks)."""
    ex = explore(seed)
    depths = sorted({k[1] for k in ex["time"]})
    T = np.array([sum(v for k, v in ex["time"].items() if k[1] == d) for d in depths])
    F = np.array([sum(v for k, v in ex["fills"].items() if k[1] == d) for d in depths])
    keep = T > 300.0
    A, k = inv.estimate_intensity(np.array(depths)[keep], T[keep], F[keep])
    tape = ex["res"].tape
    top = tape.top[tape.n_open - 1:]
    mid = 0.5 * (top["bid"] + top["ask"])
    grid = np.arange(0.0, tape.cfg.seconds, 1.0)
    m = mid[np.searchsorted(top["t"], grid, side="right") - 1]
    sigma2 = float(np.var(np.diff(m)))
    return {"depths": np.array(depths)[keep], "time": T[keep], "fills": F[keep], "A": A, "k": k,
            "sigma": math.sqrt(sigma2)}


# The Avellaneda-Stoikov experiment (their section 4): s = 100, T = 1, sigma = 2, dt = 0.005, k = 1.5, A = 140,
# 1,000 paths, the mid moving +/- sigma sqrt(dt) each step.
AS = {"T": 1.0, "dt": 0.005, "sigma": 2.0, "A": 140.0, "k": 1.5, "paths": 1000, "seed": 7}
GAMMAS = (0.01, 0.1, 1.0)


def _stats(r: dict) -> dict:
    return {"profit": float(r["pnl"].mean()), "sd": float(r["pnl"].std()), "q": float(r["q_T"].mean()),
            "sd_q": float(r["q_T"].std()), "fills": float(r["fills"].mean())}


def as_average_spread(gamma: float) -> float:
    pol = inv.as_policy(gamma, AS["sigma"], AS["k"], AS["T"])
    ts = np.arange(0.0, AS["T"], AS["dt"])
    return float(np.mean([sum(pol(t, np.zeros(1)))[0] for t in ts]))


@functools.cache
def as_table() -> dict:
    """Inventory and symmetric strategies at each gamma, on common random numbers."""
    kw = dict(T=AS["T"], dt=AS["dt"], sigma=AS["sigma"], A=AS["A"], k=AS["k"], paths=AS["paths"], seed=AS["seed"],
              mid="binomial")
    out = {}
    for g in GAMMAS:
        sp = as_average_spread(g)
        out[g] = {"spread": sp,
                  "inventory": _stats(inv.simulate(inv.as_policy(g, AS["sigma"], AS["k"], AS["T"]), **kw)),
                  "symmetric": _stats(inv.simulate(inv.symmetric(sp / 2), **kw))}
    return out


PHIS = (0.0, 0.5, 2.0, 5.0, 20.0, 50.0)
HALVES = (0.5, 0.67, 0.8, 1.0, 1.5, 2.0)


@functools.cache
def frontier() -> dict:
    """Mean and standard deviation of P&L: Cartea-Jaimungal quotes for a range of running penalties phi (terminal
    penalty alpha = 1, inventory within +/- 30) against symmetric quotes for a range of half-spreads."""
    kw = dict(T=AS["T"], dt=AS["dt"], sigma=AS["sigma"], A=AS["A"], k=AS["k"], paths=AS["paths"], seed=AS["seed"],
              mid="binomial", qmax=30)
    cj = {}
    for phi in PHIS:
        sol = inv.CJSolution(AS["A"], AS["k"], phi, 1.0, 30, AS["T"], 200)
        cj[phi] = _stats(inv.simulate(inv.cj_policy(sol), **kw))
    sym = {h: _stats(inv.simulate(inv.symmetric(h), **kw)) for h in HALVES}
    return {"cj": cj, "symmetric": sym}


# --- back in the simulated market -----------------------------------------------------------------------------
LOT = 100
TAPE_SEEDS = (51, 52, 53, 54, 55, 56)
SESSION = 1200.0               # seconds of each simulated session


class TouchQuoter:
    """Rest at the others' best bid and ask, one lot each, on the sides the touch-only solution says to post."""

    def __init__(self, sol: inv.TouchSolution):
        self.sol = sol

    def on_start(self, ctx):
        pass

    def on_market(self, ctx, t, top):
        x = ctx.external(top)
        b, a = self.sol.post(t, ctx.position // LOT)
        ctx.quote(int(x["bid"]), LOT if b else 0, int(x["ask"]), LOT if a else 0)

    def on_fill(self, ctx, fill):
        pass


CAL_SEEDS = (41, 42, 43)


@functools.cache
def touch_calibration() -> dict:
    """From the symmetric Quoter's own fills on calibration sessions (never the test sessions): the fill intensity of
    one lot at the touch, per side (lots per second), and its capture net of adverse selection at ten seconds
    (ticks per share)."""
    fills, time, net = 0.0, 0.0, []
    for s in CAL_SEEDS:
        r = mh.run_tape(mh.SymmetricQuoter(LOT, 5 * LOT), tape_cfg(s, SESSION))
        fills += r.volume() / LOT
        time += 2 * SESSION
        m = r.markouts([10.0], "mid")[:, 0]
        net += list(m)
    return {"lam": fills / time, "c": float(np.mean(net)), "n": int(fills)}


def touch_solution(phi: float, qmax: int = 5) -> inv.TouchSolution:
    cal = touch_calibration()
    return inv.TouchSolution(cal["lam"], cal["c"], phi, 0.0, qmax, SESSION, int(SESSION))


@functools.cache
def tape_run(kind: str, seed: int, phi: float = 1e-4) -> mh.Result:
    cfg = tape_cfg(seed, SESSION)
    q = mh.SymmetricQuoter(LOT, 5 * LOT) if kind == "symmetric" else TouchQuoter(touch_solution(phi))
    return mh.run_tape(q, cfg)


PHI_TAPE = (3e-4, 1e-3)


def tape_compare(phi: float = 3e-4) -> dict:
    """Symmetric (at most five lots) against the touch-only solution, mean over the sessions."""
    out = {}
    for kind in ("symmetric", "touch"):
        rs = [tape_run(kind, s, phi) for s in TAPE_SEEDS]
        inv_abs = [np.abs(r.inventory()[1]).mean() / LOT if len(r.fills) else 0.0 for r in rs]
        pnl = [r.pnl() for r in rs]
        out[kind] = {"pnl": float(np.mean(pnl)), "sd_pnl": float(np.std(pnl, ddof=1)),
                     "volume": float(np.mean([r.volume() for r in rs])), "abs_q": float(np.mean(inv_abs)),
                     "max_q": float(np.mean([np.abs(r.inventory()[1]).max() / LOT for r in rs]))}
    return out


def one_path(gamma: float = 0.1, seed: int = 3) -> dict:
    """One path of the Avellaneda-Stoikov experiment with the inventory strategy: mid, reservation price, quotes and
    inventory at every step (the paper's figure 1, redrawn)."""
    rng = np.random.default_rng(seed)
    n = int(round(AS["T"] / AS["dt"]))
    pol = inv.as_policy(gamma, AS["sigma"], AS["k"], AS["T"])
    s, q = 100.0, 0
    rows = []
    for i in range(n):
        t = i * AS["dt"]
        db, da = (float(x[0]) for x in pol(t, np.array([q])))
        tau = AS["T"] - t
        rows.append((t, s, s - q * gamma * AS["sigma"] ** 2 * tau, s - db, s + da, q))
        ub, ua, z = rng.random(), rng.random(), rng.standard_normal()
        if ub < AS["A"] * math.exp(-AS["k"] * db) * AS["dt"]:
            q += 1
        if ua < AS["A"] * math.exp(-AS["k"] * da) * AS["dt"]:
            q -= 1
        s += AS["sigma"] * math.sqrt(AS["dt"]) * (1.0 if z >= 0 else -1.0)
    a = np.array(rows)
    return {"t": a[:, 0], "s": a[:, 1], "r": a[:, 2], "bid": a[:, 3], "ask": a[:, 4], "q": a[:, 5]}


def depth_curves(phis=(0.5, 5.0, 50.0), qmax: int = 30, show: int = 10) -> dict:
    """Cartea-Jaimungal bid and ask depths at t = 0 against inventory, for several running penalties."""
    qs = np.arange(-show, show + 1)
    out = {"q": qs}
    for phi in phis:
        sol = inv.CJSolution(AS["A"], AS["k"], phi, 1.0, qmax, AS["T"], 200)
        b, a = sol.depths(np.zeros(len(qs)), qs)
        out[phi] = (b, a)
    return out
