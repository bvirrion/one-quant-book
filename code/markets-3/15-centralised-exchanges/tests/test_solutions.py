"""Numbers in the solutions of Book 3, Chapter 15."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_cex as m


def test_exercises():
    assert 50e6 / 2 * (0.001 + 0.001) == 50_000
    assert round(50e6 / 2 * (0.00011 + 0.00023)) == 8_500
    assert math.ceil(math.log2(2_000_000)) == 21
    assert round(m.omitted(0.01, 100), 3) == 0.634
    assert round(100 * (270 + 310) / 6_991, 1) == 8.3
    assert 1023 - m.fake_negative(m.customers(), 0.02, 0)[3] == 15


def test_problem():
    assert round(100 * 694 / 10_544, 1) == 6.6 and round(100 * 1_078 / 10_544, 1) == 10.2
    assert round(100 * 1 / 1_591, 2) == 0.06 and round(100 * 6 / 1_591, 1) == 0.4
    assert round(100 * 2_540 / 11_233, 1) == 22.6 and 11_233 - 2_540 == 8_693
    assert 3_306 == max([398, 167, 520, 136, 180, 1_848, 3_306, 410, -17, 21, 44])
