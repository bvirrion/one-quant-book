"""Acceptance tests of the Book 5, Chapter 3 build (Black-Scholes kernels)."""
import math
import pathlib
import random
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_bs import black, bs, greeks, implied_vol, ncdf


def test_textbook_value_and_parity():
    assert abs(bs(100, 100, 1, 0.05, 0, 0.2, "C") - 10.450583572185579) < 1e-12
    c, p = bs(100, 110, 0.5, 0.03, 0.01, 0.25, "C"), bs(100, 110, 0.5, 0.03, 0.01, 0.25, "P")
    assert abs(c - p - (100 * math.exp(-0.005) - 110 * math.exp(-0.015))) < 1e-12


def test_tail_accuracy_of_cdf():
    assert ncdf(-10) > 0 and abs(ncdf(-10) / 7.619853024160527e-24 - 1) < 1e-12


@pytest.mark.parametrize("name,bump", [("delta", "s"), ("vega", "v"), ("rho", "r"), ("theta", "t")])
def test_greeks_against_central_differences(name, bump):
    h = 1e-4
    base = {"s": 100.0, "t": 0.5, "r": 0.03, "v": 0.25}

    def f(**kw):
        a = {**base, **kw}
        return bs(a["s"], 110, a["t"], a["r"], 0.01, a["v"], "P")
    up, dn = f(**{bump: base[bump] + h}), f(**{bump: base[bump] - h})
    num = (up - dn) / (2 * h) * (-1 if bump == "t" else 1)
    assert abs(greeks(100, 110, 0.5, 0.03, 0.01, 0.25, "P")[name] - num) < 1e-5


def test_second_order_greeks():
    h = 1e-4
    g = greeks(100, 110, 0.5, 0.03, 0.01, 0.25, "C")
    dv = (greeks(100, 110, 0.5, 0.03, 0.01, 0.25 + h, "C")["delta"] - greeks(100, 110, 0.5, 0.03, 0.01, 0.25 - h, "C")["delta"]) / (2 * h)
    vv = (greeks(100, 110, 0.5, 0.03, 0.01, 0.25 + h, "C")["vega"] - greeks(100, 110, 0.5, 0.03, 0.01, 0.25 - h, "C")["vega"]) / (2 * h)
    gg = (greeks(100 + h, 110, 0.5, 0.03, 0.01, 0.25, "C")["delta"] - greeks(100 - h, 110, 0.5, 0.03, 0.01, 0.25, "C")["delta"]) / (2 * h)
    assert abs(g["vanna"] - dv) < 1e-6 and abs(g["volga"] - vv) < 1e-5 and abs(g["gamma"] - gg) < 1e-8


def test_implied_vol_round_trip_random():
    rng = random.Random(7)
    for _ in range(5000):
        k = 100 * math.exp(rng.uniform(-2, 2))
        t = rng.choice([1 / 365, 0.02, 0.25, 1, 5, 30])
        v, r = rng.uniform(0.01, 1.5), rng.choice("CP")
        p = black(100, k, t, 0.97, v, r)
        intrinsic = 0.97 * max((100 - k) if r == "C" else (k - 100), 0.0)
        if p < 1e-10 or p - intrinsic < 1e-9 * p:       # no time value left to invert
            continue
        assert abs(black(100, k, t, 0.97, implied_vol(p, 100, k, t, 0.97, r), r) - p) <= 1e-11 * max(p, 1.0)


def test_implied_vol_refuses_impossible_prices():
    with pytest.raises(ValueError):
        implied_vol(0.5, 100, 80, 1, 1, "C")
    with pytest.raises(ValueError):
        implied_vol(100.0, 100, 80, 1, 1, "C")
