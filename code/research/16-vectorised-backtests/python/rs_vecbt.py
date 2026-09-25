"""Vectorised backtests (One Quant Book 7, chapter 16).

The one-day reversal on firm.synthmkt (seed 1): a dollar-neutral book of gross exposure 1, rebuilt every day from
minus the day's return, backtested in one vectorised pass and then corrected one lie at a time: the universe of the
names alive at the end of the sample; the names listed at each decision; the 500 most liquid; trading costs; borrow
fees; and trading at the next close instead of the close the signal was computed from. NumPy only.
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("vecbt", "synthmkt", "features"):
    sys.path.insert(0, str(ROOT / c))
from firm_features import past_return  # noqa: E402
from firm_synthmkt import simulate  # noqa: E402
from firm_vecbt import backtest, signal_to_weights  # noqa: E402

YEAR, TOP, COST, BORROW = 252, 500, 0.0010, 0.005


@functools.lru_cache(maxsize=1)
def panel():
    return simulate()


def sharpe(x) -> float:
    x = np.asarray(x, float)[1:]
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


def liquid(P, top: int = TOP, window: int = 21) -> np.ndarray:
    """The `top` names by mean dollar volume over the last `window` days, as known at each close."""
    dv = np.where(P.listed, P.price * P.volume, 0.0)
    c = np.cumsum(dv, axis=0)
    avg = (c - np.vstack([np.zeros((window, dv.shape[1])), c[:-window]])) / window
    rank = np.argsort(np.argsort(-avg, axis=1), axis=1)
    return (rank < top) & P.listed


def monthly(w: np.ndarray, every: int = 21) -> np.ndarray:
    """Hold each month-end's book for the month: rows between rebalances repeat the last rebalance's weights."""
    idx = (np.arange(len(w)) // every) * every
    return w[idx]


def waterfall(signal: str = "reversal"):
    """Sharpe ratio (annualised), mean annual return and mean daily turnover of each step; each step keeps the
    corrections before it."""
    P = panel()
    R = P.ret
    sig = -np.nan_to_num(P.ret) if signal == "reversal" else past_return(P.ret, YEAR - 21, 21)
    survivors = np.broadcast_to(P.listed[-1], P.listed.shape)
    steps = [("naive", dict(universe=survivors & P.listed, lag=1, cost=0.0, borrow=0.0)),
             ("point-in-time universe", dict(universe=P.listed, lag=1, cost=0.0, borrow=0.0)),
             ("500 most liquid", dict(universe=liquid(P), lag=1, cost=0.0, borrow=0.0)),
             ("10 bp costs", dict(universe=liquid(P), lag=1, cost=COST, borrow=0.0)),
             ("borrow 50 bp", dict(universe=liquid(P), lag=1, cost=COST, borrow=BORROW)),
             ("next close", dict(universe=liquid(P), lag=2, cost=COST, borrow=BORROW))]
    out = []
    for name, k in steps:
        w = signal_to_weights(sig, k["universe"])
        if signal != "reversal":
            w = monthly(w)
        res = backtest(w, R, lag=k["lag"], cost=k["cost"], borrow=k["borrow"])
        out.append((name, sharpe(res.net), float(res.net[1:].mean() * YEAR), float(res.turnover[2:].mean()), res))
    return out


def lookahead():
    """The lag-0 backtest: the book built from today's close multiplied by today's return."""
    P = panel()
    w = signal_to_weights(-np.nan_to_num(P.ret), P.listed)
    res = backtest(w, P.ret, lag=0)
    return sharpe(res.net), float(res.net.mean() * YEAR)


def breakeven_cost():
    """The cost per unit traded at which the liquid, close-trading reversal book's net return is zero."""
    P = panel()
    w = signal_to_weights(-np.nan_to_num(P.ret), liquid(P))
    res = backtest(w, P.ret, lag=1)
    return float(res.gross[1:].mean() / (2 * res.turnover[2:].mean()))


def compounding():
    """Final capital of the liquid, costed, close-trading book with and without compounding (it matters when the
    returns are large)."""
    P = panel()
    w = signal_to_weights(-np.nan_to_num(P.ret), liquid(P))
    a = backtest(w, P.ret, lag=1, cost=COST, borrow=BORROW, compound=True)
    b = backtest(w, P.ret, lag=1, cost=COST, borrow=BORROW, compound=False)
    return float(a.capital[-1]), float(b.capital[-1])


def smoothed(days: int = 3):
    """Exercise 7: the reversal built from minus the mean of the last `days` returns, on the liquid universe, traded
    at the signal's close: turnover, gross Sharpe ratio and break-even cost per unit traded."""
    P = panel()
    r = np.nan_to_num(P.ret)
    c = np.cumsum(r, axis=0)
    avg = (c - np.vstack([np.zeros((days, r.shape[1])), c[:-days]])) / days
    w = signal_to_weights(-avg, liquid(P))
    res = backtest(w, P.ret, lag=1)
    return {"turnover": float(res.turnover[2:].mean()), "sharpe": sharpe(res.gross),
            "breakeven": float(res.gross[1:].mean() / (2 * res.turnover[2:].mean()))}
