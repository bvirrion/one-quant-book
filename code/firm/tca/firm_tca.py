"""firm.tca -- transaction-cost analysis: benchmarks, attribution, reversion, pre-trade estimates and
difficulty-adjusted comparisons (build of One Quant Book 10, chapter 19; on Book 7's firm.markout and firm.tcost).

Prices in any consistent unit (ticks in the book's simulations); `side` +1 for a buy, -1 for a sell; costs positive
when the order paid more (a buy) or received less (a sell). Per-share numbers are per share of the target quantity
for the attribution (so that opportunity cost counts) and per filled share for the benchmarks.

API (stable):
    attribute(side, target, decision, arrival, fills, mid, cf_mid, end, t_arrival)   per share of target: delay,
                                            spread, impact,
                                            timing, opportunity, fees, total; fills (t, px, qty, fee per share);
                                            mid and cf_mid are (times, prices) of the market with and without the
                                            order: impact is the mid's move the order caused, timing the rest. The
                                            total equals firm.markout.shortfall's (delay + execution + opportunity +
                                            fees) divided by the target
    benchmarks(side, fills, arrival, window, day, close)   per filled share: against arrival, the interval VWAP
                                            (window = (px, qty) of the market's trades during the order), the day's
                                            VWAP and the close
    reversion(side, t_end, mid, horizons)   side x (mid(t_end + h) - mid(t_end)): negative when the price gives back
                                            the order's push (temporary impact), positive when it keeps going
    pretrade(half_spread, eta, sigma, participation, exponent=0.5)   half-spread + eta sigma participation^exponent
    fit_pretrade(cost, sigma, participation, half_spread)            firm.tcost.fit_impact
    cluster_ols(y, X, clusters) -> (beta, cov)   least squares with cluster-robust (CR1) covariance
    adjusted_difference(cost, treat, controls, clusters)   {raw, raw_se, adj, adj_se, lo, hi}: the treatment's
                                            coefficient alone and with the controls, clustered, 95% interval
    peer_compare(cost, predicted, groups, clusters)   {group: (mean of cost - predicted, clustered se, n)}
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

for c in ("markout", "tcost"):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / c))
from firm_markout import ref_at, shortfall  # noqa: E402
from firm_tcost import fit_impact  # noqa: E402


def attribute(side: int, target: float, decision: float, arrival: float, fills, mid, cf_mid, end: float,
              t_arrival: float) -> dict:
    f = np.asarray(fills, float).reshape(-1, 4)
    t, px, q, fee = f[:, 0], f[:, 1], f[:, 2], f[:, 3]
    m = ref_at(mid[0], mid[1], t - 1e-9)                 # the mid just before each fill
    cf = ref_at(cf_mid[0], cf_mid[1], t - 1e-9)
    cf0 = float(ref_at(cf_mid[0], cf_mid[1], [t_arrival])[0])
    own0 = arrival - cf0                     # what earlier orders did to the arrival mid
    out = {"delay": side * q.sum() * (arrival - decision),
           "spread": side * float(q @ (px - m)),
           "impact": side * float(q @ (m - cf - own0)),
           "timing": side * float(q @ (cf - cf0)),
           "opportunity": side * (target - q.sum()) * (end - decision),
           "fees": float(q @ fee)}
    ref = shortfall(side, target, decision, arrival, np.c_[px, q], end, 0.0)
    out = {k: v / target for k, v in out.items()}
    out["total"] = sum(out.values())
    out["check"] = (ref["total"] + float(q @ fee)) / target - out["total"]
    out["filled"] = float(q.sum() / target)
    return out


def benchmarks(side: int, fills, arrival: float, window, day, close: float) -> dict:
    f = np.asarray(fills, float).reshape(-1, 2)
    avg = float(f[:, 1] @ f[:, 0] / f[:, 1].sum())

    def vwap(tr):
        tr = np.asarray(tr, float).reshape(-1, 2)
        return float(tr[:, 1] @ tr[:, 0] / tr[:, 1].sum())
    return {"arrival": side * (avg - arrival), "interval_vwap": side * (avg - vwap(window)),
            "day_vwap": side * (avg - vwap(day)), "close": side * (avg - close)}


def reversion(side: int, t_end: float, mid, horizons) -> np.ndarray:
    h = np.asarray(horizons, float)
    p = ref_at(mid[0], mid[1], np.r_[t_end, t_end + h])
    return side * (p[1:] - p[0])


def pretrade(half_spread, eta: float, sigma, participation, exponent: float = 0.5):
    p = np.asarray(participation, float)
    return np.asarray(half_spread, float) + eta * np.asarray(sigma, float) * p**exponent


def fit_pretrade(cost, sigma, participation, half_spread, bins: int = 10) -> dict:
    return fit_impact(cost, sigma, participation, half_spread, bins)


def cluster_ols(y, X, clusters):
    y, X = np.asarray(y, float), np.asarray(X, float)
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    e = y - X @ beta
    ids, inv = np.unique(np.asarray(clusters), return_inverse=True)
    scores = np.zeros((len(ids), k))
    np.add.at(scores, inv, X * e[:, None])               # each cluster's summed score
    meat = scores.T @ scores
    m = len(ids)
    scale = m / (m - 1) * (n - 1) / (n - k)
    return beta, scale * xtx_inv @ meat @ xtx_inv


def adjusted_difference(cost, treat, controls, clusters) -> dict:
    cost, treat = np.asarray(cost, float), np.asarray(treat, float)
    one = np.ones(len(cost))
    b0, v0 = cluster_ols(cost, np.c_[one, treat], clusters)
    b1, v1 = cluster_ols(cost, np.c_[one, treat, np.asarray(controls, float)], clusters)
    se = math.sqrt(v1[1, 1])
    return {"raw": float(b0[1]), "raw_se": float(math.sqrt(v0[1, 1])), "adj": float(b1[1]), "adj_se": se,
            "lo": float(b1[1] - 1.96 * se), "hi": float(b1[1] + 1.96 * se), "beta": b1}


def peer_compare(cost, predicted, groups, clusters) -> dict:
    r = np.asarray(cost, float) - np.asarray(predicted, float)
    g, c = np.asarray(groups), np.asarray(clusters)
    out = {}
    for k in np.unique(g):
        sel = g == k
        _, v = cluster_ols(r[sel], np.ones((sel.sum(), 1)), c[sel])
        out[k] = (float(r[sel].mean()), float(math.sqrt(v[0, 0])), int(sel.sum()))
    return out
