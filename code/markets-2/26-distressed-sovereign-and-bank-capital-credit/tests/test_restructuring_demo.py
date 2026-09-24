"""Tests of the Chapter 26 demo: chart data and the shape of the holdout curve."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from restructuring_demo import CAC, holdout_curve, offer_curve


def test_offer_curve_decreasing():
    rows = offer_curve()
    assert all(a[1] > b[1] and a[2] > b[2] for a, b in zip(rows, rows[1:], strict=False))
    assert all(abs(a - b - 5.0) < 1e-9 for _, a, b in rows)


def test_holdout_curve_jumps_at_the_cac():
    rows = holdout_curve()
    below = [r for r in rows if r[0] < 100 * CAC]
    above = [r for r in rows if r[0] >= 100 * CAC]
    assert all(r[1] == r[2] for r in below) and all(r[1] < r[3] for r in above)
    assert all(a[2] <= b[2] for a, b in zip(rows, rows[1:], strict=False))
