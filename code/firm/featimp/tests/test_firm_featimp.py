import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "gbdt"))
from firm_featimp import (
    cluster_features,
    drop_column_importance,
    false_selection_bound,
    permutation_importance,
    rank_gauss,
    shap_values,
    stability_selection,
    winsorise,
)
from firm_gbdt import make


def _data(n=6000, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, 4))
    X[:, 1] = X[:, 0] + 0.05 * rng.standard_normal(n)                  # a near-copy of feature 0
    y = X[:, 0] + 0.3 * X[:, 2] + rng.standard_normal(n)
    return X, y


def r2(y, p):
    return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)


def test_transforms():
    x = np.r_[np.arange(98.0), 1e6, -1e6]
    w = winsorise(x, 0.01)
    assert w.max() < 1e6 and w.min() > -1e6
    g = rank_gauss(np.array([10.0, -3.0, 5.0]))
    assert g[1] < 0 < g[0] and abs(g[2]) < 1e-12


def test_permutation_and_groups():
    from sklearn.linear_model import LinearRegression

    X, y = _data()
    m = LinearRegression().fit(X[:3000], y[:3000])
    imp = permutation_importance(m.predict, X[3000:], y[3000:], r2, reps=3)
    assert abs(imp[3]) < 0.01 and imp[2] > 0.01                        # noise ~ 0; the weak signal is found
    pair = permutation_importance(m.predict, X[3000:], y[3000:], r2, reps=3, groups=[[0, 1]])[0]
    assert pair > 0.3                                                   # the pair carries the strong signal

    def fp(A, b, At):
        return LinearRegression().fit(A, b).predict(At)

    d = drop_column_importance(fp, X[:3000], y[:3000], X[3000:], y[3000:], r2)
    dg = drop_column_importance(fp, X[:3000], y[:3000], X[3000:], y[3000:], r2, groups=[[0, 1]])[0]
    assert d[0] < 0.01 and d[1] < 0.01 and dg > 0.3                     # substitution: singly nothing, jointly all


def test_shap_additivity_and_clusters():
    X, y = _data()
    m = make({"n_estimators": 50}).fit(X, y)
    s = shap_values(m, X[:100])
    bias = m.predict(X[:100], pred_contrib=True)[:, -1]
    assert np.allclose(s.sum(axis=1) + bias, m.predict(X[:100]))
    groups = cluster_features(X, 0.5)
    assert sorted(map(sorted, groups)) == [[0, 1], [2], [3]]


def test_stability_selection():
    X, y = _data()

    def sel(A, b):
        c = np.array([abs(np.corrcoef(A[:, j], b)[0, 1]) for j in range(A.shape[1])])
        return c > 0.1

    f = stability_selection(sel, X, y, n_sub=20)
    assert f[0] == 1.0 and f[2] > 0.9 and f[3] < 0.2
    assert false_selection_bound(10, 1000, 0.75) == 0.2
