"""Acceptance tests of firm.hawkes (Python)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_hawkes import (
    compensator,
    fit,
    intensity,
    loglik,
    residuals,
    simulate_branching,
    simulate_multivariate,
    simulate_thinning,
)


def test_reference_values_shared_with_cpp_and_rust():
    t = np.array([0.5, 1.2, 1.3, 4.0, 4.1, 4.15, 9.0])
    assert abs(loglik((0.1, 0.7, 1.0), t, 10.0) - (-12.20712398254631)) < 1e-12
    assert abs(compensator(t, 0.1, 0.7, 1.0)[6] - 5.083844743294921) < 1e-12


def test_mean_counts_thinning_and_branching():
    T = 50_000.0
    a = simulate_thinning(0.2, 0.5, 1.0, T, 1).size
    b = simulate_branching(0.2, 0.5, 1.0, T, 2)[0].size
    assert abs(a / (0.4 * T) - 1) < 0.04 and abs(b / (0.4 * T) - 1) < 0.04


def test_fit_recovers_parameters_and_residuals_are_exponential():
    t = simulate_thinning(0.2, 0.5, 1.0, 50_000.0, 3)
    f = fit(t, 50_000.0)
    assert abs(f["branching"] - 0.5) < 0.04 and abs(f["beta"] - 1.0) < 0.15
    r = residuals(t, 0.2, 0.5, 1.0)
    assert abs(r.mean() - 1) < 0.02 and abs(r.var() - 1) < 0.05


def test_intensity_and_multivariate():
    lam = intensity(np.array([1.0]), 0.1, 0.7, 1.0, np.array([0.5, 1.0, 2.0]))
    assert np.allclose(lam, [0.1, 0.1, 0.1 + 0.7 * np.exp(-1.0)])
    mu = [0.1, 0.1]
    alpha = [[0.2, 0.4], [0.4, 0.2]]
    beta = [[1.0, 1.0], [1.0, 1.0]]
    out = simulate_multivariate(mu, alpha, beta, 40_000.0, 4)
    rho = np.max(np.abs(np.linalg.eigvals(np.array(alpha) / np.array(beta))))
    expected = np.linalg.solve(np.eye(2) - np.array(alpha) / np.array(beta), mu) * 40_000.0
    assert rho < 1 and all(abs(o.size / e - 1) < 0.06 for o, e in zip(out, expected, strict=True))
