import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
from firm_intraml import aggressive, features, gbm, gbm_predict, r2, ridge, ridge_predict, targets  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402


def test_features_are_causal_and_targets_forward():
    tape = simulate(TapeConfig(seconds=600, seed=3))
    t, X, names, mid = features(tape)
    assert X.shape == (570, 10) and np.isfinite(X).all()
    y = targets(tape, t, (5,))[5]
    assert np.isnan(y[-1]) and abs(np.nanmean(y)) < 1.0
    cut = simulate(TapeConfig(seconds=600, seed=3))
    cut.top = cut.top[cut.top["t"] <= 300.0]                          # the future removed does not change the past
    cut.trades = cut.trades[cut.trades["t"] <= 300.0]
    t2, X2, _, _ = features(cut)
    k = np.searchsorted(t, 299.0)
    assert np.allclose(X[:k], X2[:k])


def test_models_recover_a_planted_signal():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((4000, 3))
    y = 0.5 * X[:, 0] + np.where(X[:, 1] > 0.5, 1.0, 0.0) + 0.5 * rng.standard_normal(4000)
    m = ridge(X[:3000], y[:3000], 1.0)
    g = gbm(X[:3000], y[:3000], trees=60, rate=0.1)
    assert r2(y[3000:], ridge_predict(m, X[3000:])) > 0.4 and r2(y[3000:], gbm_predict(g, X[3000:])) > 0.6


def test_aggressive_by_hand():
    pnl = aggressive(np.array([0.5, -0.5, 0.1]), np.array([2.0, 1.0, 3.0]), np.array([1.0, 1.0, 1.0]), 0.2)
    assert pnl.tolist() == [1.0, -2.0]
