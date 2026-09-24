"""Tests of the Chapter 12 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_options import vanilla_vs_average


def test_apo_about_half_the_vanilla():
    v = vanilla_vs_average()
    assert 0.4 < v["apo"] / v["vanilla"] < 0.6
