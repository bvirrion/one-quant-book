"""firm.mlbase -- the model harness and the baseline to beat (build of One Quant Book 12, chapter 4).

Every cross-sectional model of Book 12 goes through the same harness, so that a new model is always compared with the
same baselines on the same splits and the same report. Data are panels: X (T, N, K) features known at the end of
period t, r (T, N) the return of period t + 1 (firm.mlsynth's convention).

API (stable):
    rank_features(X)                      per-period cross-sectional ranks mapped to [-1, 1] (NaN-free input)
    xs_target(r, months)                  returns minus each period's cross-sectional mean, flattened
    fit(model, X, r, months, target)      fit a scikit-learn-style regressor on the flattened panel ('xs' or 'raw')
    predict(model, X, months)             (len(months), N) predictions
    long_short(pred, r, q)                (returns (m,), weights (m, N)): equal-weighted top minus bottom 1/q
    report(pred, r, q, cost_bp, periods)  dict(r2, ic, ic_t, ls_sr, ls_sr_net, turnover): R-squared against zero,
                                          mean rank IC and its HAC t (firm.predictor), the long-short Sharpe ratio
                                          gross and net of cost_bp per unit traded, annualised, and the turnover
                                          (share of the gross book traded per period, 0 to 2)
    cv_path(make, params, X, r, months, n_folds, embargo) -> (params, mean CV R-squared) on purged folds of months
    Harness(make, target).run(X, r, train, test) -> (model, predictions, report)
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

_FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("predictor", "overfit", "mlsynth"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_mlsynth import r2_oos  # noqa: E402
from firm_overfit import purged_kfold  # noqa: E402
from firm_predictor import ic_series, ic_summary  # noqa: E402


def rank_features(X):
    n = X.shape[1]
    return 2.0 * (np.argsort(np.argsort(X, axis=1), axis=1) + 0.5) / n - 1.0


def xs_target(r, months):
    m = np.asarray(months)
    return (r[m] - r[m].mean(axis=1, keepdims=True)).reshape(-1)


def _flat(X, months):
    m = np.asarray(months)
    return X[m].reshape(len(m) * X.shape[1], X.shape[2])


def fit(model, X, r, months, target: str = "xs"):
    y = xs_target(r, months) if target == "xs" else r[np.asarray(months)].reshape(-1)
    return model.fit(_flat(X, months), y)


def predict(model, X, months):
    m = np.asarray(months)
    return model.predict(_flat(X, m)).reshape(len(m), X.shape[1])


def long_short(pred, r, q: int = 10):
    m, n = pred.shape
    k = max(1, n // q)
    order = np.argsort(pred, axis=1)
    w = np.zeros((m, n))
    rows = np.arange(m)[:, None]
    w[rows, order[:, -k:]] = 1.0 / k
    w[rows, order[:, :k]] = -1.0 / k
    return (w * r).sum(axis=1), w


def report(pred, r, q: int = 10, cost_bp: float = 20.0, periods: int = 12) -> dict:
    ic = ic_series(pred, r, "rank")
    s = ic_summary(ic, h=1, periods=periods)
    ls, w = long_short(pred, r, q)
    traded = np.r_[np.abs(w[0]).sum(), np.abs(np.diff(w, axis=0)).sum(axis=1)]   # per unit of capital (gross 2)
    net = ls - traded * cost_bp * 1e-4
    turn = traded / np.abs(w).sum(axis=1)                              # share of the gross book traded
    sr = float(ls.mean() / ls.std() * math.sqrt(periods))
    return {"r2": r2_oos(r, pred), "ic": float(s["mean"]), "ic_t": float(s["t_hac"]), "ls_sr": sr,
            "ls_sr_net": float(net.mean() / net.std() * math.sqrt(periods)), "turnover": float(turn.mean())}


def cv_path(make, params, X, r, months, n_folds: int = 5, embargo: int = 1):
    """Purged k-fold over months (a label spans one period), pooled out-of-fold R-squared against zero."""
    months = np.asarray(months)
    folds = purged_kfold(months, months, n_folds, embargo)
    scores = []
    for p in params:
        pred = np.full((len(months), X.shape[1]), np.nan)
        for tr, te in folds:
            m = fit(make(p), X, r, months[tr])
            pred[te] = predict(m, X, months[te])
        scores.append(r2_oos(r[months], pred))
    return list(params), np.array(scores)


class Harness:
    def __init__(self, make, target: str = "xs"):
        self.make, self.target = make, target

    def run(self, X, r, train, test, **kw):
        m = fit(self.make(), X, r, train, self.target)
        p = predict(m, X, test)
        return m, p, report(p, r[np.asarray(test)], **kw)
