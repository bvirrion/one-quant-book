"""Numbers gate: every numerical answer printed in Book 6, chapter 13 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_credit as m
from firm_cdscurve import HazardCurve, bootstrap, par_spread, risky_bond, standard_upfront

P = m.protection_position()
B = m.basis_package()


def test_text():
    t = m.hazard_table()
    assert [round(r[1], 2) for r in t] == [1.00, 1.51, 2.04, 2.86, 3.03, 3.32]
    assert [round(r[2], 2) for r in t] == [1.00, 1.25, 1.50, 2.00, 2.25, 2.50]
    assert (round(t[0][3], 3), round(t[3][3], 2), round(t[5][3], 1), round(t[3][3], 1)) == (0.995, 9.76, 23.1, 9.8)
    assert round(m.upfront_5y() * 100, 3) == 0.872 and round(m.zero_rate(5) * 100, 2) == 3.42
    u = {r[0]: r for r in m.upfront_table()}
    assert (round(u[500][1], 2), round(u[500][2], 2)) == (15.06, 0.0)
    assert (round(P["mtm"]), round(P["cs01"][3]), round(P["annuity"], 2), round(P["jtd"] / 1e6, 2)) == (
        88_133, 4_391, 4.41, 5.91)
    c25 = bootstrap(m.DISC, m.TENORS, m.SPREADS, 0.25)
    assert (round(100 * c25.hazards[0], 2), round(100 * c25.hazards[-1], 2)) == (0.80, 2.64)
    assert round(100 * (1 - c25.survival(5)), 2) == 7.87
    s = list(m.SPREADS)
    s[2] = 0.0050
    c = bootstrap(m.DISC, m.TENORS, s, m.R)
    assert c.hazards[2] < 1e-12 and round(1e4 * par_spread(c, m.DISC, 3, m.R), 1) == 51.0
    cv = m.curve()
    assert round(100 * risky_bond(HazardCurve([5.0], [0.0]), m.DISC, 5, 0.05, m.R), 2) == 107.08
    assert round(100 * B["model_price"], 2) == 101.38
    assert (round(m.DISC.df_t(5) * cv.survival(5), 4), round(m.DISC.df_t(5), 4)) == (0.7604, 0.8427)
    assert round(B["bond_spread"] * 1e4) == 220 and round(B["basis_bp"], 1) == -99.8


def test_exercises():
    assert round(0.018 / 0.6 * 100, 2) == 3.00 and round(100 * math.exp(-0.15), 2) == 86.07
    assert round(100 * (1 - math.exp(-0.15)), 1) == 13.9
    assert round(-6e6 + P["mtm"]) == -5_911_867
    assert round(P["annuity"] * 10e6 * 1e-4) == 4_407
    z = m.zero_rate(5)
    assert round(100 * standard_upfront(5, 0.035, 0.05, z, m.R), 2) == -5.98
    assert round(100 * standard_upfront(5, 0.035, 0.01, z, m.R), 2) == 9.96
    assert round(100e6 * (0.40 - 0.97) + 100e6 * 0.60 - 10 * P["mtm"]) == round(B["jtd_par"]) == 2_118_667


def test_problem():
    assert round(B["jtd_mv"]) == 345_107
    assert (round(B["cs01_par"]), round(B["cs01_mv"])) == (-2_141, -3_453)
    assert round(100 * B["be_recovery_mv"], 1) == 28.5


def test_interview():
    assert round(0.02 / 0.6 * 100, 2) == 3.33 and round(100 * math.exp(-5 * 0.02 / 0.6), 1) == 84.6
