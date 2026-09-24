"""Acceptance tests of the Book 6, chapter 3 build (ladders, Jacobian, PCA, hedges, gamma)."""
import datetime as dt
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "curvebuild"))
from firm_curvebuild import Swap, calibrate, swap_pv, with_quote
from firm_ratesrisk import (
    TentBumped,
    cross_gamma,
    key_rate_ladder,
    min_variance_hedge,
    par_ladder,
    par_to_zero,
    pca,
    zero_ladder,
)

SPOT = dt.date(2026, 9, 29)
TEN = [1, 2, 5, 10, 30]
INS = [Swap(SPOT, n, r, f"{n}Y") for n, r in zip(TEN, [0.036, 0.034, 0.0343, 0.0375, 0.0403], strict=True)]


def pv_of(years, fixed, notional=1e8, payer=True):
    return lambda c: swap_pv(c, SPOT, years, fixed, notional, payer)


@pytest.mark.parametrize("kind", ["flat_forward", "monotone_convex"])
def test_par_ladder_maps_to_zero_ladder_through_the_jacobian(kind):
    cal = calibrate(SPOT, INS, kind)
    pv = pv_of(7, 0.04)
    np.testing.assert_allclose(par_to_zero(par_ladder(SPOT, INS, kind, pv), cal.jacobian),
                               zero_ladder(cal.curve, pv), rtol=1e-4, atol=1.0)


def test_key_rates_sum_to_a_parallel_zero_shift():
    c = calibrate(SPOT, INS, "flat_forward").curve
    keys = [c.t(i.maturity) for i in INS]
    pv = pv_of(8, 0.035)
    par = (pv(c.bumped(None, 1e-6)) - pv(c)) * 1e-4 / 1e-6
    assert key_rate_ladder(c, keys, pv).sum() == pytest.approx(par, rel=1e-5)
    assert TentBumped(c, keys, 0, 1e-4).weight(0.1) == 1.0 and TentBumped(c, keys, 1, 1e-4).weight(0.1) == 0.0


def test_pca_recovers_a_planted_factor_structure():
    rng = np.random.default_rng(1)
    level, slope = np.ones(5) / np.sqrt(5), np.linspace(-1, 1, 5) / np.linalg.norm(np.linspace(-1, 1, 5))
    x = rng.normal(0, 10, (4000, 1)) * level + rng.normal(0, 3, (4000, 1)) * slope + rng.normal(0, 0.3, (4000, 5))
    w, v, share = pca(x)
    assert share[0] == pytest.approx(100 / 109.45, abs=0.02) and share[:2].sum() > 0.99
    assert abs(v[:, 0] @ level) > 0.999 and v[:, 0].sum() > 0 and v[-1, 1] > v[0, 1]


def test_minimum_variance_hedge():
    rng = np.random.default_rng(2)
    a = rng.normal(size=(6, 6))
    cov = a @ a.T
    g = rng.normal(size=6)
    h, share = min_variance_hedge(g, g.reshape(-1, 1), cov)
    assert h[0] == pytest.approx(-1.0) and share == pytest.approx(0.0, abs=1e-12)
    h, share = min_variance_hedge(g, np.eye(6)[:, :3], cov)
    assert 0 <= share <= 1


def test_cross_gamma_is_symmetric_and_explains_second_order_pnl():
    kind = "flat_forward"
    pv = pv_of(30, 0.0403)
    g = cross_gamma(SPOT, INS, kind, pv)
    np.testing.assert_allclose(g, g.T)
    move = np.array([-10.0, -8, -2, 5, 12])
    ladder = par_ladder(SPOT, INS, kind, pv)
    moved = [with_quote(i, i.quote() + m * 1e-4) for i, m in zip(INS, move, strict=True)]
    full = pv(calibrate(SPOT, moved, kind).curve) - pv(calibrate(SPOT, INS, kind).curve)
    assert full == pytest.approx(ladder @ move + 0.5 * move @ g @ move, rel=2e-3)
