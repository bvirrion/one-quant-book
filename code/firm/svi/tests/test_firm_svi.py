"""Acceptance tests of the Book 5, Chapter 8 build (SVI and SSVI)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_svi import event_variance, fit_svi, implied_move, nelder_mead, ssvi, ssvi_check, svi, svi_check


def test_exact_slice_recovered():
    k = np.linspace(-0.5, 0.4, 31)
    p = (0.01, 0.1, -0.6, 0.05, 0.12)
    q, rmse = fit_svi(k, svi(k, *p))
    assert rmse < 1e-6 and np.max(np.abs(svi(k, *q) - svi(k, *p))) < 1e-5


def test_checks():
    assert all(svi_check(0.01, 0.1, -0.6, 0.0, 0.1).values())
    assert not svi_check(0.01, 1.5, -0.6, 0.0, 0.1)["wings<=2"]
    th = [0.002, 0.01, 0.04]
    assert all(ssvi_check(th, -0.6, 1.0, 0.5).values())
    assert not ssvi_check(th, -0.6, 60.0, 0.5)["butterfly 2"]


def test_ssvi_atm_is_theta():
    assert abs(float(ssvi(0.0, 0.04, -0.7, 1.2, 0.4)) - 0.04) < 1e-15


def test_event_variance_recovers_planted_jump():
    base, jump = 0.3, 0.07
    t1, t2 = 5 / 365, 12 / 365
    ev = event_variance(base ** 2 * t1, t1, base ** 2 * t2 + jump ** 2, t2)
    assert abs(ev - jump ** 2) < 1e-15 and abs(implied_move(ev)[1] - jump * math.sqrt(2 / math.pi)) < 1e-15


def test_nelder_mead_rosenbrock():
    x, v = nelder_mead(lambda z: (1 - z[0]) ** 2 + 100 * (z[1] - z[0] ** 2) ** 2, [-1.2, 1.0], [0.5, 0.5], tol=1e-14,
                       max_iter=5000)
    assert np.allclose(x, [1, 1], atol=1e-4)
