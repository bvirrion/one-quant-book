"""Tests of the Chapter 31 demo: data files and chart data."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from macro_demo import curve_rows, daily, payroll_dates, payroll_moves


def test_data_files():
    dates, y2, y10 = daily()
    assert dates == sorted(dates) and len(dates) == len(y2) == len(y10)
    assert len(payroll_dates()) == 44 and "2025-10-03" not in payroll_dates()
    assert all(r["date"] >= "2025-09-02" for r in curve_rows())


def test_payroll_moves_cover_every_release():
    assert len(payroll_moves()) == 44
