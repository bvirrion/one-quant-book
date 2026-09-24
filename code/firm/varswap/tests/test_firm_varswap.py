"""Acceptance tests of the Book 5, Chapter 14 build (variance and volatility swaps)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_varswap import (
    cir_laplace,
    heston_mean_variance,
    heston_vix_future,
    heston_vol_swap,
    index_variance,
    integrated_cir_laplace,
    jump_error,
    log_payoff_strip,
    mark_to_market,
    realised_variance,
    strip_from_vols,
    variance_notional,
    vol_swap_approx,
)


def test_flat_smile_index_is_its_variance():
    for vol, t in ((0.2, 30 / 365), (0.3, 1.0)):
        ks = np.arange(20.0, 400.01, 0.25)
        k, c, p = strip_from_vols(lambda x, v=vol: v, 100.0, t, ks)
        assert abs(math.sqrt(index_variance(k, c, p, 100.0, t)) - vol) < 2e-4
    # a forward between strikes: the (F / K0 - 1)^2 term keeps the answer right
    ks = np.arange(20.0, 400.01, 0.25)
    k, c, p = strip_from_vols(lambda x: 0.2, 100.1, 0.25, ks)
    assert abs(math.sqrt(index_variance(k, c, p, 100.1, 0.25)) - 0.2) < 2e-4


def test_strip_replicates_the_log_payoff_inside_its_range():
    ks = np.arange(50.0, 200.01, 0.5)
    s = np.array([60.0, 90.0, 100.0, 130.0, 190.0])
    assert np.max(np.abs(log_payoff_strip(s, 100.0, ks) + 2 * np.log(s / 100.0))) < 1e-4


def test_conventions():
    prices = 100 * np.exp(np.cumsum([0.0, 0.01, -0.01, 0.02]))
    assert abs(realised_variance(prices) - 252 * (0.0001 + 0.0001 + 0.0004) / 3) < 1e-12
    assert variance_notional(100_000, 0.20) == 250_000
    assert abs(mark_to_market(1.0, 0.2, 0.0, 0.0, 0.04, 1.0)) < 1e-15
    assert abs(mark_to_market(1.0, 0.2, 0.09, 0.5, 0.04, 0.5) - 0.025) < 1e-15
    r = np.array([1e-3, -1e-3])
    assert np.allclose(jump_error(r), r ** 3 / 3, rtol=1e-2)
    assert jump_error(-0.2) < 0 < jump_error(0.2)


def test_heston_exact_values():
    v0, k, vb, eta, t = 0.04, 1.5, 0.04, 0.6, 1.0
    assert abs(integrated_cir_laplace(np.array([0.0]), v0, k, vb, eta, t)[0] - 1) < 1e-14
    assert abs(cir_laplace(np.array([0.0]), v0, k, vb, eta, t)[0] - 1) < 1e-14
    assert abs(heston_mean_variance(0.04, 2.0, 0.09, 1e-8) - 0.04) < 1e-7
    vs = heston_vol_swap(v0, k, vb, eta, t)
    assert vs < 0.2
    # tiny vol-of-vol: the volatility swap tends to the variance swap, as the approximation says
    small = heston_vol_swap(v0, k, vb, 0.01, t)
    assert abs(small - 0.2) < 1e-4
    # against a Monte Carlo of the integrated variance (full-truncation Euler, 500 steps)
    rng = np.random.default_rng(1)
    n, steps = 100_000, 500
    v, integ = np.full(n, v0), np.zeros(n)
    for _ in range(steps):
        vp = np.maximum(v, 0.0)
        integ += vp / steps
        v = v + k * (vb - vp) / steps + eta * np.sqrt(vp / steps) * rng.standard_normal(n)
    mc = np.sqrt(integ)
    assert abs(vs - mc.mean()) < 4 * mc.std() / math.sqrt(n) + 1e-3
    fut, fwd = heston_vix_future(v0, k, vb, eta, 1e-9)
    assert abs(fut - fwd) < 1e-6
    fut, fwd = heston_vix_future(v0, k, vb, eta, 1.0)
    assert fut < fwd


def test_convexity_approximation():
    assert abs(vol_swap_approx(0.04, 0.0) - 0.2) < 1e-15
    assert vol_swap_approx(0.04, 1e-4) < 0.2
