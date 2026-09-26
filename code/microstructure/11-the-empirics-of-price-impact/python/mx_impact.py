"""One Quant Book 10, chapter 11: measuring price impact, on a reactive agent market and on the firm's metaorders.

    MARKET                              the agent population of firm.agentmkt used here (a thin, reactive book)
    single_and_aggregate(seed)          one hour: the response to a trade by lag and trade size, and the mid change
                                        over ten-second intervals against their signed volume
    replay_pitfall(seed, q)             the same metaorder sent into firm.tape's replayed flow and into a copy of the
                                        session without it: the difference of the two mid paths
    counterfactual(sizes, seeds)        metaorders of 30 children over ten minutes in the agent market, each against
                                        the same session without it: mean impact and standard error by size, during,
                                        at the end and after the execution
    panel(seed, alpha_share, a)         the firm's metaorder records, simulated: 50 stocks with their volatility and
                                        volume, 2,000 metaorders, a square-root impact with prefactor 0.8, price noise,
                                        and a share of orders timed by a forecast of a drift a sigma sqrt(T) in their
                                        direction
    panel_fits(seed)                    exponent and prefactor with cluster-bootstrap intervals: all orders, with the
                                        timed orders, and with their forecast removed (cached)
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("agentmkt", "exchsim", "tape", "impactfit"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_agentmkt import T0, Metaorder, PopulationConfig, session  # noqa: E402
from firm_exchsim import SEC, ExchangeConfig, LatencyModel, Phases, SessionSpec, Simulator, TapeBackground  # noqa: E402
from firm_impactfit import aggregate, decontaminate, fit_power, response  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

MARKET = PopulationConfig(lo_rate=3.0, near=0.3, cancel=0.05, depth=10, fund=0.05)


def _mids(res):
    tp = res.tape()
    top = tp.top
    ok = (top["bid"] > 0) & (top["ask"] > 0)
    return top["t"][ok], 0.5 * (top["bid"][ok] + top["ask"][ok]), tp


def _at(tt, mm, t):
    return float(mm[max(np.searchsorted(tt, t, side="right") - 1, 0)])


@functools.cache
def single_and_aggregate(seed: int = 1, seconds: float = 3600.0) -> dict:
    res, _ = session(MARKET, seconds, seed)
    tt, mm, tp = _mids(res)
    r = response(tp.trades, tt, mm)
    a = aggregate(tp.trades, tt, mm, 10.0, [-1e9, -2000, -1000, -400, 400, 1000, 2000, 1e9])
    return {"response": r, "aggregate": a, "volume": int(tp.trades["qty"].sum()), "trades": len(tp.trades)}


def replay_pitfall(seed: int = 1, q: int = 24_000, seconds: float = 1800.0) -> dict:
    def run(meta: bool):
        end = T0 + int(seconds * SEC)
        sim = Simulator(ExchangeConfig(phases=Phases(start_ns=T0 - SEC, open_ns=T0, close_ns=end, end_ns=end + 1)),
                        seed=seed)
        sim.add_background(TapeBackground(TapeConfig(seconds=seconds, seed=seed, news_at=None)))
        if meta:
            sim.add_agent(Metaorder([(T0 + 300 * SEC, 1, q, 30, 600 * SEC)]),
                          SessionSpec(firm="META", latency=LatencyModel(20_000, 20_000, 20_000)))
        return _mids(sim.run())
    tb, mb, _ = run(False)
    tw, mw, _ = run(True)
    diff = [(_at(tw, mw, 300 + h) - _at(tw, mw, 300 - 1e-6)) - (_at(tb, mb, 300 + h) - _at(tb, mb, 300 - 1e-6))
            for h in (300, 600, 900, 1200)]
    return {"diff": diff}


H = (300, 600, 900, 1200)


@functools.cache
def counterfactual(sizes=(1500, 6000, 24_000), seeds=tuple(range(1, 7)), seconds: float = 1800.0) -> dict:
    out = {}
    for seed in seeds:
        tb, mb, tpb = _mids(session(MARKET, seconds, seed)[0])
        for q in sizes:
            res, _ = session(MARKET, seconds, seed, agents=[Metaorder([(T0 + 300 * SEC, 1, q, 30, 600 * SEC)])])
            tw, mw, _ = _mids(res)
            out.setdefault(q, []).append([(_at(tw, mw, 300 + h) - _at(tw, mw, 300 - 1e-6))
                                          - (_at(tb, mb, 300 + h) - _at(tb, mb, 300 - 1e-6)) for h in H])
        if seed == seeds[0]:
            out["hourly_volume"] = float(tpb.trades["qty"].sum() * 3600 / seconds)
    return {q: (np.mean(v, axis=0), np.std(v, axis=0, ddof=1) / np.sqrt(len(v))) if q != "hourly_volume" else v
            for q, v in out.items()}


def panel(seed: int = 1, alpha_share: float = 0.0, a: float = 0.5, n_stocks: int = 50,
          per_stock: int = 40, y: float = 0.8, delta: float = 0.5, dur_fixed: float | None = None) -> dict:
    """Impact at completion as a fraction of price: y sigma (Q/V)^delta, plus price noise
    sigma sqrt(T / day), plus, for timed orders, the forecast drift a sigma sqrt(T / day) in their
    direction. sigma is daily volatility."""
    rng = np.random.default_rng(seed)
    sig = rng.uniform(0.01, 0.03, n_stocks)
    stock = np.repeat(np.arange(n_stocks), per_stock)
    n = len(stock)
    part = np.exp(rng.uniform(np.log(1e-4), np.log(0.05), n))        # Q / V
    dur = np.clip(part / 0.1, 0.002, 0.5)                            # days, at 10% of volume
    if dur_fixed is not None:
        dur = np.full(n, dur_fixed)
    s = sig[stock]
    timed = rng.random(n) < alpha_share
    forecast = np.where(timed, a * s * np.sqrt(dur), 0.0)
    impact = y * s * part**delta + s * np.sqrt(dur) * rng.standard_normal(n) + forecast
    return {"impact": impact, "sigma": s, "participation": part, "stock": stock,
            "forecast": forecast, "timed": timed}


@functools.cache
def panel_fits(seed: int = 1) -> dict:
    out = {}
    for name, share in (("clean", 0.0), ("timed", 0.3)):
        p = panel(seed, share)
        out[name] = fit_power(p["impact"], p["sigma"], p["participation"], clusters=p["stock"])
        if name == "timed":
            d = decontaminate(p["impact"], p["forecast"])
            out["corrected"] = fit_power(d["clean"], p["sigma"], p["participation"], clusters=p["stock"])
            out["beta"] = d["beta"]
    return out
