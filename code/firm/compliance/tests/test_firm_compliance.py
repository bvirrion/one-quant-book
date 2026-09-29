import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_compliance as fc  # noqa: E402


def test_lists_and_preclear_order():
    lists = fc.Lists([("A", 10, 20)], [("B", 5, 8)])
    assert lists.on("restricted", "A", 10) and not lists.on("restricted", "A", 21) and lists.on("watch", "B", 8)
    trades = {"C": [3, 9]}
    assert fc.preclear((1, "A", 1, 15), lists, trades, {}) == (False, "restricted list")
    assert fc.preclear((1, "B", 1, 6), lists, trades, {}) == (False, "watch list")
    assert fc.preclear((1, "C", 1, 10), lists, trades, {}) == (False, "firm traded recently")
    assert fc.preclear((1, "C", 1, 12), lists, trades, {}) == (True, "approved")
    assert fc.preclear((1, "D", -1, 30), lists, trades, {(1, "D"): 10}) == (False, "holding period")
    assert fc.preclear((1, "D", -1, 40), lists, trades, {(1, "D"): 10}) == (True, "approved")
    assert fc.preclear((1, "D", 1, 40), lists, trades, {}, {(1, "D")}) == (False, "insider")


def test_register():
    reg = fc.Register()
    reg.cross(7, "p", "X", 10)
    reg.cross(8, "p", "X", 12)
    reg.cleanse("p", 20)
    assert reg.insiders("X", 11) == {7} and reg.insiders("X", 15) == {7, 8} and reg.insiders("X", 20) == set()


def test_triage():
    score = np.arange(100.0)
    label = (score >= 95).astype(int)
    t = fc.triage(score, label, 0.10, 5)
    assert t["alerts"] == 10 and t["true_alerts"] == 5 and t["found"] == 2.5
    assert fc.triage(score, label, 0.10, 5, "score")["found"] == 5.0
    best, res = fc.best_rate(score, label, 5, (0.05, 0.10, 0.20))
    assert best == 0.05 and res[0.05] == 5.0 and res[0.20] == 1.25
