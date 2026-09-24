"""Acceptance tests of the Book 3, Chapter 6 build (balancing group)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_balancing import BalancingGroup, capture_price, day_settlement, imbalance, settle


def test_balanced_producer():
    g = BalancingGroup()
    g.schedule_production(10, 100.0)
    g.trade(10, -100.0, 80.0)
    assert g.schedule(10) == 0.0 and g.cash[10] == 8000.0


def test_imbalance_sign_and_settlement():
    assert imbalance(100.0, -100.0, 70.0) == -30.0               # produced 30 short
    assert settle(-30.0, 200.0) == -6000.0                       # buys 30 MWh at 200
    assert settle(20.0, 50.0, 120.0) == 1000.0 and settle(-20.0, 50.0, 120.0) == -2400.0


def test_day_settlement_and_capture():
    d = day_settlement({1: (100.0, 60.0), 2: (80.0, 70.0)}, {1: 90.0, 2: 85.0}, {1: 150.0, 2: 20.0})
    assert math.isclose(d["revenue"], 6000 + 5600) and math.isclose(d["imbalance"], -1500 + 100)
    assert math.isclose(capture_price([10.0, 50.0], [3.0, 1.0]), 20.0)
    with pytest.raises(ValueError):
        capture_price([10.0], [0.0])
