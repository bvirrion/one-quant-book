import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fundpit import (
    days_to_event,
    dispersion,
    duration_kind,
    in_window,
    load,
    quarterly,
    restated,
    revision,
    split_ratio,
    sue,
    ttm,
)

FACTS = [  # one company, fiscal year = calendar year; Q4 only inside the annual figure
    {"entity": "X", "start": "2024-01-01", "end": "2024-03-31", "val": 1.0, "filed": "2024-05-02"},
    {"entity": "X", "start": "2024-04-01", "end": "2024-06-30", "val": 1.1, "filed": "2024-08-01"},
    {"entity": "X", "start": "2024-01-01", "end": "2024-06-30", "val": 2.1, "filed": "2024-08-01"},
    {"entity": "X", "start": "2024-07-01", "end": "2024-09-30", "val": 1.2, "filed": "2024-11-01"},
    {"entity": "X", "start": "2024-01-01", "end": "2024-09-30", "val": 3.3, "filed": "2024-11-01"},
    {"entity": "X", "start": "2024-01-01", "end": "2024-12-31", "val": 4.8, "filed": "2025-02-20"},
    {"entity": "X", "start": "2024-01-01", "end": "2024-03-31", "val": 0.5, "filed": "2025-05-01"},   # 2:1 split
]


def test_kinds_and_quarters():
    assert [duration_kind(f["start"], f["end"]) for f in FACTS[:6]] == ["Q", "Q", "H", "Q", "9M", "FY"]
    s = load(FACTS)
    q = quarterly(s, "X", "eps", "2025-03-01")
    assert list(q) == ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"]
    assert math.isclose(q["2024-12-31"], 1.5)                       # 4.8 - 3.3
    assert quarterly(s, "X", "eps", "2024-12-31").get("2024-12-31") is None          # not yet filed
    assert math.isclose(ttm(q)["2024-12-31"], 4.8)
    assert math.isclose(quarterly(s, "X", "eps", "2025-06-01")["2024-03-31"], 0.5)   # the later view


def test_restated_and_split():
    r = restated(load(FACTS), "X", "eps_Q")
    assert r == [("2024-03-31", 1.0, 0.5, "2024-05-02", "2025-05-01")]
    assert split_ratio(1.0, 0.5) == 2 and split_ratio(1.0, 0.8) is None and split_ratio(2.8, 0.4) == 7
    assert split_ratio(0.17, 0.06) == 3 and split_ratio(0.76, 0.75) is None       # cents rounded after a 3:1 split


def test_sue():
    x = np.r_[np.arange(12.0), 20.0]              # seasonal differences all 4, then a jump
    s = sue(x + np.tile([0.0, 0.1, 0.0, -0.1], 4)[:13], n=8)
    assert np.isnan(s[:12]).all() and s[12] > 10
    rng = np.random.default_rng(0)
    y = np.cumsum(rng.standard_normal(400))
    assert 0.7 < np.nanstd(sue(y, 8)) < 1.6


def test_analysts_and_calendar():
    assert math.isclose(revision([1, 2, 11, 12], [1.0, 1.2, 1.5, 1.7], 12, 10), 1.6 - 1.1)
    assert math.isclose(dispersion([1.0, 1.2, 1.4]), 0.2 / 1.2)
    d = days_to_event(["2024-03-31", "2024-06-30"], ["2024-04-25", "2024-07-30", "2024-01-20"])
    assert list(d) == [25, 30]
    assert list(in_window(np.arange(10), [5], 1, 2)) == [False] * 4 + [True] * 4 + [False] * 2
