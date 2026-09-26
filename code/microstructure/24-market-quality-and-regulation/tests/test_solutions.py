"""Numbers gate: every numerical answer printed in Book 10, chapter 24 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_mq import study  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_named_result_and_table():
    s = study()
    q = s["quoted"]
    assert (r(q["ba"]["coef"], 2), r(q["ba"]["se"], 2), r(q["did"]["coef"], 2), r(q["did"]["se"], 2),
            r(q["truth"], 2), r(q["truth_se"], 2)) == (1.60, 0.08, 0.89, 0.09, 0.87, 0.03)
    m = q["means"]
    assert (r(m[(True, False)], 2), r(m[(True, True)], 2), r(m[(False, False)], 2), r(m[(False, True)], 2)) == (
        1.58, 3.18, 1.56, 2.27)
    assert r(m[(False, True)] - m[(False, False)], 2) == 0.71
    rows = {"effective": (2.74, 0.12, 1.31, 0.14, 1.36, 0.06), "realised": (1.81, 0.08, 1.06, 0.10, 1.15, 0.07),
            "impact": (0.93, 0.09, 0.25, 0.10, 0.21, 0.07), "variance_ratio": (-0.19, 0.02, -0.13, 0.06, -0.14, 0.03),
            "otr": (-2.64, 0.05, -1.18, 0.07, -1.19, 0.02)}
    for k, want in rows.items():
        v = s[k]
        assert (r(v["ba"]["coef"], 2), r(v["ba"]["se"], 2), r(v["did"]["coef"], 2), r(v["did"]["se"], 2),
                r(v["truth"], 2), r(v["truth_se"], 2)) == want, k
    d = s["depth"]
    assert (r(d["ba"]["coef"], 0), r(d["ba"]["se"], 0), r(d["did"]["coef"], 0), r(d["did"]["se"], 0), r(d["truth"], 0),
            r(d["truth_se"], 0)) == (-138, 8, -20, 13, -31, 2)
    pre = [abs(c) for k, (c, _) in s["event"].items() if k < 7]
    assert max(pre) < 0.07 and len(pre) == 7
    assert r(s["otr"]["means"][(True, False)] + s["otr"]["did"]["coef"], 1) < s["otr"]["means"][(True, False)]


def test_exercises():
    assert r(900 / 250) == 3.6 and r(900 / 250 - 1.18) == 2.4
    low = study("low")["quoted"]
    assert (r(low["did"]["coef"], 2), r(low["did"]["se"], 2), r(low["truth"], 2)) == (1.11, 0.06, 0.94)
