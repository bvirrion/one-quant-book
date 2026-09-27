"""Numbers gate: every numerical answer printed in Book 10, chapter 28 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_execalgo import IS, KEYS, SIZES, TWAP, ab_study, run, stress  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_named_result():
    s = ab_study()
    assert s["n"] == 200
    assert (r(s["mean"]), r(s["lo"]), r(s["hi"])) == (-0.15, -0.44, 0.14)
    b, se = s["beta"], s["beta_se"]
    assert (r(b[0]), r(b[1]), r(b[2]), r(se[0]), r(se[1]), r(se[2])) == (1.25, -0.70, -0.69, 0.08, 0.04, 0.22)
    c = s["cells"]
    assert (r(c[(4000, 0.5)][0]), r(c[(32000, 3.0)][0]), r(c[(16000, 3.0)][0])) == (1.06, -1.96, -0.63)
    assert round(4000 * 2 ** (-b[0] / b[1]), -2) == 13_700 and r(math.log2(13_700 / 4000)) == 1.78
    p = s["participation"]
    assert (round(100 * p[SIZES[0]], 1), round(100 * p[SIZES[-1]], 1)) == (2.4, 15.9)
    assert round(13_700 / 16_000 * p[16000], 2) == 0.08                # break-even near 8% of volume
    a = s["attribution"]
    assert (r(a["is"]["spread"]), r(a["twap"]["spread"]), r(a["is"]["fees"]), r(a["twap"]["fees"]),
            r(a["is"]["impact"]), r(a["twap"]["impact"])) == (-0.15, 0.51, -0.02, 0.30, 1.73, 0.93)
    # rolling out
    assert r(s["sd"]) == 1.33 and round((1.96 + 0.84) ** 2 * 1.33**2 / 0.15**2, -1) == 620
    # exercise 7
    assert r(s["before_fees"]) == -0.47 and r(a["twap"]["fees"] - a["is"]["fees"]) == 0.32
    # exercise 3
    assert r(1.25 - 0.70 * 2 - 0.69) == -0.84


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_stress():
    st = stress()
    h = st["halt"]
    ev = {e: t for t, _, e, _ in h["log"]}
    assert (ev["pause"], ev["resume"], ev["finish"], ev["done"]) == (200.0, 260.0, 661.0, 662.0)
    assert h["state"] == "done" and (r(h["shortfall"]), r(st["base"]["shortfall"])) == (2.62, 2.31)
    sp = st["spike"]
    ev = {e: (t, d) for t, _, e, d in sp["log"]}
    assert ev["limit"][0] == 252.0 and ev["limit off"][0] == 465.0 and ev["done"][0] == 587.0
    assert "1001800" in ev["limit"][1] and "1000700" in ev["limit off"][1] and st["limit"] == 1_001_050
    assert (r(sp["shortfall"]), r(st["nolimit"]["shortfall"])) == (3.79, 4.31) and 465 - 252 == 213
    assert all(px <= st["limit"] for t, px, _ in sp["algo"].fills if 252 < t < 465)
    k = st["kill"]
    assert k["state"] == "killed" and k["log"][-1][:3] == (299.6, "killed", "kill") and "8500 of 16000" in k["log"][-1][3]
    assert k["filled"] == 8700


def test_exercises_1_2():
    tol = 20 / 600 * 10_000
    assert round(tol) == 333 and min(d for d in range(0, 2000, 100) if int((d - tol) // 100) * 100 >= 100) == 500
    assert round(0.3 / 0.7 * 32_000) == 13_714 and round(0.3 / 0.7 * 32_000) - 8000 == 5714
    assert np.isclose(10_000 / 2, 5000)


def test_small_runs():
    # One order of 4,000 shares on one seed, the algorithm against TWAP, instead of the 200-order A/B test: both
    # complete, the cost attribution adds up, and TWAP pays the spread and the fees that the passive algorithm earns.
    a, t = run(IS(4000, 0.5), 1), run(TWAP(4000), 1)
    for x in (a, t):
        assert x["state"] == "done" and x["filled"] == 4000 and 0 < x["participation"] < 1
        assert abs(sum(x["tca"][k] for k in KEYS[:-1]) - x["tca"]["total"]) < 1e-9
    assert a["tca"]["spread"] < 0 < t["tca"]["spread"] and a["tca"]["fees"] < t["tca"]["fees"]
