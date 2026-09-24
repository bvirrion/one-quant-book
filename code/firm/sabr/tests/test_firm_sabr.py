"""Acceptance tests of the Book 5, Chapter 11 build (SABR)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_sabr import alpha_from_atm, calibrate, deltas, hagan_lognormal, one_day_hedge_errors


def test_flat_limit():
    for k in (0.8, 1.0, 1.3):
        assert abs(hagan_lognormal(1.0, k, 1.0, 0.25, 1.0, -0.5, 1e-9) - 0.25) < 1e-6


def test_atm_reproduced():
    a = alpha_from_atm(0.03, 2.0, 0.22, 0.5, -0.4, 0.6)
    assert abs(hagan_lognormal(0.03, 0.03, 2.0, a, 0.5, -0.4, 0.6) - 0.22) < 1e-12


def test_calibration_recovers_parameters():
    ks = np.linspace(0.02, 0.045, 11)
    a = alpha_from_atm(0.03, 1.0, 0.2, 0.5, -0.35, 0.45)
    vols = [hagan_lognormal(0.03, k, 1.0, a, 0.5, -0.35, 0.45) for k in ks]
    (a2, r2, n2), rmse = calibrate(0.03, 1.0, ks, vols, 0.5, 0.2)
    assert rmse < 1e-7 and abs(r2 + 0.35) < 1e-4 and abs(n2 - 0.45) < 1e-4


def test_minimum_variance_delta_best_for_negative_correlation():
    a = alpha_from_atm(0.03, 1.0, 0.2, 0.5, -0.6, 0.5)
    e = one_day_hedge_errors(0.03, 0.03, 1.0, a, 0.5, -0.6, 0.5, n=50_000)
    assert e["bartlett"] < e["black"] < e["hagan"]
    d = deltas(0.03, 0.03, 1.0, a, 0.5, -0.6, 0.5)
    assert d["bartlett"] < d["black"] < d["hagan"]
