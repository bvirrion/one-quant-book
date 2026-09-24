"""Tests of the Chapter 8 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_metals import NICKEL


def test_timeline_is_ordered():
    hours = [h for _, h, _ in NICKEL]
    assert hours == sorted(hours) and max(p for *_, p in NICKEL) == 101_365
