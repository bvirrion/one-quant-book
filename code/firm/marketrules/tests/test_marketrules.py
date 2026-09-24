"""Acceptance tests of the Chapter 12 build."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_marketrules import MarketRules, Order, RuleBook

D = dt.date
BOOK = RuleBook([
    MarketRules("LIMITLAND", D(2020, 1, 1), 100, 1, 0.10, 0.10, False, False, 1, 0.0010, 0.0010),
    MarketRules("TAXLAND", D(2020, 1, 1), 1, 1, 0.0, 0.0, True, True, 1, 0.0, 0.0002),
    MarketRules("TAXLAND", D(2026, 4, 1), 1, 1, 0.0, 0.0, True, True, 1, 0.0, 0.0005),
])


def test_lot_tick_and_limit_band():
    assert BOOK.limit_band("LIMITLAND", D(2026, 9, 1), 2000) == (1800, 2200)
    assert BOOK.limit_band("LIMITLAND", D(2026, 9, 1), 2005) == (1805, 2205)      # 1804.5 -> 1805, 2205.5 -> 2205
    ok = BOOK.validate("LIMITLAND", D(2026, 9, 1), Order(+1, 300, 2200), 2000, 0)
    assert ok == []
    bad = BOOK.validate("LIMITLAND", D(2026, 9, 1), Order(+1, 250, 2201), 2000, 0)
    assert "quantity is not a multiple of the lot" in bad and "price outside the daily limit" in bad


def test_same_day_sell_rejection():
    msg = BOOK.validate("LIMITLAND", D(2026, 9, 1), Order(-1, 500, 2100), 2000, opening_position=300)
    assert msg == ["sale exceeds the position held at the start of the day"]
    assert BOOK.validate("LIMITLAND", D(2026, 9, 1), Order(-1, 300, 2100), 2000, opening_position=300) == []


def test_rules_are_versioned_by_date():
    assert BOOK.tax("TAXLAND", D(2026, 3, 31), -1, 1e6) == pytest.approx(200)
    assert BOOK.tax("TAXLAND", D(2026, 4, 1), -1, 1e6) == pytest.approx(500)
    with pytest.raises(KeyError):
        BOOK.rules("TAXLAND", D(2019, 12, 31))
