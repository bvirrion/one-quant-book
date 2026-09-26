"""One Quant Book 10, chapter 27: an agent-based market on the exchange simulator, calibrated to stylised facts by the
method of simulated moments, and taken apart one agent type at a time.

    BASE                         the population's fixed part: liquidity providers, fundamentalists (who see the hidden
                                 value V, so are also the informed traders), the tick and the value's jump rate
    config(noise, tail, chart)   BASE with the three calibrated parameters: the noise takers' rate, the Pareto tail of
                                 their sign runs (0: independent signs; the runs are metaorders cut into children),
                                 the chartists' rate per tick of trend
    run(params, seed, drop)      one simulated hour with an inventory-skewing market maker; drop removes one agent
                                 type ("runs", "chartists", "fundamentalists", "maker", "noise"); returns the facts
    target()                     the facts of eight hours of firm.tape (Book 7's synthetic market, no news window):
                                 their mean (the target) and standard deviation across hours (the scale)
    calibration()                the method of simulated moments on the 27-point grid, three hours each with the
                                 same seeds (common random numbers); the best point's distance in and out of sample,
                                 the starting point's, and the floor: six fresh hours of the target market itself
    ablation()                   the calibrated population on six fresh hours, whole and with each type removed:
                                 each fact's move in target standard deviations, with its paired standard error
    sign_curves()                trade-sign autocorrelation by lag, with and without sign runs; the excess the runs add
                                 and its log-log slope over lags 1-7, against the power law the run lengths imply
                                 (Lillo, Mike and Farmer: exponent 1 - tail)
    maker_study()                the market maker at three inventory skews: its inventory and profit
All deterministic (fixed seeds); the studies are cached.
"""
from __future__ import annotations

import functools
import itertools
import pathlib
import sys
from dataclasses import replace

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("agentmkt", "exchsim", "tape"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_agentmkt import FACTS, MarketMaker, PopulationConfig, distance, facts, msm, session  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

SECONDS, SAMPLE = 3600.0, 30.0
BASE = PopulationConfig(lo_rate=3.0, near=0.5, cancel=0.02, depth=10, mo_lots=2.0, fund=0.2, v_rate=0.1)
GRID = list(itertools.product((0.9, 1.2, 1.5), (0.0, 1.5, 2.5), (0.0, 0.05, 0.1)))
SEEDS, FRESH = (1, 2, 3), (11, 12, 13, 14, 15, 16)
SKEW = 0.1
DROPS = ("runs", "chartists", "fundamentalists", "maker", "noise")


def config(noise: float, tail: float, chart: float) -> PopulationConfig:
    return replace(BASE, noise=noise, run_tail=tail, chart=chart)


def drop_type(cfg: PopulationConfig, drop: str | None) -> tuple[PopulationConfig, bool]:
    """The population without one agent type, and whether the market maker stays."""
    if drop == "runs":
        return replace(cfg, run_tail=0.0), True
    if drop == "chartists":
        return replace(cfg, chart=0.0), True
    if drop == "fundamentalists":
        return replace(cfg, fund=0.0), True
    if drop == "noise":
        return replace(cfg, noise=0.0), True
    return cfg, drop != "maker"


def _session(params, seed, drop=None, skew=SKEW):
    cfg, maker = drop_type(config(*params), drop)
    return session(cfg, SECONDS, seed, agents=[MarketMaker(skew=skew)] if maker else [])[0]


@functools.cache
def run(params: tuple, seed: int, drop: str | None = None) -> dict:
    return facts(_session(params, seed, drop).tape(), SAMPLE)


@functools.cache
def target() -> dict:
    days = [facts(simulate(TapeConfig(seed=s, news_at=None)), SAMPLE) for s in range(1, 9)]
    return {"mean": {k: float(np.mean([d[k] for d in days])) for k in FACTS},
            "sd": {k: float(np.std([d[k] for d in days], ddof=1)) for k in FACTS}, "days": days}


def _mean(rows):
    return {k: float(np.mean([r[k] for r in rows])) for k in FACTS}


@functools.cache
def calibration() -> dict:
    t = target()
    out = msm(run, GRID, t["mean"], t["sd"], SEEDS)
    fresh = _mean([run(out["best"], s) for s in FRESH])
    start = GRID[0]
    start_facts = _mean([run(start, s) for s in SEEDS])
    return {**out, "fresh": fresh, "distance_fresh": distance(fresh, t["mean"], t["sd"]), "start": start,
            "start_facts": start_facts, "distance_start": distance(start_facts, t["mean"], t["sd"]),
            "surface": {p: d for d, p, _ in out["all"]}, "floor": floor()}


def floor() -> float:
    """The distance of six fresh hours of the target market itself: what sampling noise alone gives."""
    t = target()
    days = [facts(simulate(TapeConfig(seed=s, news_at=None)), SAMPLE) for s in FRESH]
    return distance(_mean(days), t["mean"], t["sd"])


@functools.cache
def ablation() -> dict:
    t, best = target(), calibration()["best"]
    full = _mean([run(best, s) for s in FRESH])
    out = {"full": full}
    for d in DROPS:
        rows = [run(best, s, d) for s in FRESH]
        m = _mean(rows)
        z = {k: (m[k] - full[k]) / t["sd"][k] for k in FACTS}
        diff = {k: [(r[k] - run(best, s)[k]) / t["sd"][k] for r, s in zip(rows, FRESH, strict=True)] for k in FACTS}
        se = {k: float(np.std(v, ddof=1) / np.sqrt(len(v))) for k, v in diff.items()}
        out[d] = {"facts": m, "z": z, "se": se, "carried": max(z, key=lambda k: abs(z[k])),
                  "distance": distance(m, t["mean"], t["sd"])}
    return out


def sign_acf(tape, lags) -> np.ndarray:
    tr = tape.trades
    new = np.r_[True, (np.diff(tr["t"]) > 0) | (np.diff(tr["sign"]) != 0)]
    x = tr["sign"][new].astype(float)
    x = x - x.mean()
    return np.array([x[k:] @ x[:-k] / (x @ x) for k in lags])


LAGS = (1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100)


@functools.cache
def sign_curves() -> dict:
    best = calibration()["best"]
    out = {}
    for name, drop in (("runs", None), ("none", "runs")):
        out[name] = np.mean([sign_acf(_session(best, s, drop).tape(), LAGS) for s in FRESH[:3]], axis=0)
    excess = out["runs"] - out["none"]
    k = 5                                             # lags 1-7, where the excess is clearly positive
    slope = np.polyfit(np.log(np.array(LAGS[:k], float)), np.log(excess[:k]), 1)[0]
    return {**out, "excess": excess, "slope": float(slope), "implied": -(best[1] - 1.0), "tail": best[1]}


@functools.cache
def maker_study(skews=(0.0, 0.1, 0.3)) -> dict:
    best = calibration()["best"]
    out = {}
    for k in skews:
        inv, pnl, spread, path = [], [], [], None
        for s in FRESH[:3]:
            res = _session(best, s, None, k)
            mm, tape = res.agents["mm"], res.tape()
            pos = np.cumsum([f[3] * f[5] for f in mm.fills]) / 100.0
            t = np.array([f[0] for f in mm.fills], float) / 1e9 - 34_200.0      # seconds from the open
            w = np.diff(np.r_[t, SECONDS])                                      # each position's holding time
            inv.append(float(np.sqrt(w @ pos**2 / SECONDS)))
            top = tape.top[(tape.top["bid"] > 0) & (tape.top["ask"] > 0)]
            mid = 0.5 * (top["bid"][-1] + top["ask"][-1])
            pnl.append(mm.cash + (pos[-1] * 100 if len(pos) else 0) * mid * 0.01)
            spread.append(facts(tape, SAMPLE)["spread"])
            if path is None:
                path = (t, pos)
        out[k] = {"inventory_rms": float(np.mean(inv)), "pnl": float(np.mean(pnl)),
                  "pnl_sd": float(np.std(pnl, ddof=1)), "spread": float(np.mean(spread)), "path": path}
    return out
