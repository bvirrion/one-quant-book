"""Acceptance tests of the Book 3, Chapter 11 build (degree days and freight)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_degreeday import burn, c10_to_f, cdd, detrend, ffa_settlement, hdd, put_payoff, swap_payoff


def test_degree_days():
    assert math.isclose(c10_to_f(0), 32.0) and math.isclose(c10_to_f(100), 50.0)
    assert hdd(40.0) == 25.0 and hdd(70.0) == 0.0 and cdd(80.0) == 15.0


def test_payoffs_and_burn():
    assert swap_payoff(5100, 5000, 20.0) == 2000.0
    assert put_payoff(4500, 5000, 20.0) == 10_000.0 and put_payoff(4500, 5000, 20.0, cap=5000) == 5000
    b = burn([4000.0, 5000.0, 6000.0, 5500.0], lambda x: put_payoff(x, 5000, 1.0))
    assert b["mean"] == 250.0 and b["freq"] == 0.25 and b["max"] == 1000.0


def test_detrend_removes_slope():
    years = [2000.0, 2001.0, 2002.0, 2003.0]
    d = detrend([10.0, 9.0, 8.0, 7.0], years, 2004.0)
    assert all(math.isclose(v, 6.0) for v in d)


def test_ffa():
    assert math.isclose(ffa_settlement([20_000, 22_000, 24_000], 21_000, 30), 30_000)
