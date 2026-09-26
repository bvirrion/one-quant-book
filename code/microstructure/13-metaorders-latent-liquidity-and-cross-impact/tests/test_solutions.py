"""Numbers gate: every numerical answer printed in Book 10, chapter 13 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_cross import cross_study, fair, llob_scan  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_llob():
    s = llob_scan()
    assert [r(p) for p in s["peaks"]] == [0.05, 0.18, 0.52, 1.74, 4.9, 12.2, 23.3, 44.0]
    assert [r(x) for x in s["slopes"]] == [1.01, 0.99, 1.0, 0.94, 0.76, 0.59, 0.53]
    assert (r(np.sqrt(2 * 1000.0), 1), r(np.sqrt(2 * 300.0), 1)) == (44.7, 24.5)
    f = fair(10.0)
    assert (r(f["peak"]), r(f["average"]), r(f["average"] / f["peak"]), r(f["cross_after"], 1), r(f["ratio"])) == \
        (1.74, 1.16, 0.66, 1.9, 0.16)
    g = fair(300.0)
    assert (r(g["peak"], 1), r(g["average"] / g["peak"]), r(g["cross_after"], 1), r(g["ratio"])) == (23.3, 0.66, 2.3, 0.27)


def test_cross():
    c = cross_study()
    assert [r(x) for x in c["estimate"].ravel()] == [0.96, 0.42, 0.42, 0.81]
    assert ([r(100 * x, 1) for x in c["explained"]], r(c["corr_flow"])) == ([4.5, 5.3], 0.58)
    s, p = c["same"], c["pair"]
    assert (r(s["joint"], 1), r(s["own_estimate"], 1), r(s["sequential"], 1)) == (52.1, 36.0, 64.6)
    assert (r(p["joint"], 1), r(p["own_estimate"], 1), r(p["sequential"], 1)) == (20.0, 36.0, 38.4)
    assert (r(100 * s["saving_vs_sequential"], 0), r(100 * p["saving_vs_sequential"], 0)) == (19.0, 48.0)
    assert (r(100 * s["slow_saving"], 1), r(100 * p["slow_saving"], 1)) == (0.0, 3.7)
    assert (r(100 * (1 - s["own_estimate"] / s["joint"]), 0), r(100 * (p["own_estimate"] / p["joint"] - 1), 0)) == (31.0, 80.0)
    assert np.allclose(s["schedule"][0], s["schedule"][1])


def test_exercises():
    # 1: square-root regime of the latent book: Q = 50 (thousand shares), L = 2 (thousand shares per tick squared)
    assert r(np.sqrt(2 * 50 / 2.0), 2) == 7.07
    # 3: fair pricing with a square-root path: the average of sqrt(t/T) over the execution is 2/3 of the peak
    assert r(2 / 3, 3) == 0.667


def test_exercise_7_slower_execution():
    from mx_cross import SIZES
    s = llob_scan(SIZES, 100.0)
    assert [r(x) for x in s["slopes"]] == [1.0, 1.0, 1.0, 1.0, 0.99, 0.94, 0.75]
    assert (r(s["peaks"][3], 3), r(s["peaks"][-1], 1)) == (0.562, 38.6)
