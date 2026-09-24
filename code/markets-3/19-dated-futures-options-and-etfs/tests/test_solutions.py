"""Numbers in the solutions of Book 3, Chapter 19."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_etf as m


def test_exercises():
    assert round(100 * (85_669 / 83_499 - 1) * 365 / 183, 2) == 5.18
    assert round(100 * math.log(85_669 / 83_499) * 365 / 183, 2) == 5.12
    assert round(0.0492 * 84_539) == 4_159
    assert round(0.1042 - 0.0505, 4) == 0.0537 and round(1 - 80_000 / 84_539, 4) == 0.0537
    assert round(10 - 0.25 - 0.30, 2) == 9.45
    best = max(m.delta_table(), key=lambda r: r[4])
    assert best[0] == 70_000


def test_problem():
    assert round(0.0495 * 200e6) == 9_900_000 and round(0.35 * 200e6) == 70_000_000
    assert round(-0.0013 * 200e6) == -260_000
    assert round(100 * (0.045 + 0.0025 + 0.003), 2) == 5.05
    assert round(0.0495 / 0.50 * 100, 1) == 9.9
    assert round(0.01 * 200e6) == 2_000_000
    assert round(0.10 * 11 / 12 * 200e6 / 1e6, 1) == 18.3
    assert round((180 - 0.9 * 140), 0) == 54
