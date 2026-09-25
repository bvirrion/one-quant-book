"""Options-implied signals for stocks (One Quant Book 8, chapter 15).

An options layer on firm.synthmkt (seed 1): implied volatilities and option volume for every stock and day, with
informed traders who, in the ten days before each earnings announcement, buy puts ahead of bad surprises (weighted
1.5) and calls ahead of good ones (firm.optsignal). Over years 3 to 10: the mean daily rank IC of the skew (minus),
the call-put volatility spread, the option-to-stock volume ratio (minus) and implied minus realised volatility against
the market-adjusted return over the next 1, 5, 20 and 60 days, in all stocks and in those announcing within ten days;
and a weekly decile book on the volatility spread (in all stocks, or only in those announcing within ten days), before
and after 10 basis points per unit traded. NumPy only.
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

FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("optsignal", "earnstrat", "factorlib", "vecbt", "predictor", "synthmkt"):
    sys.path.insert(0, str(FIRM / c))
from firm_earnstrat import calendar  # noqa: E402
from firm_factorlib import sort_book  # noqa: E402
from firm_optsignal import OptionConfig, signals, simulate_options  # noqa: E402
from firm_predictor import ic_series  # noqa: E402
from firm_synthmkt import simulate  # noqa: E402
from firm_vecbt import backtest  # noqa: E402

YEAR, START, WEEK, COST, HORIZONS = 252, 504, 5, 0.0010, (1, 5, 20, 60)
SIGNS = {"skew": -1, "spread": 1, "os": -1, "ivrv": 1}


@functools.lru_cache(maxsize=1)
def market():
    P = simulate()
    R = np.where(P.listed, P.ret, np.nan)
    cap = np.where(P.listed, P.price * P.shares, 0.0)
    cprev = np.vstack([cap[:1], cap[:-1]])
    mkt = np.nansum(cprev * np.nan_to_num(R), axis=1) / np.maximum(cprev.sum(axis=1), 1e-12)
    lr = np.log1p(np.nan_to_num(R))
    c2 = np.cumsum(lr * lr, axis=0)
    rv = np.sqrt(np.maximum((c2 - np.vstack([np.zeros((63, lr.shape[1])), c2[:-63]])) / 63, 1e-8) * YEAR)
    flag, sur = calendar(P.earnings, *R.shape)
    opt = simulate_options(flag, sur, P.listed, rv, OptionConfig())
    return P, R, mkt, flag, signals(opt, rv)


def forward(h: int):
    P, R, mkt, *_ = market()
    ab = np.log1p(np.nan_to_num(R)) - np.log1p(mkt)[:, None]
    c = np.concatenate([np.zeros((1, ab.shape[1])), np.cumsum(ab, axis=0)])
    T = ab.shape[0]
    y = np.full(ab.shape, np.nan)
    y[:T - h] = c[h + 1:] - c[1:T - h + 1]
    return np.where(P.listed, y, np.nan)


def upcoming(window: int = 10):
    """True where the stock announces within the next `window` days."""
    _, _, _, flag, _ = market()
    out = np.zeros(flag.shape, bool)
    for k in range(1, window + 1):
        out[:-k] |= flag[k:]
    return out


@functools.lru_cache(maxsize=32)
def ic(name: str, h: int, only_events: bool = False):
    P, *_, sig = market()
    s = SIGNS[name] * sig[name]
    if only_events:
        s = np.where(upcoming(), s, np.nan)
    rows = np.arange(START, P.ret.shape[0] - 60)
    v = ic_series(s[rows], forward(h)[rows], min_names=10)
    return float(np.nanmean(v))


@functools.lru_cache(maxsize=8)
def book(name: str = "spread", events: bool = False):
    """Weekly decile book on the signal (in all stocks, or only in those announcing within ten days)."""
    P, R, *_, sig = market()
    s = SIGNS[name] * sig[name]
    if events:
        s = np.where(upcoming(), s, np.nan)
    W = sort_book(s, P.listed & np.isfinite(s), 0.2 if events else 0.1)
    W = W[(np.arange(len(W)) // WEEK) * WEEK]
    res = backtest(W, R, lag=1, cost=COST)
    g, n = res.gross[START:], res.net[START:]
    sr = lambda x: float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))  # noqa: E731
    return {"sr_gross": sr(g), "sr_net": sr(n), "ret_gross": float(g.mean() * YEAR), "ret_net": float(n.mean() * YEAR)}
