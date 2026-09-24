"""Numbers in the solutions of Book 3, Chapter 18."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_liq as m
from firm_liquidation import bankruptcy_price_linear, liq_price_inverse, liq_price_linear


def test_exercises():
    assert round(liq_price_linear(1, 100, 5, 0.005), 2) == 95.48 and bankruptcy_price_linear(1, 100, 5) == 95
    assert round(liq_price_linear(1, 100, 20, 0.005), 2) == 80.40
    assert round(liq_price_inverse(100, 100, 0.2, 0.005), 2) == 83.75
    assert round(0.01 / (1 - 0.8), 4) == 0.05
    assert round(100 * m.critical_shock(m.population(max_leverage=20)), 2) == 1.65
    assert round(100 * m.critical_shock(m.population(max_leverage=10)), 2) == 5.37


def test_problem():
    assert round(liq_price_linear(250, 100, 1_000, 0.005), 2) == 96.48
    assert bankruptcy_price_linear(250, 100, 1_000) == 96
    assert 250 * (96 - 95.5) == 125 and round(250 * (96.8 - 96)) == 200
    pop = m.population()
    assert round(100 * m.critical_shock(pop), 2) == 1.11
    r = m.cascade(pop, 0.05)
    assert round(r.price, 2) == 83.83 and round(r.deficit / 1e6, 2) == 3.21
    assert round(-(2e6 + r.fund_change) / 1e6, 2) == 1.21
