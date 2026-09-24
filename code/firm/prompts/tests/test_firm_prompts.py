"""Acceptance tests of the Book 3, Chapter 8 build (prompt dates)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_prompts import add_months, lme_roll, prompt_dates, third_wednesday, three_month_date, variation_margin


def test_calendar_helpers():
    assert add_months(dt.date(2026, 11, 30), 3) == dt.date(2027, 2, 28)
    assert lme_roll(dt.date(2026, 10, 17)) == dt.date(2026, 10, 16)                # Saturday: back to Friday
    assert lme_roll(dt.date(2026, 10, 18)) == dt.date(2026, 10, 19)                # Sunday: forward to Monday
    assert lme_roll(dt.date(2026, 10, 17), frozenset({dt.date(2026, 10, 16)})) == dt.date(2026, 10, 19)
    assert three_month_date(dt.date(2026, 11, 30)) == dt.date(2027, 2, 26)         # not into the fourth month
    assert third_wednesday(2026, 12) == dt.date(2026, 12, 16)


def test_prompt_structure():
    p = prompt_dates(dt.date(2026, 9, 24))
    assert p["daily"][0] == dt.date(2026, 9, 25) and p["cash"][0] == dt.date(2026, 9, 28)
    assert p["three_month"][0] == dt.date(2026, 12, 24) and p["daily"][-1] == dt.date(2026, 12, 24)
    assert all(d.weekday() == 2 for d in p["weekly"]) and p["weekly"][-1] <= dt.date(2027, 3, 31)
    assert all(d.weekday() == 2 and 15 <= d.day <= 21 for d in p["monthly"])
    assert p["monthly"][0] > p["weekly"][-1]


def test_short_pays_when_price_rises():
    assert variation_margin(-1000, 48_078, 101_365) == -53_287_000
