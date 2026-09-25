"""firm.earnstrat -- earnings-event strategies (build of One Quant Book 8, chapter 7).

Event calendars as (T, N) arrays from a list of (day, id, surprise) announcements; the event-time long-short book that
buys positive surprises and sells negative ones for a holding window after each announcement; the market-adjusted
announcement return; the ratio of announcement-day to ordinary-day absolute moves (what an option straddle across the
announcement prices); cumulative abnormal returns in event time for an event study. NumPy only.

API (stable):
    calendar(events, T, N)                    (flag (T, N) bool, surprise (T, N) NaN off event days)
    event_book(flag, surprise, listed, hold, threshold, delay)
                                              weights held after the close of t: +0.5 spread over names that announced a
                                              surprise above threshold in the `hold` days ending `delay` days before t,
                                              -0.5 over those below -threshold
    announcement_move(ret, flag)              mean |return| on event days / mean |return| on other days
    event_car(abret, flag, surprise, before, after, threshold)
                                              mean cumulative abnormal return from `before` days before to `after`
                                              days after events with positive and with negative surprises
"""
from __future__ import annotations

import numpy as np


def calendar(events, T: int, N: int):
    flag = np.zeros((T, N), bool)
    sur = np.full((T, N), np.nan)
    for t, i, s in events:
        if t < T and i < N:
            flag[t, i] = True
            sur[t, i] = s
    return flag, sur


def _recent(x, hold, delay):
    """True at t where x had an event in [t - delay - hold + 1, t - delay]."""
    c = np.concatenate([np.zeros((1, x.shape[1])), np.cumsum(x, axis=0)])
    hi = np.maximum(np.arange(1, len(x) + 1) - delay, 0)
    lo = np.maximum(hi - hold, 0)
    return (c[hi] - c[lo]) > 0


def event_book(flag, surprise, listed, hold: int, threshold: float = 1.0, delay: int = 0):
    s = np.where(flag, np.asarray(surprise, float), 0.0)
    up = _recent((s > threshold).astype(float), hold, delay)
    down = _recent((s < -threshold).astype(float), hold, delay)
    up, down = up & listed, down & listed
    nu, nd = up.sum(axis=1, keepdims=True), down.sum(axis=1, keepdims=True)
    return np.where(up, 0.5 / np.maximum(nu, 1), 0.0) - np.where(down, 0.5 / np.maximum(nd, 1), 0.0)


def announcement_move(ret, flag):
    a = np.abs(np.asarray(ret, float))
    ok = np.isfinite(a)
    return float(a[flag & ok].mean() / a[~flag & ok].mean())


def event_car(abret, flag, surprise, before: int, after: int, threshold: float = 0.0):
    ab = np.nan_to_num(np.asarray(abret, float))
    T = ab.shape[0]
    out = {}
    for name, sel in (("positive", surprise > threshold), ("negative", surprise < -threshold)):
        paths = []
        for t, i in zip(*np.nonzero(flag & sel), strict=True):
            if t - before >= 0 and t + after < T:
                paths.append(np.cumsum(ab[t - before:t + after + 1, i]))
        out[name] = np.mean(paths, axis=0) if paths else np.zeros(before + after + 1)
    return out
