"""Acceptance tests of the Book 3, Chapter 1 build (physical deal model)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_physdeal import (
    Leg,
    cost_split,
    exposure,
    fixed_fraction,
    formula_price,
    hedge_trades,
    locked_margin,
    netback,
    pricing_days,
)


def test_pricing_days_around_bill_of_lading():
    assert pricing_days(10, 2, 2) == [8, 9, 10, 11, 12]
    assert pricing_days(10, 0, 5, include_event=False) == [11, 12, 13, 14, 15]


def test_formula_price_and_missing_day():
    a = {d: 80.0 + d for d in range(20)}
    assert math.isclose(formula_price(a, [8, 9, 10, 11, 12], 0.5), 90.5)
    with pytest.raises(ValueError):
        formula_price(a, [25], 0.0)


def test_exposure_builds_and_unwinds():
    buy = Leg(+1, 700_000, tuple(pricing_days(10, 2, 2)), 0.2)
    sell = Leg(-1, 700_000, tuple(pricing_days(30, 2, 2)), 1.1)
    assert exposure([buy, sell], 5) == 0.0                    # both floating
    assert math.isclose(fixed_fraction(buy, 9), 0.4)
    assert exposure([buy, sell], 12) == 700_000              # purchase fully priced, sale floating
    assert exposure([buy, sell], 40) == 0.0                   # both priced


def test_hedge_offsets_exposure_every_day():
    buy = Leg(+1, 700_000, tuple(pricing_days(10, 2, 2)), 0.2)
    sell = Leg(-1, 700_000, tuple(pricing_days(30, 2, 2)), 1.1)
    trades = hedge_trades([buy, sell])
    assert sum(trades.values()) == 0 and trades[8] == -140 and trades[32] == 140
    held = 0
    for d in range(45):
        held += trades.get(d, 0)
        assert math.isclose(held * 1_000 + exposure([buy, sell], d), 0.0)


def test_incoterms_and_netback():
    assert cost_split("FOB", 1.5, 0.05) == {"seller": 0.0, "buyer": 1.55}
    assert cost_split("CIF", 1.5, 0.05) == {"seller": 1.55, "buyer": 0.0}
    with pytest.raises(ValueError):
        cost_split("DDP", 1.0, 0.0)
    assert math.isclose(netback(80.0, 1.5, 0.05, 0.001), 80.0 * 0.999 - 1.55)
    assert math.isclose(locked_margin(Leg(1, 1, (0,), 0.2), Leg(-1, 1, (1,), 1.1), 0.65, 0.03), 0.22)
