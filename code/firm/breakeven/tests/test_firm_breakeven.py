"""Acceptance tests of the Book 2, Chapter 11 build (index ratios, breakevens, linker carry)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_breakeven import (
    breakeven,
    forward_index,
    index_ratio,
    linker_carry,
    month_shift,
    monthly_accrual,
    ref_index,
    seasonal_factors,
    zc_swap_payment,
)

CPI_1996 = {(1996, 1): 154.40, (1996, 2): 154.90}


def test_regulation_example():
    # 31 CFR 356 Appendix B: Ref CPI 15 April 1996 = 154.63333; ratio 16 April over 15 April = 1.00011
    assert ref_index(dt.date(1996, 4, 15), CPI_1996) == 154.63333
    assert ref_index(dt.date(1996, 4, 16), CPI_1996) == 154.65
    assert index_ratio(dt.date(1996, 4, 16), dt.date(1996, 4, 15), CPI_1996) == 1.00011


def test_first_of_month_is_the_lagged_index():
    assert ref_index(dt.date(1996, 4, 1), CPI_1996) == 154.40
    assert month_shift(2022, 1, -3) == (2021, 10) and month_shift(2021, 12, 1) == (2022, 1)
    assert math.isclose(monthly_accrual(1996, 4, CPI_1996), 154.90 / 154.40 - 1)


def test_breakeven_and_swap():
    assert math.isclose(breakeven(0.04, 0.015), 1.04 / 1.015 - 1)
    assert breakeven(0.03, 0.03) == 0.0
    f = forward_index(300.0, 0.025, 5)
    assert math.isclose(zc_swap_payment(1e8, 300.0, f, 0.025, 5), 0.0, abs_tol=1e-6)
    assert zc_swap_payment(1e8, 300.0, f * 1.01, 0.025, 5) > 0


def test_seasonal_factors_sum_to_zero():
    idx = {}
    level = 100.0
    for y in (2020, 2021, 2022):
        for m in range(1, 13):
            level *= 1.002 + (0.003 if m in (1, 2, 3) else -0.001)
            idx[(y, m)] = level
    f = seasonal_factors(idx)
    assert math.isclose(sum(f.values()), 0.0, abs_tol=1e-9)
    assert f[1] > 0 > f[12]


def test_carry_signs():
    assert math.isclose(linker_carry(1e8, 0.01, 0.0, 0.0, 30), 1e6)
    assert math.isclose(linker_carry(1e8, 0.0, 0.0, 0.036, 30), -3e5)
