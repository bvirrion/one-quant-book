"""Tests of the Chapter 29 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_map as m


def test_sizes_and_velocity():
    assert m.SIZES[0][1] / m.SIZES[-1][1] > 1_000
    assert round(100 * m.turnover_velocity(1_203.6, 31_800), 1) == 3.8


def test_shifts():
    assert m.shifts() == [(0, 540, 2), (480, 1020, 3), (960, 60, 3)]
    assert [x[2] for x in m.shifts(weekday=6)] == [1, 1, 1]
