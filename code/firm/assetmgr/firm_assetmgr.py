"""firm.assetmgr -- index replication, factor products and transitions (build of One Quant Book 8, chapter 29).

Cap-weighted index weights; a factor covariance for the listed names (exposures B, factor covariance F, specific
variances D); sampled replication: hold n names and choose long-only weights that minimise the ex-ante tracking
error to the index (a quadratic programme on firm.portopt.qp); the realised tracking error of a book rebalanced
periodically and drifting with returns in between; a factor product that tilts the index toward a style within a
tracking-error budget; and a transition planner that spreads a trade list over days, trading the square-root impact
of firm.tcost against the risk of the unexecuted part. NumPy only.

API (stable):
    cap_weights(price, shares, listed)           (M,) index weights from capitalisation
    covariance(B, F, D)                          B F B' + diag(D)
    sampled(b, Sigma, n)                         (w, te) long-only weights on the n largest index names, ex-ante TE
    drift_active(R, w0, b_path, start, end)      daily active returns of weights w0 held from `start` to `end`
    tilt(b, z, k)                                index weights times exp(k z), renormalised
    transition(value, adv, sigma, half_spread, eta, active_sd, days)
                                                 expected cost and its standard deviation (fractions of the fund) when
                                                 the trade list `value` (fractions of the fund) is spread over `days`
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "portopt"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tcost"))
from firm_portopt import qp  # noqa: E402
from firm_tcost import impact_bp  # noqa: E402


def cap_weights(price, shares, listed):
    cap = np.where(listed, np.nan_to_num(price) * np.nan_to_num(shares), 0.0)
    return cap / cap.sum()


def covariance(B, F, D):
    B = np.asarray(B, float)
    return B @ np.asarray(F, float) @ B.T + np.diag(np.asarray(D, float))


def sampled(b, Sigma, n: int):
    b = np.asarray(b, float)
    keep = np.argsort(-b)[:n]
    S = Sigma[np.ix_(keep, keep)]
    # minimise (w - b)' Sigma (w - b) over w on `keep`: w_k' S w_k - 2 w_k' (Sigma b)_k, sum w = 1, w >= 0
    q = -(Sigma @ b)[keep]
    res = qp(2 * S, 2 * q, A=np.ones((1, n)), b=np.array([1.0]), G=-np.eye(n), h=np.zeros(n), tol=1e-10)
    w = np.zeros(len(b))
    w[keep] = np.maximum(res["x"], 0.0)
    w /= w.sum()
    a = w - b
    return w, math.sqrt(max(a @ Sigma @ a, 0.0))


def drift_active(R, w0, b_path, start: int, end: int):
    R = np.nan_to_num(np.asarray(R, float))
    w = np.asarray(w0, float).copy()
    out = np.zeros(end - start)
    for i, t in enumerate(range(start, end)):
        out[i] = w @ R[t] - b_path[t - 1] @ R[t]
        w = w * (1 + R[t])
        w /= max(w.sum(), 1e-12)
    return out, w


def tilt(b, z, k: float):
    w = np.asarray(b, float) * np.exp(k * np.nan_to_num(np.asarray(z, float)))
    return w / w.sum()


def transition(value, adv, sigma, half_spread: float, eta: float, active_sd: float, days: int):
    v = np.abs(np.asarray(value, float))
    part = v / days / np.maximum(np.asarray(adv, float), 1e-12)
    cost = float((v * (half_spread + impact_bp(eta, sigma, part))).sum())
    remaining = [(days - d) / days for d in range(days)]          # share still to trade at the start of each day
    risk = active_sd * math.sqrt(sum(x * x for x in remaining))
    return cost, risk
