"""Numbers gate: every numerical answer printed in Book 2, Chapter 29 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/sizing"))
from firm_sizing import drawdown_probability, fraction_for_drawdown, growth, kelly_fraction, shrinkage
from sizing_demo import coin_table, drawdown_table, problem, zero_growth_fraction

P = problem()
COIN = {r["c"]: r for r in coin_table()}
DD = {c: (t, s) for c, t, s in drawdown_table()}


def test_text():
    assert abs(kelly_fraction(0.6) - 0.2) < 1e-12 and round(100 * growth(0.2, 0.6), 2) == 2.01
    assert round(25 * 1.04 ** 300 / 1e6, 1) == 3.2 and round(25 * math.exp(300 * growth(0.2, 0.6))) == 10_504
    assert round(zero_growth_fraction(), 3) == 0.389
    assert round(COIN[1.0]["median"]) == 10_504 and round(COIN[0.5]["median"]) == 2_279
    assert (round(COIN[0.5]["p10"]), round(COIN[1.0]["p10"])) == (251, 121)
    assert 0.45 < COIN[2.0]["below"] < 0.55 and COIN[2.0]["median"] < 25
    assert (round(100 * DD[1.0][1], 1), round(100 * DD[0.5][1], 1)) == (48.4, 11.1)
    assert round(100 * drawdown_probability(0.5, 0.5), 1) == 12.5
    assert round(fraction_for_drawdown(0.5, 0.1), 2) == 0.46
    assert round(shrinkage(1, 1.0), 1) == 0.5 and round(shrinkage(9, 1.0), 1) == 0.9
    assert round(P["c_star"], 3) == 0.669 and P["c_sim"] == 0.7
    assert round(100 * (1 - P["g_full"] / P["g_best"])) == 19


def test_exercises():
    assert abs(kelly_fraction(0.4, 2.0) - 0.1) < 1e-12 and abs(0.4 * 2 - 0.6 - 0.2) < 1e-12
    assert (2 * 0.5 - 0.25, 2 * 0.25 - 0.0625) == (0.75, 0.4375)
    assert (round(drawdown_probability(1.0, 0.2), 3), round(drawdown_probability(0.5, 0.2), 3)) == (0.2, 0.008)
    assert round(fraction_for_drawdown(0.8, 0.1), 2) == 0.18
    assert (round(100 * COIN[0.5]["hit_cap"], 1), round(100 * COIN[1.0]["hit_cap"], 1)) == (94.2, 93.7)


def test_problem():
    assert round(P["kelly"], 6) == 0.1 and round(100 * growth(0.1, 0.55), 3) == 0.501
    assert (round(P["mu"], 6), round(P["s"], 3), round(P["sharpe"], 4)) == (0.1, 0.995, 0.1005)
    assert P["p_dd_full"] == 0.5
    assert round(P["se"], 4) == 0.0704 and round(P["t"], 2) == 1.42
    assert (round(1e4 * P["g_full"], 1), round(1e4 * P["g_best"], 1)) == (29.1, 35.9)
    assert round(100 * P["p_dd_c"]) == 25
    assert (round(shrinkage(50, P["sharpe"]), 2), round(shrinkage(2000, P["sharpe"]), 2)) == (0.34, 0.95)
