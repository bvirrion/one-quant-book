"""Acceptance tests of the Book 5, Chapter 17 build (multi-asset options)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_bs import black
from firm_multiasset import (
    basket_moment_match,
    basket_payoff,
    best_of_payoff,
    composite_vol,
    correlated_paths,
    equicorrelation,
    implied_correlation,
    index_variance,
    local_correlation_paths,
    quanto_forward,
    realised_correlation,
    worst_of_payoff,
)


def test_paths_are_martingales_with_the_right_correlation():
    p = correlated_paths([100.0, 50.0], [0.2, 0.4], [[1, 0.6], [0.6, 1]], [0.5, 1.0], n_paths=200_000, seed=1)
    assert np.allclose(p[:, -1, :].mean(axis=0), [100.0, 50.0], rtol=3e-3)
    lr = np.log(p[:, 1, :] / p[:, 0, :])
    assert abs(np.corrcoef(lr, rowvar=False)[0, 1] - 0.6) < 0.01


def test_single_asset_limits():
    p = correlated_paths([1.0, 1.0], [0.3, 0.3], equicorrelation(2, 0.999999), [1.0], n_paths=200_000, seed=2)
    wo = worst_of_payoff(p, 1.0, "P").mean()
    bo = best_of_payoff(p, 1.0, "C").mean()
    ref = black(1.0, 1.0, 1.0, 1.0, 0.3, "C")
    assert abs(wo - ref) < 0.003 and abs(bo - ref) < 0.003
    # moment matching against simulation for a basket
    p3 = correlated_paths(np.ones(3), [0.25, 0.3, 0.35], equicorrelation(3, 0.4), [1.0], n_paths=200_000, seed=3)
    mc = basket_payoff(p3, np.ones(3) / 3, 1.0).mean()
    assert abs(mc - basket_moment_match(np.ones(3) / 3, np.ones(3), [0.25, 0.3, 0.35], equicorrelation(3, 0.4), 1.0, 1.0)) < 0.002


def test_correlation_algebra():
    w, v = np.array([0.5, 0.3, 0.2]), np.array([0.2, 0.3, 0.4])
    for rho in (0.1, 0.5, 0.9):
        assert abs(implied_correlation(math.sqrt(index_variance(w, v, rho)), w, v) - rho) < 1e-12
    rng = np.random.default_rng(4)
    z = rng.standard_normal((20_000, 3)) @ np.linalg.cholesky(equicorrelation(3, 0.3)).T
    assert abs(realised_correlation(z, [1 / 3] * 3) - 0.3) < 0.02


def test_local_correlation_reduces_to_constant():
    rho = 0.4
    p = local_correlation_paths([100.0] * 4, [0.2, 0.25, 0.3, 0.35], [0.25] * 4, lambda t, x: np.full_like(x, rho), [1.0],
                                n_paths=100_000, seed=5, steps_per_date=12)
    lr = np.log(p[:, -1, :] / p[:, 0, :])
    c = np.corrcoef(lr, rowvar=False)
    assert abs(c[np.triu_indices(4, 1)].mean() - rho) < 0.01


def test_quanto():
    assert abs(quanto_forward(100.0, 0.2, 0.1, 0.0, 1.0) - 100.0) < 1e-12
    assert quanto_forward(100.0, 0.2, 0.1, 0.5, 1.0) < 100.0
    p = correlated_paths([100.0], [0.2], [[1.0]], [1.0], n_paths=200_000, seed=6, quanto=(0.1, np.array([-0.5])))
    se = p[:, -1, 0].std() / math.sqrt(len(p))
    assert abs(p[:, -1, 0].mean() - quanto_forward(100.0, 0.2, 0.1, -0.5, 1.0)) < 4 * se
    assert abs(composite_vol(0.2, 0.1, 0.0) - math.sqrt(0.05)) < 1e-15
