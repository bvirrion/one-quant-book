"""Numbers gate: every numerical answer printed in Book 16, chapter 21 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_teams as m  # noqa: E402

tp = m.tp


def r(x, d=2):
    return round(float(x), d)


def test_inventory():
    s = m.services()
    assert (len(s), len(m.deps()), r(sum(x.pages_per_week for x in s), 1), r(sum(x.change_per_week for x in s), 1)) == (
        20, 33, 6.2, 34.5)
    c = m.consolidated_services()
    assert (len(c), len(m.consolidated_deps()), r(sum(x.pages_per_week for x in c), 1)) == (14, 23, 4.3)
    assert r(100 * (1 - 4.3 / 6.2), 0) == 31


def test_designs():
    c = m.compare_all()
    rows = {k: (v["cross_edges"], r(v["coordination"], 1), r(v["pages_max"]), r(v["pages_mean"]), v["bus_factor"])
            for k, v in c.items()}
    assert rows == {"embedded": (18, 22.5, 0.43, 0.41, 3), "central": (30, 33.0, 0.9, 0.41, 2),
                    "consolidated": (19, 29.0, 0.67, 0.29, 3)}
    assert c["embedded"]["teams"] == 4 and c["central"]["teams"] == 7 and c["consolidated"]["teams"] == 5
    assert r(tp.pages(m.services(), m.central())["market data"]) == 0.9


def test_moves():
    a = m.after_move()
    assert (a["embedded"]["bus_factor"], r(a["embedded"]["pages_max"])) == (3, 0.57)
    assert (a["central"]["bus_factor"], r(a["central"]["pages_max"]), a["central"]["weakest"]) == (
        1, 1.5, ["equities gateway", "futures gateway", "options gateway"])
    b = tp.report(m.consolidated_services(), m.consolidated_deps(), tp.move(m.consolidated(), "trading platform",
                                                                          "infrastructure"))
    assert (b["bus_factor"], r(b["pages_max"]), b["weakest"]) == (2, 1.0, ["gateway", "md", "risk"])


def test_small_runs():
    s = [tp.Service("a", 1.0, 1.0), tp.Service("b", 2.0, 0.5)]
    d = tp.Design({"a": "x", "b": "y"}, {"x": 1, "y": 2})
    assert tp.coordination(s, [("a", "b")], d) == 2.0 and tp.bus_factor(s, d) == (1, ["a"])


def test_hours():
    assert r(0.9 * 6, 1) == 5.4 and r(100 * 5.4 / 40, 1) == 13.5 and r(100 * 1.5 * 6 / 40, 1) == 22.5
    assert r(0.425 * 6 / 40 * 100, 1) == 6.4 and r(6.2 / 15) == 0.41 and r(4.3 / 15) == 0.29
