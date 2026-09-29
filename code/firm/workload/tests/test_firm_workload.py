"""Acceptance tests for firm.workload."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_workload as fw  # noqa: E402

MON = dt.date(2026, 9, 21)          # a Monday; UK, EU and US on summer time


def s(root, tz, o, c, a, b):
    return fw.cal.Session(root, tz, dt.time.fromisoformat(o), dt.time.fromisoformat(c), a, b)


def test_utc_week_and_gaps():
    ses = [s("X", "UTC", "00:00", "12:00", 0, 4)]
    m = fw.week_matrix(ses, ["X"], MON)
    assert fw.open_hours(m) == 60.0
    spans = fw.closed_spans(m)
    assert spans[0] == (12 * 60, 24 * 60) and spans[-1][1] == fw.WEEK


def test_time_zone_shift():
    ses = [s("L", "Europe/London", "09:00", "10:00", 0, 0)]
    m = fw.week_matrix(ses, ["L"], MON)
    assert m[0].argmax() == 8 * 60 and fw.open_hours(m) == 1.0      # 09:00 BST is 08:00 UTC


def test_round_the_clock_and_headcount():
    ses = [s("C", "UTC", "00:00", "00:00", 0, 6)]                     # close <= open: through midnight, every day
    m = fw.week_matrix(ses, ["C"], MON)
    assert fw.open_hours(m) == 168.0 and fw.closed_spans(m) == []
    assert fw.continuous_shifts(9, 1) == 3 and fw.continuous_shifts(12, 0) == 2
    assert fw.headcount(48.0, 1, 48.0, 0.0) == 1.0
    assert fw.headcount(96.0, 1, 48.0, 4.0) == pytest.approx(2 * 52 / 48)
    assert fw.oncall_nights(30.0, 8) == 3.75


def test_markets_and_shifts():
    ses = [s("A", "UTC", "08:00", "16:00", 0, 4), s("B", "UTC", "14:00", "20:00", 0, 4)]
    mk = fw.to_markets(ses, ["A", "B"], MON)
    assert mk[0].hours[0] == [(480, 960)] and mk[0].hours[5] == []
    tab = fw.shift_table(mk, 9, 1)
    assert [(a, b) for a, b, _ in tab[0]] == [(480, 1020), (960, 60)] and tab[6] == []
    assert max(t for _, _, t in tab[0]) == 2


def test_inputs():
    i = fw.Input("limit", 48, "h", "documented", "Directive 2003/88/EC art. 6")
    assert fw.by_status([i])["documented"] == ["limit"]
    with pytest.raises(ValueError):
        fw.Input("x", 1, "h", "rumour")
