import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from zero_day import atm_gamma_by_minutes, simulate_with_hedgers, straddle_price


def test_gamma_explodes_into_expiry():
    g = atm_gamma_by_minutes(100.0, 0.16, [390 * 21, 390, 60, 5])
    assert g[0] < g[1] < g[2] < g[3] and g[1] / g[0] == pytest.approx(21**0.5, rel=0.01)


def test_one_day_straddle_costs_about_point_eight_of_a_daily_sigma():
    p = straddle_price(100.0, 0.16, 1 / 252)
    assert p == pytest.approx(0.8 * 100 * 0.16 / 252**0.5, rel=0.01)


def test_long_gamma_hedgers_damp_and_short_gamma_hedgers_amplify():
    damp = simulate_with_hedgers(3000, 78, 0.001, -0.3, 1)
    amp = simulate_with_hedgers(3000, 78, 0.001, +0.3, 1)
    assert damp < 0.85 and amp > 1.3 and simulate_with_hedgers(3000, 78, 0.001, 0.0, 1) == pytest.approx(1.0)
