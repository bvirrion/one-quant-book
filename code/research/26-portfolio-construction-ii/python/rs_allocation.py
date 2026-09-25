"""Portfolio construction II (One Quant Book 7, chapter 26).

Part A: the 50 largest names of firm.synthmkt, a long-only fully invested book (at most 10% a name), rebuilt monthly
from year 3 to year 10 with chapter 25's alpha forecast and chapter 24's risk model, by eight rules: mean-variance on
the factor model; mean-variance on the sample covariance of the last year; robust mean-variance (an ellipsoid of one
standard error around the alpha); Black-Litterman around capitalisation weights, with each alpha as a view;
equal risk contribution; hierarchical risk parity; equal weights; capitalisation weights. For each: the turnover that
a one-basis-point change in one stock's alpha causes, and the realised performance after costs.
Part B: the same 50 names long-short, daily, with the simulation's three planted expected-return components as
signals (a persistent drift with a half-life of 504 days, a post-earnings drift over 60 days, a one-day reversal) and
quadratic trading costs lambda/2 dx'Sigma dx: daily re-optimisation to the Markowitz portfolio against Garleanu and
Pedersen's aim-portfolio rule, and two simpler rules. NumPy only.
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
sys.path.insert(0, str(HERE.parents[3] / "firm" / "allocation"))
sys.path.insert(0, str(HERE.parents[2] / "25-portfolio-construction-i" / "python"))
from firm_allocation import (  # noqa: E402
    black_litterman,
    erc,
    gp_aim,
    gp_trade_rate,
    hrp,
    implied_returns,
    mean_variance,
    robust_mv,
)
from rs_portcons import COST, IC, MONTH, NOISE, YEAR, dates, forecasts, market, risk  # noqa: E402

N_LONG, CAP, GAMMA_A, KAPPA, TAU = 50, 0.10, 20.0, 3.0, 0.05
METHODS = ("mean-variance", "sample mean-variance", "robust", "Black-Litterman", "equal risk contribution",
           "hierarchical risk parity", "equal weight", "cap weight")


def inputs(t0):
    """The 50 largest of chapter 25's universe: indices, alpha, residual vol, factor-model Sigma, sample Sigma, caps."""
    P, R, cap, _ = market()
    uni, alpha, vol, truth, _ = forecasts()[t0]
    c = np.nan_to_num(cap[t0, uni])
    keep = np.sort(np.argsort(-c)[:N_LONG])
    X, F, spec = risk(t0, uni)
    S = (X @ F @ X.T + np.diag(spec))[np.ix_(keep, keep)]
    Rw = np.nan_to_num(R[t0 - YEAR + 1:t0 + 1][:, uni[keep]])
    return uni[keep], alpha[keep], vol[keep], S, MONTH * np.cov(Rw.T), c[keep] / c[keep].sum()


def redrawn_alpha(t0, draw: int):
    """Chapter 25's forecast with the noise drawn again (an equally good forecast with different errors)."""
    uni, _, vol, truth, _ = forecasts()[t0]
    rng = np.random.default_rng([26, draw, t0])
    f = truth + NOISE * truth.std() * rng.standard_normal(len(uni))
    z = (f - f.mean()) / f.std()
    ids, *_ = inputs(t0)
    keep = np.searchsorted(uni, ids)
    return (IC * vol * z)[keep]


def weights(method: str, t0: int, alpha=None):
    ids, a, vol, S, Ssample, wm = inputs(t0)
    a = a if alpha is None else alpha
    if method == "mean-variance":
        return mean_variance(a, S, GAMMA_A, 0.0, CAP, 1.0)
    if method == "sample mean-variance":
        return mean_variance(a, Ssample, GAMMA_A, 0.0, CAP, 1.0)
    if method == "robust":
        return robust_mv(a, S, np.diag(a.std() ** 2 * np.ones(len(a))), KAPPA, GAMMA_A, 0.0, CAP, 1.0)
    if method == "Black-Litterman":
        pi = implied_returns(S, wm, GAMMA_A)
        Pm = np.eye(len(a))
        mu, post = black_litterman(pi, S, Pm, pi + a, TAU * np.diag(np.diag(S)), TAU)
        return mean_variance(mu, post, GAMMA_A, 0.0, CAP, 1.0)
    if method == "equal risk contribution":
        return erc(S)
    if method == "hierarchical risk parity":
        return hrp(S)
    if method == "equal weight":
        return np.full(len(a), 1.0 / len(a))
    return wm


def stability(method: str, n_dates: int = 6, bp: float = 1e-4):
    """Average and largest one-way turnover (half the sum of absolute weight changes; the book's gross is one)
    caused by adding one basis point to one stock's monthly alpha, over every stock and n_dates rebalances."""
    ds = dates()[:: max(1, len(dates()) // n_dates)][:n_dates]
    out = []
    for t0 in ds:
        _, a, _, _, _, _ = inputs(t0)
        base = weights(method, t0)
        for i in range(len(a)):
            b = a.copy()
            b[i] += bp
            out.append(0.5 * np.abs(weights(method, t0, b) - base).sum())
    return float(np.mean(out)), float(np.max(out))


def redraw_turnover(method: str, n_dates: int = 12, draws: int = 4):
    """Average one-way turnover between the book built on chapter 25's forecast and books built on the same truth
    with the noise drawn again."""
    ds = dates()[:: max(1, len(dates()) // n_dates)][:n_dates]
    out = []
    for t0 in ds:
        base = weights(method, t0)
        for k in range(draws):
            out.append(0.5 * np.abs(weights(method, t0, redrawn_alpha(t0, k)) - base).sum())
    return float(np.mean(out))


@functools.lru_cache(maxsize=16)
def backtest(method: str):
    """Monthly rebuild, held over the month's days; returns, one-way turnover a month, costs at 10 bp of the weight
    traded (both ways)."""
    P, R, _, _ = market()
    prev, daily, net, turns = {}, [], [], []
    for t0 in dates():
        ids, *_ = inputs(t0)
        w = weights(method, t0)
        w0 = np.array([prev.get(i, 0.0) for i in ids])
        traded = float(np.abs(w - w0).sum() + sum(abs(v) for k, v in prev.items() if k not in set(ids.tolist())))
        r = np.nan_to_num(R[t0 + 1:t0 + 1 + MONTH][:, ids]) @ w
        n = r.copy()
        n[0] -= COST * traded
        daily.append(r)
        net.append(n)
        turns.append(0.5 * traded)
        prev = dict(zip(ids.tolist(), w.tolist(), strict=True))
    d, n = np.concatenate(daily), np.concatenate(net)
    sr = lambda x: float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))  # noqa: E731
    top = float(max(np.max(weights(method, t)) for t in dates()[::12]))
    return {"ret": float(d.mean() * YEAR), "vol": float(d.std(ddof=1) * math.sqrt(YEAR)), "sr": sr(d), "sr_net": sr(n),
            "turnover": float(np.mean(turns[1:])), "max_weight": top}


GAMMA_D, RHO = 72.0, 1e-4
PHI = {"momentum": 1 - 0.5 ** (1 / 504), "pead": 1 / 60, "reversal": 1.0}
RULES = ("daily Markowitz", "aim portfolio", "partial adjustment", "monthly Markowitz")


@functools.lru_cache(maxsize=1)
def daily_inputs():
    """Per day from the first rebalance: the names (chapter 25's fifty largest, fixed for the month), the daily
    covariance (the month's forecast / 21), the three signals known at the close, and the next day's returns."""
    P, R, _, _ = market()
    out = []
    for t0 in dates():
        ids, _, _, S, _, _ = inputs(t0)
        Sd = S / MONTH
        for t in range(t0, t0 + MONTH):
            sig = [np.nan_to_num(P.alpha[k][t, ids]) for k in PHI]
            out.append((t, ids, Sd, sig, np.nan_to_num(R[t + 1, ids]), t == t0))
    return out


@functools.lru_cache(maxsize=64)
def multiperiod(rule: str, lam: float):
    """Daily positions (weights of capital, long-short) under one rule; quadratic costs lam/2 dx'Sigma dx."""
    rate = gp_trade_rate(GAMMA_D, lam, RHO)
    a = rate * lam
    prev, gross, cost, turns = {}, [], [], []
    for _t, ids, Sd, sig, ret, first in daily_inputs():
        x0 = np.array([prev.get(i, 0.0) for i in ids])
        gone = sum(v * v for k, v in prev.items() if k not in set(ids.tolist()))
        mk = np.linalg.solve(GAMMA_D * Sd, sum(sig))
        if rule == "daily Markowitz":
            x = mk
        elif rule == "aim portfolio":
            x = (1 - rate) * x0 + rate * gp_aim(Sd, sig, list(PHI.values()), GAMMA_D, a)
        elif rule == "partial adjustment":
            x = (1 - rate) * x0 + rate * mk
        else:
            x = np.linalg.solve(GAMMA_D * Sd, sig[0] + sig[1]) if first else x0
        dx = x - x0
        cost.append(0.5 * lam * float(dx @ Sd @ dx) + 0.5 * lam * gone * float(np.mean(np.diag(Sd))))
        gross.append(float(x @ ret))
        turns.append(float(np.abs(dx).sum()))
        prev = dict(zip(ids.tolist(), x.tolist(), strict=True))
    g, c = np.array(gross), np.array(cost)
    n = g - c
    sr = lambda v: float(v.mean() / v.std(ddof=1) * math.sqrt(YEAR))  # noqa: E731
    return {"sr": sr(g), "sr_net": sr(n), "ret": float(g.mean() * YEAR), "cost": float(c.mean() * YEAR),
            "vol": float(g.std(ddof=1) * math.sqrt(YEAR)), "turnover": float(np.mean(turns)), "rate": rate}
