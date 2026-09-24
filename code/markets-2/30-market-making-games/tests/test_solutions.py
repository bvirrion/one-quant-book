"""Numbers gate: every numerical answer printed in Book 2, Chapter 30 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/mmgame"))
from firm_mmgame import Table, expected_pnl
from mmgame_demo import FINE, curves, distribution, first_trade, one_game, problem

F = first_trade()
P = problem()


def test_text():
    d = dict(distribution())
    assert (min(d), max(d)) == (6, 64)
    assert F["mean"] == 35.0 and round(F["sd"], 2) == 8.03
    assert round(math.exp(-10 / 8), 2) == 0.29 and round(F["p_informed_given_buy"], 2) == 0.31
    assert (round(F["after_buy"], 2), round(F["after_sell"], 2), round(F["after_pass"], 2)) == (38.13, 31.87, 35.0)
    value, mids, pnl = one_game()
    assert value == 31 and round(pnl, 1) == 18.6 and round(max(mids)) == 39
    assert (P["width"], round(P["pnl"], 1)) == (11.5, 16.4)
    assert (round(P["pnl_8"], 1), round(P["pnl_15"], 1)) == (14.1, 15.1)
    assert (P["width_naive"], round(P["pnl_naive"], 1)) == (14.0, 12.0)
    assert round(20 * 4 * math.exp(-1), 1) == 29.4 and round(P["no_informed_8"], 1) == 28.6


def test_exercises():
    assert round(4 * math.exp(-1), 2) == 1.47
    d = dict(distribution())
    above = sum(p for s, p in d.items() if s > 40)
    assert round(100 * above) == 25 and round(100 * 0.2 * above) == 5
    assert round(100 * 0.8 * math.exp(-10 / 8) / 2, 1) == 11.5
    for pi, w, pnl in ((0.3, 12.5, 13.8), (0.1, 11.0, 20.6)):
        best = max(expected_pnl(FINE, Table(informed=pi), 2000, 30), key=lambda x: x[1])
        assert (best[0], round(best[1], 1)) == (w, pnl)
    assert round(curves()["learn20"][0][1]) == -22


def test_problem():
    assert round(math.exp(-10 / 8) * 5, 2) == 1.43 and round(P["trade_prob"], 2) == 0.24
