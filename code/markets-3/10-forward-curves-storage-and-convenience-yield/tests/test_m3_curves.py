"""Tests of the Chapter 10 teaching module (Book 3)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_curves import front, index_series, month_index


def test_front_contract_around_april_2020():
    assert front(dt.date(2020, 4, 21)) == month_index(2020, 5)
    assert front(dt.date(2020, 4, 22)) == month_index(2020, 6)


def test_index_is_positive_through_2020():
    s = index_series()
    assert all(v > 0 for _, v, _ in s)
