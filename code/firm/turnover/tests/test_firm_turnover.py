"""Acceptance tests of the Chapter 27 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_turnover import MarketStats, activity_kept, contracts_after_lot_change, ranking, shares

A = MarketStats("small weekly index options", "option", 100e9, 25, 22_000.0, 40.0, 0.012)
B = MarketStats("large index options", "option", 0.9e9, 100, 5_500.0, 18.0, 1.0)
C = MarketStats("index futures", "future", 0.5e9, 50, 5_500.0, 0.0, 1.0)


def test_units():
    assert A.notional_usd == pytest.approx(100e9 * 25 * 22_000 * 0.012)
    assert B.premium_usd == pytest.approx(0.9e9 * 100 * 18.0) and C.premium_usd == 0.0
    assert A.premium_to_notional_bp == pytest.approx(18.18, abs=0.01)


def test_three_measures_three_rankings():
    ms = [A, B, C]
    assert ranking(ms, "contracts")[0] == A.name
    assert ranking(ms, "premium_usd")[0] == B.name
    assert sum(shares(ms, "notional_usd").values()) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        shares([C], "premium_usd")


def test_lot_change_arithmetic():
    assert contracts_after_lot_change(90e9, 25, 75) == pytest.approx(30e9)
    assert activity_kept(90e9, 24e9, 25, 75) == pytest.approx(0.8)
