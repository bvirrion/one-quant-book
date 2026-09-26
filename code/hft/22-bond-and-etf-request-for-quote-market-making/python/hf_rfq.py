"""Bond and ETF request-for-quote market making (One Quant Book 11, chapter 22).

A client sells a bond that has not traded for weeks to n dealers; every dealer's value estimate is off by 25 cents
(per 100 face) at one standard deviation; the client's urgency discount is exponential with a 30-cent mean. The
symmetric equilibrium markup by number of dealers, the auto-quoter's profit and win rate there, what a model that
ignores the winner's curse would do, and a logistic win-probability model fitted from a history of randomised bids.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "rfqmm"))
import firm_rfqmm as rm  # noqa: E402

MARKUPS = np.arange(0.0, 100.1, 2.5)
DEALERS = (1, 2, 3, 5, 8, 10)
N = 40000


@functools.cache
def equilibria() -> dict:
    out = {}
    for n in DEALERS:
        e = rm.equilibrium(n, MARKUPS, n=N)
        nv = rm.naive_markup(e["rows"])
        out[n] = {k: e[k] for k in ("markup", "pnl", "win", "pnl_per_win", "curse")} | {
            "naive": nv, "naive_pnl": e["rows"][nv]["pnl"], "naive_win": e["rows"][nv]["win"]}
    return out


def win_model(n_dealers: int = 5, seed: int = 11) -> dict:
    """History: 20,000 requests with our markup drawn uniformly in 0-80 cents against competitors at the equilibrium;
    fit P(win | markup); compare with the simulated win rate at the equilibrium markup."""
    eq = equilibria()[n_dealers]["markup"]
    rng = np.random.default_rng(seed)
    ms = rng.uniform(0.0, 80.0, 20000)
    wins = np.empty(len(ms), bool)
    for i, m in enumerate(ms):
        wins[i] = rm.simulate(n_dealers, float(m), n=1, seed=seed * 100000 + i, comp_markup=eq)["win"][0]
    a, b = rm.fit_win_model(ms, wins)
    fitted = 1.0 / (1.0 + np.exp(-(a + b * eq)))
    edges = np.arange(0.0, 80.1, 10.0)
    bins = [(0.5 * (lo + hi), float(wins[(ms >= lo) & (ms < hi)].mean()))
            for lo, hi in zip(edges[:-1], edges[1:], strict=True)]
    return {"a": a, "b": b, "fitted_at_eq": float(fitted), "simulated_at_eq": equilibria()[n_dealers]["win"],
            "eq": eq, "bins": bins}


def curse_theory(sigma: float = 25.0) -> dict:
    """The expected largest of n estimation errors (firm.rfq.expected_max_normal): the winner's curse before markups."""
    return {n: sigma * rm.rfq.expected_max_normal(n) for n in DEALERS}


def etf_example() -> float:
    return rm.etf_rfq_bid(100.00, 50000, 1250.0, 5.0, 1.0)


def better_model(our_sigma: float = 15.0, n_dealers: int = 5, comp_markup: float = 42.5) -> dict:
    """Exercise 7: our estimate more precise than the competitors'."""
    o = rm.optimise(n_dealers, MARKUPS, n=N, comp_markup=comp_markup, our_sigma=our_sigma)
    return {"markup": o["best"], **o["rows"][o["best"]]}
