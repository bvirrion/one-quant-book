"""Acceptance tests of the Book 5, Chapter 21 build (convertible bonds)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_convertible import Convertible, bond_floor, greeks, power_hazard, price_grid, value_at

R, Q, VOL = 0.03, 0.01, 0.3


def test_straight_bond_limits():
    straight = Convertible(ratio=1e-9, call_trigger=1e12)
    g = price_grid(straight, R, Q, VOL, power_hazard(0.0, 30, 0))
    assert abs(value_at(30, g) - bond_floor(straight, R, 0.0)) < 1e-3
    lam, rec = 0.05, 0.4
    g = price_grid(straight, R, Q, VOL, power_hazard(lam, 30, 0))
    k = r_l = R + lam
    coupons = sum(2.0 * math.exp(-k * t) for t in range(1, 6))
    exact = coupons + 100 * math.exp(-r_l * 5) + lam * rec * 100 * (1 - math.exp(-r_l * 5)) / r_l
    assert abs(value_at(30, g) - exact) < 0.02


def test_bounds_and_features():
    cb = Convertible()
    g = price_grid(cb, R, Q, VOL, power_hazard(0.05, 30, 1.2))
    s, v = g
    floor = price_grid(Convertible(ratio=1e-9, call_trigger=1e12), R, Q, VOL, power_hazard(0.05, 30, 1.2))[1]
    inside = (s > 5) & (s < 200)
    assert np.all(v[inside] >= np.maximum(floor[inside], cb.ratio * s[inside]) - 1e-9)
    assert np.all(np.diff(v[inside]) > 0)
    no_call = price_grid(Convertible(call_trigger=1e12), R, Q, VOL, power_hazard(0.05, 30, 1.2))
    put = price_grid(Convertible(puts=((3.0, 100.0),)), R, Q, VOL, power_hazard(0.05, 30, 1.2))
    assert value_at(50, no_call) > value_at(50, g) and value_at(20, put) > value_at(20, g)
    d = greeks(30, price_grid(cb, R, Q, VOL, power_hazard(0.05, 30, 0.0)))
    assert 0 < d["delta"] < cb.ratio and d["gamma"] > 0


def test_credit_link_raises_the_delta_at_low_spots():
    const = price_grid(Convertible(), R, Q, VOL, power_hazard(0.05, 30, 0.0))
    e2c = price_grid(Convertible(), R, Q, VOL, power_hazard(0.05, 30, 1.2))
    assert greeks(20, e2c)["delta"] > greeks(20, const)["delta"]
