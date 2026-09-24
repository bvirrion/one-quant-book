"""Numbers gate: every numerical answer printed in Book 2, Chapter 5 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/repo"))
from firm_repo import RepoTrade, carry, fails_charge, margin_call, special_rate_floor, value_of_specialness
from repo_demo import SETTLE, financed_note, sponsored

F = financed_note()
D = F["dirty"]


def test_text():
    assert round(100e6 * 0.02125 * 30 / 184) == 346_467
    assert round(100e6 * D / 100 * 0.039 * 30 / 360) == 327_830
    sp = sponsored()
    first, last = sp[0], sp[-1]
    assert 4 <= last[1] / first[1] <= 6 and 3.5 <= last[2] / first[2] <= 5      # four- to fivefold
    assert round(1.34, 2) == 1.34 and 54 > 0


def test_exercises():
    assert round(50e6 * 0.039 * 4 / 360, 2) == 21_666.67
    assert round(100e6 * 1.015 * 0.98) == 99_470_000
    assert round(100e6 * 0.008 / 360, 2) == 2_222.22
    assert round(F["dv01"]) == 80_444
    c43 = carry(100e6, 4.25, D, 0.043, 30, period_days=184)
    assert round(100e6 * D / 100 * 0.043 * 30 / 360) == 361_454 and round(c43) == -14_987
    assert round(fails_charge(100e6, 1.0), 2) == 5_555.56 and round(fails_charge(100e6, 1.0, days=5), 2) == 27_777.78
    assert fails_charge(100e6, 3.75, days=5) == 0.0
    assert special_rate_floor(0.0) == -0.03 and special_rate_floor(0.0375) == 0.0
    t = RepoTrade("repo", "x", 100e6, D, 0.02, 0.039, SETTLE, SETTLE + dt.timedelta(days=30))
    assert round(t.interest(SETTLE + dt.timedelta(days=1))) == 10_709
    assert round(t.cash + t.interest(SETTLE + dt.timedelta(days=1))) == 98_864_202
    assert round(100e6 * (D - 1.5) / 100) == 99_370_911
    assert round(margin_call(t, D - 1.5, SETTLE + dt.timedelta(days=1))) == 1_510_928
    assert round(margin_call(t, D, SETTLE + dt.timedelta(days=30))) == 327_830


def test_problem():
    path = [(30, 0.0045), (30, 0.0025), (30, 0.0010)]
    assert [round(0.039 - s, 4) for _, s in path] == [0.0345, 0.0365, 0.0380]
    assert round(100e6 * D / 100 * 0.0045 * 30 / 360) == 37_827
    v = value_of_specialness(D, path)
    assert round(v / 100 * 100e6) == 67_247 and round(v, 4) == 0.0672
    assert round(v * 32, 2) == 2.15 and round(v / (F["dv01"] / 1e6), 2) == 0.84
    fair = 4.210 - v / (F["dv01"] / 1e6) / 100
    assert round(fair, 3) == 4.202 and round((fair - 4.195) * 100, 1) == 0.7
    assert round(value_of_specialness(D, [(30, 0.009), (30, 0.005), (30, 0.002)]), 4) == 0.1345
    assert round(100e6 * D / 100 * 0.039 / 360) == 10_928
