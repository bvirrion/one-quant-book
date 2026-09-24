"""Acceptance tests of firm.dpsolve."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_dpsolve import backward_induction, gauss_hermite_normal


def test_gauss_hermite_moments():
    z, w = gauss_hermite_normal(10)
    assert abs(w.sum() - 1) < 1e-12 and abs(w @ z**2 - 1) < 1e-12 and abs(w @ z**4 - 3) < 1e-10


def test_merton_policy_is_wealth_independent():
    z, wz = gauss_hermite_normal(20)
    gross = np.exp(0.07 - 0.5 * 0.18**2 + 0.18 * z)
    grid = np.linspace(math.log(0.05), math.log(50), 241)
    controls = np.linspace(0, 1.5, 301)

    def tr(t, x, u):
        return x[..., None] + np.log(np.maximum(1 + 0.02 + u[..., None] * (gross - 1.02), 1e-12)), wz

    res = backward_induction(grid, controls, 5, lambda t, x, u: 0 * x, tr, lambda x: np.exp(x) ** -2 / -2)
    inner = (grid > math.log(0.3)) & (grid < math.log(10))
    assert np.ptp(res["policy"][0][inner]) == 0 and abs(res["policy"][0][inner][0] - 0.517) < 0.006


def test_optimal_stopping_of_a_random_walk():
    """Stop a +-1 walk on 0..10 to collect max(x - 4, 0) within 30 steps: the value function is the
    smallest excessive majorant; at the end it equals the payoff and it never lies below it."""
    grid = np.arange(0, 11, dtype=float)

    def tr(t, x, u):
        nxt = np.stack([np.minimum(x + 1, 10), np.maximum(x - 1, 0)], axis=-1)
        return nxt, np.array([0.5, 0.5])

    payoff = np.maximum(grid - 4, 0)
    res = backward_induction(grid, np.array([0.0]), 30, lambda t, x, u: 0 * x, tr, lambda x: np.maximum(x - 4, 0),
                             stop=lambda t, x: np.maximum(x - 4, 0))
    assert np.all(res["values"] >= payoff - 1e-12) and res["stop"][0][10] and not res["stop"][0][5]
