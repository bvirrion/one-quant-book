"""Acceptance tests of the Book 6, chapter 9 build (Bermudans and callables)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "shortrate"))
from firm_bermudan import bermudan_lsm, bermudan_tree, callable_zero_tree, exercise_boundary, switch_option
from firm_shortrate import HullWhite, HWTree


class Sloped:
    def df_t(self, t):
        return math.exp(-(0.02 + 0.001 * t) * t)


C = Sloped()
M = HullWhite(C, 0.03, [0.008])
TREE = HWTree(C, 0.03, 0.008, 6.0, 1 / 24)
K = (1 - C.df_t(6.0)) / sum(C.df_t(float(i)) for i in range(1, 7))


def test_single_exercise_is_the_european_and_bermudan_dominates():
    euros = [bermudan_tree(TREE, [e], 6, K) for e in (1, 2, 3, 4, 5)]
    for e, v in zip((1, 2, 3, 4, 5), euros, strict=True):
        assert v == pytest.approx(M.swaption(e, 6 - e, K, payer=False), rel=1e-2)
    berm = bermudan_tree(TREE, [1, 2, 3, 4, 5], 6, K)
    assert max(euros) < berm < sum(euros)
    assert switch_option(berm, euros) == pytest.approx(berm - max(euros))


def test_regression_monte_carlo_is_close_to_the_tree():
    berm = bermudan_tree(TREE, [1, 2, 3, 4, 5], 6, K)
    price, se = bermudan_lsm(M, [1, 2, 3, 4, 5], 6, K, paths=40000)
    assert abs(price - berm) < 4 * se + 0.01 * berm


def test_callable_zero_limits_and_boundary():
    tree = HWTree(C, 0.03, 0.008, 10.0, 1 / 12)
    r = callable_zero_tree(tree, 10, 0.2, [3, 5])                 # accretes far above rates: called at year 3
    assert r["callable"] == pytest.approx(1.2**3 * C.df_t(3.0), rel=1e-9)
    assert r["straight"] == pytest.approx(1.2**10 * C.df_t(10.0), rel=1e-9)
    lo = callable_zero_tree(tree, 10, 0.0, [3, 5])      # accretes at zero: called only if rates go negative
    assert 0.0 < lo["option"] < 1e-3 and lo["callable"] < lo["straight"]
    b = exercise_boundary(TREE, [1, 2, 3, 4, 5], 6, K)
    assert all(rate < K for _, rate in b)
