"""Numbers gate: every numerical answer printed in Book 5, Chapter 22 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_fd import (
    accuracy_study,
    barrier_alignment,
    dividend_example,
    fd,
    gamma_profile,
    hook,
    project_after_solve,
    reference,
)

A = accuracy_study()


def test_hook_and_budget():
    h = hook()
    assert (round(h["n200"], 4), round(h["n201"], 4), round(h["ref"], 4)) == (6.0864, 6.0975, 6.0904)
    assert (round(100 * (h["n200"] - h["ref"]), 2), round(100 * (h["n201"] - h["ref"]), 2)) == (-0.40, 0.72)
    assert A["n_crr"] == 1500 and A["work_crr"] == 1_125_750 and A["m_fd"] == 200 and A["work_fd"] == 40_600
    assert round(A["speedup"]) == 28
    assert [round(100 * abs(A["fd_err"][m]), 3) for m in (50, 100, 200, 400)] == [1.040, 0.302, 0.091, 0.029]
    assert round(100 * abs(A["raw_err"][200]), 3) == 0.125
    assert (round(100 * abs(A["tri_err"][1600]), 2), round(100 * abs(A["tri_err"][3200]), 3)) == (0.11, 0.054)
    assert abs(A["crr_err"][1500]) < 0.001 and abs(A["crr_err"][1501]) < 0.001 and abs(A["crr_err"][1451]) > 0.001


def test_gamma_dividend_barrier():
    g = gamma_profile()
    s, gc = g["cn"]
    _, gr = g["rannacher"]
    _, ge = g["exact"]
    m = (s > 92) & (s < 108)
    i = int(np.argmin(np.abs(s - 100.0)))
    assert (round(float(gc[i]), 3), round(float(ge[i]), 3)) == (0.217, 0.141)
    assert round(float(np.abs(gr[m] - ge[m]).max()), 4) == 0.0002
    d = dividend_example()
    assert (round(d["euro"], 3), round(d["escrowed"], 3), round(d["american"], 3), round(d["american_no_div"], 3)) == (
        6.835, 6.719, 7.407, 6.090)
    b = barrier_alignment()
    assert round(b["exact"], 3) == 8.665
    assert (round(b["aligned"][40], 4), round(b["aligned"][200], 4)) == (0.0049, 0.0002)
    assert (round(b["misaligned"][40], 2), round(b["misaligned"][200], 2), round(b["misaligned"][300], 3)) == (1.10, 0.16, 0.046)


def test_exercises():
    assert round(math.log2(0.30 / 0.091), 2) == 1.72 and round(0.091 / 2 ** math.log2(0.30 / 0.091), 3) == 0.028
    v8, v16 = fd(800), fd(1600)
    assert (round(v16, 6), round(v16 - v8, 6), round(reference(), 7)) == (6.090331, 0.000068, 6.0903535)
    rich = fd(200) + (fd(200) - fd(100)) / 3
    assert round(100 * abs(rich - reference()), 3) == 0.021
    errs = [round(100 * abs(project_after_solve(m) - reference()), 2) for m in (100, 200, 400)]
    assert errs == [0.80, 0.35, 0.16]
    assert 0.0003 < abs(A["crr_err"][2000]) < 0.0008 and 0.0003 < abs(A["crr_err"][2001]) < 0.0008


def test_boundary():
    from dv_fd import exercise_boundary, tree_boundary
    eb = dict(exercise_boundary([1.0]))
    assert round(eb[1.0], 2) == 80.85
    tb = [s for tau, s in tree_boundary() if tau > 0.97]
    assert (round(min(tb), 2), round(max(tb), 2)) == (80.68, 81.04)
