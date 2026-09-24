"""Acceptance tests of firm.impulse."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_impulse import (
    band_cost,
    optimal_band,
    optimal_fixed_band,
    optimal_proportional_band,
    reflect_cost,
    simulate_band,
    stop_threshold_drift,
)


def test_renewal_formula_against_simulation():
    sim = simulate_band(3.0, 1.0, 1.0, 1.0, 2.0, 0.5, T=20_000.0, dt=1e-3, seed=1)
    assert abs(sim["avg_cost"] - band_cost(3.0, 1.0, 1.0, 1.0, 2.0, 0.5)) / band_cost(3.0, 1.0, 1.0, 1.0, 2.0, 0.5) < 0.03


def test_power_laws():
    b1, b16 = optimal_fixed_band(1.0, 1.0, 1.0)[0], optimal_fixed_band(1.0, 1.0, 16.0)[0]
    assert abs(b16 / b1 - 2.0) < 1e-12
    p1, p8 = optimal_proportional_band(1.0, 1.0, 1.0)[0], optimal_proportional_band(1.0, 1.0, 8.0)[0]
    assert abs(p8 / p1 - 2.0) < 1e-12


def test_numerical_optimum_reduces_to_closed_forms():
    a, b, c = optimal_band(20.0, 0.5, 300.0, 0.0)
    assert a < 1e-3 * b and abs(b - optimal_fixed_band(20.0, 0.5, 300.0)[0]) < 0.05
    a2, b2, c2 = optimal_band(20.0, 0.5, 1e-6, 25.0)
    bp, cp = optimal_proportional_band(20.0, 0.5, 25.0)
    assert abs(b2 - a2) < 0.2 and abs(c2 - cp) < 1.0 and abs(reflect_cost(bp, 20.0, 0.5, 25.0) - cp) < 1e-9


def test_smooth_pasting():
    b, th = stop_threshold_drift(0.5, 2.0, 0.02, 5.0)
    value = lambda x: (b - 5.0) * math.exp(th * (x - b))  # noqa: E731
    h = 1e-6
    assert abs(value(b) - (b - 5.0)) < 1e-12 and abs((value(b) - value(b - h)) / h - 1.0) < 1e-5
