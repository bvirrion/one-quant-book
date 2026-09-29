"""Numbers gate: every answer of Book 18, chapter 21 against a brute-force oracle on random inputs."""
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import iv_oracles as oracle
from iv_algos import (
    PriceLevels,
    RollingMedian,
    WindowStats,
    arbitrage_cycle,
    best_k_trades,
    best_trade,
    first_at_or_after,
    first_duplicate,
    max_open,
    merge_halts,
    merge_tapes,
    pair_sum,
    sliding_max,
    top_k,
)

SEEDS = range(300)


def test_q1_pair_sum():
    assert pair_sum([5, 1, 7, 3], 10) == (2, 3)
    for s in SEEDS:
        r = random.Random(s)
        xs = [r.randint(0, 20) for _ in range(r.randint(0, 15))]
        t = r.randint(0, 40)
        got = pair_sum(xs, t)
        assert (got is not None) == oracle.pair_sum(xs, t)
        if got:
            i, j = got
            assert i < j and xs[i] + xs[j] == t


def test_q2_first_duplicate():
    assert first_duplicate([4, 9, 2, 9, 4]) == 9 and first_duplicate([1, 2]) is None


def test_q3_merge():
    for s in SEEDS:
        r = random.Random(s)
        a = sorted((r.randint(0, 50), "a") for _ in range(r.randint(0, 10)))
        b = sorted((r.randint(0, 50), "b") for _ in range(r.randint(0, 10)))
        assert merge_tapes(a, b) == sorted(a + b, key=lambda x: (x[0], x[1] != "a"))


def test_q4_best_trade():
    assert best_trade([7, 1, 5, 3, 6, 4]) == 5 and best_trade([5, 4, 3]) == 0
    for s in SEEDS:
        r = random.Random(s)
        xs = [r.randint(0, 30) for _ in range(r.randint(0, 12))]
        brute = max([xs[j] - xs[i] for i in range(len(xs)) for j in range(i + 1, len(xs))] + [0])
        assert best_trade(xs) == brute


def test_q5_binary_search():
    assert first_at_or_after([1, 3, 3, 7], 3) == 1 and first_at_or_after([1, 3], 9) == 2


def test_q6_sliding_max():
    assert sliding_max([4, 2, 12, 3, 8, 1], 3) == [12, 12, 12, 8]
    for s in SEEDS:
        r = random.Random(s)
        xs = [r.randint(0, 9) for _ in range(r.randint(1, 30))]
        k = r.randint(1, len(xs))
        assert sliding_max(xs, k) == oracle.sliding_max(xs, k)


def test_q7_rolling_median():
    for s in SEEDS:
        r = random.Random(s)
        xs = [r.randint(0, 6) for _ in range(r.randint(1, 60))]
        k = r.randint(1, 9)
        rm = RollingMedian(k)
        assert [rm.push(x) for x in xs] == oracle.rolling_median(xs, k)


def test_q8_top_k():
    stream = [("A", 5), ("B", 9), ("A", 7), ("C", 3), ("C", 8)]
    assert top_k(stream, 2) == ["A", "C"]


def test_q9_max_open():
    assert max_open([(0, 5), (1, 3), (3, 6), (5, 7)]) == 2
    for s in SEEDS:
        r = random.Random(s)
        orders = []
        for _ in range(r.randint(1, 12)):
            a = r.randint(0, 20)
            orders.append((a, a + r.randint(1, 8)))
        assert max_open(orders) == oracle.max_open(orders)


def test_q10_merge_halts():
    assert merge_halts([(9, 12), (1, 3), (2, 6), (6, 8)]) == [(1, 8), (9, 12)]


def test_q11_arbitrage():
    ok = [[1, 0.9, 1.1], [1 / 0.9, 1, 1.1 / 0.9], [1 / 1.1, 0.9 / 1.1, 1]]
    assert not arbitrage_cycle(ok)
    bad = [row[:] for row in ok]
    bad[1][2] = 1.30  # 1 -> 0.9 -> 1.17 -> 1.064: a cycle that makes money
    assert arbitrage_cycle(bad)
    assert math.isclose(0.9 * 1.30 / 1.1, 1.0636, rel_tol=1e-4)


def test_q12_k_trades():
    assert best_k_trades([3, 2, 6, 5, 0, 3], 2) == 7
    assert best_k_trades([1, 3, 2, 8, 4, 9], 1, fee=2) == 6
    for s in range(120):
        r = random.Random(s)
        xs = [r.randint(0, 9) for _ in range(r.randint(0, 8))]
        k = r.randint(0, 3)
        f = r.choice([0.0, 1.0])
        assert math.isclose(best_k_trades(xs, k, f), oracle.best_k_trades(xs, k, f))


def test_q13_price_levels():
    bids = PriceLevels(bid=True)
    for p, q in [(100, 5), (101, 3), (99, 7)]:
        bids.add(p, q)
    assert bids.best() == 101
    bids.cancel(101, 3)
    assert bids.best() == 100
    for s in SEEDS:
        r = random.Random(s)
        side = PriceLevels(bid=r.random() < 0.5)
        book = {}
        for _ in range(60):
            p = r.randint(90, 110)
            if book.get(p, 0) and r.random() < 0.4:
                q = r.randint(1, book[p])
                side.cancel(p, q)
                book[p] -= q
            else:
                q = r.randint(1, 5)
                side.add(p, q)
                book[p] = book.get(p, 0) + q
            live = [x for x, v in book.items() if v > 0]
            want = (max(live) if side.sign == -1 else min(live)) if live else None
            assert side.best() == want


def test_q14_window_stats():
    for s in range(100):
        r = random.Random(s)
        xs = [r.gauss(0, 1) for _ in range(r.randint(1, 50))]
        k = r.randint(2, 10)
        ws = WindowStats(k)
        for got, want in zip([ws.push(x) for x in xs], oracle.window_stats(xs, k), strict=True):
            assert math.isclose(got[0], want[0], abs_tol=1e-9) and math.isclose(got[1], want[1], abs_tol=1e-9)


def _two_venues(fills):
    counts, left, best = {}, 0, 0
    for right, v in enumerate(fills):
        counts[v] = counts.get(v, 0) + 1
        while len([c for c in counts.values() if c > 0]) > 2:
            counts[fills[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


def _two_venues_brute(fills):
    n = len(fills)
    return max((j - i for i in range(n) for j in range(i + 1, n + 1) if len(set(fills[i:j])) <= 2), default=0)


def test_worked_answers():
    tape = list("ABACCCBA")
    assert _two_venues(tape) == 4 == _two_venues_brute(tape)
    for s in range(300):
        r = random.Random(s)
        xs = [r.choice("ABCD") for _ in range(r.randint(0, 20))]
        assert _two_venues(xs) == _two_venues_brute(xs)
