"""Numbers gate: every numerical answer printed in Book 16, chapter 24 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_entry as m  # noqa: E402

ep = m.ep


def r(x, d=0):
    return round(float(x), d)


def test_plan():
    sch, cp = m.plan()
    assert cp == ["legal entity", "regulatory registration", "exchange membership", "certification", "first trade"]
    assert m.first_trade() == 10.0 and sch["clearing limits set"] == (7.5, 8.0, 1.0)
    assert sch["connectivity"][2] == 4.0 and sch["market data licences"][2] == 6.0 and sch["software adaptation"][2] == 2.0
    c = ep.cost_by_month(m.TASKS, 12)
    assert r(c.sum(), 1) == 948.5 and r(c.max()) == 170


def test_scenarios():
    v = m.scenario_npvs()
    assert {k: r(x) for k, x in v.items()} == {"weak": -3547, "base": 1996, "strong": 8463}
    assert r(100 * ep.irr(ep.entry_cash(m.TASKS, m.first_trade(), 450.0, m.TAU, m.RUN, m.HORIZON))) == 104


@pytest.mark.reference
def test_staging():
    s = m.staging()
    p, st, k = s["plain"], s["staged"], s["killed"]
    assert (r(p.mean()), r(st.mean()), r(st.mean() - p.mean()), r(100 * k.mean(), 1)) == (2525, 2725, 200, 22.7)
    assert (r(100 * (p < 0).mean(), 1), r(100 * (st < 0).mean(), 1)) == (38.6, 39.6)
    assert (r(np.percentile(p, 5)), r(np.percentile(st, 5))) == (-3566, -1916)
    R = s["R"]
    assert (r(100 * (R < m.RUN).mean(), 1), r(100 * ((R < m.RUN) & ~k).mean(), 1), r(100 * ((R >= m.RUN) & k).mean(), 1)) == (
        20.9, 3.6, 5.5)
    curve = dict((th, v) for th, v, _ in m.threshold_curve())
    assert max(curve, key=curve.get) == 250 and r(curve[300]) == 150 and r(curve[400]) == -138


def test_small_runs():
    p, s, k = ep.staged_npv(m.TASKS, m.first_trade(), np.array([100.0, 600.0]), m.TAU, m.RUN, m.HORIZON, m.RATE,
                            m.KILL_AFTER, m.THRESHOLD, 0.0)
    assert list(k) == [True, False] and s[0] > p[0]


def test_exercises():
    from dataclasses import replace
    t = [replace(x, months=2.0) if x.name == "regulatory registration" else x for x in m.TASKS]
    assert ep.schedule(t)["first trade"][1] == 9.0 and "clearing agreement" in ep.critical_path(t)
    assert 60.0 * 4 == 240.0
