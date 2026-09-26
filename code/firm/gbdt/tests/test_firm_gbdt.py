import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_gbdt import SeedEnsemble, fit_early_stop, make, plateau_select, predict_dict, to_dict


def _data(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1, 1, (n, 4))
    y = np.sin(2 * X[:, 0]) + 0.5 * X[:, 1] + 0.5 * rng.standard_normal(n)
    return X, y


def test_deterministic_and_dump_parity():
    X, y = _data()
    a = make({"n_estimators": 50}).fit(X, y).predict(X)
    b = make({"n_estimators": 50}).fit(X, y)
    assert np.array_equal(a, b.predict(X))
    Xn = X.copy()
    Xn[::7, 2] = np.nan
    assert np.allclose(predict_dict(to_dict(b), Xn), b.predict(Xn), atol=1e-10)


def test_early_stopping_and_dump_of_best_iteration():
    X, y = _data()
    m, best, curve = fit_early_stop({"learning_rate": 0.1}, X[:3000], y[:3000], X[3000:], y[3000:], max_trees=500,
                                    patience=30)
    assert 5 < best < 500 and np.argmin(curve) + 1 == best
    assert np.allclose(predict_dict(to_dict(m), X[3000:]), m.predict(X[3000:]), atol=1e-10)


def test_monotone_constraint_holds():
    X, y = _data()
    m = make({"n_estimators": 100}, monotone={"x1": 1}, names=["x0", "x1", "x2", "x3"]).fit(X, y)
    grid = np.tile(X[:200], (1, 1))
    lo, hi = grid.copy(), grid.copy()
    lo[:, 1], hi[:, 1] = -0.5, 0.5
    assert np.all(m.predict(hi) >= m.predict(lo) - 1e-12)


def test_ensemble_and_plateau():
    X, y = _data()
    e = SeedEnsemble({"n_estimators": 30}, seeds=(1, 2, 3)).fit(X, y)
    assert np.allclose(e.predict(X), np.mean([m.predict(X) for m in e.models], axis=0))
    assert plateau_select([0.10, 0.12, 0.119, 0.05], se=0.005, complexity=[1, 3, 2, 0]) == 2
