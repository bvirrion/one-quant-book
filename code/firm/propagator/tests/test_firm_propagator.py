import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_propagator import (  # noqa: E402
    fit_kernel,
    impact_matrix,
    obizhaeva_wang,
    optimal_liquidation,
    propagate,
    round_trip,
    sign_acf,
)


def test_kernel_recovered_from_correlated_signs():
    rng = np.random.default_rng(1)
    n = 60_000
    eps = np.empty(n)
    eps[0] = 1
    for t in range(1, n):                                  # AR(1)-like persistent signs
        eps[t] = eps[t - 1] if rng.random() < 0.8 else -eps[t - 1]
    g_true = np.concatenate([[0.0], 1.0 / (1 + np.arange(30)) ** 0.4])
    p = propagate(eps, g_true) + 0.05 * rng.standard_normal(n)
    _, g = fit_kernel(eps, p, 20)
    assert np.allclose(g[1:15], g_true[1:15], atol=0.02)
    c = sign_acf(eps, 3)
    assert abs(c[1] - 0.6) < 0.02


def test_round_trips_and_liquidation():
    t = np.linspace(0, 1, 11)
    gam = impact_matrix(t, lambda x: np.exp(-3 * x))
    assert round_trip(gam) < 0                             # a positive definite kernel: no profitable round trip
    assert np.all(optimal_liquidation(gam, 1.0) > 0)       # convex: sells only
    bad = impact_matrix(t, lambda x: np.exp(-((x / 0.3) ** 3)))
    assert round_trip(bad) > 0                             # not positive definite: a round trip pays
    mid = impact_matrix(t, lambda x: np.exp(-((x / 0.3) ** 1.8)))
    assert round_trip(mid) < 0 and np.any(optimal_liquidation(mid, 1.0) < 0)   # positive definite, not convex
    b0, r, b1 = obizhaeva_wang(1.0, 3.0, 1.0)
    assert np.isclose(b0 + r * 1.0 + b1, 1.0) and np.isclose(b0, 0.2)
    x = optimal_liquidation(impact_matrix(np.linspace(0, 1, 201), lambda s: np.exp(-3 * s)), 1.0)
    assert abs(x[0] - 0.2) < 0.02 and abs(x[-1] - 0.2) < 0.02    # the discrete optimum approaches Obizhaeva-Wang
