"""Numbers gate: every numerical answer printed in Book 9, chapter 16 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_sysmacro import correlations, stats, years  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_stats():
    s = stats()
    assert {k: r(v["sr"]) for k, v in s.items()} == {
        "value": 0.84, "reversal": -0.84, "momentum": 0.78, "carry": 0.33, "surprise": 0.29, "combined": 1.15,
        "combined, price value": 0.31, "combined, no value": 0.81}
    assert {k: round(100 * v["max_dd"]) for k, v in s.items() if k in ("value", "momentum", "carry", "surprise", "combined")} == {
        "value": -25, "momentum": -23, "carry": -32, "surprise": -38, "combined": -21}
    assert r(years(), 1) == 24.5


def test_correlations():
    c = correlations()
    assert r(c[1, 2]) == -0.43 and np.abs(c[np.triu_indices(5, 1)][[0, 1, 2, 3, 5, 6, 7, 8, 9]]).max() < 0.06
    assert r((0.84 + 0.78 + 0.33 + 0.29) / math.sqrt(4)) == 1.12


def test_exercises():
    from s2_sysmacro import noisy_anchor
    n = noisy_anchor()
    assert (r(n["value"]), r(n["combined"])) == (0.69, 1.05)
    assert (r((0.84 + 0.78) / math.sqrt(2 + 2 * -0.43)), round(100 * (1 - 0.5 ** (1 / 3))), 3 * 21) == (1.52, 21, 63)
