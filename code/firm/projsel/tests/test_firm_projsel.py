import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_projsel as ps  # noqa: E402


def test_select_greedy_and_budget():
    pr = [ps.Project("a", 2, 0.5, 10), ps.Project("b", 1, 0.2, 10), ps.Project("c", 3, 0.1, 10), ps.Project("d", 1, 0.5, 4, 0.5)]
    ch = ps.select(pr, 3)
    assert [x.name for x in ch] == ["a", "b"] and sum(x.cost for x in ch) <= 3
    assert ps.expected_net(pr[2]) < 0 and ps.expected_net(pr[3]) == 0.0


def test_shapley_efficiency_symmetry_and_dummy():
    rng = np.random.default_rng(1)
    s = rng.standard_normal((2000, 3))
    s[:, 1] = s[:, 0]                       # contributors 0 and 1 bring the same signal
    y = s[:, 0] + 0.5 * s[:, 2] + rng.standard_normal(2000)
    v = ps.game(s, y)
    sh = ps.shapley(v, 3)
    assert math.isclose(sh.sum(), v(frozenset(range(3))), rel_tol=1e-9)
    assert math.isclose(sh[0], sh[1], rel_tol=1e-6)
    loo = ps.leave_one_out(v, 3)
    assert abs(loo[0]) < 1e-6 and loo.sum() < v(frozenset(range(3)))
    approx = ps.shapley(v, 3, samples=3000, rng=np.random.default_rng(2))
    assert np.allclose(approx, sh, rtol=0.05)


def test_dummy_player_gets_zero():
    v = lambda S: float(len(S & {0, 1}))  # noqa: E731
    assert np.allclose(ps.shapley(v, 3), [1, 1, 0])
