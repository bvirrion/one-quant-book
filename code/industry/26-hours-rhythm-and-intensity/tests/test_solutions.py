"""Numbers gate: every numerical answer printed in Book 17, chapter 26 (text and solutions)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_hours as a  # noqa: E402

fw = a.fw


def r(x, d=2):
    return round(float(x), d)


def test_coverage():
    c = a.coverage()
    assert c["futures_open_h"] == 120.0 and c["futures_closed"] == [(118 * 60, 166 * 60)]
    assert c["all_open_h"] == 166.0 and c["all_closed"] == [(127 * 60, 129 * 60)]
    h = c["per_root_h"]
    assert (h["ZN"], h["BRN"], r(h["FESX"], 1), r(h["HSI"], 1), h["BTC"]) == (115.0, 112.0, 99.2, 81.2, 164.0)


def test_staffing():
    s = a.staffing()
    assert (s["futures_shift_hours"], s["continuous_shift_hours"]) == (144.0, 189.0)
    assert (r(s["futures_people"], 1), r(s["continuous_people"]), r(s["continuous_people_no_leave"], 1)) == (
        6.5, 8.53, 7.9)
    assert (math.ceil(s["futures_people"]), math.ceil(s["continuous_people"])) == (7, 9)
    assert r(fw.headcount(144, 2, leave_weeks=0.0), 1) == 6.0 and r(s["oncall"], 1) == 3.8
    assert math.ceil(24 / 7.5) == 4 and r(a.NIGHTS_PER_MONTH / 12, 1) == 2.5 and r(a.NIGHTS_PER_MONTH, 2) == 30.44
    assert r(fw.headcount(189, 3), 1) == 12.8
    tab, _ = a.shifts_futures()
    assert [len(tab[d]) for d in range(7)] == [3, 3, 3, 3, 3, 0, 1]


def test_march_week():
    ses = a.sessions()
    mon = dt.date(2026, 3, 23)
    f = fw.week_matrix(ses, list(a.FUTURES), mon)
    b = fw.week_matrix(ses, list(a.FUTURES + a.CRYPTO), mon)
    assert fw.open_hours(f) == 121.0 and fw.closed_spans(f) == [(119 * 60, 166 * 60)] and fw.open_hours(b) == 166.0


def test_small_runs():
    assert fw.by_status(a.INPUTS)["anecdote"] == [] and len(fw.by_status(a.INPUTS)["documented"]) == 3
