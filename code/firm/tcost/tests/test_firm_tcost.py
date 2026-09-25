import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tcost import (
    breakeven_cost,
    cost_aware,
    fit_impact,
    impact_bp,
    net_trades,
    netting_saving,
    prox_cost,
    smooth,
    trade_cost,
)


def test_fit_recovers_a_planted_law():
    rng = np.random.default_rng(0)
    n = 20000
    sigma = rng.uniform(0.01, 0.03, n)
    part = np.exp(rng.uniform(np.log(1e-4), np.log(0.2), n))
    cost = 2e-4 + impact_bp(0.8, sigma, part, 0.5) + sigma * 0.3 * rng.standard_normal(n)
    f = fit_impact(cost, sigma, part, 2e-4)
    assert abs(f["exponent"] - 0.5) < 3 * f["se_exponent"] + 0.02 and abs(f["eta_fixed"] - 0.8) < 3 * f["se_eta"]


def test_prox_and_cost():
    v = np.array([-0.3, 0.001, 0.5])
    x = prox_cost(v, 0.01, 0.2)
    for vi, xi in zip(v, x, strict=True):                              # optimality against a fine grid
        grid = np.linspace(-1, 1, 200001)
        obj = 0.5 * (grid - vi) ** 2 + 0.01 * np.abs(grid) + 0.2 * np.abs(grid) ** 1.5
        assert abs(grid[np.argmin(obj)] - xi) < 2e-5
    assert x[1] == 0.0
    c = trade_cost([0.01, -0.02], 1e8, [0.02, 0.02], [1e7, 1e7], [2e-4, 2e-4], 0.8)
    assert abs(c - (0.03 * 2e-4 + 0.8 * 0.02 * (0.01 * math.sqrt(0.1) + 0.02 * math.sqrt(0.2)))) < 1e-15


def test_cost_aware_optimum():
    rng = np.random.default_rng(1)
    n = 20
    B = rng.standard_normal((n, 2)) * 0.01
    S = B @ B.T + np.diag(rng.uniform(1e-4, 4e-4, n))
    alpha = rng.standard_normal(n) * 1e-3
    free = np.linalg.solve(5.0 * S, alpha)
    w = cost_aware(alpha, S, np.zeros(n), 1.0, np.full(n, 0.02), np.full(n, 1e12), np.zeros(n), 0.0, 5.0)
    assert np.allclose(w, free, atol=1e-8)                              # no costs: mean-variance
    w0 = free * 0.5
    wc = cost_aware(alpha, S, w0, 1e9, np.full(n, 0.02), np.full(n, 1e7), np.full(n, 2e-4), 0.8, 5.0)
    obj = lambda x: alpha @ x - 2.5 * x @ S @ x - trade_cost(x - w0, 1e9, np.full(n, 0.02), np.full(n, 1e7),  # noqa: E731
                                                             np.full(n, 2e-4), 0.8)
    for _ in range(50):
        trial = wc + 1e-4 * rng.standard_normal(n)
        assert obj(trial) <= obj(wc) + 1e-12
    assert np.abs(wc - w0).sum() < np.abs(free - w0).sum()               # costs: trade less


def test_netting_smoothing_breakeven():
    a, b = np.array([0.02, -0.01, 0.0]), np.array([-0.01, -0.01, 0.03])
    net, T = net_trades([a, b])
    assert np.allclose(net, [0.01, -0.02, 0.03]) and T.shape == (2, 3)
    cost = lambda d: float(np.abs(d).sum())  # noqa: E731
    r = netting_saving([a, b], cost)
    assert abs(r["saving"] - 0.02) < 1e-12 and abs(r["shares"].sum() - r["saving"]) < 1e-12
    x = smooth(np.r_[np.zeros(5), np.ones(200)], 10.0)
    assert abs(x[15] - (1 - 0.5**1.1)) < 1e-12 and x[-1] > 0.99            # 1 - lambda^(k + 1) after a step
    assert breakeven_cost(0.10, 20.0) == 0.005
