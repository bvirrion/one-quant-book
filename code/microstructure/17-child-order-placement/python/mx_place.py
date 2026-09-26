"""One Quant Book 10, chapter 17: child-order placement -- join, step behind, reprice, cross, or let a plan decide.

    MARKET                           firm.agentmkt's population for this chapter: a calmer book (about fifteen lots at
                                     the best, a one-tick spread 98% of the time, the mid moving every nine seconds)
    calibration(), market_stats()    firm.placement's Markov book fitted on a 30-minute session of MARKET, and the
                                     session's statistics
    plan()                           the dynamic-programming solution for 8 lots in 60 seconds
    model_study()                    on the Markov book: crossing at once, joining and waiting, the plan, and a
                                     tabular Q-learning policy (Monte Carlo, common random numbers)
    policies()                       the executor's policies: cross, join, one tick behind, join and reprice,
                                     imbalance-conditioned, the plan
    sim_study()                      each policy on the same slices of the simulated market (800 shares in 60 s, nine
                                     slices a session alternating buys and sells, 24 sessions): cost per share against
                                     the mid at the start, its dispersion, the share filled passively, the share left to
                                     the clean-up trade, the paired difference to crossing
    urgent_study()                   one lot with five seconds left: join (repricing) minus cross by queue imbalance
    dp_thresholds(), threshold_curve()   the plan's imbalance threshold for several sizes and horizons, and for one
                                     lot against the seconds left
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("placement", "agentmkt", "exchsim"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_agentmkt import SEC, T0, PopulationConfig, session  # noqa: E402
from firm_placement import (  # noqa: E402
    Cross,
    DPPolicy,
    Imbalance,
    Post,
    SliceExecutor,
    calibrate,
    imbalance_threshold,
    q_policy,
    qlearn,
    simulate,
    solve,
)

MARKET = PopulationConfig(lo_rate=2.0, near=0.5, cancel=0.02, depth=10, noise=0.6, mo_lots=2.0, fund=0.05,
                          v_rate=0.1)
QTY, LOTS, HORIZON = 800, 8, 60.0
DT, NMAX = 0.2, 40


@functools.cache
def _calibration_run(seconds: float = 1800.0, seed: int = 99):
    return session(MARKET, seconds, seed)[0]


@functools.cache
def calibration():
    return calibrate(_calibration_run())


@functools.cache
def market_stats(seconds: float = 1800.0) -> dict:
    """Time-weighted share of a one-tick spread, mean best-queue size (lots), mid changes a second, volume."""
    tp = _calibration_run().tape()
    top = tp.top
    ok = (top["bid"] > 0) & (top["ask"] > 0)
    t = top["t"][ok]
    dt = np.diff(np.r_[t, seconds])
    one = float((dt * (top["ask"][ok] - top["bid"][ok] == 1)).sum() / dt.sum())
    q = (top["bid_qty"][ok] + top["ask_qty"][ok]) / 200.0
    mid = top["ask"][ok] + top["bid"][ok]
    return {"one_tick": one, "queue": float((dt * q).sum() / dt.sum()),
            "moves": float((np.diff(mid) != 0).sum() / seconds), "volume": float(tp.trades["qty"].sum() / seconds),
            "fresh_mean": float(np.arange(1, len(calibration().fresh) + 1) @ np.asarray(calibration().fresh))}


@functools.cache
def plan():
    return solve(calibration(), LOTS, HORIZON, dt=DT, n_max=NMAX, a_max=NMAX)


def _dp_rule(p):
    def rule(r, n, a, k):
        return p.cross[k][r, n, np.maximum(a, 1)]
    return rule


@functools.cache
def model_study(paths: int = 40_000, episodes: int = 200_000) -> dict:
    m, p = calibration(), plan()
    rules = {"cross": lambda r, n, a, k: np.ones(len(r), bool),
             "join": lambda r, n, a, k: np.zeros(len(r), bool),
             "plan": _dp_rule(p)}
    q = qlearn(m, LOTS, HORIZON, dt=DT, episodes=episodes, batch=2_000, seed=17, n_cap=NMAX, a_cap=NMAX)
    rules["Q-learning"] = q_policy(q, dt=DT)
    out = {}
    for name, rule in rules.items():
        c = simulate(m, rule, LOTS, HORIZON, dt=DT, paths=paths, seed=23, n_cap=NMAX, a_cap=NMAX) / LOTS
        out[name] = (float(c.mean()), float(c.std(ddof=1) / math.sqrt(paths)))
    out["plan_value"] = p.fresh_value[-1][LOTS] / LOTS
    out["threshold"] = imbalance_threshold(p, LOTS)
    out["q_visited"] = float((q != 0).any(axis=-1).mean())
    return out


RULE = 0.5                               # a desk's rule of thumb: cross at once above this imbalance


def policies() -> dict:
    return {"cross": Cross(), "join": Post(0, False), "behind": Post(-1, False), "reprice": Post(0, True),
            "imbalance": Imbalance(RULE, Post(0, True)), "plan": DPPolicy(plan())}


SLICES, GAP, FIRST = 9, 120.0, 60.0


def run_policy(policy, seed: int, qty: int = QTY, horizon: float = HORIZON, gap: float = GAP,
               slices: int = SLICES) -> list:
    """(imbalance at start, cost per share in ticks, passive share, clean-up share, sign) for each slice; slices
    alternate buys and sells, `gap` seconds apart from FIRST."""
    plan_ = [(T0 + int((FIRST + i * gap) * SEC), "B" if i % 2 == 0 else "S", qty, horizon) for i in range(slices)]
    ex = SliceExecutor(plan_, policy, check_s=1.0)
    res, _ = session(MARKET, FIRST + slices * gap, seed, agents=[ex])
    fills = res.agents["placer"].fills
    out = []
    for i, t0, imb, mid in ex.log:
        f = [x for x in fills if t0 <= x[0] < t0 + int(gap * SEC)]
        q = np.array([x[5] for x in f], float)
        p = np.array([x[4] for x in f], float) / 100.0
        passive = np.array([x[6] == "A" for x in f])
        late = np.array([x[0] >= t0 + int((horizon - 1.0) * SEC) and x[6] != "A" for x in f])
        sign = 1 if i % 2 == 0 else -1
        cost = sign * (float(q @ p) / q.sum() - mid / 100.0)
        out.append((imb, cost, float(q[passive].sum() / q.sum()), float(q[late].sum() / q.sum()), sign))
    return out


@functools.cache
def sim_study(seeds=tuple(range(1, 25))) -> dict:
    out, rows = {}, {}
    for name, pol in policies().items():
        rows[name] = np.array([r for s in seeds for r in run_policy(pol, 1700 + s)])
        a = rows[name]
        n = math.sqrt(len(a))
        out[name] = {"cost": float(a[:, 1].mean()), "se": float(a[:, 1].std(ddof=1) / n),
                     "sd": float(a[:, 1].std(ddof=1)), "passive": float(a[:, 2].mean()),
                     "cleanup": float(a[:, 3].mean()), "high": float((a[:, 0] > RULE).mean())}
    base = rows["cross"][:, 1]
    for name in rows:
        d = rows[name][:, 1] - base
        out[name]["vs_cross"] = (float(d.mean()), float(d.std(ddof=1) / math.sqrt(len(d))))
    out["n"] = int(len(base))
    return out


URGENT = dict(qty=100, horizon=5.0, gap=15.0, slices=76)
EDGES = (-1.0001, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0001)


@functools.cache
def urgent_study(seeds=tuple(range(1, 25))) -> dict:
    """One lot with five seconds left: crossing at once against joining the bid (repricing), paired slice by slice
    (common random numbers), by queue imbalance at the start."""
    rc = np.array([r for s in seeds for r in run_policy(Cross(), 1800 + s, **URGENT)])
    rj = np.array([r for s in seeds for r in run_policy(Post(0, True), 1800 + s, **URGENT)])
    imb, d = rc[:, 0], rj[:, 1] - rc[:, 1]
    buckets = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:], strict=True):
        sel = (imb >= lo) & (imb < hi)
        buckets.append((float(lo), float(hi), int(sel.sum()), float(d[sel].mean()),
                        float(d[sel].std(ddof=1) / math.sqrt(sel.sum()))))
    return {"n": int(len(d)), "cross": float(rc[:, 1].mean()), "join": float(rj[:, 1].mean()),
            "diff": float(d.mean()), "diff_se": float(d.std(ddof=1) / math.sqrt(len(d))), "buckets": buckets,
            "passive": float(rj[:, 2].mean())}


CASES = ((1, 3.0), (1, 5.0), (1, 15.0), (1, 60.0), (8, 15.0), (8, 60.0))


@functools.cache
def threshold_curve(lots: int = 1, seconds: float = 30.0) -> list:
    """The plan's imbalance threshold for `lots` against the seconds left (one solve, every step)."""
    p = solve(calibration(), lots, seconds, dt=DT, n_max=NMAX, a_max=NMAX)
    return [(k * DT, *imbalance_threshold(p, lots, k)) for k in range(5, len(p.cross), 5)]


@functools.cache
def dp_thresholds() -> dict:
    m = calibration()
    out = {}
    for lots, secs in CASES:
        p = solve(m, lots, secs, dt=DT, n_max=NMAX, a_max=NMAX)
        out[(lots, secs)] = imbalance_threshold(p, lots)
    return out


if __name__ == "__main__":
    m = calibration()
    print(m)
    ms = model_study()
    print(ms)
