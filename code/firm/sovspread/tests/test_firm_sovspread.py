"""Acceptance tests of the Book 2, Chapter 7 build (sovereign spread monitor)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_sovspread import alerts, decompose, spreads, zscore


def test_spreads_in_bp_on_common_dates():
    y = {"DE": [("a", 2.0), ("b", 2.1)], "IT": [("a", 3.5), ("b", 3.4), ("c", 3.3)]}
    assert spreads(y, "DE") == {"IT": [("a", pytest.approx(150.0)), ("b", pytest.approx(130.0))]}


def test_decomposition_adds_up_and_signs():
    d = decompose({"s": 5.0, "e": 6.0}, {"s": 2.0, "e": 1.5}, "s", "e")
    assert d.change_bp == pytest.approx(150.0)
    assert d.issuer_bp == pytest.approx(100.0) and d.benchmark_bp == pytest.approx(50.0)
    assert d.issuer_bp + d.benchmark_bp == pytest.approx(d.change_bp)


def test_zscore_and_alerts():
    s = [(str(k), 100.0 + (k % 2)) for k in range(30)] + [("jump", 110.0)]
    z = dict(zscore(s, 20))
    assert abs(z["29"]) < 1.5 and z["jump"] > 10
    assert alerts(s, 20, 3.0) == ["jump"]
