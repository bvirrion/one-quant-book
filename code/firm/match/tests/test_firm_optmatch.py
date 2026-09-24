"""Acceptance tests of the Chapter 24 build."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_optmatch import Quote, customer_priority_pro_rata, price_improvement_auction

BOOK = [Quote("mm1", 100, "mm"), Quote("cust1", 10, "customer"), Quote("dmm", 100, "mm", designated=True),
        Quote("firm", 50, "firm"), Quote("cust2", 5, "customer"), Quote("mm2", 250, "mm")]


def test_customers_first_whatever_their_time():
    f = customer_priority_pro_rata(BOOK, 12)
    assert f == {"cust1": 10, "cust2": 2}


def test_entitlement_beats_the_pro_rata_share():
    f = customer_priority_pro_rata(BOOK, 115, entitlement_pct=40)
    # 15 to customers; of the 100 left the designated maker takes 40 (its pro-rata share would be 20);
    # the other 60 are shared over 400 lots: 15, 7, 37 and the odd lot to the oldest
    assert f == {"cust1": 10, "cust2": 5, "dmm": 40, "mm1": 16, "firm": 7, "mm2": 37}
    plain = customer_priority_pro_rata(BOOK, 115)
    assert plain == {"cust1": 10, "cust2": 5, "mm1": 20, "dmm": 20, "firm": 10, "mm2": 50}


def test_auction_without_improvement():
    r = price_improvement_auction(100, 250, +1, [("a", 250, 100), ("b", 250, 100)])
    assert (r.price, r.improved, r.initiator_qty) == (250, False, 40) and r.fills == {"a": 30, "b": 30}
    one = price_improvement_auction(100, 250, +1, [("a", 250, 100)])
    assert one.initiator_qty == 50 and one.fills == {"a": 50}
    none = price_improvement_auction(100, 250, +1, [])
    assert none.initiator_qty == 100 and none.fills == {}


def test_auction_with_improvement_takes_the_order_away_from_the_initiator():
    r = price_improvement_auction(100, 250, +1, [("a", 249, 60), ("b", 250, 100), ("c", 250, 100)])
    assert r.improved and r.fills["a"] == 60 and r.initiator_qty == 40 and r.fills["b"] + r.fills["c"] == 0
    full = price_improvement_auction(100, 250, +1, [("a", 249, 70), ("b", 249, 70)])
    assert full.price == 249 and full.initiator_qty == 0 and full.fills == {"a": 50, "b": 50}
    sell = price_improvement_auction(100, 250, -1, [("a", 251, 100)])
    assert sell.price == 251 and sell.fills == {"a": 100}


def test_conservation():
    for resp in ([], [("a", 250, 7)], [("a", 249, 33), ("b", 250, 1), ("c", 250, 500)], [("a", 248, 5), ("b", 249, 5)]):
        r = price_improvement_auction(100, 250, +1, resp, book_customers=3)
        assert sum(r.fills.values()) + r.initiator_qty == 100
