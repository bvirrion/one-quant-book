"""Acceptance tests of the Book 6, chapter 8 build (market model)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_lmm import (
    black,
    calibrate_to_caplets,
    hjm_drift_gaussian,
    implied_black,
    mc_caplet,
    mc_swaption,
    rebonato_vol,
)

F0 = np.array([0.020, 0.022, 0.024, 0.026, 0.027, 0.028])
VOLS = np.array([0.30, 0.30, 0.28, 0.26, 0.25, 0.24])


def test_caplet_calibration_and_one_period_rebonato():
    m = calibrate_to_caplets(F0, VOLS)
    for k in range(1, 6):
        assert m.integrated_cov(k, k, float(k)) == pytest.approx(VOLS[k] ** 2 * k, rel=1e-9)
        assert rebonato_vol(m, k, k + 1) == pytest.approx(VOLS[k], rel=1e-9)
    assert np.all(np.linalg.eigvalsh(m.corr()) > 0)


def test_monte_carlo_reprices_caplets_under_the_spot_measure():
    m = calibrate_to_caplets(F0, VOLS)
    p = m.discount_factors()
    k = 3
    price, se = mc_caplet(m, k, F0[k], 20000, seed=3)
    exact = black(F0[k], F0[k], k, VOLS[k], p[k + 1])
    assert abs(price - exact) < 3 * se


def test_deep_in_the_money_swaption_is_the_forward_swap():
    m = calibrate_to_caplets(F0, VOLS, beta=0.2)
    s, ann, _ = m.swap(2, 5)
    price, se = mc_swaption(m, 2, 5, s - 0.02, 20000, seed=5)
    assert abs(price - ann * 0.02) < 3 * se + 1e-5
    v = implied_black(black(s, s, 2, 0.2, ann), s, s, 2, ann)
    assert v == pytest.approx(0.2, abs=1e-8)


def test_lower_correlation_lowers_swaption_volatility_and_hjm_drift():
    lo = rebonato_vol(calibrate_to_caplets(F0, VOLS, beta=0.5), 2, 5)
    hi = rebonato_vol(calibrate_to_caplets(F0, VOLS, beta=0.01), 2, 5)
    assert lo < hi
    assert hjm_drift_gaussian(1.0, 1.0, 0.01, 0.05) == 0.0
    assert hjm_drift_gaussian(0.0, 10.0, 0.01, 0.05) == pytest.approx(
        0.01**2 * math.exp(-0.5) * (1 - math.exp(-0.5)) / 0.05)
