"""Numbers gate: every numerical answer printed in Book 16, chapter 16 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_compliance as m  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_preclearance():
    rs = m.reasons()
    assert sum(rs.values()) == 1215 and rs == {"approved": 964, "firm traded recently": 202, "restricted list": 23,
                                               "holding period": 6, "watch list": 5, "insider": 15}
    assert r(100 * rs["approved"] / 1215) == 79.3 and r(100 * rs["firm traded recently"] / 251) == 80.5


def test_queue():
    score, label = m.alerts()
    assert len(score) == 11600 and int(label.sum()) == 100
    q50, q150 = m.queue(50), m.queue(150)
    assert (q50["capacity"], q50["best_rate"], r(q50["best_found"], 0)) == (100, 0.008, 65)
    assert (q150["capacity"], q150["best_rate"], r(q150["best_found"], 0)) == (300, 0.025, 81)
    d = q50["default"]
    assert (d["alerts"], d["true_alerts"], r(d["found"]), r(d["missed"])) == (580, 89, 15.3, 84.7)
    assert r(q150["default"]["found"]) == 46.0
    s50 = m.queue(50, "score")
    assert r(s50["default"]["found"], 0) == 66 and r(m.queue(150, "score")["default"]["found"], 0) == 81
    assert r(100 * 100 / 11600, 2) == 0.86
    assert m.naive()["found"] == 0.0 and m.naive()["alerts"] == 576


def test_small_runs():
    fc = m.fc
    lists = fc.Lists([("X", 5, 10)], [("Y", 0, 3)])
    assert fc.preclear((1, "X", 1, 7), lists, {}, {}) == (False, "restricted list")
    assert fc.preclear((1, "Z", -1, 20), lists, {}, {(1, "Z"): 5}) == (False, "holding period")
