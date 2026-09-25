"""Acceptance tests of firm.bars."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_bars import asof, continuous, dollar_bars, imbalance_bars, tick_bars, time_bars, volume_bars, vwap

T = np.array([0.5, 1.2, 1.9, 3.1, 3.2, 5.5])
P = np.array([10.0, 10.2, 9.9, 10.1, 10.3, 10.0])
Q = np.array([100.0, 200.0, 100.0, 300.0, 100.0, 200.0])


def test_time_bars_and_empty_intervals():
    b = time_bars(T, P, Q, 2.0, 0.0, 6.0)
    assert list(b.n) == [3, 2, 1] and b.high[0] == 10.2 and b.close[1] == 10.3
    assert abs(b.vwap[0] - vwap(P[:3], Q[:3])) < 1e-12 and b.volume.sum() == Q.sum()
    e = time_bars(T, P, Q, 1.0, 0.0, 6.0)
    assert list(e.n) == [1, 2, 0, 2, 0, 1] and e.close[2] == e.close[1] and e.close[4] == e.close[3]


def test_threshold_bars_close_on_the_crossing_trade():
    v = volume_bars(T, P, Q, 300.0)
    assert list(v.last) == [1, 3, 5] and list(v.volume) == [300.0, 400.0, 300.0]
    d = dollar_bars(T, P, Q, 3000.0)
    assert (d.value >= 3000.0).all() and tick_bars(T, P, Q, 2).n.tolist() == [2, 2, 2]


def test_imbalance_bars_partition_the_trades():
    rng = np.random.default_rng(0)
    s = np.where(rng.random(2000) < 0.55, 1.0, -1.0)
    b = imbalance_bars(np.arange(2000.0), np.full(2000, 10.0), np.ones(2000), s, expected_n=50)
    assert b.first[0] == 0 and (b.first[1:] == b.last[:-1] + 1).all() and len(b) > 5


def test_asof():
    out = asof([1.0, 2.0, 4.0], [10.0, 20.0, 40.0], [0.5, 1.0, 3.9, 9.0])
    assert np.isnan(out[0]) and list(out[1:]) == [10.0, 20.0, 40.0]


def test_continuous_series():
    c1 = np.array([50.0, 51.0, 52.0, 53.0, 60.0, 61.0])     # expiry on day 3; c1 becomes the old c2 on day 4
    c2 = np.array([55.0, 56.0, 57.0, 59.0, 65.0, 66.0])
    exp = np.array([False, False, False, True, False, False])
    out = continuous(c1, c2, exp, days_before=2)            # roll at the close of day 1 (gap 5)
    assert list(out["rolls"]) == [1] and list(out["held"]) == [50.0, 51.0, 57.0, 59.0, 60.0, 61.0]
    assert list(out["back"]) == [55.0, 56.0, 57.0, 59.0, 60.0, 61.0]
    assert np.allclose(out["ratio"][:2], np.array([50.0, 51.0]) * 56.0 / 51.0)
    held_ret = np.diff(np.log(out["held"]))
    assert np.isclose(np.diff(np.log(out["ratio"]))[0], held_ret[0])
