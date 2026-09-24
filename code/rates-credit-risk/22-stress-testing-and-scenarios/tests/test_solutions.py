"""Numbers gate: every numerical answer printed in Book 6, chapter 22 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_stress as m

H = {n: (x, p) for n, x, p in m.historical_table()}
HY = m.hypothetical(100)
REV = m.reverse(10e6)
BR = m.broker_loss_move()
BR20 = m.broker_loss_move(0.20)


def moves(x):
    return (round(1e4 * x[0]), round(1e4 * x[1]), round(100 * x[2], 2), round(100 * x[3], 2))


def test_text():
    assert moves(H["Lehman 2008"][0]) == (-61, 15, -3.52, -7.85) and round(-H["Lehman 2008"][1] / 1e6, 2) == 17.26
    assert moves(H["March 2020"][0]) == (-12, 18, -5.71, 5.11) and round(-H["March 2020"][1] / 1e6, 2) == 20.13
    assert moves(H["September 2022"][0]) == (5, 21, -3.50, 0.46) and round(-H["September 2022"][1] / 1e6, 2) == 11.61
    assert round(m.var10() / 1e6, 2) == 6.63
    assert round(-HY["alone"] / 1e6, 2) == 14.80 and round(-HY["pnl"] / 1e6, 2) == 10.04
    assert (round(1e4 * HY["x"][0]), round(100 * HY["x"][2], 2), round(100 * HY["x"][3], 2)) == (80, -0.36, 2.25)
    assert round(HY["distance"], 1) == 5.3
    assert moves(REV["x_lin"]) == (33, 58, -3.18, 1.78) and round(REV["d_lin"], 2) == 3.93
    assert round(-REV["pnl_lin_full"] / 1e6, 2) == 14.00
    assert moves(REV["x_nl"]) == (10, 17, -3.45, 2.15) and round(REV["d_nl"], 2) == 2.47


def test_exercises():
    assert round(0.6 * 5 / 10 * 40) == 12 and 10 / 2.5 == 4
    w = m.reverse_without_straddle()
    assert (round(w["d_lin"], 2), round(w["d_nl"], 2)) == (3.84, 3.95)


def test_problem():
    assert BR["margin"] == 1.5e9 and round(BR["sd"] / 1e6) == 905
    assert [round(100 * x, 1) for x in BR["x"]] == [-8.7, -7.9, -7.1, -6.3, -5.4]
    assert round(BR["distance"], 2) == 1.66 and round(100 * BR["prob"], 1) == 4.9
    assert round(BR20["distance"], 2) == 4.42 and f"{BR20['prob']:.1e}" == "5.0e-06"
    assert math.isclose(BR["uniform_fall"], 0.075)
