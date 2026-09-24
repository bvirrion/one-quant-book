import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_portcredit as f


def test_recursion_without_correlation_is_binomial():
    dist = f.loss_distribution(np.full(20, 0.1), 1e-10)
    binom = [math.comb(20, k) * 0.1 ** k * 0.9 ** (20 - k) for k in range(21)]
    assert np.allclose(dist, binom, atol=1e-10)


def test_large_pool_approaches_book_2_limit():
    pool = f.Pool(np.full(1000, 0.01))
    p = 1 - math.exp(-0.05)
    el = f.expected_tranche_losses(pool, 0.3, 0.03, 0.07, maturity=5.0, freq=1)[-1]
    assert abs(el - f.lhp_expected_tranche_loss(0.03, 0.07, p, 0.3, 0.4)) < 5e-3


def test_base_and_compound_agree_on_a_flat_skew_and_index_ignores_correlation():
    pool = f.Pool(np.full(50, 0.01))
    assert np.allclose(f.base_el(pool, 0.3, 0.3, 0.03, 0.07), f.expected_tranche_losses(pool, 0.3, 0.03, 0.07))
    i1 = f.tranche_price(f.expected_tranche_losses(pool, 0.1, 0.0, 1.0), 0.03, 0.0)["par"]
    i2 = f.tranche_price(f.expected_tranche_losses(pool, 0.7, 0.0, 1.0), 0.03, 0.0)["par"]
    assert abs(i1 - i2) < 1e-10


def test_student_t_and_default_correlation():
    assert abs(f.t_cdf(2.131847, 4) - 0.95) < 1e-6 and abs(f.t_inv(0.05, 4) + 2.131847) < 1e-5
    assert abs(f.default_correlation(0.05, 0.0)) < 1e-12 < f.default_correlation(0.05, 0.3)


def test_simulated_mean_loss():
    loss = f.simulate_losses(100, 0.05, 0.3, 0.4, 200_000, seed=3)
    assert abs(loss.mean() - 0.6 * 0.05) < 1e-3
    loss_t = f.simulate_losses(100, 0.05, 0.3, 0.4, 200_000, seed=3, nu=4)
    assert abs(loss_t.mean() - 0.6 * 0.05) < 1.5e-3
