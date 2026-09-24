"""Acceptance tests of the Book 2, Chapter 29 build (sizing)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_sizing import (
    drawdown_probability,
    fraction_for_drawdown,
    growth,
    growth_uncertain,
    kelly_fraction,
    shrinkage,
    simulate,
)


def test_kelly_maximises_growth():
    f = kelly_fraction(0.6)
    assert abs(f - 0.2) < 1e-12
    assert growth(f, 0.6) > max(growth(f - 0.01, 0.6), growth(f + 0.01, 0.6))
    assert kelly_fraction(0.45) == 0.0 and growth(1.0, 0.6) == -math.inf


def test_overbetting_twice_kelly_has_zero_growth_approximately():
    assert abs(growth(0.4, 0.6)) < 0.01


def test_drawdown_formula_and_inverse():
    assert abs(drawdown_probability(1.0, 0.5) - 0.5) < 1e-12
    c = fraction_for_drawdown(0.5, 0.1)
    assert abs(drawdown_probability(c, 0.5) - 0.1) < 1e-12


def test_simulated_drawdowns_match_theory_roughly():
    for c in (0.5, 1.0):
        sims = simulate(0.1 * c, 0.55, n=4000, paths=400, seed=3)
        freq = sum(1 for _, low, _ in sims if low <= 0.5) / len(sims)
        assert abs(freq - drawdown_probability(c, 0.5)) < 0.06


def test_shrinkage_maximises_expected_growth():
    mu, s, n = 0.1, 1.0, 200
    c = shrinkage(n, mu / s)
    assert growth_uncertain(c, mu, s, n) > max(growth_uncertain(c - 0.05, mu, s, n), growth_uncertain(c + 0.05, mu, s, n))
