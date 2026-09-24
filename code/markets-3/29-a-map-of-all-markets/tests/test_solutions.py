"""Numbers in the solutions of Book 3, Chapter 29."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_map as m


def test_exercises():
    assert round(100 * 1_203.6 / 31_800, 1) == 3.8
    assert (math.ceil(24 / 7), math.ceil(24 / 11)) == (4, 3)
    assert len(m.shifts(8, 1)) == 4 and len(m.shifts(12, 1)) == 3
    assert sum(x[2] for x in m.shifts()) == 8 and sum(x[2] for x in m.shifts(weekday=6)) == 3


def test_problem():
    s = m.shifts()
    assert [(a // 60, b // 60) for a, b, _ in s] == [(0, 9), (8, 17), (16, 1)]
    assert 5 * 8 + 2 * 3 == 46
    assert round(17.65 / (96_462.544 * 83_500 / 1e9), 1) == 2.2
