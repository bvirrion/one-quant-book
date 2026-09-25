"""firm.pit -- point-in-time storage and as-of joins (build of One Quant Book 7, chapter 3).

A bitemporal store keeps every value a fact has ever had, keyed by its valid time (the date the value
describes: the month of a payroll figure, the quarter of an earnings number) and its knowledge time
(when the value became known to the firm: a release, a filing, a vendor delivery). A query names
both, so that a backtest asks only what was known at its decision time. Times are any comparable
type (numbers, ISO strings, datetime.date) used consistently. NumPy only for the array join.

API (stable):
    Store()
    .put(entity, field, valid, known, value)       record a value; a later knowledge time for the same
                                                   (entity, field, valid) is a revision
    .asof(entity, field, valid, known)             the value of `valid` as known at `known` (None if unknown)
    .first(entity, field, valid)                   (knowledge time, value) of the first release
    .vintages(entity, field, valid)                [(known, value), ...] in knowledge order
    .snapshot(entity, field, known)                {valid: value} for every valid time known at `known`
    .latest(entity, field)                         {valid: value}, today's (last) view
    Guard(store, decision_time)                    the same queries, refusing any knowledge time after the
                                                   decision time (raises LookAheadError)
    asof_join(left_t, right_t, right_v, tolerance=None, strict=False)
                                                   for each left time, the last right value at or before it
                                                   (strictly before if strict), NaN if none or too old
"""
from __future__ import annotations

import bisect

import numpy as np


class LookAheadError(RuntimeError):
    """A query asked for knowledge that did not exist at the decision time."""


class Store:
    def __init__(self):
        self._v: dict[tuple, list] = {}          # (entity, field, valid) -> sorted [(known, value)]

    def put(self, entity, field, valid, known, value) -> None:
        rows = self._v.setdefault((entity, field, valid), [])
        keys = [k for k, _ in rows]
        i = bisect.bisect_right(keys, known)
        if i > 0 and keys[i - 1] == known:
            rows[i - 1] = (known, value)          # a correction at the same knowledge time replaces
        else:
            rows.insert(i, (known, value))

    def vintages(self, entity, field, valid) -> list:
        return list(self._v.get((entity, field, valid), []))

    def asof(self, entity, field, valid, known):
        rows = self._v.get((entity, field, valid))
        if not rows:
            return None
        i = bisect.bisect_right([k for k, _ in rows], known)
        return rows[i - 1][1] if i else None

    def first(self, entity, field, valid):
        rows = self._v.get((entity, field, valid))
        return rows[0] if rows else None

    def snapshot(self, entity, field, known) -> dict:
        out = {}
        for (e, f, valid), rows in self._v.items():
            if e == entity and f == field:
                i = bisect.bisect_right([k for k, _ in rows], known)
                if i:
                    out[valid] = rows[i - 1][1]
        return dict(sorted(out.items()))

    def latest(self, entity, field) -> dict:
        return dict(sorted((valid, rows[-1][1]) for (e, f, valid), rows in self._v.items()
                           if e == entity and f == field))


class Guard:
    """A view of a store for one decision time: every query that names a later knowledge time raises."""

    def __init__(self, store: Store, decision_time):
        self.store, self.t = store, decision_time

    def _check(self, known):
        if known > self.t:
            raise LookAheadError(f"asked for knowledge at {known!r} after the decision time {self.t!r}")

    def asof(self, entity, field, valid, known=None):
        known = self.t if known is None else known
        self._check(known)
        return self.store.asof(entity, field, valid, known)

    def snapshot(self, entity, field, known=None):
        known = self.t if known is None else known
        self._check(known)
        return self.store.snapshot(entity, field, known)


def asof_join(left_t, right_t, right_v, tolerance=None, strict: bool = False) -> np.ndarray:
    """For each left time, the value of the last right row at or before it (strictly before when
    `strict`, for a right table whose rows are known only after their stamp); NaN when there is none,
    or when it is older than `tolerance`. right_t must be sorted."""
    left_t, right_t = np.asarray(left_t, float), np.asarray(right_t, float)
    right_v = np.asarray(right_v, float)
    i = np.searchsorted(right_t, left_t, side="left" if strict else "right") - 1
    ok = i >= 0
    if tolerance is not None:
        ok &= (left_t - right_t[np.maximum(i, 0)]) <= tolerance
    return np.where(ok, right_v[np.maximum(i, 0)], np.nan)
