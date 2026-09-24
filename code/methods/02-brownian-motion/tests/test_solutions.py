"""Numbers gate: every numerical answer printed in Book 4, Chapter 2 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_brownian import (
    SIGMA,
    Phi,
    bgk_probability,
    convergence_table,
    qv_table,
    reflection_example,
    simulate_touch,
    stop_problem,
    touch_probability,
)

P = stop_problem()


def r(x, k=1):
    return round(100 * x, k)


def test_text():
    assert round(0.30 / math.sqrt(252), 3) == 0.019 and round(0.30 * math.sqrt(21 / 252), 3) == 0.087
    assert (r(P["p_end"], 0), r(P["p_touch"], 0), r(P["p_daily_sim"], 0)) == (41, 82, 72)
    assert round(P["b"], 4) == -0.0202 and round(P["s"], 4) == 0.0866 and round(P["b"] / P["s"], 3) == -0.233
    assert r(P["p_touch"]) == 81.6 and r(P["p_touch_drift"]) == 82.4
    assert round(P["shift"], 4) == 0.0110 and r(1 - math.exp(P["b"] - P["shift"])) == 3.1
    assert r(P["p_bgk_daily"]) == 71.9 and r(P["p_daily_sim"]) == 72.0
    conv = dict(convergence_table())
    assert (r(conv[4]), r(conv[16]), r(conv[64])) == (77.1, 79.1, 80.5)
    assert r(P["p_cross_1pct"], 0) == 57 and r(P["p_bridge_sim"]) == 81.6
    assert round(qv_table()[-1][1], 3) == 1.006
    e = reflection_example()
    assert round(e["tau"], 3) == 0.618


def test_exercises():
    assert round(2 / math.sqrt(10), 3) == 0.632
    assert r(2 * (1 - Phi(1.0))) == 31.7
    assert (round(100 * 0.2 / math.sqrt(252), 2), round(100 * 0.2 * math.sqrt(5 / 252), 2)) == (1.26, 2.82)
    b = math.log(0.95)
    assert round(b, 4) == -0.0513
    assert r(touch_probability(b, 0.30, 0.25)) == 73.2 and r(bgk_probability(b, 0.30, 0.25, 1 / 252)) == 67.8
    assert r(math.exp(-0.5)) == 60.7
    rng = np.random.default_rng(7)
    qv = (rng.standard_normal((2000, 4096)) ** 2).sum(axis=1) / 4096
    assert round(math.sqrt(2 / 4096), 3) == 0.022 and round(qv.std(), 3) == 0.022
    assert round((1.031 - 1) / 0.0221, 1) == 1.4


def test_problem():
    assert round(P["se_daily"], 3) == 0.001 and r(P["p_end"]) == 40.8
    assert r(P["p_q15_sim"]) == 79.6 and r(P["p_bgk_q15"]) == 79.6
    assert r(P["p_cross_1pct"]) == 57.1 and round(100 * P["se_bridge"], 2) == 0.08
    assert r(P["p_touch_15vol"]) == 64.1
    assert r(P["p_touch_3m"]) == 89.3 and r(P["p_bgk_daily_3m"]) == 83.5


def test_interview():
    assert abs(math.sqrt(2 / math.pi) - 0.798) < 5e-4
    rng = np.random.default_rng(3)
    x, y = rng.standard_normal((2, 400_000))
    assert abs(np.mean((x > 0) & (x + y > 0)) - 3 / 8) < 0.003


def test_time_step_and_ablation():
    """WRITING section 9. The discretely monitored probability converges to the continuous one
    as the step is divided by four (gap roughly halving: an O(sqrt(dt)) error), and the bridge
    correction is what closes it: without the correction the daily estimate is 9 points low."""
    conv = convergence_table()
    gaps = [P["p_touch"] - p for _, p in conv]
    for g0, g1 in zip(gaps, gaps[1:], strict=False):
        assert 0.35 < g1 / g0 < 0.65
    with_bridge, se = simulate_touch(P["b"], SIGMA, 21, 1, 100_000, seed=41, bridge=True)
    without, _ = simulate_touch(P["b"], SIGMA, 21, 1, 100_000, seed=41, bridge=False)
    assert abs(with_bridge - P["p_touch"]) < 3 * se and P["p_touch"] - without > 0.08
    finer, se4 = simulate_touch(P["b"], SIGMA, 21, 4, 50_000, seed=42, bridge=True)
    assert abs(finer - P["p_touch"]) < 3 * se4                       # bridge result is step-independent
