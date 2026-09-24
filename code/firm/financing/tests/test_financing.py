"""Acceptance tests of the Chapter 6 build."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_financing import FinancingTerms, accrue

TERMS = FinancingTerms(0.005, 0.003)
POS = {"AAA": 3_000_000, "BBB": -2_000_000}
PX = {"AAA": 100.0, "BBB": 100.0}


def test_reproduces_the_tutorial_over_a_360_day_year():
    day = accrue(dt.date(2026, 9, 15), POS, PX, 100e6, 0.04, TERMS, {"BBB": 0.003})   # a Tuesday
    assert day.total * 360 == pytest.approx(-2.2e6)


def test_friday_accrues_three_days():
    tue = accrue(dt.date(2026, 9, 15), POS, PX, 100e6, 0.04, TERMS, {"BBB": 0.003})
    fri = accrue(dt.date(2026, 9, 18), POS, PX, 100e6, 0.04, TERMS, {"BBB": 0.003})
    assert fri.total == pytest.approx(3 * tue.total)


def test_missing_borrow_fee_is_an_error():
    with pytest.raises(KeyError):
        accrue(dt.date(2026, 9, 15), POS, PX, 100e6, 0.04, TERMS, {})
