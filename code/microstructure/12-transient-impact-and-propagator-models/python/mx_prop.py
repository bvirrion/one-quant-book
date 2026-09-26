"""One Quant Book 10, chapter 12: the propagator model on a simulated market, and which kernels let a trader profit.

    MARKET                        firm.agentmkt's population with noise-order signs in runs of Pareto length (tail 1.5)
    flow(seed, seconds)           market orders (executions merged) with the mid just before each: signs, prices
    kernel_study(seed)            the sign autocorrelation and its power-law exponent, the response, the fitted kernel,
                                  and the diffusion check: the variance of price changes over l orders divided by l,
                                  for the market and for the propagator driven by the same signs (cached)
    kernel_family(kappas)         kernels G(t) = exp(-(t / tau)^kappa) on 21 trades over one unit of time: the most
                                  profitable round trip and the smallest trade of the optimal liquidation
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("agentmkt", "exchsim", "impactfit", "propagator"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_agentmkt import PopulationConfig, session  # noqa: E402
from firm_impactfit import orders  # noqa: E402
from firm_propagator import (  # noqa: E402
    fit_kernel,
    impact_matrix,
    optimal_liquidation,
    propagate,
    response,
    round_trip,
    sign_acf,
)

MARKET = PopulationConfig(lo_rate=3.0, near=0.3, cancel=0.05, depth=10, fund=0.05, run_tail=1.5)
LAGS = (1, 2, 5, 10, 20, 50, 100)


def flow(seed: int = 1, seconds: float = 7200.0):
    res, _ = session(MARKET, seconds, seed)
    tp = res.tape()
    top = tp.top
    ok = (top["bid"] > 0) & (top["ask"] > 0)
    tt, mid = top["t"][ok], 0.5 * (top["bid"][ok] + top["ask"][ok])
    o = orders(tp.trades)
    p = mid[np.clip(np.searchsorted(tt, o["t"] - 1e-9, side="right") - 1, 0, len(mid) - 1)]
    return o["sign"].astype(float), p


def _var_ratio(p, lags):
    return [float(np.var(p[lag:] - p[:-lag]) / lag) for lag in lags]


@functools.cache
def kernel_study(seed: int = 1) -> dict:
    eps, p = flow(seed)
    c = sign_acf(eps, 200)
    lag = np.arange(2, 51)                              # where the correlation is well above its noise
    gamma = float(-np.polyfit(np.log(lag), np.log(c[2:51]), 1)[0])
    r = response(eps, p, 100)
    k, g = fit_kernel(eps, p, 100)
    model = propagate(eps, g)
    return {"n": len(eps), "acf": c, "gamma": gamma, "response": r, "G": g,
            "var_market": _var_ratio(p, LAGS), "var_model": _var_ratio(model, LAGS),
            "var_shuffled": _var_ratio(propagate(np.random.default_rng(seed).permutation(eps), g), LAGS)}


KAPPAS = (0.5, 1.0, 1.5, 1.8, 2.2, 2.5, 3.0)       # 2 itself (the Gaussian) is singular on a fine grid


def kernel_family(kappas=KAPPAS, n: int = 21, tau: float = 0.3) -> dict:
    t = np.linspace(0.0, 1.0, n)
    out = {}
    for kap in kappas:
        gam = impact_matrix(t, lambda x, kap=kap: np.exp(-((x / tau) ** kap)))
        x = optimal_liquidation(gam, 1.0)
        out[kap] = {"round_trip": round_trip(gam), "min_trade": float(x.min()), "buys": int(np.sum(x < 0))}
    return out
