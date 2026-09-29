import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_ddrules as dd  # noqa: E402


def test_rules_on_hand_path():
    r = np.zeros((1, 40))
    r[0, 5:15] = -0.01
    _, s = dd.apply(dd.Rule("stop", 0.05), r)
    assert s[0] == 10
    sizes, s = dd.apply(dd.Rule("ladder", 0.03, 0.08), r)
    assert sizes[0, 9] == 0.5 and s[0] == -1          # halved at 3%, the rest of the fall costs half: 7% < 8%
    _, s = dd.apply(dd.Rule("time", 20), r)
    assert s[0] == 21                                  # no new high since day 0


def test_posterior_detects_a_break():
    rng = np.random.default_rng(1)
    dead = dd.paths(200, 2520, 1.0, 0.10, rng, break_day=252, sr_dead=-2.0)
    alive = dd.paths(200, 2520, 1.0, 0.10, rng)
    pa = dd.posterior(alive, 1.0, -2.0, 0.10, 1 / 2520)
    pd = dd.posterior(dead, 1.0, -2.0, 0.10, 1 / 2520)
    assert pd[:, -1].mean() > 0.9 > pa[:, -1].mean()


def test_evaluate_and_lorden():
    rng = np.random.default_rng(2)
    alive = dd.paths(300, 2520, 1.0, 0.10, rng)
    dead = dd.paths(300, 2520, 1.0, 0.10, rng, break_day=756, sr_dead=-1.0)
    e = dd.evaluate(dd.Rule("stop", 0.10), alive, dead, 756)
    assert 0 < e["false_per_100y"] < 100 and e["pnl_dead"] > e["pnl_dead_unmanaged"]
    assert math.isclose(dd.cusum_delay(1.0, 0.0, math.e), 2 * 252)
