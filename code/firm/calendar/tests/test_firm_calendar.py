"""Acceptance tests of the Chapter 22 build."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_calendar import UTC, is_open, load, open_roots, utc_intervals

S = load(str(pathlib.Path(__file__).resolve().parents[4] / "data/markets-1/sessions_sample.csv"))


def at(y, m, d, hh, mm=0):
    return dt.datetime(y, m, d, hh, mm, tzinfo=UTC)


def test_daylight_saving_moves_the_european_open_in_utc():
    # Berlin is UTC+2 in September and UTC+1 in December: 02:10 local is 00:10 or 01:10 UTC
    assert is_open(S, "FESX", at(2026, 9, 16, 0, 30)) and not is_open(S, "FESX", at(2026, 12, 16, 0, 30))
    assert is_open(S, "FESX", at(2026, 12, 16, 1, 30))


def test_hong_kong_lunch_break_and_the_session_across_midnight():
    assert is_open(S, "HSI", at(2026, 9, 16, 3, 0)) and not is_open(S, "HSI", at(2026, 9, 16, 4, 30))   # 11:00 and 12:30 HKT
    assert is_open(S, "HSI", at(2026, 9, 16, 18, 0))                                                    # 02:00 HKT Thursday
    assert not is_open(S, "HSI", at(2026, 9, 16, 19, 30))                                               # 03:30 HKT


def test_week_boundaries():
    assert not is_open(S, "ES", at(2026, 9, 19, 12, 0))               # Saturday
    assert is_open(S, "ES", at(2026, 9, 20, 22, 30))                  # Sunday 17:30 Chicago
    assert not is_open(S, "ES", at(2026, 9, 18, 21, 30))              # Friday 16:30 Chicago: the week is over
    assert not is_open(S, "HSI", at(2026, 9, 19, 10, 0))              # Saturday 18:00 HKT: no Saturday evening session
    assert is_open(S, "HSI", at(2026, 9, 18, 17, 0))                  # Saturday 01:00 HKT belongs to Friday's session


def test_who_is_open():
    assert open_roots(S, at(2026, 9, 16, 1, 0)) == ["ES", "FESX"]     # 09:00 HKT: Hong Kong has not opened
    assert open_roots(S, at(2026, 9, 16, 2, 0)) == ["ES", "FESX", "HSI"]
    assert open_roots(S, at(2026, 9, 16, 21, 30)) == []               # ES break, Europe closed, Hong Kong closed


def test_utc_intervals_are_clipped_to_the_day():
    iv = utc_intervals(S, "HSI", dt.date(2026, 9, 16))
    hours = [(a.hour + a.minute / 60, (b - a).total_seconds() / 3600) for a, b in iv]
    assert hours == [(1.25, 2.75), (5.0, 3.5), (9.0, 10.0)]           # Hong Kong is UTC+8 all year
    es = utc_intervals(S, "ES", dt.date(2026, 9, 16))                 # Chicago is UTC-5 in September
    assert [(a.hour, b.hour if b.day == a.day else 24) for a, b in es] == [(0, 21), (22, 24)]
