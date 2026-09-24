"""Tests of the Chapter 28 demo: chart data shapes and the ordering of the routes."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from access_cost_demo import cost_curves, sensitivity


def test_cost_curves_cross_once():
    rows = cost_curves()
    order = ["rent" if r[1] < r[2] else "buy" for r in rows[1:]]
    assert order[0] == "rent" and order[-1] == "buy"
    assert sum(1 for a, b in zip(order, order[1:], strict=False) if a != b) == 1


def test_breakeven_falls_with_the_sponsor_spread():
    rows = [r for r in sensitivity() if not math.isnan(r[1])]
    assert all(a[1] > b[1] for a, b in zip(rows, rows[1:], strict=False))
