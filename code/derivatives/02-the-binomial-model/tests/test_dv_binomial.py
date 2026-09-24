"""Unit tests of the Chapter 2 teaching module."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_binomial import terminal_law, whiteboard


def test_terminal_law_is_a_probability_with_the_right_mean():
    x, w = terminal_law(50)
    assert abs(w.sum() - 1) < 1e-12
    assert abs((w * np.exp(x)).sum() - np.exp(0.05)) < 1e-12       # share grows at r under Q


def test_american_call_equals_european_without_dividends():
    w = whiteboard()
    assert w["am_put"] >= w["put"]
