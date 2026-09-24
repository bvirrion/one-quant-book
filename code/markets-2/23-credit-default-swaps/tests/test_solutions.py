"""Numbers gate: every numerical answer printed in Book 2, Chapter 23 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/cds"))
from cds_demo import IG, R, first_stage, problem, tutorial
from firm_cds import cash_settlement, hazard_from_spread

T = tutorial()
P = problem()


def test_hook():
    assert P["final"] == 8.625 and P["paid_per_100"] == 91.375
    assert (P["gross"], P["net"]) == (72e9, 5.2e9)


def test_text():
    assert cash_settlement(10e6, 40) == 6e6 and 10e6 * 0.01 / 4 == 25_000
    assert round(100 * T["lam_100"], 4) == round(100 * T["triangle_100"], 4) == 1.6667
    assert round(100 * T["surv5_100"], 1) == 92.0
    assert (round(T["annuity_100"], 3), round(T["annuity_200"], 3)) == (4.332, 4.165)
    assert round(100 * T["ig_200"], 2) == 4.16 and round(T["ig_200"] * 10e6, -3) == 416_000
    assert [round(100 * T[k], 2) for k in ("hy_300", "hy_800", "hy_1200")] == [-8.01, 9.98, 20.28]
    assert round(T["dv01_10m"], -2) == 4_300
    lams = [hazard_from_spread(IG, s, R) for s in (0.01, 0.03, 0.08)]
    assert [round(100 * x) for x in lams] == [2, 5, 13] and round(100 * lams[0], 1) == 1.7
    fs = first_stage()
    assert (fs["crossed"], fs["half"], round(fs["raw_mean"], 3), fs["imm"]) == (1, 7, 9.804, 9.75)
    assert (round(fs["sells"] / 1e3, 2), round(fs["buys"] / 1e3, 2), fs["oi"]) == (5.69, 0.77, 4920)
    assert P["cap"] == 10.75 and fs["penalty"] == 12_500


def test_exercises():
    assert round(100 * 0.03 / 0.6) == 5 and round(100 * math.exp(-0.25), 1) == 77.9
    assert round(100 * T["ig_50"], 2) == -2.21 and round(-T["ig_50"] * 10e6, -3) == 221_000
    assert 10e6 - 10e6 * 0.30 == 7e6
    lams = [hazard_from_spread(IG, s, R) for s in (0.01, 0.03, 0.08)]
    assert [round(100 * x, 4) for x in lams[:2]] == [1.6667, 5.0001] and round(100 * lams[2], 3) == 13.335
    assert [round(100 * s / 0.6, 3) for s in (0.01, 0.03, 0.08)] == [1.667, 5.0, 13.333]


def test_problem():
    assert P["final"] == 8.625 and P["all_high"] == 10.75 and P["thin"] == 8.5
    assert P["final"] - P["imm"] == -1.125
    assert (P["a_cash"], P["a_bond"]) == (18_275_000, 1_725_000) and P["a_cash"] + P["a_bond"] == 20e6
    assert P["b_cash"] == 45_687_500 and P["c_cash"] == -36_550_000
    assert (P["d_cash"], P["d_bonds"]) == (-27_412_500, 2_587_500) and -P["d_cash"] + P["d_bonds"] == 30e6
