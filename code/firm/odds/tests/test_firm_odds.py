"""Acceptance tests of the Book 3, Chapter 27 build (odds conversion and hedging)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_odds import additive, hedge_equal, kelly, multiplicative, overround, power, shin

BOOK = [1.5, 4.0, 7.0]                       # a three-way market with an overround


def test_overround_and_methods_sum_to_one():
    assert round(overround(BOOK), 6) == round(1 / 1.5 + 1 / 4 + 1 / 7 - 1, 6)
    for f in (multiplicative, additive, power):
        assert abs(sum(f(BOOK)) - 1) < 1e-9
    p, z = shin(BOOK)
    assert abs(sum(p) - 1) < 1e-9 and 0 < z < 0.2


def test_longshot_shaded_most_by_power_and_shin():
    m, pw, (s, _) = multiplicative(BOOK), power(BOOK), shin(BOOK)
    assert pw[2] < m[2] and s[2] < m[2]           # longshot gets less probability than proportional removal
    assert pw[0] > m[0] and s[0] > m[0]


def test_kelly_and_hedge():
    assert kelly(0.5, 2.0) == 0.0 and round(kelly(0.6, 2.0), 6) == 0.2
    lay, win, lose = hedge_equal(100, 3.0, 2.5)
    assert lay == 120 and round(win, 6) == round(lose, 6) == 20
