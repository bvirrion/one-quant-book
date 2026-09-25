"""firm.vecbt -- the level-1 (vectorised) backtester and the BacktestResult type (build of Book 7, chapter 16).

A target book is a panel of weights (T periods x N names), each row decided at the close of its period from what was
known then. The backtester enforces an execution lag (the number of periods between the decision and the first
return the book earns), a tradable-universe mask, per-name position caps, linear trading costs on the weight traded,
borrow fees on short positions, interest on cash and on borrowed cash, and compounding (or not). It returns a
BacktestResult, the type every backtester of the firm returns (firm.evbt, firm.lobreplay) and firm.perf reads.

API (stable):
    BacktestResult(dates, names, weights, trades, gross, costs, net, capital, meta)
        weights (T, N)    the book held over each period, as a fraction of capital at the period's start
        trades (T, N)     the weight traded at the start of each period (to reach `weights` from the drifted book)
        gross (T,)        return of the book over the period before costs
        costs {k: (T,)}   'trading', 'borrow', 'financing' (financing may be negative: interest earned)
        net (T,)          gross minus all costs
        capital (T,)      capital at the end of each period (compounded from 1, or cumulated if not compounding)
        .turnover (T,)    sum of |trades| / 2;  .gross_exposure (T,), .net_exposure (T,)
    signal_to_weights(signal, universe, gross, neutral)   z-scored signal to a book of given gross, dollar neutral
    backtest(weights, returns, lag, universe, cost, borrow, cash_rate, borrow_spread, cap, compound, periods)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class BacktestResult:
    dates: np.ndarray
    names: np.ndarray
    weights: np.ndarray
    trades: np.ndarray
    gross: np.ndarray
    costs: dict
    net: np.ndarray
    capital: np.ndarray
    meta: dict = field(default_factory=dict)

    @property
    def turnover(self) -> np.ndarray:
        return np.abs(self.trades).sum(axis=1) / 2.0

    @property
    def gross_exposure(self) -> np.ndarray:
        return np.abs(self.weights).sum(axis=1)

    @property
    def net_exposure(self) -> np.ndarray:
        return self.weights.sum(axis=1)


def signal_to_weights(signal, universe=None, gross: float = 1.0, neutral: bool = True) -> np.ndarray:
    """Each row: the signal over the names in the universe (NaN or outside: weight 0), z-scored across them if
    neutral (a dollar-neutral book) or taken as it is otherwise, scaled to the given gross exposure."""
    s = np.asarray(signal, float)
    if universe is not None:
        s = np.where(universe, s, np.nan)
    if neutral:
        s = (s - np.nanmean(s, axis=1, keepdims=True)) / np.nanstd(s, axis=1, keepdims=True)
    z = np.nan_to_num(s)
    g = np.abs(z).sum(axis=1, keepdims=True)
    return np.where(g > 0, z / np.where(g > 0, g, 1.0) * gross, 0.0)


def backtest(weights, returns, lag: int = 1, universe=None, cost=0.0, borrow: float = 0.0, cash_rate: float = 0.0,
             borrow_spread: float = 0.0, cap: float | None = None, compound: bool = True, periods: int = 252,
             dates=None, names=None) -> BacktestResult:
    """weights[t] is decided at the close of period t; with lag L it is held over period t + L (lag 0 is the
    look-ahead of multiplying a book by the return that produced it). Names outside the universe at decision time are
    not held; a return that is NaN (not listed) earns nothing. cost: per unit of weight traded, a scalar or (T, N).
    borrow, cash_rate, borrow_spread: annual rates; cash = 1 - sum of weights earns cash_rate, negative cash pays
    cash_rate + borrow_spread; short positions pay borrow."""
    w = np.asarray(weights, float).copy()
    r = np.nan_to_num(np.asarray(returns, float))
    T, N = r.shape
    if universe is not None:
        w = np.where(universe, w, 0.0)
    if cap is not None:
        w = np.clip(w, -cap, cap)
    held = np.zeros((T, N))
    if lag == 0:
        held = w
    else:
        held[lag:] = w[:-lag]
    trades = np.zeros((T, N))
    drift = np.zeros(N)
    c = np.broadcast_to(np.asarray(cost, float), (T, N)) if np.ndim(cost) else np.full((T, N), float(cost))
    gross, tcost, bcost, fin = (np.zeros(T) for _ in range(4))
    for t in range(T):
        trades[t] = held[t] - drift
        tcost[t] = float(np.abs(trades[t]) @ c[t])
        gross[t] = float(held[t] @ r[t])
        bcost[t] = borrow / periods * float(-held[t][held[t] < 0].sum())
        cash = 1.0 - held[t].sum()
        fin[t] = -(cash_rate / periods) * cash if cash >= 0 else -(cash_rate + borrow_spread) / periods * cash
        grown = held[t] * (1.0 + r[t])
        total = 1.0 + gross[t]
        drift = grown / total if total > 0 else np.zeros(N)
    net = gross - tcost - bcost - fin
    capital = np.cumprod(1.0 + net) if compound else 1.0 + np.cumsum(net)
    return BacktestResult(np.arange(T) if dates is None else np.asarray(dates),
                          np.arange(N) if names is None else np.asarray(names), held, trades, gross,
                          {"trading": tcost, "borrow": bcost, "financing": fin}, net, capital,
                          {"lag": lag, "compound": compound, "periods": periods})
