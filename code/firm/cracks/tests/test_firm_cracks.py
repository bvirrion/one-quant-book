"""Acceptance tests of the Book 3, Chapter 3 build (cracks and margins)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_cracks import (
    arbitrage_open,
    barrels_per_tonne,
    crack,
    gross_refining_margin,
    hedge_lots,
    per_tonne_to_per_barrel,
    three_two_one,
)


def test_units():
    assert math.isclose(barrels_per_tonne(0.845), 7.4435, abs_tol=1e-4)     # ICE gasoil density
    assert math.isclose(per_tonne_to_per_barrel(744.35, 0.845), 100.0, rel_tol=1e-4)


def test_three_two_one_is_a_crack():
    c = three_two_one(80.0, 2.50, 3.00)
    assert math.isclose(c, (2 * 105.0 + 126.0 - 240.0) / 3)
    with pytest.raises(ValueError):
        crack(80.0, {"g": 100.0}, {"g": 2}, 3)


def test_margin_with_processing_gain():
    m = gross_refining_margin(80.0, {"g": 0.47, "d": 0.30, "o": 0.30}, {"g": 100.0, "d": 110.0, "o": 60.0})
    assert math.isclose(m, 47 + 33 + 18 - 80)


def test_hedge_lots_balance():
    lots = hedge_lots(90_000, 92, {"gasoline": 2, "diesel": 1}, 3)
    assert lots == {"crude": 8280, "gasoline": -5520, "diesel": -2760}
    assert lots["crude"] + lots["gasoline"] + lots["diesel"] == 0


def test_arbitrage():
    assert arbitrage_open(2.50, 2.62, 0.08) > 0 and arbitrage_open(2.50, 2.55, 0.08) < 0
