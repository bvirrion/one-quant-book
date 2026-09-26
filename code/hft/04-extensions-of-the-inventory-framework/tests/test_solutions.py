"""Numbers gate: every numerical answer printed in Book 11, chapter 4 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_extensions as e  # noqa: E402

mm = e.mm


def r(x, d=3):
    return round(float(x), d)


def test_closed_form_table():
    rows = e.depth_rows()
    assert [(r(v["stationary"]), r(v["closed"])) for v in rows.values()] == [
        (0.708, 0.707), (0.79, 0.787), (0.872, 0.868), (0.953, 0.948)]
    assert all(abs(v["T1"] - v["stationary"]) < 1e-8 for v in rows.values())
    err = e.closed_form_error()
    assert (r(err[0.5]), r(err[5.0], 2), r(err[50.0], 1)) == (0.034, 0.7, 5.0)


def test_two_assets():
    ec = e.equal_capture()
    x = ec[0.1]
    assert (r(x["mean"], 1), r(x["risk_joint"], 1), r(x["risk_separate"], 1), r(100 * x["reduction"], 0)) == (
        673.3, 24.3, 30.8, 21)
    red = [100 * v["reduction"] for v in ec.values()]
    assert (round(min(red)), round(max(red))) == (10, 22)
    c = e.cross_skew()
    i = list(c["q1"]).index(0)
    assert (r(c[-4][i]), r(c[0][i]), r(c[4][i])) == (0.572, 0.7, 0.828)


def test_drift_and_adverse():
    n, y = e.drift_case(False), e.drift_case(True)
    assert (r(y["mean"], 1), r(n["mean"], 1), r(100 * (y["mean"] / n["mean"] - 1), 1)) == (355.6, 335.7, 5.9)
    assert (r(y["sd"], 1), r(n["sd"], 1), r(y["q"], 2)) == (18.0, 15.8, 1.97)
    fine = [e.adverse_case(a) for a in e.ADJUSTS]
    coarse = [e.adverse_case(a, e.SIM["dt"]) for a in e.ADJUSTS]
    assert [r(x["mean"], 1) for x in fine] == [262.7, 267.2, 258.9]
    assert [r(x["objective"], 1) for x in fine] == [253.1, 258.6, 251.2]
    assert [round(x["fills"]) for x in fine] == [498, 396, 315]
    assert [r(x["objective"], 1) for x in coarse] == [270.8, 270.2, 259.3]
    assert r(140 * math.exp(-1.5 * 0.708) * 0.005, 2) == 0.24


def test_exercises():
    c = math.sqrt(0.5 * math.e / 210)
    assert (r(c, 4), r(1 / 1.5 + 2.5 * c), r(1 / 1.5 - 1.5 * c), r(2 / 1.5 + c)) == (0.0804, 0.868, 0.546, 1.414)
    assert 17**3 == 4913 and r(17**10 / 1e12, 1) == 2.0
    b, a = mm.stationary(140, 1.5, 0.5, 20, mu=2.0)
    assert (r(b[20]), r(a[20]), r(b[22]), r(a[22])) == (0.543, 0.872, 0.708, 0.708)
