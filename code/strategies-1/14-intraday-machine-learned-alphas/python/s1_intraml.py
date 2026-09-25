"""Intraday machine-learned alphas (One Quant Book 8, chapter 14).

Twenty one-hour sessions of firm.tape (seeds 1 to 20, default configuration with a news window at mid-session);
features every second; targets the mid's change over the next 5, 30 and 120 seconds, in ticks. Models are trained on
sessions 1 to 14 and tested on 15 to 20 (whole sessions apart, so overlapping targets cannot leak): ridge regression and
a gradient-boosted ensemble of 60 depth-two trees. Out-of-sample R-squared and rank IC by horizon; the P&L per share of
trading the forecasts on the test sessions: aggressively (crossing the spread in and out) when the forecast exceeds the
spread, passively (joining the touch, filled only when traded through within 10 seconds, exiting across the spread) when
it exceeds a fifth of a tick, and coupled (aggressive above the spread, passive between). NumPy only.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("intraml", "tape"):
    sys.path.insert(0, str(FIRM / c))
from firm_intraml import (  # noqa: E402
    aggressive,
    features,
    gbm,
    gbm_predict,
    passive,
    r2,
    ridge,
    ridge_predict,
    targets,
)
from firm_tape import TapeConfig, simulate  # noqa: E402

TRAIN, TEST, HORIZONS, PASSIVE, WAIT = range(1, 15), range(15, 21), (5, 30, 120), 0.2, 10.0


@functools.lru_cache(maxsize=32)
def session(seed: int):
    tape = simulate(TapeConfig(seed=seed))
    t, X, names, mid = features(tape)
    return tape, t, X, targets(tape, t, HORIZONS)


def stack(seeds, h):
    X = np.vstack([session(s)[2] for s in seeds])
    y = np.concatenate([session(s)[3][h] for s in seeds])
    ok = np.isfinite(y)
    return X[ok], y[ok]


@functools.lru_cache(maxsize=8)
def models(h: int):
    X, y = stack(TRAIN, h)
    return ridge(X, y, 1.0), gbm(X, y, 60, 0.1)


def _rank_ic(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


@functools.lru_cache(maxsize=8)
def scores(h: int):
    m_r, m_g = models(h)
    X, y = stack(TEST, h)
    pr, pg = ridge_predict(m_r, X), gbm_predict(m_g, X)
    Xt, yt = stack(TRAIN, h)
    return {"r2_ridge": r2(y, pr), "r2_gbm": r2(y, pg), "ic_ridge": _rank_ic(pr, y), "ic_gbm": _rank_ic(pg, y),
            "r2_gbm_train": r2(yt, gbm_predict(m_g, Xt)), "n_test": len(y), "sd_move": float(y.std())}


@functools.lru_cache(maxsize=8)
def trading(h: int):
    """Mean P&L per share (ticks) and counts on the test sessions, for the gradient-boosted forecasts."""
    _, m_g = models(h)
    agg, pas, spreads = [], [], []
    for s in TEST:
        tape, t, X, ys = session(s)
        pred = gbm_predict(m_g, X)
        spread = X[:, 1]
        big = np.abs(pred) > spread                                # cross only when the forecast beats the spread
        agg.append(aggressive(np.where(big, pred, 0.0), ys[h], spread, 1e-12))
        pas.append(passive(tape, t, np.where(big, 0.0, pred), h, PASSIVE, WAIT))
        spreads.append(spread)
    a, p = np.concatenate(agg), np.concatenate(pas)
    return {"agg_mean": float(a.mean()) if len(a) else 0.0, "agg_n": len(a),
            "pas_mean": float(p.mean()) if len(p) else 0.0, "pas_n": len(p),
            "coupled": float((a.sum() + p.sum()) / max(len(a) + len(p), 1)),
            "spread": float(np.concatenate(spreads).mean())}


@functools.lru_cache(maxsize=8)
def naive(h: int):
    """Every forecast above a fifth of a tick traded aggressively, and every one traded passively."""
    _, m_g = models(h)
    agg, pas = [], []
    for s in TEST:
        tape, t, X, ys = session(s)
        pred = gbm_predict(m_g, X)
        agg.append(aggressive(pred, ys[h], X[:, 1], PASSIVE))
        pas.append(passive(tape, t, pred, h, PASSIVE, WAIT))
    a, p = np.concatenate(agg), np.concatenate(pas)
    return {"agg_mean": float(a.mean()), "agg_n": len(a), "pas_mean": float(p.mean()), "pas_n": len(p)}


@functools.lru_cache(maxsize=4)
def without_own_returns(h: int = 5):
    """Out-of-sample R-squared of ridge and boosted trees without the mid's own past changes (features 7 and 8)."""
    keep = [0, 1, 2, 3, 4, 5, 6, 9]
    X, y = stack(TRAIN, h)
    Xt, yt = stack(TEST, h)
    m_r, m_g = ridge(X[:, keep], y, 1.0), gbm(X[:, keep], y, 60, 0.1)
    return {"r2_ridge": r2(yt, ridge_predict(m_r, Xt[:, keep])), "r2_gbm": r2(yt, gbm_predict(m_g, Xt[:, keep]))}
