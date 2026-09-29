"""Numbers gate: every numerical answer printed in Book 16, chapter 27 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_crisis as m  # noqa: E402

cd = m.cd


def r(x, d=1):
    return round(float(x), d)


def test_baseline():
    b = m.baseline()
    assert (b["horizon"], r(b["total_calls"])) == (6, 78.8)
    assert [r(x) for x in b["cash"][[0, 5, 6, 23, 24, 47, 48]]] == [32.0, 30.2, -5.2, -35.0, -42.8, -42.8, -33.2]
    n = m.no_failure()
    assert (n["horizon"], r(n["total_calls"]), r(n["cash"].min())) == (23, 45.0, -13.0)
    assert r(33.0 * 0.4) == 13.2 and r(33.0 * 0.6) == 19.8


def test_plan():
    s = m.steps()
    assert [(a, h, r(c, 2)) for a, h, c in s] == [("sell money-market funds", 9, 0.02), ("repo the bond portfolio", 15, 0.12),
                                                  ("draw the committed line", 24, 0.42), ("cut 10% of positions", 72, 1.42)]
    _, p = m.plan()
    assert (r(p["cash"].min()), r(p["total_calls"])) == (11.8, 65.8)
    cash_only = cd.run(m.ACCOUNTS, m.CASH0, m.scenario(), [a for a in m.MENU if a.cut == 0], m.HOURS)
    assert (cash_only["horizon"], r(cash_only["cash"].min())) == (24, -2.8)


def test_small_runs():
    sc = cd.Scenario(tuple([1.0] * 5), tuple([1.0] * 5), "FCM")
    r0 = cd.run([cd.Account("PB", 10.0, 10.0)], 1.0, sc, (), 5)
    assert r0["horizon"] == 5 and np.allclose(r0["cash"], 1.0)


def test_exercises():
    menu = [a for a in m.MENU if "line" not in a.name]
    ch, res = cd.greedy(m.ACCOUNTS, m.CASH0, m.scenario(), menu, 72, 72)
    assert [a.name for a in ch][-1] == "cut a further 10%" and (res["horizon"], r(res["cost"], 2)) == (72, 3.12)
