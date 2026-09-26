"""Numbers gate: every numerical answer printed in Book 11, chapter 27 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_risk as h  # noqa: E402

rc = h.rc


def r(x, d=0):
    return round(float(x), d)


def test_table():
    t = h.table()
    rows = [(v["stopped_by"], r(v["seconds"]), r(v["loss"] / 1e6, 1), r(100 * v["false_alarm"], 1)) for v in t.values()]
    assert rows == [("end of the runaway", 2700, 477.1, 0.0), ("kill switch (person)", 300, 53.0, 0.0),
                    ("end of the runaway", 2700, 161.1, 10.2), ("price collar", 600, 106.0, 0.0),
                    ("capital threshold", 407, 71.8, 0.0), ("position limit", 102, 18.0, 7.6),
                    ("loss limit", 12, 2.1, 0.0), ("loss limit", 35, 2.1, 10.2)]


def test_sweep_and_exercises():
    s = h.sweep()
    assert [r(100 * s["loss"][v][1]) for v in (0.5e6, 1e6, 1.5e6)] == [19, 2, 0]
    assert r(s["loss"][1.5e6][0] / 1e6, 1) == 1.6
    assert (r(s["position"][1.5e8][1] * 100), r(rc.runaway({"position": 1.5e8})["seconds"])) == (50, 61)
    assert r(1481 * 100 * 1.16, -2) == 171800 and r(2e6 / (1481 * 100 * 1.16), 1) == 11.6
    assert (r(2.5e8 / 2.46e6), r(1e9 / 2.46e6)) == (102, 407)
    assert r(100 * (42.10 / 40 - 1), 2) == 5.25
