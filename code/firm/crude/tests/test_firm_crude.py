"""Acceptance tests of the Book 3, Chapter 2 build (crude toolkit)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_crude import (
    api_gravity,
    basket_benchmark,
    calendar_month_average,
    cl_last_trading_day,
    implied_storage_cost,
    quality_adjusted,
    specific_gravity,
    storage_floor,
)


def test_api_round_trip():
    assert math.isclose(api_gravity(1.0), 10.0)            # water is 10 degrees API
    assert math.isclose(specific_gravity(api_gravity(0.85)), 0.85)


def test_quality_escalators():
    assert math.isclose(quality_adjusted(80.0, 40.0, 0.3, 38.0, 0.4, 0.05, 0.10), 80.0 + 0.10 + 0.10)


def test_most_competitive_grade():
    g, p = basket_benchmark({"A": 80.0, "B": 80.5, "C": 79.9}, {"B": 0.8})
    assert g == "B" and math.isclose(p, 79.7)


def test_cl_last_trading_days():
    assert cl_last_trading_day(2020, 5) == dt.date(2020, 4, 21)     # 25 April 2020 was a Saturday
    assert cl_last_trading_day(2024, 1) == dt.date(2023, 12, 20)    # without the holiday calendar
    assert cl_last_trading_day(2024, 1, frozenset({dt.date(2023, 12, 25)})) == dt.date(2023, 12, 19)
    assert cl_last_trading_day(2026, 11) == dt.date(2026, 10, 20)   # 25 Oct 2026 is a Sunday


def test_cma_and_storage():
    s = {dt.date(2026, 3, 2): 90.0, dt.date(2026, 3, 3): 92.0, dt.date(2026, 4, 1): 50.0}
    assert calendar_month_average(s, 2026, 3) == 91.0
    assert math.isclose(storage_floor(20.0, 0.5, 1.0), 19.5)
    assert math.isclose(implied_storage_cost(-37.63, 20.43), 58.06)
