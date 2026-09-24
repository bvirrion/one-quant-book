import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from financing_demo import (
    Book,
    annual_cost_cash,
    annual_cost_swap,
    forced_sale,
    margin_call_price,
    max_leverage,
    return_on_equity,
    spiral,
    wipeout_drop,
)


def test_leverage_identities():
    assert return_on_equity(0.10, 1, 0.04) == pytest.approx(0.10)
    assert return_on_equity(-wipeout_drop(5), 5, 0.0) == pytest.approx(-1.0)
    assert max_leverage(0.02) == pytest.approx(50)


def test_margin_call_price_restores_the_ratio():
    p = margin_call_price(100, 0.50, 0.25)
    assert (p - 50) / p == pytest.approx(0.25)


def test_forced_sale_restores_leverage():
    a, lev, x = 100.0, 5.0, 0.04
    e = a / lev - a * x
    assert (a * (1 - x) - forced_sale(a, lev, x)) / e == pytest.approx(lev)


def test_spiral_is_worse_with_more_leverage_and_converges_without_impact():
    assert spiral(8, 0.05, 0.10)[-1] > spiral(3, 0.05, 0.10)[-1]
    assert spiral(5, 0.05, 0.0)[-1] == pytest.approx(0.05)


def test_swap_costs_the_spread_on_the_equity_more_than_cash():
    b = Book(300.0, 200.0, 100.0)
    cash = annual_cost_cash(b, 0.04, 0.005, 0.003, 0.003)
    swap = annual_cost_swap(b, 0.04, 0.005, 0.003, 0.003)
    assert swap - cash == pytest.approx(b.equity * 0.005)
