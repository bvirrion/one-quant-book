"""Numbers gate: every numerical answer printed in Book 9, chapter 29 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "surveil"))
from firm_surveil import spoof_scores, tpr_at_fpr  # noqa: E402
from s2_surveil import counts, data, detectors  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_counts():
    assert counts() == {"spoof": (11600, 100), "close": (5600, 100), "wash": (5100, 100)}


def test_detector_table():
    d = detectors()
    s, c, w = d["spoof"], d["close"], d["wash"]
    assert [r(100 * s[k]["tpr"], 0) for k in ("order-to-trade", "fill-rate gap", "cancel after fill", "gap x cancel")] == [
        0, 37, 51, 77]
    assert (r(100 * s["order-to-trade"]["by_type"][0]), r(100 * s["fill-rate gap"]["by_type"][2]),
            r(100 * s["cancel after fill"]["by_type"][1]), r(100 * s["gap x cancel"]["by_type"][2])) == (1.8, 7.7, 3.8, 7.7)
    assert [r(100 * c[k]["tpr"], 0) for k in c] == [1, 21, 61]
    assert [r(100 * c[k]["by_type"][1]) for k in c] == [3.7, 3.7, 3.3]
    assert [r(100 * w[k]["tpr"], 0) for k in w] == [74, 97] and [r(100 * w[k]["by_type"][1]) for k in w] == [4.0, 5.0]


def test_roc_and_workload():
    d = data()["spoof"]
    s = spoof_scores(d)["gap x cancel"]
    assert [r(100 * tpr_at_fpr(s, d["label"], f)["tpr"], 0) for f in (0.001, 0.01, 0.1)] == [63, 77, 100]
    assert (r(0.01 * 11500, 0), r(0.001 * 11500), r(0.1 * 11500, 0)) == (115, 11.5, 1150)          # exercises 2, 7


def test_exercises():
    assert r(24814 * 0.005, 0) == 124                                                                # exercise 1
    assert r(25.743 + 12.872) == 38.6                                                                # exercise 3
    assert (r(100 * 77 / (77 + 115)), r(100 * 7.7 / (7.7 + 115))) == (40.1, 6.3)                     # interview 6
