"""Asia-specific equity strategies (One Quant Book 8, chapter 18).

firm.synthmkt's ten-year market (1,000 names), its returns scaled by 1.5 to the volatility of a retail-dominated
market, printed through firm.limitmkt's daily price limits: 5%, 10% (the default) and 20%. Behaviours: attention
buying of 3% the day after a limit-up close, decaying by 0.6 a day; a magnet that pushes half the targets within 2% of
the upper limit to lock; queue fills that fall with how far the target is beyond the limit. Measured, for limit-up
closes: their frequency, the share pushed, the return from the close to the next open (what a buyer at the close could
sell at under T+1) for all buyers and weighted by the queue's fill probability, and the return from the next open to
the close five days later; the distribution of daily moves just below the limit, with and without the magnet; and a
northbound-flow signal whose flows know a little of the next five days' returns, as published daily or, as now,
quarterly five days late. NumPy only.
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

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "synthmkt"))
sys.path.insert(0, str(ROOT / "firm" / "limitmkt"))
from firm_limitmkt import LimitConfig, apply_limits, holdings_seen, northbound  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

LIMITS = (0.05, 0.10, 0.20)
COST = 0.0015            # a round trip: 5 bp stamp duty on the sale, 10 bp of commissions and spread (assumed)
SKILL, HORIZON, QUARTER, LAG = 0.02, 5, 63, 5


@functools.lru_cache(maxsize=1)
def panel():
    return simulate(MarketConfig())


@functools.lru_cache(maxsize=8)
def market(limit: float = 0.10, attention: float = 0.03, push: float = 0.5):
    return apply_limits(panel().ret, LimitConfig(limit=limit, attention=attention, push=push),
                        np.random.default_rng(18))


def limit_ups(limit: float = 0.10, attention: float = 0.03, push: float = 0.5):
    """Limit-up closes with five more listed days: next-open, filled and week-after returns (simple)."""
    P, o = panel(), market(limit, attention, push)
    T = P.ret.shape[0]
    live = P.listed
    far = np.arange(T)[:, None] < np.asarray(P.end)[None, :] - 6          # not in a listing's last days
    ok = o["up"][:-6] & live[1:-5] & live[6:] & far[:-6]
    nxt = np.expm1(o["open"][1:-5] - o["close"][:-6])
    week = np.expm1(o["close"][6:] - o["open"][1:-5])
    fill, pushed = o["fill"][:-6], o["pushed"][:-6]
    out = {"freq": float(o["up"][live].mean()), "n": int(ok.sum()), "share_pushed": float(pushed[ok].mean())}
    for name, m in (("all", ok), ("real", ok & ~pushed), ("pushed", ok & pushed)):
        if not m.any():
            continue
        out[name] = {"open": float(nxt[m].mean()), "fill": float(fill[m].mean()),
                     "filled": float((fill[m] * nxt[m]).sum() / fill[m].sum()), "week": float(week[m].mean()),
                     "se": float(nxt[m].std() / math.sqrt(m.sum()))}
    return out


def band(push: float = 0.5, limit: float = 0.10, width: float = 0.005):
    """Share of listed stock-days whose close-to-close log move falls in each bin from 5% to the limit."""
    P, o = panel(), market(limit, 0.03, push)
    live = P.listed[1:] & P.listed[:-1]
    move = (o["close"][1:] - o["close"][:-1])[live]
    ub = math.log1p(limit)
    edges = np.arange(0.05, ub - width + 1e-9, width)
    rows = [(float(e), float(((move >= e) & (move < e + width)).mean())) for e in edges]
    return rows, float((move >= ub - 1e-12).mean())


@functools.lru_cache(maxsize=2)
def flows(every: int = 1, lag: int = 0):
    """Northbound signal: IC with the next five days' return and a weekly book's Sharpe ratio after costs."""
    P, o = panel(), market()
    live = P.listed
    T = live.shape[0]
    close = np.where(live, o["close"], np.nan)
    fwd = np.full(close.shape, np.nan)
    fwd[:-HORIZON] = np.expm1(close[HORIZON:] - close[:-HORIZON])
    f = np.where(live, northbound(np.nan_to_num(fwd), SKILL, np.random.default_rng(19)), 0.0)
    H = holdings_seen(f, every, lag)
    sig = H - holdings_seen(f, every, lag + every)
    ics, pnl, prev = [], [], None
    for t in range(QUARTER + 2 * LAG, T - HORIZON, HORIZON):
        m = live[t] & ~np.isnan(sig[t]) & ~np.isnan(fwd[t])
        s = np.where(m, sig[t], 0.0)
        a = np.argsort(np.argsort(s[m]))
        ics.append(np.corrcoef(a, np.argsort(np.argsort(fwd[t][m])))[0, 1])
        w = np.where(m, s - s[m].mean(), 0.0)
        w /= np.abs(w).sum()
        turn = np.abs(w - (prev if prev is not None else 0.0)).sum()
        pnl.append(float(np.nansum(w * fwd[t])) - COST / 2 * turn)
        prev = w
    x = np.array(pnl)
    return {"ic": float(np.mean(ics)), "ic_se": float(np.std(ics) / math.sqrt(len(ics))),
            "sr": float(x.mean() / x.std(ddof=1) * math.sqrt(252 / HORIZON))}
