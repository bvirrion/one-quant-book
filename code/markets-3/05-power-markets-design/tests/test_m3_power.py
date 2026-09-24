"""Tests of the Chapter 5 teaching module (Book 3)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_power import load_de, to_berlin


def test_data_file_is_two_full_years():
    rows = load_de()
    assert len(rows) == 8784 + 8760
    assert to_berlin(rows[0][0]) == dt.datetime(2024, 1, 1, 0, 0) and to_berlin(rows[-1][0]) == dt.datetime(2025, 12, 31, 23, 0)
    assert all((b[0] - a[0]) == dt.timedelta(hours=1) for a, b in zip(rows, rows[1:], strict=False))


def test_dst_switch():
    assert to_berlin(dt.datetime(2025, 3, 30, 0, 59)).hour == 1 and to_berlin(dt.datetime(2025, 3, 30, 1, 0)).hour == 3
    assert to_berlin(dt.datetime(2025, 10, 26, 1, 0)).hour == 2
