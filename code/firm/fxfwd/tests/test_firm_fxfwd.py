"""Acceptance tests of the Book 2, Chapter 16 build (forwards, FX swaps, basis)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fxfwd import basis_on_quote, forward, fx_swap_legs, hedged_yield, implied_rate_quote, points


def test_cip_without_basis():
    f = forward(150.0, 0.01, 0.04, 90)
    assert math.isclose(f, 150.0 * (1 + 0.01 * 0.25) / (1 + 0.04 * 0.25))
    assert f < 150.0                                          # the higher-yielding base trades at a discount
    assert math.isclose(implied_rate_quote(150.0, f, 0.04, 90), 0.01)


def test_basis_round_trip():
    f = forward(150.0, 0.01, 0.04, 90, basis_quote=-0.0025)
    assert math.isclose(basis_on_quote(150.0, f, 0.01, 0.04, 90), -0.0025)
    assert f < forward(150.0, 0.01, 0.04, 90)                 # negative basis: dollars dearer forward


def test_points_and_legs():
    assert math.isclose(points(149.0, 150.0, 0.01), -100.0)
    legs = fx_swap_legs(10e6, 150.0, 149.0)
    assert legs["near_base"] + legs["far_base"] == 0 and math.isclose(legs["near_quote"] + legs["far_quote"], -10e6)


def test_hedged_yield():
    assert math.isclose(hedged_yield(0.0475, 0.0368, 0.00977, 0.0), 0.0475 - (0.0368 - 0.00977))
    assert hedged_yield(0.0475, 0.0368, 0.00977, -0.0025) < hedged_yield(0.0475, 0.0368, 0.00977, 0.0)
