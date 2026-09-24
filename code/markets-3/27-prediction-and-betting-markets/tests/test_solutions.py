"""Numbers in the solutions of Book 3, Chapter 27."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_betting as m
from firm_odds import hedge_equal, multiplicative, overround, power


def test_exercises():
    assert round(100 * overround([1.8, 2.1]), 2) == 3.17
    assert [round(100 * x, 2) for x in multiplicative([1.8, 2.1])] == [53.85, 46.15]
    lay, win, lose = hedge_equal(100, 3.0, 2.5)
    assert lay == 120 and round(win) == round(lose) == 20
    assert [round(100 * x, 2) for x in power([1.5, 4.0, 7.0])] == [64.82, 22.71, 12.48]
    assert round(100 * m.kelly_stake(), 1) == 16.7
    b = m.flb_book()
    r13 = [x for o, x in b if 1 <= o < 3]
    assert round(100 * sum(r13) / len(r13), 2) == -3.14
    assert round(100 * dict((k, r) for k, r, _ in m.returns_by_odds(b))["50-1000"], 2) == -42.06


def test_problem():
    g = m.election_gap()
    assert round(g["cost"], 3) == 0.975 and round(g["profit"], 4) == 0.0214
    assert round(100 * g["breakeven_gap"], 2) == 1.86
    assert round(10_000 * g["profit"]) == 214 and round(10_000 * g["cost"]) == 9_750
    assert round(100 * (0.65 / 0.58 - 1), 1) == 12.1
