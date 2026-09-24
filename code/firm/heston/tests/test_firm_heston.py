"""Acceptance tests of the Book 5, Chapter 10 build (Heston model)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_bs import black
from firm_heston import Heston, black_limit_vol, calibrate, call_prices, implied_vols

KS = np.array([80.0, 90, 100, 110, 120])


def test_martingale_and_normalisation():
    m = Heston(0.04, 1.5, 0.04, 0.6, -0.7)
    assert np.allclose(m.cf(np.array([0.0, -1j]), 2.0), [1.0, 1.0], atol=1e-12)


def test_small_eta_limit_is_black_scholes():
    m = Heston(0.08, 1.5, 0.04, 1e-4, -0.7)
    ref = [black(100, k, 1.0, 1.0, black_limit_vol(m, 1.0), "C") for k in KS]
    assert np.max(np.abs(call_prices(m, 100, KS, 1.0) - ref)) < 1e-3


def test_parity_and_discounting():
    m = Heston(0.04, 1.5, 0.04, 0.6, -0.7)
    c = call_prices(m, 105.0, KS, 1.0, df=0.97)
    assert np.all(np.diff(c) < 0) and np.all(c > 0.97 * np.maximum(105 - KS, 0))


def test_calibration_recovers_parameters():
    true = Heston(0.03, 2.0, 0.05, 0.7, -0.6)
    quotes = [(t, KS, implied_vols(true, 100.0, KS, t)) for t in (0.25, 1.0, 2.0)]
    fit, rmse = calibrate(quotes, 100.0, Heston(0.04, 1.5, 0.04, 0.5, -0.5))
    assert rmse < 1e-5
    assert abs(fit.rho - true.rho) < 0.01 and abs(fit.v0 - true.v0) < 1e-3
