"""Acceptance tests of the Book 2, Chapter 2 build: the worked examples of 31 CFR 356, App. B."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mmyield import (
    discount_from_price,
    implied_turn,
    investment_rate,
    money_market_yield,
    price_from_discount,
    term_proceeds,
    year_days,
)


def test_cfr_price_example():
    assert price_from_discount(0.07610, 90) == 98.097500


def test_cfr_discount_example():
    assert round(discount_from_price(95.934567, 182) * 100, 3) == 8.042


def test_cfr_short_investment_rate_example():
    p = price_from_discount(0.07930, 20)
    assert p == pytest.approx(99.559444, abs=1e-6)
    assert round(investment_rate(p, 20, 365) * 100, 3) == 8.076


def test_cfr_long_investment_rate_example():
    assert round(investment_rate(92.265000, 364, 365) * 100, 3) == 8.237


def test_leap_year_rule():
    assert year_days(dt.date(2019, 2, 28)) == 365
    assert year_days(dt.date(2019, 3, 1)) == 366


def test_ordering_discount_mmy_bey():
    p = price_from_discount(0.038, 91)
    d, m, i = 0.038, money_market_yield(p, 91), investment_rate(p, 91, 365)
    assert d < m < i
    assert i == pytest.approx(m * 365 / 360)


def test_long_formula_is_continuous_at_half_year():
    p = price_from_discount(0.04, 182)
    short = (100 - p) / p * 365 / 182
    assert investment_rate(p, 182, 365) == pytest.approx(short)
    assert investment_rate(price_from_discount(0.04, 183), 183, 365) == pytest.approx(short, abs=2e-4)


def test_term_and_turn():
    assert term_proceeds(1e6, 0.04, 90) == pytest.approx(1_010_000)
    r = 0.039
    week = ((1 + r / 360) ** 7 - 1) * 360 / 7            # a flat rate compounded over seven days
    four = ((1 + r / 360) ** 4 - 1) * 360 / 4            # the same over the four turn days
    assert implied_turn(week, 7, r, 3, 4) == pytest.approx(four, rel=1e-12)
    assert implied_turn(week + 0.001, 7, r, 3, 4) > four
