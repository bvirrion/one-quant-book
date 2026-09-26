"""Feature engineering, selection and importance (One Quant Book 12, chapter 6).

A task with planted roles: x1 acts linearly, x2 through its square, x3 and x4 only through their product, x1b is x1's
near-twin (correlation 0.95, no effect of its own), and the rest is noise; the signal is 4% of the variance, as on
market data. Boosted trees are fitted on 20,000 rows and every importance is computed on 20,000 others: impurity (gain),
permutation, drop-column, mean absolute SHAP, and their clustered versions; stability selection with the lasso and with
boosting over 100 candidates; and a heavy-tailed feature used raw, winsorised and ranked.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("featimp", "gbdt"):
    sys.path.insert(0, str(ROOT / c))
from firm_featimp import (  # noqa: E402
    cluster_features,
    drop_column_importance,
    false_selection_bound,
    mdi,
    permutation_importance,
    rank_gauss,
    shap_values,
    stability_selection,
    winsorise,
)
from firm_gbdt import make  # noqa: E402

N = 20000
B = 0.12
NAMES = ["x1", "x2", "x3", "x4", "x1b"] + [f"n{i}" for i in range(10)]
TRUE = [0, 1, 2, 3]


@functools.lru_cache(maxsize=4)
def data(seed=1, p=15):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((2 * N, p))
    X[:, 4] = 0.95 * X[:, 0] + np.sqrt(1 - 0.95**2) * rng.standard_normal(2 * N)
    f = B * X[:, 0] + B * (X[:, 1] ** 2 - 1) / np.sqrt(2) + B * X[:, 2] * X[:, 3]
    y = f + rng.standard_normal(2 * N)
    return X[:N], y[:N], X[N:], y[N:], f[N:]


def r2(y, p):
    return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)


PARAMS = dict(num_leaves=15, n_estimators=300, learning_rate=0.03, min_child_samples=200)


@functools.lru_cache(maxsize=2)
def model(seed=1):
    X, y, _, _, _ = data(seed)
    return make(PARAMS).fit(X, y)


def _fit_predict(X, y, Xt):
    return make(PARAMS).fit(X, y).predict(Xt)


@functools.lru_cache(maxsize=2)
def importances(seed=1):
    X, y, Xt, yt, ft = data(seed)
    m = model(seed)
    groups = cluster_features(Xt, 0.5)
    out = {"test_r2": r2(yt, m.predict(Xt)), "truth_r2": r2(yt, ft), "groups": groups,
           "gain": mdi(m), "perm": permutation_importance(m.predict, Xt, yt, r2, reps=3, seed=seed),
           "drop": drop_column_importance(_fit_predict, X, y, Xt, yt, r2),
           "shap": np.abs(shap_values(m, Xt)).mean(axis=0),
           "perm_cluster": permutation_importance(m.predict, Xt, yt, r2, reps=3, seed=seed, groups=groups)}
    return out


def ranks(v):
    """Rank of each feature (1 = most important)."""
    return np.argsort(np.argsort(-np.asarray(v))) + 1


@functools.lru_cache(maxsize=2)
def twins(seed=1):
    """Test R-squared of the model refitted without x1, without x1b, and without both."""
    X, y, Xt, yt, _ = data(seed)

    def without(cols):
        keep = [j for j in range(X.shape[1]) if j not in cols]
        return r2(yt, _fit_predict(X[:, keep], y, Xt[:, keep]))

    return {"all": r2(yt, model(seed).predict(Xt)), "no_x1": without([0]), "no_x1b": without([4]),
            "no_both": without([0, 4])}


@functools.lru_cache(maxsize=2)
def stability(seed=1, p=100, n_sub=30, threshold=0.6, q=6):
    """Selection frequencies over half-samples of 10,000 rows: the lasso at a penalty that keeps a handful of features,
    and boosting's q features of largest gain; the false selections at the threshold, and the Meinshausen-Buhlmann bound
    with q the average number selected per subsample (the sum of the frequencies)."""
    from sklearn.linear_model import Lasso

    X, y, _, _, _ = data(seed, p)
    X, y = X[: N // 2], y[: N // 2]

    def lasso(Xs, ys):
        return Lasso(alpha=0.025, max_iter=3000).fit(Xs, ys).coef_ != 0

    def boost(Xs, ys):
        g = mdi(make(dict(PARAMS, n_estimators=100)).fit(Xs, ys))
        mask = np.zeros(len(g), bool)
        mask[np.argsort(-g)[:q]] = True
        return mask

    out = {}
    for name, sel in (("lasso", lasso), ("boosting", boost)):
        freq = stability_selection(sel, X, y, n_sub=n_sub, seed=seed)
        chosen = np.flatnonzero(freq >= threshold)
        noise = [j for j in chosen if j not in TRUE and j != 4]
        out[name] = {"freq": freq, "chosen": chosen, "false": len(noise),
                     "fsr": len(noise) / max(len(chosen), 1), "q": float(freq.sum()),
                     "bound": false_selection_bound(float(freq.sum()), p, threshold)}
    return out


@functools.lru_cache(maxsize=2)
def heavy_tail(seed=2, n=20000, df=1.5):
    """A heavy-tailed feature (Student t, 1.5 degrees of freedom) whose effect saturates: linear regression on it raw,
    winsorised at 1%, and ranked to normal scores, out of sample."""
    from sklearn.linear_model import LinearRegression

    rng = np.random.default_rng(seed)
    z = rng.standard_t(df, 2 * n)
    y = 0.2 * np.tanh(z) + rng.standard_normal(2 * n)
    out = {}
    for name, tf in (("raw", lambda v: v), ("winsorised", winsorise), ("ranked", rank_gauss)):
        v = tf(z)
        m = LinearRegression().fit(v[:n, None], y[:n])
        out[name] = r2(y[n:], m.predict(v[n:, None]))
    out["truth"] = r2(y[n:], 0.2 * np.tanh(z[n:]))
    return out
