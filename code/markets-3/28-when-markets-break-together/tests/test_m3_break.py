"""Tests of the Chapter 28 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_break as m


def test_ablation_table():
    t = {name: (round(s, 1), round(x, 2), round(c, 2)) for name, s, x, c in m.ablation_table()}
    assert t["base case"] == (223.6, 8.88, 0.99) and t["8 steps a day"] == (225.6, 8.73, 0.99)
    assert t["no margin spiral"][0] == 0.0 and t["no price impact"][1] == 4.94
    assert t["one asset per holder"][2] < 0.1


def test_correlations_and_data():
    before, after = m.correlations()
    assert round(before, 2) == 0.30 and round(after, 2) == 0.99
    d = dict((x[0], x[1]) for x in m.march_2020())
    assert d["2020-03-09"] == 0.54 and d["2020-03-18"] == 1.18
