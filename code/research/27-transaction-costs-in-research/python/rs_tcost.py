"""Transaction costs in research (One Quant Book 7, chapter 27).

Part A: a year of the firm's parent orders, simulated from a planted cost law (half spread 2 bp, square-root impact
0.7 sigma sqrt(Q / V)) plus the price's move while the order works; the law estimated back from the fills.
Part B: chapter 26's fifty names traded daily from a noisy forecast of the three planted signals (the true expected
return plus noise as large, new each day), with spread and square-root impact at a range of fund sizes: the
mean-variance book ignoring costs, the book optimised with the costs inside (firm.tcost.cost_aware), and both on the
forecast smoothed with a half-life. Net Sharpe ratio against fund size and against the smoothing half-life. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "firm" / "tcost"))
sys.path.insert(0, str(HERE.parents[2] / "26-portfolio-construction-ii" / "python"))
from firm_tcost import cost_aware, fit_impact, impact_bp, trade_cost  # noqa: E402
from rs_allocation import daily_inputs  # noqa: E402
from rs_portcons import YEAR, adv, dates, market  # noqa: E402

ETA, EXPONENT, HALF_SPREAD, N_ORDERS = 0.7, 0.5, 2e-4, 5000
GAMMA, NOISE, SEED = 72.0, 1.5, 27
AUMS = (1e7, 1e8, 1e9, 1e10)


@functools.lru_cache(maxsize=4)
def fills(n: int = N_ORDERS, seed: int = SEED):
    """(cost, sigma, participation) of n parent orders: participation log-uniform from 0.01% to 20% of daily volume,
    daily volatility from 1% to 3%, cost = half spread + impact + the price's move over the order's life (a normal
    with standard deviation sigma * sqrt(participation / 0.1), the order working at 10% of volume)."""
    rng = np.random.default_rng(seed)
    part = np.exp(rng.uniform(math.log(1e-4), math.log(0.2), n))
    sigma = rng.uniform(0.01, 0.03, n)
    move = sigma * np.sqrt(part / 0.1) * rng.standard_normal(n)
    return HALF_SPREAD + impact_bp(ETA, sigma, part, EXPONENT) + move, sigma, part


def estimate(n: int = N_ORDERS, seed: int = SEED):
    return fit_impact(*fills(n, seed), HALF_SPREAD)


@functools.lru_cache(maxsize=1)
def liquidity():
    """ADV (dollars) of each month's fifty names."""
    out = {}
    for t0 in dates():
        ids = daily_inputs_ids(t0)
        _, _, cap, _ = market()
        uni_all = np.array(sorted(ids))
        out[t0] = dict(zip(uni_all.tolist(), adv(t0, uni_all).tolist(), strict=True))
    return out


def daily_inputs_ids(t0):
    for t, ids, *_ in daily_inputs():
        if t == t0:
            return ids
    raise KeyError(t0)


@functools.lru_cache(maxsize=64)
def run(book: str, aum: float, half_life: float = 0.0, noise: float = NOISE):
    """Daily positions; book 'naive' (mean-variance, costs ignored) or 'cost-aware'; the forecast smoothed with the
    half-life (days, 0: raw). Costs: half spread and square-root impact at fund size aum."""
    rng = np.random.default_rng(SEED)
    liq = liquidity()
    lam = 0.5 ** (1.0 / half_life) if half_life > 0 else 0.0
    prev, state, gross, cost, turns = {}, {}, [], [], []
    t0 = None
    for t, ids, Sd, sig, ret, first in daily_inputs():
        if first:
            t0 = t
        truth = sum(sig)
        f = truth + noise * truth.std() * rng.standard_normal(len(ids))
        s = np.array([lam * state[i] + (1 - lam) * f[k] if i in state else f[k] for k, i in enumerate(ids)])
        state = dict(zip(ids.tolist(), s.tolist(), strict=True))
        sd = np.sqrt(np.diag(Sd))
        a = np.array([liq[t0][i] for i in ids])
        w0 = np.array([prev.get(i, 0.0) for i in ids])
        gone = np.array([v for k, v in prev.items() if k not in set(ids.tolist())])
        if book == "naive":
            w = np.linalg.solve(GAMMA * Sd, s)
        else:
            w = cost_aware(s, Sd, w0, aum, sd, a, np.full(len(ids), HALF_SPREAD), ETA, GAMMA, iters=300)
        c = trade_cost(w - w0, aum, sd, a, np.full(len(ids), HALF_SPREAD), ETA)
        if len(gone):
            c += trade_cost(gone, aum, np.full(len(gone), sd.mean()), np.full(len(gone), a.mean()),
                            np.full(len(gone), HALF_SPREAD), ETA)
        gross.append(float(w @ ret))
        cost.append(c)
        turns.append(float(np.abs(w - w0).sum()))
        prev = dict(zip(ids.tolist(), w.tolist(), strict=True))
    g, c = np.array(gross), np.array(cost)
    sr = lambda v: float(v.mean() / v.std(ddof=1) * math.sqrt(YEAR))  # noqa: E731
    return {"sr": sr(g), "sr_net": sr(g - c), "ret": float(g.mean() * YEAR), "cost": float(c.mean() * YEAR),
            "vol": float(g.std(ddof=1) * math.sqrt(YEAR)), "turnover": float(np.mean(turns))}


HALF_LIVES = (0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0)


def smoothing_curve(book: str, aum: float = 1e9):
    return {h: run(book, aum, h)["sr_net"] for h in HALF_LIVES}


@functools.lru_cache(maxsize=4)
def netting(aum: float = 1e9, half_life: float = 20.0):
    """Two teams trade the same names from their own forecasts of the same truth (independent noise, each smoothed
    with the half-life, each the mean-variance book): their trades cost apart and netted (fractions of the firm's
    capital a year, each team running aum). The saving comes from trades in opposite directions; where the teams
    trade the same way, square-root impact makes the combined trade cost more than the two apart. All costs are in
    units of one team's capital a year."""
    liq = liquidity()
    rng = {k: np.random.default_rng(SEED + j) for j, k in enumerate(("a", "b"))}
    lam = 0.5 ** (1.0 / half_life)
    prev, state = {"a": {}, "b": {}}, {"a": {}, "b": {}}
    alone = {"a": 0.0, "b": 0.0}
    netted = same_extra = 0.0
    days, t0 = 0, None
    for t, ids, Sd, sig, _ret, first in daily_inputs():
        if first:
            t0 = t
        sd = np.sqrt(np.diag(Sd))
        adv_ = np.array([liq[t0][i] for i in ids])
        hs = np.full(len(ids), HALF_SPREAD)
        truth = sum(sig)
        dw = {}
        for k in ("a", "b"):
            f = truth + NOISE * truth.std() * rng[k].standard_normal(len(ids))
            sm = np.array([lam * state[k][i] + (1 - lam) * f[j] if i in state[k] else f[j] for j, i in enumerate(ids)])
            state[k] = dict(zip(ids.tolist(), sm.tolist(), strict=True))
            w = np.linalg.solve(GAMMA * Sd, sm)
            w0 = np.array([prev[k].get(i, 0.0) for i in ids])
            dw[k] = w - w0
            alone[k] += trade_cost(dw[k], aum, sd, adv_, hs, ETA)
            prev[k] = dict(zip(ids.tolist(), w.tolist(), strict=True))
        both = dw["a"] + dw["b"]
        netted += trade_cost(both, aum, sd, adv_, hs, ETA)             # both in weights of one team's capital
        same = np.sign(dw["a"]) == np.sign(dw["b"])
        same_extra += trade_cost(np.where(same, both, 0), aum, sd, adv_, hs, ETA) - \
            sum(trade_cost(np.where(same, dw[k], 0), aum, sd, adv_, hs, ETA) for k in ("a", "b"))
        days += 1
    k = YEAR / days
    total = alone["a"] + alone["b"]
    return {"a": alone["a"] * k, "b": alone["b"] * k, "netted": netted * k, "saving": (total - netted) * k,
            "saving_share": (total - netted) / total, "same_side_extra": same_extra * k}
