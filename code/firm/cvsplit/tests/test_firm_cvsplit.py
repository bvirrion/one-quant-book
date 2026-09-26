import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_cvsplit import (
    CPCVSplit,
    PurgedKFold,
    WalkForwardSplit,
    adversarial_validation,
    canary,
    fold_overlap,
    nested_cv,
    truncation_test,
)


def test_splitters_work_with_sklearn():
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import cross_val_score

    rng = np.random.default_rng(0)
    X = rng.standard_normal((300, 3))
    y = X @ [1.0, 0.0, -1.0] + 0.1 * rng.standard_normal(300)
    t0 = np.arange(300)
    cv = PurgedKFold(t0, t0 + 4, 5, embargo=2)
    assert cv.get_n_splits() == 5 and cross_val_score(Ridge(), X, y, cv=cv).min() > 0.9
    for tr, te in cv.split(X):
        assert fold_overlap(t0, t0 + 4, tr, te) == 0                   # purged: no training span touches the test
    assert CPCVSplit(t0, t0 + 4, 6, 2).get_n_splits() == 15
    wf = list(WalkForwardSplit(100, 50, 10).split())
    assert len(wf) == 5 and all(tr.max() < te.min() for tr, te in wf)


def test_nested_cv_picks_the_right_penalty_and_flat_is_optimistic():
    from sklearn.linear_model import Ridge

    def r2(y, p):
        return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)

    rng = np.random.default_rng(1)
    X = rng.standard_normal((400, 120))
    y = X[:, 0] + X[:, 1] + 1.0 * rng.standard_normal(400)
    t0 = np.arange(400)
    res = nested_cv(lambda alpha: Ridge(alpha=alpha), {"alpha": [0.01, 100.0, 1e5]}, X, y, PurgedKFold(t0, t0, 4),
                    lambda tr: PurgedKFold(t0[tr], t0[tr], 3), r2)
    assert all(c["alpha"] == 100.0 for c in res["chosen"])
    assert res["flat_best"] >= res["outer_scores"].mean() - 1e-12


def test_truncation_and_canary():
    x = np.random.default_rng(2).standard_normal(200)

    def causal(d):
        return np.cumsum(d) / np.arange(1, len(d) + 1)

    def centred(d):                                                     # a moving average that looks ahead
        return np.convolve(d, np.ones(5) / 5, mode="same")

    assert truncation_test(causal, x, [50, 100, 150]) < 1e-12
    assert truncation_test(centred, x, [50, 100, 150]) > 0.01

    def leaky(y):                                                       # scores a feature made of the target itself
        f = y + np.random.default_rng(0).standard_normal(len(y))
        return float(np.corrcoef(f[100:], y[100:])[0, 1])

    m, se = canary(leaky, lambda rng: rng.standard_normal(200), reps=4)
    assert m > 5 * se and m > 0.5


def test_adversarial_validation():
    rng = np.random.default_rng(3)
    a, b = rng.standard_normal((400, 4)), rng.standard_normal((400, 4))
    assert abs(adversarial_validation(a, b) - 0.5) < 0.08
    assert adversarial_validation(a, b + [2.0, 0, 0, 0]) > 0.8                 # Bayes AUC of a 2-sd shift: 0.92
