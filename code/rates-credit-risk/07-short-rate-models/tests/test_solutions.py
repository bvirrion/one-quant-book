"""Numbers gate: every numerical answer printed in Book 6, chapter 7 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_shortrate as m
from firm_shortrate import zero_rate_vol

FIT = m.fit_table()
CAL = m.calibrations()


def test_text():
    assert [round(1e4 * zero_rate_vol(k, 0.008, 10), 1) for k in (0.03, 0.10)] == [69.1, 50.6]
    assert (round(FIT[0][1], 1), round(FIT[-1][1], 1)) == (60.8, 91.0)
    assert round(CAL["constant"].sigmas[0] * 1e4, 1) == 86.0
    cons = [r[2] for r in FIT]
    assert (round(min(cons), 1), round(max(cons), 1)) == (76.0, 76.7)
    assert (round(FIT[0][2] - FIT[0][1], 1), round(FIT[-1][2] - FIT[-1][1], 1)) == (15.3, -14.2)
    s = [x * 1e4 for x in CAL["piecewise"].sigmas]
    assert (round(s[0], 1), round(max(s), 1), round(s[-1], 1)) == (68.7, 116.3, 104.2)
    t = {dt: m.tree_check(dt=dt) for dt in (1 / 12, 1 / 24, 1 / 48, 1 / 96)}
    j = t[1 / 24]
    assert (round(j["forward"] * 100, 3), round(j["annuity"], 3), round(j["jamshidian"], 6)) == (2.933, 4.102, 0.026018)
    assert [round(t[dt]["tree"], 6) for dt in (1 / 12, 1 / 24, 1 / 48, 1 / 96)] == [0.026119, 0.026079, 0.026044,
                                                                                    0.026016]
    g = dict(m.g2_table())
    assert (round(g[10.0], 3), round(g[30.0], 3)) == (0.774, 0.687)


def test_exercises():
    assert (round(1e4 * zero_rate_vol(0.03, 0.008, 10), 1), round(1e4 * zero_rate_vol(0.03, 0.008, 30), 1)) == (
        69.1, 52.7)
    assert round((0.03 - 0.01**2 / (2 * 0.1**2)) * 100, 2) == 2.50
    jm = math.ceil(0.184 / (0.03 / 12))
    jw = math.ceil(0.184 / (0.03 / 52))
    assert (jm, 2 * jm + 1, jw, 2 * jw + 1) == (74, 149, 319, 639)


def test_problem():
    assert FIT[0][2] > FIT[0][1] and FIT[-1][2] < FIT[-1][1]
