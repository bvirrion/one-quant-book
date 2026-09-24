"""Acceptance tests of the Chapter 19 build."""
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_match import Quote, Resting, best_of, configurable, fifo, implied_in, implied_out_front, pro_rata

BOOK = [Resting("a", 10, top=True), Resting("b", 200), Resting("c", 40, lmm=True), Resting("d", 250)]


def test_fifo_walks_the_queue():
    assert fifo(BOOK, 100) == {"a": 10, "b": 90}
    assert fifo(BOOK, 1000) == {"a": 10, "b": 200, "c": 40, "d": 250}


def test_pro_rata_floors_then_gives_leftovers_by_time():
    # 100 * (10, 200, 40, 250) / 500 = 2, 40, 8, 50 exactly
    assert pro_rata(BOOK, 100) == {"a": 2, "b": 40, "c": 8, "d": 50}
    # 33 lots: floors 0, 13, 2, 16 = 31; the 2 left over go to the oldest orders
    assert pro_rata(BOOK, 33) == {"b": 13, "c": 2, "d": 16, "a": 2}
    # with a minimum of 3 lots, c's 2 lots are dropped and redistributed by time
    assert pro_rata(BOOK, 33, min_alloc=3) == {"b": 13, "d": 16, "a": 4}


def test_configurable_split():
    got = configurable(BOOK, 100, top_pct=10, lmm_pct=10, fifo_pct=40)
    # top: a gets 10; lmm: c gets 10; left 80: 32 by time -> b; 48 pro rata over open (0, 168, 30, 250) = 448
    assert got["a"] == 10 and got["c"] >= 10 and sum(got.values()) == 100
    assert got["b"] == 32 + 48 * 168 // 448 + 1                     # the single leftover lot goes to the oldest open order


def test_conservation_and_bounds_on_random_books():
    rng = random.Random(19)
    for _ in range(300):
        book = [Resting(str(i), rng.randint(1, 300), lmm=rng.random() < 0.2, top=(i == 0)) for i in range(rng.randint(1, 8))]
        qty = rng.randint(1, 1200)
        for algo in (fifo, pro_rata, lambda b, q: configurable(b, q, 15, 10, 30, 2)):
            fills = algo(book, qty)
            assert sum(fills.values()) == min(qty, sum(o.qty for o in book))
            assert all(0 < fills[o.oid] <= o.qty for o in book if o.oid in fills)


def test_implied_prices():
    front, back = Quote(10050, 30, 10052, 25), Quote(10020, 40, 10023, 10)
    imp = implied_in(front, back)
    assert imp == Quote(27, 10, 32, 25)
    direct = Quote(28, 5, 32, 7)
    assert best_of(direct, imp) == Quote(28, 5, 32, 32)
    out = implied_out_front(Quote(28, 5, 31, 7), back)
    assert out == Quote(10048, 5, 10054, 7)
    assert implied_in(Quote(None, 0, 10052, 25), back).bid is None
