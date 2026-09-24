"""Acceptance tests of the Book 2, Chapter 8 build (policy-path extraction)."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_meetings import MonthContract, convexity_adjustment, move_probability, policy_path, rate_after, strip_rate


def test_month_without_meeting_is_its_average():
    c = MonthContract(2026, 11, 96.10)
    assert rate_after(c, 3.0) == pytest.approx(3.90)


def test_known_path_is_recovered():
    before, after = 3.87, 4.12
    m = dt.date(2026, 12, 9)
    avg = (9 * before + 22 * after) / 31
    c = MonthContract(2026, 12, 100 - avg, m)
    assert rate_after(c, before) == pytest.approx(after)
    assert move_probability(after, before) == pytest.approx(1.0)


def test_turn_is_removed_before_solving():
    before, after, turn = 3.87, 3.87, 10.0
    avg = (9 * before + 21 * after + (after + turn / 100)) / 31
    c = MonthContract(2026, 12, 100 - avg, dt.date(2026, 12, 9), turn_days=1, turn_bp=turn)
    assert rate_after(c, before) == pytest.approx(after)


def test_chaining():
    cs = [MonthContract(2026, 11, 96.0), MonthContract(2026, 12, 100 - (9 * 4.0 + 22 * 4.25) / 31, dt.date(2026, 12, 9))]
    path = policy_path(cs, 3.9)
    assert path[0][1] == pytest.approx(4.0) and path[1][1] == pytest.approx(4.25)


def test_strip_and_convexity():
    assert strip_rate([4.0, 4.0], [0.25, 0.25]) == pytest.approx(4.0 + 4.0 * 4.0 / 100 * 0.25 / 2)
    assert convexity_adjustment(0.01, 5.0, 5.25) == pytest.approx(0.0013125)
