"""Numbers gate: every numerical answer printed in Book 16, chapter 14 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_treasury as m  # noqa: E402

tr = m.tr


def r(x, d=1):
    return round(float(x), d)


def test_book_and_hand_numbers():
    assert (m.POS[m.POS > 0].sum(), -m.POS[m.POS < 0].sum(), np.abs(m.POS).sum(), m.POS.sum()) == (390, 330, 720, 60)
    a = m.BROKERS[0]
    assert r(tr.margin(a, [120.0]), 2) == 43.8 and r(tr.margin(m.BROKERS[1], [120.0]), 2) == 12.0
    assert r(tr.margin(m.BROKERS[2], [120.0]), 2) == 48.0


def test_allocations():
    s = m.summary()
    assert [r(s[k]["margin"], 2) for k in s] == [71.55, 72.0, 144.0, 53.6, 33.9]
    assert [r(s[k]["cost"], 2) for k in s] == [6.88, 5.99, 10.92, 5.82, 4.98]
    assert [r(x, 1) for x in s["optimised"]["by_broker"]] == [20.4, 6.0, 7.5]
    assert r(s["all at B"]["margin"] - s["optimised"]["margin"]) == 38.1
    assert r(100 * (1 - s["optimised"]["margin"] / s["all at B"]["margin"]), 0) == 53
    assert r(s["all at B"]["cost"] - s["optimised"]["cost"], 2) == 1.0 and r(s["optimised"]["financing"], 2) == 3.29


def test_stress():
    assert r(m.initial().sum(), 1) == 39.3
    pnl, req = m.paths(True, None, 0)
    assert r(pnl[:5].sum()) == -15.5 and list(np.round(pnl[:5].sum(0), 1)) == [-12.0, -5.8, -3.5, 5.8]
    assert [r(x) for x in req.sum(1)[[0, 4, 29]]] == [43.0, 71.8, 54.5] and (r(req[0, 3], 2), r(req[4, 3], 2)) == (2.02, 2.13)
    _, req30 = m.paths(True, None, 30)
    assert r(req30.sum(1)[4]) == 37.0
    base, s0, s30 = m.run(False), m.run(True, 0), m.run(True, 30)
    assert base["horizon"] == 31 and (s0["horizon"], r(s0["buffer"])) == (5, 8.1) and s30["horizon"] == 31
    assert r(s30["min_cash"]) == 26.7 and r(s0["calls"].sum()) == 57.9 and r(s30["calls"].sum()) == 23.0
    one = m.run(True, 0, m.allocations()["all at B"])
    assert (one["horizon"], r(one["buffer"])) == (3, 29.8)
    assert [m.run(True, n)["horizon"] for n in (5, 10)] == [6, 11]
    assert [m.run(True, 0, cash0=c)["horizon"] for c in (50, 60)] == [31, 31]
    assert [m.run(True, 0, m.allocations()["all at B"], cash0=c)["horizon"] for c in (50, 60)] == [4, 5]


def test_small_runs():
    a = m.allocations()["optimised"]
    assert np.allclose(a.sum(axis=1), 1.0)


def test_exercise_numbers():
    s = m.summary()
    assert r((72.0 - 33.9) * 0.05, 2) == 1.91 and r(s["all at B"]["financing"], 2) == 2.39 and r(s["all at A"]["financing"], 2) == 3.3
    assert r(s["pro rata"]["margin"], 1) == 53.6 and (0.5 * 10, 1.5 * 10) == (5.0, 15.0)
