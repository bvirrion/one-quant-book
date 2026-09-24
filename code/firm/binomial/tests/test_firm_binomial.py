"""Acceptance tests of the Book 5, Chapter 2 build (binomial trees)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "parity"))
from firm_binomial import params, price
from firm_parity import price as black

S, K, T, R, V = 100.0, 105.0, 0.75, 0.04, 0.25


def formula(right, q=0.0):
    return black(S * math.exp((R - q) * T), K, T, R, V, right)


@pytest.mark.parametrize("method,n", [("crr", 400), ("jr", 400), ("lr", 201)])
def test_convergence_to_formula(method, n):
    for right in ("C", "P"):
        assert abs(price(S, K, T, R, V, n, right, method=method) - formula(right)) < 0.02


def test_lr_accuracy_with_dividend_yield():
    assert abs(price(S, K, T, R, V, 101, "C", q=0.02, method="lr") - formula("C", 0.02)) < 2e-4


def test_parity_on_tree():
    c, p = price(S, K, T, R, V, 200, "C"), price(S, K, T, R, V, 200, "P")
    assert abs(c - p - (S - K * math.exp(-R * T))) < 1e-10


def test_american_call_equals_european_without_dividends():
    assert abs(price(S, K, T, R, V, 301, "C", american=True, method="lr") - price(S, K, T, R, V, 301, "C", method="lr")) < 1e-12


def test_american_put_dominates():
    am = price(S, K, T, R, V, 301, "P", american=True, method="lr")
    assert am > price(S, K, T, R, V, 301, "P", method="lr") and am >= K - S


def test_arbitrage_tree_refused():
    with pytest.raises(ValueError):
        params("crr", S, K, 1.0, 5.0, 0.0, 0.01, 1)
    with pytest.raises(ValueError):
        params("lr", S, K, T, R, 0.0, V, 100)
