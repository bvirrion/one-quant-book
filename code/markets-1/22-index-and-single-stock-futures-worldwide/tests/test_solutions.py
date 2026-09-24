"""Numbers gate: every numerical answer printed in the Chapter 22 text and solutions."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/calendar"))
from div_implied import REGIONS_2025, implied_dividends, implied_growth, trf_pnl_from_spread
from firm_calendar import UTC, load, open_roots

S = load(str(pathlib.Path(__file__).resolve().parents[4] / "data/markets-1/sessions_sample.csv"))
STRIP = [168.0, 171.5, 169.0, 166.0, 164.5, 163.5]


def test_text():
    total = sum(v for _, v in REGIONS_2025)
    assert total == pytest.approx(119.29) and 88.65 + 30.64 == pytest.approx(119.29)
    shares = [round(v / total * 100) for _, v in REGIONS_2025]
    assert shares[:2] == [63, 21] and round(4.38 / total * 100, 1) == 3.7 and round(94.79 / total * 100) == 79
    g = implied_growth(STRIP)
    assert round(g[0] * 100, 1) == 2.1 and all(x < 0 for x in g[1:])
    assert round(((163.5 / 168.0) ** 0.2 - 1) * 100, 1) == -0.5


def empty_hours(day):
    return [h for h in range(24) if not open_roots(S, dt.datetime(day.year, day.month, day.day, h, 30, tzinfo=UTC))]


def all_three_minutes(day):
    start = dt.datetime(day.year, day.month, day.day, tzinfo=UTC)
    return sum(1 for m in range(1440) if len(open_roots(S, start + dt.timedelta(minutes=m))) == 3)


def test_exercises():
    assert (6000 * 50, 5400 * 10, 26000 * 50) == (300_000, 54_000, 1_300_000)
    assert implied_dividends(5400.0, 5412.0, 0.025, 0.25) == pytest.approx(21.75)
    assert (158.2 - 171.5) * 100 * 50 == pytest.approx(-66_500)
    assert [round(x * 100, 2) for x in implied_growth(STRIP)] == [2.08, -1.46, -1.78, -0.90, -0.61]
    assert all_three_minutes(dt.date(2026, 9, 16)) == 16.25 * 60
    assert empty_hours(dt.date(2026, 9, 16)) == [21] and empty_hours(dt.date(2026, 12, 16)) == [22]
    assert trf_pnl_from_spread(5400.0, 10.0, 200, 15.0, 2.0) == pytest.approx(32_400)


def test_problem():
    assert round(171.5 / 5400 * 100, 2) == 3.18
    trend = 168.0 * 1.04**5
    assert round(trend, 1) == 204.4 and round((163.5 / trend - 1) * 100) == -20
    assert 200 * 163.5 * 100 == 3_270_000 and round((trend - 163.5) * 20_000, -3) == 818_000
    assert 168.0 * 0.7 == pytest.approx(117.6) and (117.6 - 163.5) * 20_000 == pytest.approx(-918_000)
    assert (110 - 163.5) * 20_000 == -1_070_000
    assert 0.2 * 171.5 == pytest.approx(34.3) and 500 * 10 * 34.3 == pytest.approx(171_500)
    assert 171_500 / (100 * 34.3) == pytest.approx(50)
