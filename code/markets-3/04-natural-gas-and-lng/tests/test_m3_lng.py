"""Tests of the Chapter 4 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_lng import history, load_gas


def test_data_file():
    rows = load_gas()
    assert len(rows) == 319 and rows[0]["month"] == "2000-01" and rows[-1]["month"] == "2026-07"


def test_history_is_monthly():
    h = history()
    assert h[0]["month"] == "2016-03" and len({c["month"] for c in h}) == len(h)
