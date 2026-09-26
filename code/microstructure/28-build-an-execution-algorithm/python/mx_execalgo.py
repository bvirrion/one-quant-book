"""One Quant Book 10, chapter 28: the implementation-shortfall algorithm of firm.execalgo against a TWAP baseline in
chapter 27's calibrated agent market, measured with firm.tca, and taken through a halt, a price spike and a kill.

    MARKET                        chapter 27's calibrated population (with its market maker)
    IS(qty, urgency), TWAP(qty)   the two arms: the full algorithm (schedule with urgency kappa T, passive placement,
                                  participation band 0-30%); the baseline (straight-line schedule, a market order every
                                  ten seconds for what is due)
    run(params, seed, extra)      one 13-minute session with the algorithm (start 60 s, horizon 600 s): its shortfall
                                  against the arrival mid before fees (bp), firm.tca's attribution (ticks per share)
                                  and all-in cost (bp), the state,
                                  the participation, and the audit log
    ab_study()                    200 parent orders: 4 sizes x 2 urgencies x 25 seeds, each against the TWAP of the
                                  same size on the same seed (common random numbers): the saving (TWAP - IS, all-in
                                  cost in bp: firm.tca's total with fees; also before fees) with
                                  its seed-clustered 95% interval, its regression on log size and urgency, the
                                  attribution of both arms, and the orders needed to detect the saving
    stress()                      one order through a 60-second halt, one with a limit through a buyer's price spike,
                                  one killed half-way: states and the audit log
All deterministic (fixed seeds); the studies are cached.
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("agentmkt", "exchsim", "execalgo", "tca", "markout", "tcost"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_agentmkt import T0, ZERO, MarketMaker, Metaorder, Population, PopulationConfig  # noqa: E402
from firm_exchsim import CTL, SEC, ExchangeConfig, LatencyModel, Phases, SessionSpec, Simulator  # noqa: E402
from firm_execalgo import ISAlgo, Params, shortfall_bp  # noqa: E402
from firm_tca import attribute, cluster_ols  # noqa: E402

MARKET = PopulationConfig(lo_rate=3.0, near=0.5, cancel=0.02, depth=10, mo_lots=2.0, fund=0.2, v_rate=0.1,
                          noise=1.2, run_tail=2.5, chart=0.05)
SECONDS, START, HORIZON = 780.0, 60.0, 600.0
SIZES, URGENCIES, SEEDS = (4000, 8000, 16000, 32000), (0.5, 3.0), tuple(range(1, 26))
KEYS = ("spread", "impact", "timing", "opportunity", "fees", "total")


def IS(qty: int, urgency: float, **kw) -> Params:
    return Params(qty=qty, start_s=START, horizon_s=HORIZON, urgency=urgency, **kw)


def TWAP(qty: int, **kw) -> Params:
    return Params(qty=qty, start_s=START, horizon_s=HORIZON, urgency=0.0, passive=False, band=(0.0, 1.0),
                  check_s=10.0, tol_s=0.0, **kw)


def simulate(seed: int, agents=(), controls=(), calls=()):
    """chapter 27's market for SECONDS, with agents, venue controls (t_s, Ctl) and scheduled calls (t_s, fn)."""
    end = T0 + int(SECONDS * SEC)
    sim = Simulator(ExchangeConfig(phases=Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=end, end_ns=end + 1)),
                    seed=seed)
    sim.add_agent(Population(MARKET, seed, SECONDS), SessionSpec(firm="POP", latency=ZERO, cod=False))
    for a in (MarketMaker(skew=0.1), *agents):
        sim.add_agent(a, SessionSpec(firm=a.name.upper(), latency=LatencyModel(20_000, 20_000, 20_000)))
    sim.add_events(controls=[(T0 + int(t * SEC), "", m) for t, m in controls])
    for t, fn in calls:
        sim.schedule_call(T0 + int(t * SEC), fn)
    return sim.run()


def _mids(res):
    top = res.tape().top
    ok = (top["bid"] > 0) & (top["ask"] > 0)
    return top["t"][ok], 0.5 * (top["bid"][ok] + top["ask"][ok])


@functools.cache
def counterfactual(seed: int):
    return _mids(simulate(seed))


def run(p: Params, seed: int, extra=(), controls=(), calls=(), measure=True) -> dict:
    algo = ISAlgo(p)
    res = simulate(seed, (algo, *extra), controls, [(t, getattr(algo, f)) for t, f in calls])
    t, m = _mids(res)
    last = float(m[-1]) * 100
    out = {"algo": algo, "state": algo.state, "filled": algo.filled, "log": algo.log,
           "shortfall": shortfall_bp(p.side, algo.fills, algo.arrival, p.qty, last)}
    trades = res.tape().trades
    win = (trades["t"] >= START) & (trades["t"] < START + HORIZON)
    out["participation"] = algo.filled / max(1, int(trades["qty"][win].sum()))
    if measure:
        fl = [(f[0] / SEC - T0 / SEC, f[4] / 100, f[5], f[7] / 1e6 / f[5] / 0.01) for f in res.agents[algo.name].fills]
        a0 = algo.arrival / 100
        out["tca"] = attribute(1 if p.side == "B" else -1, p.qty, a0, a0, fl, (t, m), counterfactual(seed),
                               float(m[-1]), START)
        out["cost"] = out["tca"]["total"] / a0 * 1e4                 # all-in, fees included, bp
    return out


def _summary(r):
    return {"shortfall": r["shortfall"], "cost": r["cost"], "tca": {k: r["tca"][k] for k in KEYS}, "state": r["state"],
            "participation": r["participation"]}


@functools.cache
def ab_study() -> dict:
    rows = []
    for seed in SEEDS:
        for q in SIZES:
            tw = _summary(run(TWAP(q), seed))
            for u in URGENCIES:
                s = _summary(run(IS(q, u), seed))
                rows.append({"seed": seed, "size": q, "urgency": u, "is": s, "twap": tw,
                             "saved": tw["cost"] - s["cost"], "saved_before_fees": tw["shortfall"] - s["shortfall"]})
    saved = np.array([r["saved"] for r in rows])
    cl = np.array([r["seed"] for r in rows])
    one = np.ones(len(rows))
    b, v = cluster_ols(saved, one[:, None], cl)
    X = np.c_[one, np.log2([r["size"] / 4000 for r in rows]), [r["urgency"] == 3.0 for r in rows]]
    beta, cov = cluster_ols(saved, X, cl)
    cells = {}
    for q in SIZES:
        for u in URGENCIES:
            sel = [r["saved"] for r in rows if r["size"] == q and r["urgency"] == u]
            cells[(q, u)] = (float(np.mean(sel)), float(np.std(sel, ddof=1) / math.sqrt(len(sel))))
    att = {arm: {k: float(np.mean([r[arm]["tca"][k] for r in rows])) for k in KEYS} for arm in ("is", "twap")}
    sd = float(np.std(saved, ddof=1))
    before = np.array([r["saved_before_fees"] for r in rows])
    return {"before_fees": float(before.mean()), "rows": rows, "n": len(rows), "mean": float(b[0]),
            "se": float(math.sqrt(v[0, 0])),
            "lo": float(b[0] - 1.96 * math.sqrt(v[0, 0])), "hi": float(b[0] + 1.96 * math.sqrt(v[0, 0])),
            "beta": beta.tolist(), "beta_se": np.sqrt(np.diag(cov)).tolist(), "cells": cells, "attribution": att,
            "sd": sd, "n_needed": math.ceil((1.96 + 0.84) ** 2 * sd**2 / max(abs(float(b[0])), 1e-9) ** 2),
            "completed": sum(r["is"]["state"] == "done" for r in rows),
            "participation": {q: float(np.mean([r["is"]["participation"] for r in rows if r["size"] == q]))
                              for q in SIZES}}


@functools.cache
def stress() -> dict:
    halt = run(IS(16000, 0.5), 3, controls=[(260.0, CTL["P"](1, "H", "NEWS")), (320.0, CTL["P"](1, "U", "RESM")),
                                            (320.000001, CTL["P"](1, "T", "RESM"))], measure=False)
    spike_buyer = Metaorder([(T0 + 300 * SEC, 1, 60_000, 60, 60 * SEC)], name="spike")
    base = run(IS(16000, 0.5), 3, measure=False)
    lim = int(base["algo"].arrival + 10 * 100)
    spike = run(IS(16000, 0.5, limit=lim), 3, extra=(spike_buyer,), measure=False)
    spike_buyer2 = Metaorder([(T0 + 300 * SEC, 1, 60_000, 60, 60 * SEC)], name="spike")
    nolimit = run(IS(16000, 0.5), 3, extra=(spike_buyer2,), measure=False)
    kill = run(IS(16000, 0.5), 3, calls=[(360.0, "kill")], measure=False)
    return {"halt": halt, "spike": spike, "nolimit": nolimit, "kill": kill, "base": base, "limit": lim}
