"""firm.workload -- how many people a desk's hours need (build of One Quant Book 17, chapter 26).

A desk's hours are set by the markets it trades. Sessions come from firm.calendar (exchange local time, daylight
saving through the time-zone database) and are laid on one UTC week; the minutes with something open are the desk's
coverage requirement. Shifts are planned with firm.marketmap's planner; headcount follows from the staffed hours, the
people needed on each shift and a working-time limit, allowing for leave; on-call load is nights divided by the rota.
Every input carries a status saying whether it is documented, reported by the press, anecdote or an illustrative
choice, so that a result can say what it rests on.

API (stable):
    Input(name, value, unit, status, source) ; STATUSES ; by_status(inputs) -> {status: [names]}
    week_matrix(sessions, roots, monday) -> (len(roots), 7 * 1440) bool array, UTC minutes from monday 00:00 UTC
    open_hours(matrix) -> hours of the week with at least one market open ; closed_spans(matrix) -> [(start, end)] min
    to_markets(sessions, roots, monday) -> [firm.marketmap.Market] with each root's UTC intervals by weekday
    shift_table(markets, length_h, overlap_h) -> {weekday: [(start_min, end_min, open_markets_max)]}
    continuous_shifts(length_h, overlap_h) -> shifts a day for round-the-clock cover
    headcount(staffed_hours_week, per_shift, max_week_h=48, leave_weeks=4, weeks=52) -> people (not rounded)
    oncall_nights(nights_per_month, rota) -> nights per person per month
"""
import datetime as dt
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIRM / "calendar"))
sys.path.insert(0, str(FIRM / "marketmap"))
import firm_calendar as cal  # noqa: E402
import firm_marketmap as mm  # noqa: E402

DAY = 24 * 60
WEEK = 7 * DAY
STATUSES = ("documented", "press", "anecdote", "illustrative")


@dataclass(frozen=True)
class Input:
    name: str
    value: float
    unit: str
    status: str
    source: str = ""

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"status {self.status!r} not in {STATUSES}")


def by_status(inputs):
    out = {s: [] for s in STATUSES}
    for i in inputs:
        out[i.status].append(i.name)
    return out


def week_matrix(sessions, roots, monday: dt.date):
    """Open (True) or closed for each root and each UTC minute of the week that starts at monday 00:00 UTC."""
    start = dt.datetime.combine(monday, dt.time(0), cal.UTC)
    m = np.zeros((len(roots), WEEK), bool)
    for i, root in enumerate(roots):
        for d in range(7):
            for a, b in cal.utc_intervals(sessions, root, monday + dt.timedelta(days=d)):
                lo = int((a - start).total_seconds() // 60)
                hi = int(math.ceil((b - start).total_seconds() / 60))
                m[i, max(lo, 0):min(hi, WEEK)] = True
    return m


def open_hours(matrix):
    return float(matrix.any(axis=0).sum()) / 60.0


def closed_spans(matrix):
    closed = ~matrix.any(axis=0)
    spans, t = [], 0
    while t < WEEK:
        if closed[t]:
            s = t
            while t < WEEK and closed[t]:
                t += 1
            spans.append((s, t))
        t += 1
    return spans


def to_markets(sessions, roots, monday):
    m = week_matrix(sessions, roots, monday)
    out = []
    for i, root in enumerate(roots):
        hours = {}
        for d in range(7):
            day = m[i, d * DAY:(d + 1) * DAY]
            iv, t = [], 0
            while t < DAY:
                if day[t]:
                    s = t
                    while t < DAY and day[t]:
                        t += 1
                    iv.append((s, t))
                t += 1
            hours[d] = iv
        out.append(mm.Market(root, None, "futures", True, hours))
    return out


def shift_table(markets, length_h, overlap_h):
    return {d: mm.plan_shifts(markets, d, length_h, overlap_h) for d in range(7)}


def continuous_shifts(length_h, overlap_h):
    return math.ceil(24.0 / (length_h - overlap_h))


def headcount(staffed_hours_week, per_shift, max_week_h=48.0, leave_weeks=4.0, weeks=52.0):
    """People needed so that staffed_hours_week x per_shift person-hours fit under an average of max_week_h hours a
    week, with leave_weeks of leave a year (the EU minimum is four)."""
    return staffed_hours_week * per_shift / (max_week_h * (weeks - leave_weeks) / weeks)


def oncall_nights(nights_per_month, rota):
    return nights_per_month / rota
