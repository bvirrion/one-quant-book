"""Acceptance tests of the Book 5, Chapter 6 build (American options)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "binomial"))
from firm_american import baw, bermudan_put, dividend_threshold, exercise_decision, put_boundary
from firm_binomial import price as tree


@pytest.mark.parametrize("s,k,t,r,q,v", [(100, 100, 1, 0.05, 0.0, 0.2), (90, 100, 0.5, 0.08, 0.0, 0.3),
                                         (110, 100, 0.25, 0.03, 0.0, 0.25), (100, 100, 1, 0.05, 0.04, 0.25)])
def test_quadratic_close_to_tree(s, k, t, r, q, v):
    for right in ("P", "C"):
        assert abs(baw(s, k, t, r, q, v, right)[0] - tree(s, k, t, r, v, 2001, right, american=True, q=q, method="lr")) < 0.07


def test_boundary_tends_to_perpetual_limit():
    g = 2 * 0.05 / 0.04
    long = put_boundary(100.0, 20.0, 0.05, 0.0, 0.2, n=4000)
    assert abs(long[0][1] - 100 * g / (1 + g)) < 1.5 and put_boundary(100.0, 1.0, 0.05, 0.0, 0.2)[-1][1] > 99


def test_bermudan_monotone_between_bounds():
    vals = [bermudan_put(100.0, 100.0, 1.0, 0.05, 0.2, m) for m in (1, 2, 4, 12, 50, 200)]
    assert all(b >= a - 1e-12 for a, b in zip(vals, vals[1:], strict=False)) and vals[-1] < 6.0902 + 0.005


def test_threshold_just_above_interest_on_strike():
    d = dividend_threshold(100.30, 80.0, 29 / 365, 0.04, 0.25)
    interest = 80 * (1 - math.exp(-0.04 * 29 / 365))
    assert interest < d < interest + 0.01
    assert exercise_decision(100.30, 80.0, d + 1e-6, 29 / 365, 0.04, 0.25)["exercise_now"]
    assert not exercise_decision(100.30, 80.0, d - 1e-6, 29 / 365, 0.04, 0.25)["exercise_now"]
