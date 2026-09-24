"""Acceptance tests of the Chapter 1 build. A reader's own ledger must pass them."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_ledger import Entry, Ledger, to_units


def test_sub_cent_amounts_add_exactly():
    led = Ledger()
    for i in range(10_000):
        led.post(Entry(i, "desk.mm", "rebate", "USD", to_units(0.0020)))
    assert led.balance("desk.mm") == to_units(20.0)


def test_categories_and_prefixes():
    led = Ledger()
    led.post(Entry(1, "desk.mm.equities", "spread", "USD", to_units(12.5)))
    led.post(Entry(2, "desk.mm.equities", "fee", "USD", to_units(-3.0)))
    led.post(Entry(3, "desk.arb", "spread", "USD", to_units(1.0)))
    led.post(Entry(4, "desk.mm.equities", "spread", "EUR", to_units(9.0)))
    assert led.by_category("desk.mm") == {"spread": to_units(12.5), "fee": to_units(-3.0)}
    assert led.balance("desk") == to_units(10.5)
    assert led.balance("desk", "EUR") == to_units(9.0)


def test_rejects_bad_entries():
    led = Ledger()
    with pytest.raises(ValueError):
        led.post(Entry(1, "a", "bribe", "USD", 1))
    with pytest.raises(ValueError):
        led.post(Entry(1, "a", "fee", "usd", 1))
    with pytest.raises(TypeError):
        led.post(Entry(1, "a", "fee", "USD", 0.5))
    led.post(Entry(5, "a", "fee", "USD", 1))
    with pytest.raises(ValueError):
        led.post(Entry(4, "a", "fee", "USD", 1))


def test_rounding_is_symmetric():
    assert to_units(0.00005) == 1 and to_units(-0.00005) == -1
