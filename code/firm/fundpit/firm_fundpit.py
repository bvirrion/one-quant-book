"""firm.fundpit -- fundamental features keyed on knowledge time (build of One Quant Book 7, chapter 11).

Reported facts (entity, start, end, value, filed) go into a firm.pit Store under a field per duration (Q for a quarter,
H, 9M, FY), valid time the period end and knowledge time the filing date. From it: quarterly values as known at any
date (the fourth quarter derived as the year minus the nine months, or minus the three quarters), trailing twelve
months, the standardised unexpected earnings of a seasonal random walk, the list of restated periods and whether a
restatement is a share split's rescaling, analyst revisions and dispersion, and event-calendar features (days from a
period end to its next event, days to the next scheduled event, announcement windows). Dates are ISO strings or
numbers, used consistently. NumPy only.

API (stable):
    duration_kind(start, end)                'Q', 'H', '9M', 'FY' or None, from the length in days (ISO dates)
    load(facts, field)                       Store with (entity, field + '_' + kind, end, filed, value)
    quarterly(store, entity, field, known)   {end: value} of quarters known at `known` (Q4 derived)
    ttm(quarters)                            {end: sum of the four quarters ending there} (consecutive quarters only)
    sue(values, n=8)                         (x_q - x_{q-4}) / std of the previous n seasonal differences
    restated(store, entity, field)           [(end, first, last, first_known, last_known)] for changed values
    split_ratio(first, last, ratios)         the ratio r with first = r * last to the cent, else None
    revision(dates, values, t, window)       change of the mean forecast between t - window and t
    dispersion(values)                       std / |mean| of the current forecasts
    days_to_event(ends, events, max_days)    for each period end, days to the first event after it (NaN if none)
    in_window(days, events, before, after)   True for days within [-before, +after] of an event
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "pit"))
from firm_pit import Store  # noqa: E402

KINDS = (("Q", 80, 100), ("H", 170, 190), ("9M", 260, 285), ("FY", 350, 380))


def _d(x) -> dt.date:
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x))


def duration_kind(start, end) -> str | None:
    n = (_d(end) - _d(start)).days
    return next((k for k, lo, hi in KINDS if lo <= n <= hi), None)


def load(facts, field: str = "eps") -> Store:
    """facts: iterable of dicts with entity, start, end, val, filed."""
    s = Store()
    for f in facts:
        k = duration_kind(f["start"], f["end"])
        if k is not None:
            s.put(f["entity"], f"{field}_{k}", f["end"], f["filed"], float(f["val"]))
    return s


def quarterly(store: Store, entity, field: str, known) -> dict:
    """Quarters as known at `known`; a fourth quarter is the year minus the nine months ending one quarter earlier
    (or minus the three quarters) when those are known too."""
    q = dict(store.snapshot(entity, f"{field}_Q", known))
    nine = store.snapshot(entity, f"{field}_9M", known)
    for end, fy in store.snapshot(entity, f"{field}_FY", known).items():
        if end in q:
            continue
        e = _d(end)
        near = [v for k, v in nine.items() if 80 <= (e - _d(k)).days <= 100]
        prev = sorted(k for k in q if 0 < (e - _d(k)).days <= 290)
        if near:
            q[end] = fy - near[0]
        elif len(prev) == 3:
            q[end] = fy - sum(q[k] for k in prev)
    return dict(sorted(q.items()))


def ttm(quarters: dict) -> dict:
    ends = sorted(quarters)
    out = {}
    for i in range(3, len(ends)):
        w = ends[i - 3:i + 1]
        gaps = [(_d(b) - _d(a)).days for a, b in zip(w, w[1:], strict=False)]
        if all(80 <= g <= 100 for g in gaps):
            out[ends[i]] = sum(quarters[k] for k in w)
    return out


def sue(values, n: int = 8) -> np.ndarray:
    """Standardised unexpected earnings under a seasonal random walk (expected x_q = x_{q-4}), scaled by the standard
    deviation of the previous n seasonal differences; NaN until n + 1 differences exist."""
    x = np.asarray(values, float)
    d = np.full(len(x), np.nan)
    d[4:] = x[4:] - x[:-4]
    out = np.full(len(x), np.nan)
    for i in range(4 + n, len(x)):
        sd = np.std(d[i - n:i], ddof=1)
        out[i] = d[i] / sd if sd > 0 else np.nan
    return out


def restated(store: Store, entity, field: str) -> list[tuple]:
    out = []
    for (e, f, valid), rows in sorted(store._v.items(), key=lambda kv: str(kv[0])):
        if e != entity or f != field:
            continue
        vals = [v for _, v in rows]
        if any(abs(v - vals[0]) > 1e-9 for v in vals):
            out.append((valid, vals[0], vals[-1], rows[0][0], rows[-1][0]))
    return out


def split_ratio(first: float, last: float, ratios=(2, 3, 4, 5, 7, 10, 20), cent: float = 0.005):
    """The split ratio r with first = r * last up to the rounding of the reported values (half a cent each: the later,
    smaller value's rounding error is multiplied by r)."""
    if last == 0 or first == 0:
        return None
    return next((r for r in ratios if abs(first - r * last) <= cent * (r + 1)), None)


def revision(dates, values, t, window) -> float:
    """Mean of the forecasts made in (t - window, t] minus the mean of those made in (t - 2 window, t - window]."""
    d, v = np.asarray(dates, float), np.asarray(values, float)
    now = v[(d > t - window) & (d <= t)]
    before = v[(d > t - 2 * window) & (d <= t - window)]
    return float(now.mean() - before.mean()) if len(now) and len(before) else float("nan")


def dispersion(values) -> float:
    v = np.asarray(values, float)
    return float(np.std(v, ddof=1) / abs(np.mean(v))) if len(v) > 1 and np.mean(v) != 0 else float("nan")


def days_to_event(ends, events, max_days: int = 120) -> np.ndarray:
    ev = sorted(_d(x) for x in events)
    out = np.full(len(ends), np.nan)
    for i, e in enumerate(ends):
        e = _d(e)
        nxt = next((x for x in ev if x > e), None)
        if nxt is not None and (nxt - e).days <= max_days:
            out[i] = (nxt - e).days
    return out


def in_window(days, events, before: int, after: int) -> np.ndarray:
    days, events = np.asarray(days), np.asarray(events)
    out = np.zeros(len(days), bool)
    for e in events:
        out |= (days >= e - before) & (days <= e + after)
    return out
