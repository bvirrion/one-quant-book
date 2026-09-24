"""Tests of the Chapter 11 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_weather import winters


def test_only_complete_winters():
    ws = winters()
    assert all(n in (151, 152) for _, _, n in ws) and ws[0][0] == 1991 and ws[-1][0] == 2026
