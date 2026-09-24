"""Numbers gate: every numerical answer printed in Book 4, Chapter 25 (text and solutions)."""
import math
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_float import (
    DOCUMENTED,
    cg_demo,
    cholesky_on_pairwise,
    expected_drift,
    fma_example,
    normal_equations,
    pnl_entries,
    summation_errors,
    vancouver,
    variance_errors,
)


def r(x, d=2):
    return round(float(x), d)


def test_vancouver():
    v = vancouver()
    assert v["n"] == 1_152_000 and round(expected_drift(v["n"])) == 576
    assert r(DOCUMENTED[1] - DOCUMENTED[0], 3) == 574.081 and round(expected_drift(3000 * 480)) == 720
    assert (r(v["final"]), r(v["exact"], 3)) == (422.23, 1098.892)
    e = v["exact_path"]
    ratio = float(np.mean(e[-1] / e[:-1]))
    assert (r(ratio, 3), round(e.min()), round(e.max())) == (1.175, 803, 1183)
    assert abs(expected_drift(v["n"]) * ratio - (v["exact"] - v["final"])) < 0.2
    assert r(v["exact"] - v["final"], 1) == 676.7
    assert r(vancouver(mode="round")["final"]) == 1098.57


def test_summation_and_variance():
    rows = {n: row for n, *row in summation_errors()}
    naive, pair, neu, exact = rows[1_000_000]
    assert (r(naive * 1e6, 1), r(pair * 1e8, 1), r(neu * 1e9, 1), r(exact, 3)) == (2.5, 2.8, 2.2, 47878411.409)
    assert neu < math.ulp(exact) and r(math.ulp(exact) * 1e9, 1) == 7.5
    assert all(row[2] < math.ulp(row[3]) for row in rows.values())
    v = {c: row for c, *row in variance_errors()}
    assert r(v[1.0][0] * 1e13, 1) == 2.8 and r(v[1e4][0] * 1e7, 1) == 8.0 and r(v[1e6][0] * 100, 1) == 1.3
    assert (round(v[1e8][0]), r(v[1e8][3]), r(v[1e8][4], 4)) == (1060, 86.84, 0.0819)
    assert max(row[1] for row in v.values()) < 1.02e-12 and r(v[1e8][2] * 1e8, 1) == 1.6


def test_linear_algebra():
    ne = {k: row for k, *row in normal_equations()}
    assert (r(ne[1e7][0] * 1e3, 1), r(ne[1e7][1] * 1e10, 1)) == (5.3, 1.2)
    ch = cholesky_on_pairwise()
    assert (ch["ok"], ch["fail_index"], r(ch["pivot"]), r(ch["min_eig"]), ch["fixed_ok"]) == (False, 5, -0.14, -1.42, True)
    assert ch["jitter_needed"] == 2.0
    cg = cg_demo()
    assert (r(cg["cond"] / 1e5, 1), cg["iters_plain"], cg["iters_pre"], round(cg["cond_pre"])) == (1.1, 1909, 102, 100)
    bound = 0.5 * math.sqrt(cg["cond"]) * math.log(2 / 1e-8)
    assert round(math.sqrt(cg["cond"])) == 328 and 3000 < bound < 3200 and cg["iters_plain"] < bound


def test_fma_and_exercises():
    f = fma_example()
    assert f["separate"] == 0.0 and f["fused"] == f["two_pow"] == 2.0 ** -54
    assert 1e16 + 1 - 1e16 == 0.0 and 1e8 + 1 - 1e8 == 1.0
    assert r(53 * math.log10(2)) == 15.95 and 0.005 * 10_000 * 250 == 12_500
    assert r(1000 + math.log(2), 3) == 1000.693
    assert 0.1 + 0.2 - 0.3 == math.ulp(0.3)
    assert r(1.1e-16 * 1e8 / 0.08 * 1e7, 1) == 1.4


def test_truncation_drift_scales_with_updates():
    """WRITING section 9: halving the recalculation rate halves the truncation loss (to first order), and rounding
    (the ablation) removes it."""
    half = vancouver(updates_per_day=1200)
    full = vancouver()
    loss_half, loss_full = half["exact"] - half["final"], full["exact"] - full["final"]
    assert 0.4 < loss_half / loss_full < 0.6
    assert abs(vancouver(mode="round")["final"] - full["exact"]) < 1.0
    assert len(pnl_entries(7)) == 7


def test_patriot_clock():
    """The GAO table: 1/10 chopped to 23 binary places, accumulated over 100 hours of tenths of a second."""
    c = Fraction(math.floor(Fraction(1, 10) * 2**23), 2**23)
    err = Fraction(1, 10) - c
    assert r(float(err) * 1e8, 2) == 9.54 and round(float(err * 3_600_000), 4) == 0.3433
