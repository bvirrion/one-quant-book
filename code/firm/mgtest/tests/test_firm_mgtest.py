"""Acceptance tests of firm.mgtest."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mgtest import martingale_report, revision_regression, revisions, variance_ratio, variance_shares


def _walks(n=4000, k=20, seed=1):
    rng = np.random.default_rng(seed)
    return np.cumsum(np.hstack([np.zeros((n, 1)), rng.standard_normal((n, k))]), axis=1)


def test_martingale_passes():
    for seed in range(5):
        r = revision_regression(_walks(seed=seed))
        assert abs(r["t"]) < 3.5 and abs(r["slope"]) < 0.02


def test_underreaction_is_detected():
    m = _walks(seed=7)
    f = 0.5 * m
    f[:, -1] = m[:, -1]          # the final value is revealed in full at the end
    r = revision_regression(f, col=f.shape[1] - 2)
    assert r["t"] > 10 and abs(r["slope"] - 1.0) < 0.1


def test_shares_sum_to_one_and_are_uniform():
    s = variance_shares(_walks())
    assert abs(s.sum() - 1) < 1e-12 and np.all(np.abs(s - 1 / 20) < 0.01)


def test_variance_ratio_near_one_for_iid():
    rng = np.random.default_rng(3)
    assert abs(variance_ratio(rng.standard_normal(100_000), 5) - 1) < 0.03
    ar = np.zeros(100_000)
    e = rng.standard_normal(100_000)
    for i in range(1, ar.size):
        ar[i] = -0.3 * ar[i - 1] + e[i]
    assert variance_ratio(ar, 5) < 0.7     # mean-reverting increments


def test_report_and_shapes():
    m = _walks(n=10, k=3)
    assert revisions(m).shape == (10, 3)
    rep = martingale_report(m)
    assert set(rep) == {"mean_revision", "regression", "shares"}
