"""Numbers gate: every numerical answer printed in Book 6, chapter 9 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_bermudan as m

B = m.bermudan_summary()
EU = [round(x * 1e4, 1) for x in B["euro_tree"]]
Y = m.formosa_par_yield()
F = m.formosa(Y)


def test_text():
    assert round(B["strike"] * 100, 3) == 2.585 and round(B["bermudan"] * 1e4, 1) == 358.4
    assert EU == [209.5, 245.3, 249.5, 237.8, 214.1, 184.3, 147.8, 104.3, 54.9] and B["best"] == 3
    assert round(B["switch"] * 1e4, 1) == 109.0 and round(B["switch"] / max(B["euro_tree"]) * 100) == 44
    bd = dict(m.boundary())
    assert (round(bd[1] * 100, 2), round(bd[9] * 100, 2)) == (0.82, 2.30)
    rows = [tuple(round(x, 1) for x in (r[0] * 100, r[1], r[2], r[3], r[4])) for r in m.mean_reversion_table()]
    assert rows == [(1.0, 78.1, 351.0, 249.2, 101.9), (3.0, 86.0, 358.4, 249.5, 109.0), (6.0, 98.9, 369.7, 249.7, 120.0)]
    price, se = m.lsm_check()
    assert (round(price * 1e4, 1), round(se * 1e4, 1)) == (358.1, 1.9)


def test_exercises():
    assert round(sum(EU), 1) == 1647.5
    zero30 = (1 / m.usd_curve().df_t(30.0)) ** (1 / 30) - 1
    assert (round(Y * 100, 2), round(zero30 * 100, 2)) == (5.61, 4.13)


def test_problem():
    assert round(F["callable"], 6) == 1.0
    assert (round(F["straight"], 3), round(F["option"], 3), F["best_call"], round(F["best_euro"], 3)) == (
        1.526, 0.526, 5, 0.456)
    assert round(F["option"] - F["best_euro"], 3) == 0.070
    up = m.formosa(Y, sigma=m.FORMOSA_SIGMA + 1e-4)
    vega = (up["option"] - F["option"]) * 1e9
    assert round(vega / 1e6, 2) == 2.33 and round(10 * vega / 1e6, 1) == 23.3
    assert math.isclose(round(Y * 100 - zero30_pct(), 2), 1.48, abs_tol=0.01)


def zero30_pct():
    return ((1 / m.usd_curve().df_t(30.0)) ** (1 / 30) - 1) * 100
