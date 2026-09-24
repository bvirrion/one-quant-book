"""Acceptance tests of the Book 6, chapter 5 build (shifted and normal SABR, the cube)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_sabrcube import Cube, Sabr, calibrate_section, density, hagan_lognormal, hagan_normal_beta0, price


def test_atm_lognormal_limit():
    p = Sabr(0.04, 0.5, -0.3, 0.4, 0.01)
    f, t = 0.02, 5.0
    fs = f + p.shift
    corr = 1 + (0.25 / 24 * p.alpha**2 / fs + p.rho * 0.5 * p.nu * p.alpha / (4 * fs**0.5)
                + (2 - 3 * p.rho**2) / 24 * p.nu**2) * t
    assert hagan_lognormal(f, f, t, p) == pytest.approx(p.alpha / fs**0.5 * corr, rel=1e-12)


def test_normal_sabr_without_volvol_is_bachelier():
    p = Sabr(0.007, 0.0, 0.2, 1e-9)
    assert hagan_normal_beta0(-0.004, 0.01, 3.0, p) == pytest.approx(0.007, rel=1e-6)


def test_calibration_recovers_planted_parameters_and_fits_across_models():
    true = Sabr(0.0025, 0.0, 0.1, 0.6)
    f, t = -0.003, 1.0
    ks = [f + d * 1e-4 for d in (-50, -25, 0, 25, 50, 100)]
    q = [hagan_normal_beta0(f, k, t, true) for k in ks]
    p, err = calibrate_section(f, t, ks, q, 0.0, 0.0, "normal")
    assert (p.alpha, p.rho, p.nu) == pytest.approx((0.0025, 0.1, 0.6), rel=1e-6) and err < 1e-10
    p, err = calibrate_section(f, t, ks, q, 0.5, 0.03)
    assert err < 0.2e-4


def test_parity_and_density():
    p = Sabr(0.03, 0.5, -0.2, 0.3, 0.02)
    f, k, t = 0.01, 0.015, 2.0
    assert price(f, k, t, p) - price(f, k, t, p, payer=False) == pytest.approx(f - k, abs=1e-12)
    q = Sabr(0.006, 0.0, 0.0, 0.1)
    grid = [x * 1e-4 for x in range(-400, 601, 10)]
    d = density(0.01, 1.0, q, grid, model="normal")
    assert min(d) > -1e-5 and sum(d) * 1e-3 == pytest.approx(1.0, abs=5e-3)   # tails: round-off only


def test_cube_interpolates_parameters_bilinearly():
    s = {(e, n): Sabr(0.01 * e + 0.001 * n, 0.5, -0.1, 0.3, 0.03) for e in (1.0, 5.0) for n in (2.0, 10.0)}
    c = Cube([1.0, 5.0], [2.0, 10.0], s, {k: 0.02 for k in s})
    assert c.params(1.0, 2.0) == s[(1.0, 2.0)]
    assert c.params(3.0, 6.0).alpha == pytest.approx(0.03 + 0.006)
    assert math.isfinite(c.normal_vol(3.0, 6.0, 0.021))
