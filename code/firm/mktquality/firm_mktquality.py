"""firm.mktquality -- market-quality measures on a stock-day panel, and the event studies and difference-in-differences
that evaluate a rule (build of One Quant Book 10, chapter 24; on firm.spreaddecomp and firm.tca).

Prices in any unit; spreads in basis points of the mid; trades a structured array with fields t, price, sign, qty
(firm.tape's); quotes a top-of-book path with fields t, bid, ask, bid_qty, ask_qty.

API (stable):
    day_measures(top, trades, messages, h=5.0, grid=(10.0, 60.0), px_per_ccy=1)   one stock-day: quoted, effective,
                                   realised and impact spreads (bp), time-weighted top depth (shares), Amihud (the
                                   day's |return| in bp per million of currency traded), the variance ratio of
                                   long-grid to short-grid
                                   mid returns (1 for a random walk), the order-to-trade ratio (messages per trade)
    did(y, treated, post, unit, period)   two-way fixed effects: y on unit and period dummies and treated x post;
                                   the coefficient and its standard error clustered by unit
    before_after(y, treated, post, unit)  the treated units' mean after minus before, with a standard error
                                   clustered by unit
    event_study(y, treated, period, unit, base)   treated-minus-control coefficients by period (relative to `base`)
                                   with unit and period fixed effects, clustered by unit
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

for c in ("spreaddecomp", "tca"):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / c))
from firm_spreaddecomp import decompose, mid_at, quoted_spread  # noqa: E402
from firm_tca import cluster_ols  # noqa: E402


def day_measures(top, trades, messages: int, h: float = 5.0, grid=(10.0, 60.0), px_per_ccy: float = 1.0) -> dict:
    t, bid, ask = (np.asarray(top[k], float) for k in ("t", "bid", "ask"))
    ok = (bid > 0) & (ask > 0)
    t, bid, ask = t[ok], bid[ok], ask[ok]
    mid = 0.5 * (bid + ask)
    tt, px, qty = (np.asarray(trades[k], float) for k in ("t", "price", "qty"))
    end = float(max(t[-1], tt.max() if len(tt) else t[-1]))
    qs = quoted_spread(t, bid / mid * 1e4, ask / mid * 1e4, end)          # in bp of the mid at each quote
    dec = decompose(trades, t, mid, h)
    m_tr = mid_at(t, mid, tt - 1e-9)
    scale = 2e4 / np.average(m_tr, weights=qty)                          # half-spreads (price) -> spreads (bp)
    dq = np.asarray(top["bid_qty"], float)[ok] + np.asarray(top["ask_qty"], float)[ok]
    w = np.diff(np.r_[t, end])
    value = float(px @ qty) / px_per_ccy / 1e6                          # millions of currency traded
    ret = abs(math.log(mid[-1] / mid[0])) * 1e4                           # basis points
    g0, g1 = grid
    pts = np.arange(t[0], end, g0)
    lm = np.log(mid_at(t, mid, pts))
    short = np.diff(lm)
    k = int(round(g1 / g0))
    long = lm[k::k] - lm[:-k:k][: len(lm[k::k])]
    ok = len(long) > 1 and len(short) > 1 and np.var(short) > 0
    vr = float(np.var(long) / (k * np.var(short))) if ok else float("nan")
    return {"quoted": qs, "effective": dec["effective"] * scale, "realised": dec["realised"] * scale,
            "impact": dec["impact"] * scale, "depth": float(w @ dq / w.sum() / 2), "amihud": ret / value,
            "variance_ratio": vr, "otr": messages / max(len(trades), 1)}


def _dummies(x):
    _, inv = np.unique(np.asarray(x), return_inverse=True)
    return np.eye(inv.max() + 1)[inv]


def did(y, treated, post, unit, period) -> dict:
    y = np.asarray(y, float)
    tp = np.asarray(treated, float) * np.asarray(post, float)
    x = np.c_[tp, _dummies(unit), _dummies(period)[:, 1:]]
    b, v = cluster_ols(y, x, unit)
    return {"coef": float(b[0]), "se": float(math.sqrt(v[0, 0]))}


def before_after(y, treated, post, unit) -> dict:
    y, tr, po = np.asarray(y, float), np.asarray(treated, bool), np.asarray(post, float)
    b, v = cluster_ols(y[tr], np.c_[np.ones(tr.sum()), po[tr]], np.asarray(unit)[tr])
    return {"coef": float(b[1]), "se": float(math.sqrt(v[1, 1]))}


def event_study(y, treated, period, unit, base) -> dict:
    y = np.asarray(y, float)
    per = np.asarray(period)
    tr = np.asarray(treated, float)
    periods = [p for p in np.unique(per) if p != base]
    inter = np.column_stack([tr * (per == p) for p in periods])
    x = np.c_[inter, _dummies(unit), _dummies(per)[:, 1:]]
    b, v = cluster_ols(y, x, unit)
    return {p: (float(b[i]), float(math.sqrt(v[i, i]))) for i, p in enumerate(periods)}
