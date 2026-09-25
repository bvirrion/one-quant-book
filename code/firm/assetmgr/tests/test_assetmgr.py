import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_assetmgr import cap_weights, covariance, drift_active, sampled, tilt, transition  # noqa: E402


def test_weights_and_covariance():
    b = cap_weights(np.array([10.0, 20.0, 5.0]), np.array([1.0, 1.0, 2.0]), np.array([True, True, False]))
    assert np.allclose(b, [1 / 3, 2 / 3, 0.0])
    S = covariance(np.ones((2, 1)), [[0.04]], [0.01, 0.02])
    assert np.allclose(S, [[0.05, 0.04], [0.04, 0.06]])


def test_sampled_replication():
    rng = np.random.default_rng(0)
    n = 40
    B = np.column_stack([np.ones(n), rng.standard_normal(n)])
    S = covariance(B, np.diag([1e-4, 4e-5]), np.full(n, 2e-4))
    b = rng.random(n)
    b /= b.sum()
    w_full, te_full = sampled(b, S, n)
    w_10, te_10 = sampled(b, S, 10)
    assert te_full < 1e-6 and te_10 > te_full and (w_10 >= 0).all() and math.isclose(w_10.sum(), 1.0)
    assert (w_10 > 0).sum() <= 10


def test_drift_tilt_transition():
    R = np.array([[0.0, 0.0], [0.1, 0.0]])
    a, w = drift_active(R, np.array([1.0, 0.0]), np.array([[0.5, 0.5], [0.5, 0.5]]), 1, 2)
    assert math.isclose(a[0], 0.1 - 0.05) and np.allclose(w, [1.0, 0.0])
    assert np.allclose(tilt(np.array([0.5, 0.5]), np.array([1.0, -1.0]), 0.0), [0.5, 0.5])
    c1, r1 = transition(np.array([0.1]), np.array([1.0]), np.array([0.02]), 0.0005, 0.5, 0.002, 1)
    c4, r4 = transition(np.array([0.1]), np.array([1.0]), np.array([0.02]), 0.0005, 0.5, 0.002, 4)
    assert c4 < c1 and r4 > r1 and math.isclose(r1, 0.002)
