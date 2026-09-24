"""Acceptance tests of the Book 5, Chapter 13 build (jump and Levy models)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_jumps import (
    Bates,
    EventJump,
    Kou,
    Merton,
    VarianceGamma,
    calibrate,
    call_prices,
    implied_vols,
    skew_kurtosis,
)

MODELS = [Merton(0.15, 1.0, -0.1, 0.1), Kou(0.12, 3.0, 0.3, 25.0, 12.0), VarianceGamma(0.12, 0.2, -0.14),
          Bates(0.04, 1.5, 0.04, 0.6, -0.7, 0.5, -0.1, 0.1), EventJump.from_up(0.3, 0.4, 0.2)]


def test_martingale_and_normalisation():
    for m in MODELS:
        for t in (1 / 52, 1.0):
            assert abs(m.cf(np.array([0.0]), t)[0] - 1) < 1e-12
            assert abs(m.cf(np.array([-1j]), t)[0] - 1) < 1e-10          # E[e^x] = 1


def test_closed_forms_agree_with_fourier():
    m = MODELS[0]
    for t in (1 / 52, 1.0):
        ks = [80.0, 100.0, 120.0]
        assert np.max(np.abs(call_prices(m, 100.0, ks, t) - [m.series_call(100.0, k, t) for k in ks])) < 1e-5
    vg = MODELS[2]
    for t in (1 / 52, 1 / 12, 2.0):
        ks = [85.0, 100.0, 115.0]
        assert np.max(np.abs(call_prices(vg, 100.0, ks, t) - [vg.conditional_call(100.0, k, t) for k in ks])) < 5e-5
    e = MODELS[4]
    ks = [40.0, 50.0, 60.0]
    assert np.max(np.abs(call_prices(e, 50.0, ks, 1 / 52) - [e.mixture_call(50.0, k, 1 / 52) for k in ks])) < 1e-5


def test_limits():
    # no jumps: Black-Scholes; Bates without jumps: Heston
    flat = implied_vols(Merton(0.2, 0.0, 0.0, 0.1), 100.0, [80.0, 100.0, 125.0], 0.5)
    assert np.allclose(flat, 0.2, atol=1e-6)
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "heston"))
    from firm_heston import Heston
    from firm_heston import call_prices as heston_calls
    b = Bates(0.04, 1.5, 0.04, 0.6, -0.7, 0.0, -0.1, 0.1)
    assert np.allclose(call_prices(b, 100.0, [90.0, 110.0], 0.5),
                       heston_calls(Heston(0.04, 1.5, 0.04, 0.6, -0.7), 100.0, [90.0, 110.0], 0.5), atol=1e-8)


def test_cumulant_scaling_and_skew_sign():
    for m in MODELS[:3]:
        s1, k1 = skew_kurtosis(m, 0.25)
        s2, k2 = skew_kurtosis(m, 1.0)
        assert abs(s1 / s2 - 2.0) < 1e-12 and abs(k1 / k2 - 4.0) < 1e-12 and s1 < 0 and k1 > 0
        v = implied_vols(m, 100.0, [90.0, 110.0], 1 / 12)
        assert v[0] > v[1]


def test_calibration_recovers_parameters():
    true = Merton(0.12, 2.0, -0.07, 0.05)
    ks = np.array([90.0, 95, 100, 105, 110])
    q = [(1 / 12, ks, implied_vols(true, 100.0, ks, 1 / 12)), (0.5, ks, implied_vols(true, 100.0, ks, 0.5))]
    model, _, rmse = calibrate(lambda z: Merton(math.exp(z[0]), math.exp(z[1]), z[2], math.exp(z[3])),
                               [math.log(0.13), math.log(1.5), -0.08, math.log(0.06)], q, 100.0)
    assert rmse < 1e-6 and abs(model.lam - 2.0) < 1e-3 and abs(model.mu + 0.07) < 1e-4


def test_event_fairness():
    e = EventJump.from_up(0.3, 0.25, 0.3)
    assert abs(e.p * math.exp(e.a) + (1 - e.p) * math.exp(e.b) - 1) < 1e-15
    assert abs(e.mixture_call(50.0, 1e-9, 0.1) - 50.0) < 1e-6
