"""Numbers gate: every numerical answer printed in Book 2, Chapter 28 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from access_cost_demo import problem

P = problem()


def test_text():
    assert (P["unit_rent"], P["unit_buy"], P["unit_bilateral"]) == (11.5, 5.9, 18.5)
    assert (round(P["mid_rent"], 2), round(P["mid_buy"], 2), round(P["mid_bilateral"], 2)) == (6.25, 10.95, 9.45)
    assert P["mid_best"] == "rent"
    assert round(P["be_bilateral_rent"], 2) == 0.43 and round(P["be_rent_buy"], 1) == 13.4
    assert (round(P["be_spread_5"], 1), round(P["be_spread_12"], 1)) == (28.8, 7.8)


def test_exercises():
    assert round(7.5e6 / 0.00056 / 1e9, 1) == 13.4
    assert round(P["be_no_swaps"], 1) == 15.0 and round(P["be_fixed_12"], 1) == 20.5


def test_problem():
    assert round(P["cost_at_be"], 1) == 15.9 and round(P["saving_20"], 1) == 3.7
