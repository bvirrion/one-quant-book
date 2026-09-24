import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from venue_econ import ACCESS, ICE_EXCHANGES_2025, breakeven_share, cheapest, crossover, shares, venue_profit


def test_shares_sum_to_one():
    assert sum(shares(ICE_EXCHANGES_2025).values()) == pytest.approx(1.0)


def test_ice_table_matches_the_published_total():
    assert sum(ICE_EXCHANGES_2025.values()) == 5411


def test_crossovers_are_ordered_and_consistent():
    xs = [crossover(a, b) for a, b in zip(ACCESS[:-1], ACCESS[1:], strict=True)]
    assert xs == sorted(xs)
    assert cheapest(xs[0] * 0.9).name == "broker algorithm"
    assert cheapest(xs[0] * 1.1).name == "direct market access"
    assert cheapest(xs[2] * 1.1).name == "own membership"


def test_breakeven_share_zeroes_the_profit():
    s = breakeven_share(10e9, 0.0003, 50e6, 40e6)
    assert venue_profit(s, 10e9, 0.0003, 50e6, 40e6) == pytest.approx(0.0, abs=1e-6)
