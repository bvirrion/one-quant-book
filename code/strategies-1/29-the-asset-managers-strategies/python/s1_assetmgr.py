"""The asset managers' strategies (One Quant Book 8, chapter 29).

firm.synthmkt's ten-year market: a cap-weighted index of all listed names; a risk model from the market's own truth
(beta on the market factor with its conditional variance, industry factors at 8% a year, the three styles at their
planted volatilities with point-in-time exposures z-scored each day, and each name's specific volatility). Sampled
replication holds the 25 to 400 largest names with long-only weights that minimise ex-ante tracking error, rebalanced
every 63 days and drifting with returns in between; realised tracking error and one-way turnover are measured from
the second year, and costs at 10 basis points per unit traded (assumed). A value product tilts the index by
exp(k x z) on the point-in-time book-to-price z-score. A transition from the 100-name sample to the value product for a
fund of $2 billion (half spread 5 basis points, square-root impact with eta 0.5 on daily volatility, assumed) is spread
over 1 to 10 days. NumPy only.
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
for p in ("synthmkt", "assetmgr"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_assetmgr import cap_weights, covariance, drift_active, sampled, tilt, transition  # noqa: E402
from firm_synthmkt import MarketConfig, point_in_time_styles, simulate  # noqa: E402

REBAL, START, COST = 63, 252, 0.0010
SIZES = (25, 50, 100, 200, 400)
AUM, HALF_SPREAD, ETA = 2e9, 0.0005, 0.5


@functools.lru_cache(maxsize=1)
def market():
    P = simulate(MarketConfig())
    S = point_in_time_styles(P)
    b = np.array([cap_weights(P.price[t], P.shares[t], P.listed[t]) for t in range(len(P.ret))])
    return P, S, b


def _z(x, m):
    x = np.where(m, x, np.nan)
    mu, sd = np.nanmean(x), np.nanstd(x)
    return np.where(m, np.nan_to_num((x - mu) / sd), 0.0)


def sigma_at(t: int):
    P, S, _ = market()
    cfg = MarketConfig()
    m = P.listed[t]
    ind = np.zeros((len(m), cfg.n_industries))
    ind[np.arange(len(m)), P.industry] = 1.0
    size = np.log(np.maximum(np.nan_to_num(S["size"]), 1e-12))
    styles = np.column_stack([_z(size, m), _z(S["log_bp"][t], m), _z(S["momentum"][t], m)])
    B = np.column_stack([np.where(m, P.beta, 0.0), ind * m[:, None], styles])
    F = np.diag([P.h[t]] + [cfg.ind_vol**2 / 252] * cfg.n_industries + [v**2 / 252 for v in cfg.style_vol])
    D = np.where(m, P.spec_vol**2, 0.0)
    return covariance(B, F, D)


@functools.lru_cache(maxsize=8)
def replicate(n: int):
    P, _, b = market()
    T = len(P.ret)
    active, te_ex, turn = [], [], 0.0
    w_prev = None
    for t in range(START, T - 1, REBAL):
        w, te = sampled(b[t], sigma_at(t), n)
        te_ex.append(te * math.sqrt(252))
        if w_prev is not None:
            turn += np.abs(w - w_prev).sum()
        a, w_prev = drift_active(P.ret, w, b, t + 1, min(t + 1 + REBAL, T))
        active.append(a)
    a = np.concatenate(active)
    years = len(a) / 252
    return {"te": float(a.std() * math.sqrt(252)), "te_ex": float(np.mean(te_ex)), "turnover": turn / years,
            "cost": COST * turn / years, "mean_active": float(a.mean() * 252)}


@functools.lru_cache(maxsize=1)
def full_turnover():
    """One-way turnover a year of holding the index exactly: trades only when names enter or leave."""
    P, _, b = market()
    R = np.nan_to_num(P.ret)
    turn = 0.0
    for t in range(START, len(R) - 1):
        drifted = b[t] * (1 + R[t + 1])
        drifted /= drifted.sum()
        turn += np.abs(b[t + 1] - drifted).sum() / 2
    return turn / ((len(R) - 1 - START) / 252)


@functools.lru_cache(maxsize=4)
def value_product(k: float = 0.5):
    P, S, b = market()
    T = len(P.ret)
    active, expo = [], []
    for t in range(START, T - 1, REBAL):
        z = _z(S["log_bp"][t], P.listed[t])
        w = tilt(b[t], z, k)
        expo.append(float((w - b[t]) @ z))
        a, _ = drift_active(P.ret, w, b, t + 1, min(t + 1 + REBAL, T))
        active.append(a)
    a = np.concatenate(active)
    return {"te": float(a.std() * math.sqrt(252)), "excess": float(a.mean() * 252), "exposure": float(np.mean(expo)),
            "ir": float(a.mean() / a.std() * math.sqrt(252))}


def transition_plan(days=(1, 2, 3, 5, 10), t: int = 1260):
    P, S, b = market()
    w_old, _ = sampled(b[t], sigma_at(t), 100)
    w_new = tilt(b[t], _z(S["log_bp"][t], P.listed[t]), 0.5)
    value = (w_new - w_old) * AUM
    adv = np.nan_to_num(P.volume[t] * P.price[t]) + 1.0
    sig = np.where(P.listed[t], P.spec_vol, 0.0)
    a = w_new - w_old
    active_sd = math.sqrt(a @ sigma_at(t) @ a)
    out = {}
    for d in days:
        c, r = transition(value / AUM, adv / AUM, sig, HALF_SPREAD, ETA, active_sd, d)
        out[d] = (c, r)
    return out, float(np.abs(a).sum() / 2), active_sd * math.sqrt(252)
