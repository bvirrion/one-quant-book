"""Numbers gate: every numerical answer printed in Book 6, chapter 25 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "code/firm/varmodel"))
import rc_margin as m
from firm_initmargin import schedule_im

R = m.replay_2020()
B = m.backtest_since()
S = m.schedule_today()


def mn(x, d=2):
    return round(x / 1e6, d)


def test_text():
    assert m.dv01_net() == -160e3
    assert (mn(R["hs_feb"]), mn(R["hs_peak"]), R["hs_peakday"], round(R["hs_ratio"], 2)) == (4.19, 5.25, "2020-03-18", 1.25)
    assert (mn(R["fhs_feb"]), mn(R["fhs_peak"]), R["fhs_peakday"], round(R["fhs_ratio"], 2)) == (
        4.21, 10.30, "2020-03-23", 2.45)
    assert mn(R["fhs_increase"]) == 6.09 and mn(R["hs_increase"]) == 1.06
    assert (mn(m.hs10_today()), mn(m.simm_today()), mn(S["gross"]), mn(S["net"])) == (4.15, 8.98, 13.19, 9.23)
    assert (mn(R["buffer_feb"]), mn(R["buffer_peak"]), mn(R["buffer_increase"])) == (5.26, 10.30, 5.04)
    assert (mn(R["stressed_im"]), mn(R["stressed_feb"]), mn(R["stressed_increase"])) == (6.55, 4.79, 5.51)
    assert (B["days"], B["hs"], B["fhs"], round(B["days"] * 0.01)) == (2_177, 35, 37, 22)


def test_exercises():
    assert schedule_im([("ir", 100.0, 10.0), ("ir", 100.0, 1.0)], 1.0, 1.0)["gross"] == 5.0
    assert round(1 - (0.4 + 0.6 * 30 / 120), 2) == 0.45
    from firm_varmodel import kupiec
    lr, p = kupiec(2177, 35, 0.01)
    assert (round(lr, 2), round(p, 3), round(2177 * 0.01, 1)) == (6.86, 0.009, 21.8)


def test_problem():
    assert round(mn(R["buffer_feb"]) - mn(R["fhs_feb"]), 2) == 1.05 and round(mn(R["stressed_feb"]) - mn(R["fhs_feb"]), 1) == 0.6
