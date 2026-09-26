"""One Quant Book 10, chapter 4: the three reasons for a spread, on the chapter's models and the simulated market.

    gm_learning(mus, paths, n)          mean Glosten-Milgrom spread per arrival; trades until it falls to a tenth
    gm_with_cost(mu, dv, c)             quotes and the adverse-selection share when each trade also costs c to process
    kyle_check(sigma_v, sigma_u)        the one-period Kyle model against 100,000 simulated draws
    pin_bias(activity, alpha, samples)  mean fitted PIN of 250-day samples, with and without common activity shocks
    roll_on_tape()                      Roll's estimate from firm.tape's trade prices against the quoted spread
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("spreadmodels", "tape"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_spreadmodels import (  # noqa: E402
    gm_path,
    gm_quotes,
    kyle_one_period,
    kyle_simulate,
    pin,
    pin_fit,
    roll_spread,
    simulate_days,
)
from firm_tape import TapeConfig, simulate  # noqa: E402


def gm_learning(mus=(0.1, 0.3, 0.5), paths: int = 400, n: int = 200) -> dict:
    out = {}
    for mu in mus:
        spreads = np.zeros(n)
        hits = []
        for k in range(paths):
            p = gm_path(k % 2 == 0, mu, n, seed=1000 + k)
            s = p["ask"] - p["bid"]
            spreads += s
            below = np.flatnonzero(s < 0.1 * s[0])
            hits.append(below[0] if len(below) else n)
        out[mu] = {"mean_spread": spreads / paths, "median_trades": float(np.median(hits))}
    return out


def gm_with_cost(mu: float, dv: float = 1.0, c: float = 0.0) -> dict:
    bid, ask = gm_quotes(0.5, mu, 0.0, dv)
    spread = ask - bid + 2 * c
    return {"spread": spread, "adverse_share": (ask - bid) / spread}


def kyle_check(sigma_v: float = 1.0, sigma_u: float = 2.0) -> dict:
    k = kyle_one_period(sigma_v, sigma_u)
    s = kyle_simulate(sigma_v, sigma_u)
    return {"lambda": k["lambda"], "lambda_hat": s["slope"], "posterior": k["posterior_var"],
            "posterior_hat": s["posterior_var"], "profit": k["profit"], "profit_hat": s["profit"]}


@functools.cache
def pin_bias(activity: float, alpha: float, samples: int = 20, days: int = 250) -> dict:
    th = (alpha, 0.5, 60.0, 100.0, 100.0)
    fits = [pin_fit(*simulate_days(days, th, seed=500 + k, activity_sd=activity))["pin"] for k in range(samples)]
    return {"true": pin(th), "mean": float(np.mean(fits)), "sd": float(np.std(fits))}


def roll_on_tape(seconds: float = 3600.0, seed: int = 7) -> dict:
    tp = simulate(TapeConfig(seconds=seconds, seed=seed))
    top = tp.top[tp.n_open:]
    s = top["ask"] - top["bid"]
    dt = np.diff(np.concatenate([top["t"], [tp.cfg.seconds]]))
    signs = tp.trades["sign"].astype(float)
    return {"roll": roll_spread(tp.trades["price"]), "quoted": float((s * dt).sum() / dt.sum()),
            "sign_autocorr": float(np.corrcoef(signs[1:], signs[:-1])[0, 1])}
