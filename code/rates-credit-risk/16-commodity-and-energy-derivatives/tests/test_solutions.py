"""Numbers gate: every numerical answer printed in Book 6, chapter 16 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_energy as e

MOD = e.model()
C = e.calendar_spread(0.5)
C0 = e.calendar_spread(0.0)
S = e.storage()
W = e.swing()
ST = e.storm()


def test_text():
    q = [v for _, _, v in e.vol_quotes()]
    assert (round(100 * q[0], 1), round(100 * q[-1], 1)) == (62.0, 43.0)
    assert (round(MOD.kappa, 2), round(100 * MOD.sigma_s, 1), round(100 * MOD.sigma_l, 1)) == (1.50, 60.0, 20.0)
    assert [round(100 * e.inst_vol(MOD, t), 1) for t in (0, 1, 5)] == [68.7, 27.2, 20.0]
    assert (round(100 * C["s1"], 1), round(100 * C["s2"], 1), round(C["rho"], 3)) == (34.8, 58.1, 0.970)
    assert (round(100 * C["kirk"], 2), round(100 * C["mc"], 2), round(100 * C["se"], 2)) == (29.41, 29.78, 0.01)
    assert round(100 * (C["mc"] - C["kirk"]), 2) == 0.38
    assert round(100 * C0["kirk"], 1) == round(100 * C0["mc"], 1) == 75.8
    assert max(abs(r[1]) for r in e.kirk_table()) < 0.5
    assert round(e.F0[9] - e.F0[3] + 0.5, 2) == 1.26
    assert S["plan"] == [2, 2, 2, 2, 2, 0, 0, 0, -4, -4, -2, 0]
    assert (round(S["intrinsic"] * e.UNIT), round(S["rolling"] * e.UNIT), round(S["lsm"] * e.UNIT)) == (
        634_447, 699_550, 698_182)
    assert round(S["extrinsic"] / S["intrinsic"], 2) == 0.10
    assert W["plan"] == [0, -2, -2, -2, 0]
    assert (round(W["intrinsic"], 2), round(W["lsm"], 2), round(W["strip"], 2)) == (1.84, 4.37, 6.11)


def test_exercises():
    assert round(math.exp(-1.5), 2) == 0.22
    assert round(math.exp(-e.R_FREE / 365) * (3.50 - 2.74 - 0.50), 4) == 0.2600
    assert round(100 * (C0["kirk"] - C0["mc"]), 3) == 0.007 and round(100 * (C["kirk"] - C["mc"]), 3) == -0.375


def test_problem():
    assert round((S["lsm"] - S["intrinsic"]) * e.UNIT, -3) == 64_000
    assert (ST["feb1"], ST["peak"], ST["peak_day"]) == (2.88, 23.86, "2021-02-17")
    assert round(ST["rebuy"], 2) == 2.62
    assert (ST["fast"]["volume"], ST["fast"]["days"], round(ST["fast"]["value"])) == (500_000, 5, 4_306_870)
    assert (ST["slow"]["volume"], ST["slow"]["days"], round(ST["slow"]["value"])) == (90_000, 9, 479_057)
    assert round(math.log(23.86 / 3.76), 2) == 1.85
    assert round(e.inst_vol(MOD, 0) * math.sqrt(4 / 252), 3) == 0.087
    assert round(math.log(23.86 / 3.76) / (e.inst_vol(MOD, 0) * math.sqrt(4 / 252))) == 21
