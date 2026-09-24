"""Acceptance tests of the Book 2, Chapter 28 build (access-cost model)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_clearcost import Route, annual_cost, breakeven, cheapest

RENT = Route("rent", fixed=0.5e6, repo_bp=8.0, swap_bp=0.5)
BUY = Route("buy", fixed=8e6, repo_bp=1.0, swap_bp=0.2, fund_share=0.002)


def test_cost_is_linear_plus_fixed():
    c1 = annual_cost(RENT, 1e9, 2e9, 0.005)
    c2 = annual_cost(RENT, 2e9, 4e9, 0.005)
    assert abs((c2 - RENT.fixed) - 2 * (c1 - RENT.fixed)) < 1e-6
    assert annual_cost(RENT, 0, 0, 0.005) == RENT.fixed


def test_breakeven_equalises_costs():
    b = breakeven(RENT, BUY, 2.0, 0.005)
    assert b is not None and abs(annual_cost(RENT, b, 2 * b, 0.005) - annual_cost(BUY, b, 2 * b, 0.005)) < 1e-3 * annual_cost(RENT, b, 2 * b, 0.005) * 1e-6
    assert cheapest([RENT, BUY], 0.5 * b, b, 0.005).name == "rent"
    assert cheapest([RENT, BUY], 2 * b, 4 * b, 0.005).name == "buy"


def test_no_breakeven_when_dominated():
    worse = Route("worse", fixed=9e6, repo_bp=9.0, swap_bp=1.0)
    assert breakeven(RENT, worse, 2.0, 0.005) is None
