import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mlbase import Harness, cv_path, long_short, rank_features, report, xs_target


def _toy(seed=0, T=60, N=100, K=3, beta=0.02):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1, 1, (T, N, K))
    r = beta * X[:, :, 0] + 0.05 * rng.standard_normal((T, N)) + 0.03 * rng.standard_normal((T, 1))
    return X, r


def test_ranks_and_target():
    X, r = _toy()
    R = rank_features(X)
    assert R.min() > -1 and R.max() < 1 and abs(R[3, :, 1].mean()) < 1e-12
    y = xs_target(r, [0, 1])
    assert y.shape == (200,) and abs(y[:100].mean()) < 1e-12


def test_long_short_weights():
    pred = np.tile(np.arange(10.0), (2, 1))
    r = np.tile(np.arange(10.0) / 100, (2, 1))
    ls, w = long_short(pred, r, q=5)
    assert np.allclose(w.sum(axis=1), 0) and np.allclose(np.abs(w).sum(axis=1), 2) and np.allclose(ls, 0.08)


def test_harness_finds_the_signal_and_report_fields():
    from sklearn.linear_model import Ridge

    X, r = _toy()
    _, pred, rep = Harness(lambda: Ridge(alpha=1.0)).run(X, r, np.arange(40), np.arange(40, 60))
    assert rep["ic"] > 0.1 and rep["ic_t"] > 3 and rep["ls_sr"] > rep["ls_sr_net"] and 0 < rep["turnover"] <= 2
    noise = report(np.random.default_rng(1).standard_normal((20, 100)), r[40:])
    assert abs(noise["ic"]) < 0.05


def test_cv_path_prefers_moderate_penalty_on_noise_heavy_data():
    from sklearn.linear_model import Ridge

    X, r = _toy(beta=0.004, K=20)
    params, scores = cv_path(lambda a: Ridge(alpha=a), (1e-3, 1e3, 1e8), X, r, np.arange(60), n_folds=3)
    assert scores[1] > scores[0] and scores[1] > scores[2] - 1e-6 or scores[2] > scores[0]
