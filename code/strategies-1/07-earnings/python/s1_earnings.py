"""Earnings (One Quant Book 8, chapter 7).

The post-earnings drift planted in firm.synthmkt (seed 1): each announcement carries a surprise (public at the close
of the announcement day), a jump in its direction and a drift of 1.2% per unit of surprise over the next 60 days. An
event-time book buys the names whose surprise was above one standard deviation and sells those below minus one, from
the close of the day after the announcement (or of the announcement day) for 5, 20 or 60 days (gross 1), at 10 basis
points per unit traded; the same book on the surprise measured by the market-adjusted announcement-day return instead
of the reported surprise; event-time cumulative abnormal returns; announcement-day moves against ordinary days; the
portfolio of announcers (no premium is planted); and the drift book on a market whose drift loses 70% of its size from
year 7 on (Book 7 chapter 13's break). Years 3 to 10. NumPy only.
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
for c in ("earnstrat", "vecbt", "synthmkt"):
    sys.path.insert(0, str(FIRM / c))
from firm_earnstrat import announcement_move, calendar, event_book, event_car  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402
from firm_vecbt import backtest  # noqa: E402

YEAR, START, COST, BREAK = 252, 504, 0.0010, 6 * 252
HOLDS = (5, 20, 60)


@functools.lru_cache(maxsize=2)
def panel(cut: bool = False):
    P = simulate(MarketConfig(pead_break=BREAK, pead_after=0.3) if cut else MarketConfig())
    R = np.where(P.listed, P.ret, np.nan)
    cap = np.where(P.listed, P.price * P.shares, 0.0)
    cprev = np.vstack([cap[:1], cap[:-1]])
    mkt = np.nansum(cprev * np.nan_to_num(R), axis=1) / np.maximum(cprev.sum(axis=1), 1e-12)
    flag, sur = calendar(P.earnings, *R.shape)
    return P, R, mkt, flag, sur


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


@functools.lru_cache(maxsize=16)
def run(hold: int, signal: str = "surprise", cut: bool = False, delay: int = 1):
    """Net daily returns of the event book over the evaluation days, and statistics (whole period, and years 3-6 and
    7-10)."""
    P, R, mkt, flag, sur = panel(cut)
    if signal == "surprise":
        s = sur
    else:                                              # the announcement-day market-adjusted return, standardised
        ab = np.where(flag, R - mkt[:, None], np.nan)
        s = ab / np.nanstd(ab)
    W = event_book(flag, s, P.listed, hold, 1.0, delay)
    res = backtest(W, R, lag=1, cost=COST)
    n, g = res.net[START:], res.gross[START:]
    half = BREAK - START
    return {"net": n, "sr": sharpe(n), "sr_gross": sharpe(g), "ret": float(n.mean() * YEAR),
            "turnover": float(res.turnover[START:].sum() / (len(n) / YEAR)), "sr_early": sharpe(n[:half]),
            "sr_late": sharpe(n[half:]), "ret_early": float(n[:half].mean() * YEAR),
            "ret_late": float(n[half:].mean() * YEAR)}


def car(before: int = 5, after: int = 60):
    P, R, mkt, flag, sur = panel(False)
    return event_car(R - mkt[:, None], flag, sur, before, after, 1.0)


def moves():
    """Announcement-day |return| over ordinary-day |return|, and the share of announcements a year."""
    P, R, mkt, flag, _ = panel(False)
    ev = flag[START:].sum() / P.listed[START:].sum()
    return {"ratio": announcement_move(R - mkt[:, None], flag), "event_share": float(ev)}


@functools.lru_cache(maxsize=1)
def announcers():
    """The equal-weighted portfolio of the day's announcers minus the market, bought the close before the day."""
    P, R, mkt, flag, _ = panel(False)
    out = []
    for t in range(START, R.shape[0]):
        a = flag[t] & P.listed[t - 1]
        if a.any():
            out.append(float(np.nanmean(R[t, a]) - mkt[t]))
    x = np.array(out)
    t = float(x.mean() / x.std(ddof=1) * math.sqrt(len(x)))
    return {"mean_daily_bp": float(1e4 * x.mean()), "t": t, "days": len(x)}
