import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_nettab import SeedEnsemble, fit


def _data(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1, 1, (n, 5))
    y = np.sin(3 * X[:, 0]) + X[:, 1] * X[:, 2] + 0.1 * rng.standard_normal(n)
    return X[:3000], y[:3000], X[3000:], y[3000:]


def test_reproducible_and_seed_dependent():
    X, y, Xv, yv = _data()
    a = fit(X, y, Xv, yv, epochs=5, seed=3)
    b = fit(X, y, Xv, yv, epochs=5, seed=3)
    c = fit(X, y, Xv, yv, epochs=5, seed=4)
    assert a.state_hash() == b.state_hash() != c.state_hash()
    assert np.array_equal(a.predict(Xv), b.predict(Xv))


def test_learns_a_nonlinear_function_and_keeps_best_epoch():
    X, y, Xv, yv = _data()
    f = fit(X, y, Xv, yv, hidden=(64, 32), lr=3e-3, epochs=60, patience=10, seed=1)
    r2 = 1 - np.mean((yv - f.predict(Xv)) ** 2) / np.var(yv)
    assert r2 > 0.8
    assert f.best_epoch == int(np.argmin(f.history)) + 1


def test_ensemble_averages():
    X, y, Xv, yv = _data()
    e = SeedEnsemble(seeds=(1, 2), epochs=3).fit(X, y, Xv, yv)
    assert np.allclose(e.predict(Xv), (e.members[0].predict(Xv) + e.members[1].predict(Xv)) / 2)
