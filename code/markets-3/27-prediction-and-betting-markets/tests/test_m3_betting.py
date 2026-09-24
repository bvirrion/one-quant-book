"""Tests of the Chapter 27 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_betting as m


def test_methods_table():
    t = {k: [round(100 * x, 2) for x in v] for k, v in m.methods().items()}
    assert t["multiplicative"] == [62.92, 23.60, 13.48] and t["power"] == [64.82, 22.71, 12.48]
    assert t["shin"] == [64.23, 23.15, 12.62]


def test_flb_monotone_in_the_tail():
    r = [x for _, x, _ in m.returns_by_odds(m.flb_book())]
    assert r[0] > r[3] > r[4] > r[6] and r[6] < -0.4


def test_gap_and_kelly():
    g = m.election_gap()
    assert round(g["cost"], 3) == 0.975 and round(g["profit"], 4) == 0.0214 and round(g["breakeven_gap"], 4) == 0.0186
    assert round(m.kelly_stake(), 4) == 0.1667
