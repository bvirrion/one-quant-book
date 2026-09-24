"""Acceptance tests of the Book 3, Chapter 4 build (LNG netbacks)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_lngarb import (
    Route,
    breakeven_spread,
    choose,
    eur_mwh_to_usd_mmbtu,
    fob_price,
    lift,
    netback,
    shipping_cost,
    usd_mmbtu_to_eur_mwh,
)

EU = Route("europe", 14, 60_000, 0.001, 0.50)
ASIA = Route("asia", 28, 60_000, 0.001, 0.40)


def test_units_round_trip():
    assert math.isclose(usd_mmbtu_to_eur_mwh(eur_mwh_to_usd_mmbtu(40.0, 1.16), 1.16), 40.0)
    assert math.isclose(eur_mwh_to_usd_mmbtu(1.0, 1.0), 0.293071)


def test_longer_route_costs_more():
    assert shipping_cost(ASIA, 3.5e6, 5.0) > shipping_cost(EU, 3.5e6, 5.0)
    assert math.isclose(netback(12.0, EU, 3.5e6, 5.0), 12.0 - 0.50 - shipping_cost(EU, 3.5e6, 5.0))


def test_choice_and_breakeven():
    s = breakeven_spread(EU, ASIA, 3.5e6, 5.0)
    assert s > 0
    best, _ = choose({"europe": 12.0, "asia": 12.0 + s + 0.01}, {"europe": EU, "asia": ASIA}, 3.5e6, 5.0)
    assert best == "asia"
    best, _ = choose({"europe": 12.0, "asia": 12.0 + s - 0.01}, {"europe": EU, "asia": ASIA}, 3.5e6, 5.0)
    assert best == "europe"


def test_lift_rule():
    assert fob_price(3.0, 1.15, 2.5) == 1.15 * 3.0 + 2.5
    assert lift(3.5, 3.0) and not lift(3.4, 3.0)
