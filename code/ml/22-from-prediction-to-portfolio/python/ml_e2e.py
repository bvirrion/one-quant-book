"""From prediction to portfolio (One Quant Book 12, chapter 22).

A panel of 200 names in which the first characteristic predicts returns strongly in the 100 names the desk cannot trade
and the second weakly in the 100 it can (firm.e2eport.char_panel); a linear forecast feeds a mean-variance rule with a
trading-cost proxy on the tradeable names. Five pairs of independent panels (train, test): least squares on all names
(predict, then optimise), least squares on the tradeable names, decision-focused learning through the rule, a
parametric portfolio policy trained the same way without the rule's smoothing, and the true coefficients. Then the same
comparison with 16 useless characteristics and 300 training periods, where learning through the decision overfits."""
from __future__ import annotations

import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "e2eport"))
from firm_e2eport import char_panel, least_squares, run, train_decision  # noqa: E402

SEEDS = range(5)
METHODS = ("predict then optimise", "least squares, tradeable names", "decision-focused", "parametric policy",
           "true coefficients")


def _one(seed, T=1500, n_noise=0):
    tr = char_panel(2 * seed, T=T, n_noise=n_noise)
    te = char_panel(2 * seed + 1, n_noise=n_noise)
    X, R, m = tr["X"], tr["R"], tr["tradeable"]
    b_all = least_squares(X, R)
    b_trd = least_squares(X, R, m)
    b = {"predict then optimise": b_all, "least squares, tradeable names": b_trd,
         "decision-focused": train_decision(X, R, m, b_all, "mv"),
         "parametric policy": train_decision(X, R, m, b_all, "ppp"),
         "true coefficients": np.r_[0.0, 0.0008, np.zeros(X.shape[2] - 2)]}
    pol = {"parametric policy": "ppp"}
    return {k: run(v, te["X"], te["R"], te["tradeable"], policy=pol.get(k, "mv")) | {"b": v} for k, v in b.items()}


@functools.lru_cache(maxsize=1)
def results():
    return [_one(s) for s in SEEDS]


@functools.lru_cache(maxsize=1)
def overfit():
    """300 training periods and 16 useless characteristics."""
    return [_one(s, T=300, n_noise=16) for s in SEEDS]


def summary(res):
    out = {}
    for k in METHODS:
        net = np.array([r[k]["net"] for r in res])
        out[k] = {"net": float(net.mean()), "net sd": float(net.std(ddof=1)),
                  "gross": float(np.mean([r[k]["gross"] for r in res])),
                  "turnover": float(np.mean([r[k]["turnover"] for r in res]))}
    gap = np.array([r["decision-focused"]["net"] - r["predict then optimise"]["net"] for r in res])
    out["gap"] = (float(gap.mean()), float(gap.std(ddof=1)))
    return out


def forecast_errors(seed=0):
    """Out-of-sample mean squared error of the two least-squares forecasts, on all names and on the tradeable ones:
    the all-names fit is the more accurate forecast overall and the less accurate where the desk trades."""
    tr, te = char_panel(0), char_panel(1)
    b_all, b_trd = least_squares(tr["X"], tr["R"]), least_squares(tr["X"], tr["R"], tr["tradeable"])
    out = {}
    for name, b in (("all names", b_all), ("tradeable names", b_trd)):
        e = te["R"] - te["X"] @ b
        out[name] = (float(1e4 * (e**2).mean()), float(1e4 * (e[:, te["tradeable"]] ** 2).mean()))
    return out


@functools.lru_cache(maxsize=1)
def early_stopping(epochs=(0, 1, 2, 5, 10, 20)):
    """Exercise 7, small-sample scenario: the decision-focused fit started from least squares on the tradeable names,
    its number of epochs chosen on the last 60 of the 300 training periods (trained on the first 240), then refitted on
    all 300 with that number and tested."""
    out = []
    for s in SEEDS:
        tr, te = char_panel(2 * s, T=300, n_noise=16), char_panel(2 * s + 1, n_noise=16)
        X, R, m = tr["X"], tr["R"], tr["tradeable"]
        fit, val = slice(0, 240), slice(240, 300)
        b0 = least_squares(X[fit], R[fit], m)
        score = {}
        for e in epochs:
            b = b0 if e == 0 else train_decision(X[fit], R[fit], m, b0, "mv", epochs=e, window=60)
            score[e] = run(b, X[val], R[val], m)["net"]
        best = max(score, key=score.get)
        b_all = least_squares(X, R, m)
        b = b_all if best == 0 else train_decision(X, R, m, b_all, "mv", epochs=best, window=60)
        out.append((best, run(b, te["X"], te["R"], te["tradeable"])["net"]))
    return out
