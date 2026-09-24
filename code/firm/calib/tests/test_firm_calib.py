"""Acceptance tests of the Book 5, Chapter 24 build (transform pricing and the calibration pipeline)."""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_bs import black
from firm_calib import (
    Heston,
    QuoteSet,
    calibrate,
    carr_madan_at,
    cos_calls,
    cumulants,
    filter_quotes,
    heston_to,
    jump_alarm,
    lewis_calls,
    vol_errors,
)


@dataclass(frozen=True)
class Lognormal:
    sigma: float

    def cf(self, u, t):
        u = np.asarray(u, complex)
        return np.exp(-0.5 * self.sigma ** 2 * t * (1j * u + u * u))


def test_transforms_match_black_and_each_other():
    ks = np.array([70.0, 90.0, 100.0, 110.0, 140.0])
    m = Lognormal(0.25)
    exact = np.array([black(100.0, k, 0.5, 1.0, 0.25, "C") for k in ks])
    assert np.allclose(cos_calls(m, 100.0, ks, 0.5, n=128), exact, atol=1e-9)
    assert np.allclose(lewis_calls(m, 100.0, ks, 0.5), exact, atol=1e-9)
    assert np.allclose(carr_madan_at(m, 100.0, ks, 0.5, n=4096), exact, atol=1e-5)
    c1, c2 = cumulants(m, 0.5)
    assert abs(c1 + 0.5 * 0.25 ** 2 * 0.5) < 1e-9 and abs(c2 - 0.25 ** 2 * 0.5) < 1e-6
    h = Heston(0.04, 1.5, 0.04, 0.6, -0.7)
    ref = lewis_calls(h, 100.0, ks, 1.0)
    assert np.abs(cos_calls(h, 100.0, ks, 1.0, n=256) - ref).max() < 1e-6
    assert np.abs(carr_madan_at(h, 100.0, ks, 1.0, n=4096) - ref).max() < 1e-5


def test_filter():
    q = QuoteSet(np.array([0.5] * 5), np.array([100.0, 100.0, 100.0, 100.0, 300.0]),
                 np.array([0.2, 0.0, 0.25, 0.19, 0.2]), np.array([0.21, 0.2, 0.24, 0.30, 0.21]), 100.0)
    keep, counts = filter_quotes(q)
    assert keep.tolist() == [True, False, False, False, False]
    assert counts == {"no bid": 1, "crossed": 1, "wide": 1, "far": 1}


def test_round_trip_and_penalty():
    t = np.repeat([0.25, 0.5, 1.0], 5)
    k = 100.0 * np.exp(np.tile([-1.0, -0.5, 0.0, 0.5, 1.0], 3) * 0.2 * np.sqrt(t))
    truth = Heston(0.045, 2.0, 0.05, 0.5, -0.65)
    iv = vol_errors(truth, QuoteSet(t, k, np.full_like(t, 0.2), np.full_like(t, 0.2), 100.0)) + 0.2
    q = QuoteSet(t, k, iv, iv, 100.0)
    fit = calibrate(q, heston_to(Heston(0.04, 1.5, 0.04, 0.6, -0.7)))
    assert np.allclose(heston_to(fit.model), heston_to(truth), atol=1e-5) and fit.rmse < 1e-8
    assert np.abs(vol_errors(fit.model, q)).max() < 1e-7
    prior = heston_to(Heston(0.045, 2.0, 0.05, 0.8, -0.65))
    stiff = calibrate(q, prior, prior=prior, reg=1e6)
    assert np.allclose(stiff.z, prior, atol=1e-4) and stiff.rmse > 1e-3
    assert jump_alarm(prior, heston_to(truth), [0.1] * 5) == [3]




def test_vega_weights_are_volatility_errors():
    t, k = np.array([0.5]), np.array([105.0])
    q = QuoteSet(t, k, np.array([0.2]), np.array([0.2]), 100.0)
    h = Heston(0.04, 1.5, 0.04, 0.6, -0.7)
    err = vol_errors(h, q)[0]
    price_err = cos_calls(h, 100.0, k, 0.5)[0] - black(100.0, 105.0, 0.5, 1.0, 0.2, "C")
    d1 = (math.log(100 / 105) + 0.5 * 0.04 * 0.5) / (0.2 * math.sqrt(0.5))
    vega = 100.0 * math.sqrt(0.5) * math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    assert abs(price_err / vega - err) < 0.02 * abs(err)
