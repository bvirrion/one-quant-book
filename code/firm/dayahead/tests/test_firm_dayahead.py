"""Acceptance tests of the Book 3, Chapter 5 build (day-ahead clearing)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_dayahead import BUY, SELL, Block, Order, clear, clear_with_blocks, couple, marginal_cost, spark_spread

SUPPLY = [Order(SELL, 0, 300), Order(SELL, 40, 200), Order(SELL, 90, 200), Order(SELL, 150, 100)]


def test_marginal_offer_sets_price():
    r = clear(SUPPLY + [Order(BUY, 3000, 450)])
    assert r.price == 40 and r.volume == 450
    assert math.isclose(r.welfare, 300 * 3000 + 150 * (3000 - 40))


def test_negative_price_when_inflexible_supply_exceeds_demand():
    r = clear([Order(SELL, -80, 500), Order(SELL, 30, 200), Order(BUY, 3000, 300), Order(BUY, -20, 100)])
    assert r.price == -80 and r.volume == 400        # the marginal offer is only partly filled
    with pytest.raises(ValueError):
        clear([Order(SELL, 50, 10), Order(BUY, 40, 10)])


def test_coupling_converges_or_splits():
    a = [Order(SELL, 20, 1000), Order(BUY, 3000, 500)]
    b = [Order(SELL, 80, 1000), Order(BUY, 3000, 500)]
    split = couple(a, b, 200)
    assert split["flow"] == 200 and split["price_a"] == 20 and split["price_b"] == 80
    assert math.isclose(split["rent"], 60 * 200)
    same = couple(a, b, 800)
    assert math.isclose(same["price_a"], same["price_b"]) and 499 <= same["flow"] <= 500


def test_block_not_paradoxically_accepted():
    hours = {h: [Order(SELL, 50, 100), Order(BUY, 3000, 80 + 40 * h)] for h in range(3)}
    res = clear_with_blocks(hours, [Block("cheap", 30, 60, (0, 1, 2)), Block("dear", 70, 60, (0, 1, 2))])
    assert res["accepted"] == ["cheap"]
    assert all(p >= 30 for p in res["prices"].values())


def test_costs():
    assert math.isclose(marginal_cost(30, 0.5, 0.2, 80), (30 + 16) / 0.5)
    assert math.isclose(spark_spread(100, 35, 0.5), 30)
