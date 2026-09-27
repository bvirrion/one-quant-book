"""Numbers gate: every numerical answer printed in Book 10, chapter 17 (text and solutions)."""
import dataclasses
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_place import (  # noqa: E402
    QTY,
    Cross,
    Post,
    calibration,
    dp_thresholds,
    market_stats,
    model_study,
    run_policy,
    sim_study,
    urgent_study,
)


def r(x, d=1):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_market_and_calibration():
    s = market_stats()
    assert (r(100 * s["one_tick"]), r(s["queue"]), r(1 / s["moves"]), r(s["volume"], 0)) == (97.7, 14.6, 9.4, 137)
    assert r(QTY / (60 * s["volume"]), 2) == 0.10
    c = calibration()
    assert (r(c.lam, 2), r(c.theta, 3), r(c.mu, 2), r(c.depth2)) == (0.99, 0.021, 0.69, 3.2)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_policies_in_the_simulated_market():
    s = sim_study()
    assert s["n"] == 216
    got = {k: (r(v["cost"], 2), r(v["se"], 2), r(v["sd"], 2), r(100 * v["passive"]), r(100 * v["cleanup"]))
           for k, v in s.items() if isinstance(v, dict)}
    assert got["cross"] == (0.70, 0.04, 0.53, 0.0, 0.0)
    assert got["join"] == (-0.24, 0.06, 0.89, 91.0, 9.0)
    assert got["behind"] == (0.76, 0.11, 1.59, 16.7, 83.3)
    assert got["reprice"] == (-0.22, 0.05, 0.72, 97.3, 2.7)
    assert got["imbalance"] == (-0.19, 0.05, 0.78, 90.8, 2.7)
    assert got["plan"] == got["reprice"]                                 # the plan never crossed early
    vs = {k: (r(v["vs_cross"][0], 2), r(v["vs_cross"][1], 2)) for k, v in s.items() if isinstance(v, dict)}
    assert (vs["join"], vs["behind"], vs["reprice"], vs["imbalance"]) == ((-0.94, 0.07), (0.06, 0.11), (-0.92, 0.06),
                                                                         (-0.89, 0.06))
    assert r(100 * s["imbalance"]["high"]) == 6.5
    assert r(s["imbalance"]["cost"] - s["reprice"]["cost"], 2) == 0.03


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_plan_and_learning():
    m = model_study()
    assert (r(m["cross"][0], 2), r(m["join"][0], 2), r(m["plan"][0], 2), r(m["Q-learning"][0], 2)) == (0.66, -0.40, -0.40, -0.39)
    assert r(m["plan_value"], 2) == -0.40 and m["threshold"][0] == 1.0 and r(100 * m["q_visited"]) == 4.0
    t = dp_thresholds()
    assert (r(t[(1, 15.0)][0], 2), r(t[(1, 5.0)][0], 2), r(t[(1, 3.0)][0], 2)) == (0.86, 0.79, 0.66)
    assert t[(1, 60.0)][0] == t[(8, 15.0)][0] == t[(8, 60.0)][0] == 1.0


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_urgent_lot():
    u = urgent_study()
    assert u["n"] == 1824
    b = u["buckets"]
    assert (r(b[0][3], 2), r(b[0][4], 2)) == (-0.26, 0.05)
    assert (r(b[5][3], 2), r(b[5][4], 2), r(b[6][3], 2), r(b[6][4], 2)) == (0.03, 0.07, -0.11, 0.08)
    assert all(abs(x[3]) < 0.1 for x in b[2:5])                           # a few hundredths above zero
    assert all(x[3] < 2 * x[4] for x in b)                                # crossing never significantly cheaper


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    from firm_placement import _fresh, cross_cost, solve
    c = calibration()
    assert cross_cost(8, 5, c.depth2) / 8 == 0.875
    assert r(sum(1 / (c.mu + c.theta * n) for n in range(1, 16))) == 17.8

    def share(model):
        p = solve(model, 1, 5.0, dt=0.2, n_max=40, a_max=40)
        f = _fresh(model, 40)
        w = np.outer(f[1:41], f[1:41])
        return r(100 * float((w * p.cross[-1][1, 1:, 1:]).sum() / w.sum()))
    assert (share(c), share(dataclasses.replace(c, lam=c.lam / 2))) == (6.0, 18.6)


def test_small_runs():
    # Three slices on one seed instead of 24 sessions: crossing takes liquidity on every fill, joining the queue
    # earns some passive fills, and every slice is measured.
    cross, join = run_policy(Cross(), 1701, slices=3), run_policy(Post(0, False), 1701, slices=3)
    assert len(cross) == len(join) == 3 and all(np.isfinite(x[1]) for x in cross + join)
    assert all(x[2] == 0.0 for x in cross) and sum(x[2] for x in join) > 0
    assert all(-1 <= x[0] <= 1 and 0 <= x[3] <= 1 for x in cross + join)
