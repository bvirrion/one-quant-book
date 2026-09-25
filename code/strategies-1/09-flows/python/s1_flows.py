"""Flows (One Quant Book 8, chapter 9).

Two hundred simulated mutual funds on firm.synthmkt (seed 1) hold 60 stocks each, chosen at random (or tilted to a
style of their own, a variant) and a quarter of them replaced every quarter; together
they own about 20% of each stock; each quarter their flows chase their trailing one-year returns (5% of assets per
standard deviation, plus 3% of noise), and each stock's flow-induced trading pushes its price by 1.5 per unit over the
quarter, a push that then reverses with a half-life of 126 days (MarketConfig untouched: firm.flowpress adds the
pressure on top). Measured: the price response per unit of flow-induced trading; the event-time path of the top and
bottom deciles; a book that forecasts next quarter's flow-induced trading from trailing fund returns and holdings known
with the 13F lag of 45 days; and a fire-sale reversal book entered when the quarter's trading can be known, held a year.
Costs of 10 basis points per unit traded. NumPy only.
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
FIRM = HERE.parents[3] / "firm"
for c in ("flowpress", "factorlib", "synthmkt", "vecbt"):
    sys.path.insert(0, str(FIRM / c))
from firm_factorlib import sort_book  # noqa: E402
from firm_flowpress import FlowConfig, simulate_flows  # noqa: E402
from firm_synthmkt import simulate  # noqa: E402
from firm_vecbt import backtest  # noqa: E402

YEAR, QTR, LAG, COST, START = 252, 63, 45, 0.0010, 504


@functools.lru_cache(maxsize=4)
def world(impact: float = 1.5, tilt: float = 0.0):
    P = simulate()
    R = np.where(P.listed, P.ret, np.nan)
    out = simulate_flows(R, P.listed, P.style_x, FlowConfig(impact=impact, tilt=tilt))
    return P, out


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


@functools.lru_cache(maxsize=2)
def response(impact: float = 1.5):
    """Cross-sectional slope of each quarter's log return on its flow-induced trading (median over quarters), and the
    slope of the following year's return (from the quarter's end) on it."""
    P, out = world(impact)
    lr = np.log1p(np.nan_to_num(out["R"]))
    c = np.concatenate([np.zeros((1, lr.shape[1])), np.cumsum(lr, axis=0)])
    T = lr.shape[0]
    now, later = [], []
    for k, t0 in enumerate(out["quarters"]):
        if t0 + QTR + YEAR > T:
            break
        ok = P.listed[t0:t0 + QTR + YEAR].all(axis=0)
        f = out["fit"][k][ok]
        y0 = (c[t0 + QTR] - c[t0])[ok]
        y1 = (c[t0 + QTR + YEAR] - c[t0 + QTR])[ok]
        now.append(np.polyfit(f, y0, 1)[0])
        later.append(np.polyfit(f, y1, 1)[0])
    return {"now": float(np.median(now)), "later": float(np.median(later)),
            "reversed": float(-np.median(later) / np.median(now)), "fit_sd": float(np.nanstd(out["fit"]))}


def event_path(impact: float = 1.5, span: int = 3 * YEAR, tilt: float = 0.0):
    """Mean cumulative log return, from each quarter's start, of the top and bottom deciles of that quarter's
    flow-induced trading, minus the cross-sectional mean."""
    P, out = world(impact, tilt)
    lr = np.log1p(np.nan_to_num(out["R"]))
    T = lr.shape[0]
    top, bot = [], []
    for k, t0 in enumerate(out["quarters"]):
        if t0 + span > T:
            break
        ok = P.listed[t0:t0 + span].all(axis=0)
        f = np.where(ok, out["fit"][k], np.nan)
        hi, lo = np.nanpercentile(f, 90), np.nanpercentile(f, 10)
        ab = lr[t0:t0 + span][:, ok] - lr[t0:t0 + span][:, ok].mean(axis=1, keepdims=True)
        fk = f[ok]
        top.append(np.cumsum(ab[:, fk >= hi].mean(axis=1)))
        bot.append(np.cumsum(ab[:, fk <= lo].mean(axis=1)))
    return np.mean(top, axis=0), np.mean(bot, axis=0)


@functools.lru_cache(maxsize=4)
def books(impact: float = 1.5):
    """The expected-flow book and the fire-sale reversal book: daily net returns over the evaluation days."""
    P, out = world(impact)
    R = out["R"]
    T, N = R.shape
    Wf, Wr = np.zeros((T, N)), np.zeros((T, N))
    zs, fl = [], []
    for k, t0 in enumerate(out["quarters"]):
        tr = out["trailing"][k]
        z = (tr - tr.mean()) / tr.std()
        if len(zs) >= 4:                                   # the flow-performance slope from past quarters only
            b = np.polyfit(np.concatenate(zs), np.concatenate(fl), 1)[0]
            own = out["own"][k - 1]                         # holdings at the previous quarter-end, filed by now
            pred = (b * z) @ own
            s = np.where(P.listed[t0], pred, np.nan)
            Wf[t0:t0 + QTR] = sort_book(s[None, :], np.isfinite(s)[None, :])[0]
        zs.append(z)
        fl.append(out["flow"][k])
        tr0 = t0 + QTR + LAG                                # the quarter's trading is known from the next 13F
        if tr0 < T:
            s = np.where(P.listed[tr0], -out["fit"][k], np.nan)
            w = sort_book(s[None, :], np.isfinite(s)[None, :])[0] / 4   # four overlapping yearly books
            Wr[tr0:min(tr0 + YEAR, T)] += w
    res = {}
    for name, W in (("expected", Wf), ("reversal", Wr)):
        bt = backtest(W, R, lag=1, cost=COST)
        n = bt.net[START:]
        res[name] = {"net": n, "sr": sharpe(n), "ret": float(n.mean() * YEAR),
                     "sr_gross": sharpe(bt.gross[START:]),
                     "turnover": float(bt.turnover[START:].sum() / (len(n) / YEAR))}
    return res
