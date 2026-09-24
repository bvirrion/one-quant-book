"""Acceptance tests of the Book 2, Chapter 21 build (spread measures)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_spreads import (
    asset_swap_spread,
    g_spread,
    i_spread,
    interp,
    price_from_yield,
    price_on_zero,
    spread_price_impact,
    yield_from_price,
    z_spread,
)

FLAT = [(0.5, 0.04), (30.0, 0.04)]


def test_interp_and_yield_round_trip():
    assert math.isclose(interp([(1, 0.01), (3, 0.03)], 2), 0.02) and interp([(1, 0.01), (3, 0.03)], 5) == 0.03
    p = price_from_yield(5.0, 10, 0.06)
    assert math.isclose(yield_from_price(5.0, 10, p), 0.06, abs_tol=1e-10)
    assert math.isclose(price_from_yield(6.0, 10, 0.06), 100.0)


def test_spreads_on_flat_curves():
    assert math.isclose(g_spread(0.055, 7, FLAT), 0.015) and math.isclose(i_spread(0.055, 7, FLAT), 0.015)
    p = price_on_zero(5.0, 10, FLAT, 0.01)
    assert math.isclose(z_spread(5.0, 10, p, FLAT), 0.01, abs_tol=1e-10)


def test_asset_swap_spread_zero_when_priced_on_the_curve():
    p = price_on_zero(5.0, 10, FLAT)
    assert abs(asset_swap_spread(5.0, 10, p, FLAT)) < 1e-12
    assert asset_swap_spread(5.0, 10, p - 5, FLAT) > 0


def test_impact():
    assert math.isclose(spread_price_impact(6.0, 0.01), -6.0)
