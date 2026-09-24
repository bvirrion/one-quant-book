"""Tests of the Chapter 7 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_carbon import switching_curve


def test_switching_price_rises_with_gas():
    c = [p for _, p in switching_curve([10, 20, 30, 40, 50])]
    assert all(a < b for a, b in zip(c, c[1:], strict=False))
