"""Numbers gate: every numerical answer printed in Book 4, Chapter 13 (text and solutions)."""
import functools
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_resampling import (
    coverage,
    pnl_lrv_factor,
    problem,
    reality_check,
    sampling_sd,
    se_by_block,
    spurious_rejections,
    strategy,
)


@functools.cache
def P():
    # computed on first use, so that the fast set (CI) never builds it
    return problem()

@functools.cache
def C():
    # computed on first use, so that the fast set (CI) never builds it
    return coverage()


def r(x, d=2):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_history_and_intervals():
    assert (r(P()["sr"]), r(P()["skew"], 1), round(P()["kurt"])) == (1.11, -4.7, 34)
    assert [r(v) for v in P()["rho"]] == [0.13, 0.10, -0.02]
    assert r(pnl_lrv_factor(), 1) == 3.9 and r(math.exp(0.64), 3) == r(math.exp(4 * 0.4**2), 3)
    assert (r(P()["b_sb"], 1), r(P()["b_cb"], 1)) == (18.6, 21.2)
    assert (r(P()["iid"][0]), r(P()["iid"][1]), r(P()["iid_se"])) == (0.17, 2.25, 0.53)
    assert (r(P()["block"][0]), r(P()["block"][1]), r(P()["block_se"])) == (-0.34, 2.93, 0.84)
    assert (r(P()["stationary"][0]), r(P()["stationary"][1]), r(P()["stationary_se"])) == (-0.25, 2.96, 0.83)
    assert (r(P()["delta_se"]), r(P()["jack_se"]), r(P()["jack_bias"]), r(P()["sr"] - P()["jack_bias"])) == (0.52, 0.53, 0.04, 1.06)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_truth_and_block_curve():
    assert r(sampling_sd()) == 1.10
    curve = dict(se_by_block())
    assert r(curve[1]) == 0.59 and all(0.94 <= curve[b] <= 0.98 for b in (40, 60, 90))
    assert max(curve.values()) < 1.0


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_coverage():
    assert C()["pct"] == {"iid": 68.5, "block": 82.75, "stationary": 82.75}
    c40 = coverage(block=40)
    assert c40["pct"]["stationary"] == 84.0


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_ablations_and_resample_count():
    """WRITING section 9. Ablate the mechanism credited (volatility clustering: AR coefficient 0) and check that the
    coverage verdict does not move when the number of resamples is quadrupled (the analogue of a finer time step)."""
    c0 = coverage(phi=0.0)
    assert c0["pct"]["iid"] == 91.5 and c0["pct"]["iid"] - C()["pct"]["iid"] > 20
    c4 = coverage(n_boot=2000)
    assert abs(c4["pct"]["iid"] - C()["pct"]["iid"]) <= 1.0 and abs(c4["pct"]["stationary"] - C()["pct"]["stationary"]) <= 1.5


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_permutation_and_reality_check():
    s = spurious_rejections()
    assert (s["perm"], s["shift"]) == (0.215, 0.025)
    rc = reality_check()
    assert (r(rc["t_best"]), r(rc["p_boot"], 4), r(rc["p_gauss"], 3), r(rc["block"], 1), r(rc["crit_boot"])) == (
        3.11, 0.0275, 0.030, 1.3, 2.85)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    assert (r((1 - 1 / 1260) ** 1260, 4), r(math.exp(-1), 4)) == (0.3677, 0.3679)
    assert r(0.95**60, 3) == 0.046 and 5**5 == 3125 and math.comb(9, 5) == 126
    assert r((4 / 3) ** (2 / 3), 3) == 1.211 and r(1260 ** (1 / 3)) == 10.80 and r((4 / 3) ** (2 / 3) * 1260 ** (1 / 3), 1) == 13.1
    assert r(1 - 0.99**100, 3) == 0.634 and r(1 - math.exp(-1), 3) == 0.632
    x = strategy(1)
    assert x.size == 1260 and np.isfinite(x).all()


def test_small_runs():
    # 200 bootstrap draws and 20 simulated histories instead of 4,000 and 400: every interval is ordered, and the
    # coverage counts are shares of the histories.
    p = problem(n_boot=200)
    assert all(p[k][0] < p[k][1] for k in ("iid", "block", "stationary")) and p["iid_se"] > 0
    c = coverage(n_hist=20, n_boot=100)
    assert c["n"] == 20 and all(0 <= v <= 100 for v in c["pct"].values())
