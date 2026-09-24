"""Tests of the Chapter 2 teaching module (Book 3)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_crude import load_wti, spring_2020


def test_data_file():
    rows = load_wti()
    assert len(rows) == 9158 and rows[0][0] == dt.date(1985, 1, 2) and rows[-1][0] == dt.date(2024, 4, 5)
    assert all(a < b for a, b in zip(rows, rows[1:], strict=False) for a, b in [(a[0], b[0])])
    assert len(spring_2020()) == 63
