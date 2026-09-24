"""Acceptance tests of firm.robust."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_robust import (
    gpd_fit,
    gpd_quantile,
    hill,
    huber_location,
    kendall_tau,
    mad,
    qn_scale,
    spearman,
    tail_dependence,
    trimmed_mean,
    winsorize,
)


def test_scales_are_consistent_and_robust():
    rng = np.random.default_rng(1)
    x = rng.normal(0, 2.0, 20_000)
    assert abs(mad(x) - 2) < 0.05 and abs(qn_scale(x) - 2) < 0.05
    y = x.copy()
    y[:2000] = 1e6                                     # 10% gross errors
    assert abs(mad(y) - 2) < 0.4 and abs(qn_scale(y) - 2) < 0.4 and y.std() > 1e5
    z = rng.normal(0, 1, 200)                          # Qn by bisection equals the brute-force order statistic
    d = np.sort(np.abs(z[:, None] - z[None, :])[np.triu_indices(200, 1)])
    h = 101
    assert abs(qn_scale(z) / 2.2219 - d[h * (h - 1) // 2 - 1]) < 1e-12


def test_location_estimators():
    rng = np.random.default_rng(2)
    x = rng.standard_t(3, 50_000) + 1.0
    assert abs(huber_location(x) - 1) < 0.02 and abs(trimmed_mean(x, 0.1) - 1) < 0.02
    w = winsorize(np.arange(101.0), 0.1)
    assert w.min() == 10 and w.max() == 90
    x[0] = 1e9
    assert abs(huber_location(x) - 1) < 0.02                      # breakdown point: one point cannot move it


def test_rank_correlations_gaussian_copula():
    rng = np.random.default_rng(3)
    rho = 0.6
    a = rng.standard_normal(3000)
    b = rho * a + math.sqrt(1 - rho**2) * rng.standard_normal(3000)
    assert abs(spearman(a, b) - 6 / math.pi * math.asin(rho / 2)) < 0.03
    assert abs(kendall_tau(a, b) - 2 / math.pi * math.asin(rho)) < 0.03
    assert abs(spearman(np.exp(a), b**3) - spearman(a, b)) < 1e-12     # invariant to increasing maps
    assert tail_dependence(a, a, 0.05) > 0.99


def test_hill_on_pareto():
    rng = np.random.default_rng(4)
    x = rng.pareto(3.0, 100_000) + 1.0                                    # exact Pareto, alpha = 3
    a, se = hill(x, 2000)
    assert abs(a - 3) < 3 * se and abs(se - a / math.sqrt(2000)) < 1e-12


def test_gpd_fit_and_quantile():
    rng = np.random.default_rng(5)
    xi, beta = 0.25, 0.5
    u = rng.random(20_000)
    y = beta / xi * ((1 - u) ** (-xi) - 1)                                # GPD draws by inversion
    f = gpd_fit(y)
    assert abs(f[0] - xi) < 0.03 and abs(f[1] - beta) < 0.02
    q = gpd_quantile(0.0, xi, beta, 1.0, 0.99)
    assert abs(q - beta / xi * (100**xi - 1)) < 1e-12 and abs(np.mean(y > q) - 0.01) < 0.003
