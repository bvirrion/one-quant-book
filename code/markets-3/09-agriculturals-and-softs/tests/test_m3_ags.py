"""Tests of the Chapter 9 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_ags import load_ags, load_cot


def test_data_files():
    c = load_cot()
    assert len(c) == 559 and c[0]["date"] == "2016-01-05" and c[-1]["date"] == "2026-09-15"
    assert all(r["open_interest"] > 0 for r in c)
    a = load_ags()
    assert len(a) == 319 and a[0][0] == "2000-01" and a[-1][0] == "2026-07"
