"""Acceptance tests of the Chapter 13 build (Python reference)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_auction import AuctionOrder as O
from firm_auction import uncross

BOOK = [O("b1", +1, 300, None, 1), O("b2", +1, 500, 1003, 2), O("b3", +1, 400, 1001, 3), O("b4", +1, 600, 1000, 4),
        O("s1", -1, 200, None, 5), O("s2", -1, 400, 999, 6), O("s3", -1, 500, 1001, 7), O("s4", -1, 700, 1002, 8)]


def test_the_chapter_example():
    u = uncross(BOOK, reference=1000)
    assert (u.price, u.volume, u.surplus) == (1001, 1100, 100)
    fills = dict(u.fills)
    assert fills["b1"] == 300 and fills["b2"] == 500 and fills["b3"] == 300      # b3 partially filled
    assert fills["s1"] == 200 and fills["s2"] == 400 and fills["s3"] == 500 and "s4" not in fills
    assert sum(q for i, q in u.fills if i.startswith("b")) == sum(q for i, q in u.fills if i.startswith("s")) == 1100


def test_no_cross_no_price():
    u = uncross([O("b", +1, 100, 990, 1), O("s", -1, 100, 1010, 2)], 1000)
    assert u.price is None and u.volume == 0


def test_market_pressure_picks_the_side_of_the_surplus():
    buy_heavy = [O("b", +1, 500, 1005, 1), O("s", -1, 200, 1000, 2)]
    assert uncross(buy_heavy, 1002).price == 1005          # surplus to buy at every candidate: highest
    sell_heavy = [O("b", +1, 200, 1005, 1), O("s", -1, 500, 1000, 2)]
    assert uncross(sell_heavy, 1002).price == 1000


def test_reference_price_breaks_a_balanced_tie():
    balanced = [O("b", +1, 300, 1006, 1), O("s", -1, 300, 1000, 2)]
    assert uncross(balanced, 1004).price == 1004       # zero surplus everywhere: the reference price wins
    assert uncross(balanced, 990).price == 1000        # reference outside the range: the nearest candidate


def test_time_priority_at_the_clearing_price():
    book = [O("early", +1, 300, 1000, 1), O("late", +1, 300, 1000, 2), O("s", -1, 400, 1000, 3)]
    assert dict(uncross(book, 1000).fills) == {"early": 300, "late": 100, "s": 400}
