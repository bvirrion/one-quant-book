import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from blockbid import Block, breakeven_discount, risk_std, simulate_unwind, unwind_days


def test_unwind_days():
    assert unwind_days(Block(2e6, 1e7, 0.02)) == pytest.approx(2.0)


def test_t_over_three_matches_simulation():
    b = Block(2e6, 1e7, 0.02)
    pnl = simulate_unwind(b, 0.0, 40_000, seed=11, steps=400)
    assert pnl.std() == pytest.approx(risk_std(b), rel=0.02)


def test_breakeven_loses_five_percent_of_the_time():
    b = Block(2e6, 1e7, 0.02)
    pnl = simulate_unwind(b, breakeven_discount(b), 40_000, seed=12, steps=400)
    assert (pnl < 0).mean() == pytest.approx(0.05, abs=0.006)


def test_discount_grows_with_size_and_vol():
    small, big = Block(1e6, 1e7, 0.02), Block(4e6, 1e7, 0.02)
    assert breakeven_discount(big) > breakeven_discount(small)
    assert breakeven_discount(Block(1e6, 1e7, 0.03)) > breakeven_discount(small)
