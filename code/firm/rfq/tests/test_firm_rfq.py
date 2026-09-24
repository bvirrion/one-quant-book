"""Acceptance tests of the Book 2, Chapter 22 build (RFQ auctions, composites)."""
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_rfq import best_n, composite, expected_cost, expected_max_normal, simulate_rfq


def test_expected_max():
    assert expected_max_normal(1) == 0.0
    assert math.isclose(expected_max_normal(2), 1 / math.sqrt(math.pi), abs_tol=0.01)
    assert expected_max_normal(5) > expected_max_normal(3)


def test_leakage_limits_competition():
    assert best_n(10, 5, 0.0) == 12 and best_n(10, 5, 100.0) == 1
    assert expected_cost(3, 10, 5, 1) < expected_cost(1, 10, 5, 1)


def test_simulation_matches_formula():
    sims = simulate_rfq(4, 10, 5, trials=40_000)
    assert math.isclose(statistics.fmean(sims), 10 - 5 * expected_max_normal(4), abs_tol=0.1)


def test_composite_drops_outliers():
    q = [(100.00, 5), (100.02, 30), (99.98, 60), (101.50, 1)]
    c = composite(q)
    assert 99.98 <= c <= 100.02
