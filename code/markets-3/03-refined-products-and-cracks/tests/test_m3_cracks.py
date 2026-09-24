"""Tests of the Chapter 3 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_cracks import load_products, seasonality


def test_data_file():
    rows = load_products()
    assert len(rows) == 242 and rows[0]["month"] == "2006-07" and rows[-1]["month"] == "2026-08"


def test_seasonality_sums_to_zero():
    s = seasonality()
    assert abs(sum(g for _, g, _ in s)) < 1e-6
