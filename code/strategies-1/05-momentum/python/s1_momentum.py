"""Momentum (One Quant Book 8, chapter 5).

On firm.synthmkt (seed 1), years 3 to 10: 12-1 month total-return momentum, residual momentum (on Book 7 chapter 24's
point-in-time residuals) and industry momentum, each as a decile long-short book (gross 1, equal weights) rebuilt every
21 days and held in between; the rank IC against the next month's return; Sharpe ratios before and after 10 basis
points per unit traded; the book's market beta in bear markets (the market down over the previous two years) and in
bull markets, which is where crashes come from; volatility scaling of each book to 10% a year from its trailing 126-day
volatility. The French momentum factor's derived statistics are read from data/strategies-1 (s1_fetch_mom.py).
NumPy only.
"""
from __future__ import annotations

import csv
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
for c in ("momstrat", "vecbt", "predictor"):
    sys.path.insert(0, str(FIRM / c))
sys.path.insert(0, str(HERE.parents[3] / "research" / "24-risk-models" / "python"))
from firm_momstrat import bear, decile_book, industry_mom, residual_mom, total_mom, vol_scale  # noqa: E402
from firm_predictor import ic_series  # noqa: E402
from firm_vecbt import backtest  # noqa: E402
from rs_riskmodel import START, fundamental, market  # noqa: E402

YEAR, MONTH, COST, TARGET, WINDOW = 252, 21, 0.0010, 0.10, 126
DATA = HERE.parents[4] / "data" / "strategies-1"


@functools.lru_cache(maxsize=1)
def signals():
    P, R, cap, _ = market()
    E = fundamental()["E"]
    return {"total": np.where(P.listed, total_mom(R), np.nan),
            "residual": np.where(P.listed, residual_mom(E), np.nan),
            "industry": np.where(P.listed, industry_mom(R, P.industry, cap), np.nan)}


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


def max_drawdown(r) -> float:
    w = np.cumprod(1 + np.asarray(r, float))
    return float((w / np.maximum.accumulate(w) - 1).min())


@functools.lru_cache(maxsize=8)
def book(kind: str):
    """Daily net and gross returns of the monthly decile book over the evaluation days, and its turnover."""
    P, R, _, _ = market()
    s = signals()[kind]
    W = decile_book(s, P.listed & np.isfinite(s))
    idx = (np.arange(len(W)) // MONTH) * MONTH                  # rebuilt every 21 days, held in between
    W = W[idx]
    res = backtest(W, np.where(P.listed, R, np.nan), lag=1, cost=COST)
    g, n = res.gross[START:], res.net[START:]
    return {"gross": g, "net": n, "turnover": float(res.turnover[START:].sum() / (len(g) / YEAR))}


def ic(kind: str) -> float:
    P, R, _, _ = market()
    lr = np.log1p(np.where(P.listed, R, np.nan))
    c = np.concatenate([np.zeros((1, lr.shape[1])), np.cumsum(np.nan_to_num(lr), axis=0)])
    T = lr.shape[0]
    y = np.full(lr.shape, np.nan)
    y[:T - MONTH] = c[MONTH + 1:] - c[1:T - MONTH + 1]           # log return over t + 1 .. t + 21
    rows = np.arange(START, T - MONTH, MONTH)
    v = ic_series(signals()[kind][rows], np.where(P.listed[rows + MONTH], y[rows], np.nan))
    return float(np.nanmean(v))


def summary(kind: str):
    b = book(kind)
    g, n = b["gross"], b["net"]
    return {"sr_gross": sharpe(g), "sr_net": sharpe(n), "ret_net": float(n.mean() * YEAR),
            "vol": float(n.std(ddof=1) * math.sqrt(YEAR)), "maxdd": max_drawdown(n), "turnover": b["turnover"],
            "ic": ic(kind)}


def betas(kind: str):
    """The book's daily beta on the cap-weighted market in bear and in bull states (market down or up over the
    previous 504 days, known at the close before)."""
    P, R, _, mkt = market()
    n = book(kind)["net"]
    m = mkt[START:]
    state = bear(mkt, 2 * YEAR)
    st = np.r_[False, state[:-1]][START:]
    out = {}
    for name, mask in (("bear", st), ("bull", ~st)):
        x, y = m[mask], n[mask]
        out[name] = float(np.cov(x, y)[0, 1] / x.var(ddof=1))
    out["bear_days"] = float(st.mean())
    return out


def scaled(kind: str):
    """The book scaled to TARGET by its own trailing volatility (weights known the day before)."""
    n = book(kind)["net"]
    w = vol_scale(n, TARGET, WINDOW)
    r = (w * n)[WINDOW:]
    raw = n[WINDOW:]
    return {"sr_raw": sharpe(raw), "sr_scaled": sharpe(r), "dd_raw": max_drawdown(raw), "dd_scaled": max_drawdown(r),
            "worst_raw": float(raw.min()), "worst_scaled": float(r.min()), "mean_w": float(np.nanmean(w[WINDOW:]))}


def french():
    """The French momentum factor's derived statistics (raw and volatility-scaled)."""
    with open(DATA / "mom_summary.csv") as f:
        rows = {r["version"]: r for r in csv.DictReader(f)}
    with open(DATA / "mom_worst.csv") as f:
        worst = list(csv.DictReader(f))
    return rows, worst
