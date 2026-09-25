"""Numbers gate: every numerical answer printed in Book 7, chapter 16 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_vecbt import YEAR, breakeven_cost, compounding, lookahead, smoothed, waterfall


def r(x, d=2):
    return round(float(x), d)


def test_reversal_waterfall():
    w = waterfall("reversal")
    assert [r(x[1]) for x in w] == [7.17, 7.22, 6.95, -2.58, -2.64, -9.45]
    assert [r(100 * x[2], 1) for x in w] == [27.0, 27.4, 27.4, -10.2, -10.4, -37.7]
    assert [round(100 * x[3]) for x in w] == [74, 74, 75, 75, 75, 75]
    assert r(100 * (w[3][2] - w[4][2]), 2) == 0.25
    assert r(2 * 0.75 * 0.001 * 252, 2) == 0.38
    s, a = lookahead()
    assert (round(s), round(100 * a)) == (-65, -694)
    assert r(1e4 * breakeven_cost(), 1) == 7.3
    c, u = compounding()
    assert (r(c), r(u)) == (0.35, -0.04)


def test_momentum_waterfall():
    m = waterfall("momentum")
    assert [r(x[1]) for x in m] == [0.21, 0.44, 0.32, 0.21, 0.19, 0.17]
    assert r(100 * m[2][3], 1) == 1.9
    rev = waterfall("reversal")
    g_rev, g_mom = rev[2][2] / YEAR, m[2][2] / YEAR
    assert (r(100 * g_rev, 3), r(100 * g_mom, 3)) == (0.109, 0.011)
    be_mom = g_mom / (2 * m[2][3])
    assert round(1e4 * be_mom) == 31 and round(be_mom / breakeven_cost()) == 4 and r(g_mom / g_rev, 1) == 0.1


def test_smoothed_and_exercises():
    s1, s3 = smoothed(1), smoothed(3)
    assert (round(100 * s1["turnover"]), round(100 * s3["turnover"])) == (75, 42)
    assert (r(s1["sharpe"]), r(s3["sharpe"])) == (6.95, 4.13)
    assert (r(1e4 * s1["breakeven"], 1), r(1e4 * s3["breakeven"], 1)) == (7.3, 7.4)
    assert r(1e4 * (0.12 / 252) / 0.4, 1) == 11.9
    assert (r(100 * 0.66 / 1.06, 1), r(100 * 0.40 / 1.06, 1), r(100 * (0.66 / 1.06 - 0.6), 1)) == (62.3, 37.7, 2.3)
    assert (r(0.9 ** 5), r(5 * 0.5 - 5 * 0.4, 1)) == (0.59, 0.5)
    assert np.isclose(0.03 - 0.005 * 1.0, 0.025)
