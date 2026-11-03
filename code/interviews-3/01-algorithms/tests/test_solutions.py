"""Algorithms: every printed solution on small cases, and on random cases against a brute force.

C++ solutions are driven through standard input, compiled under the chapter's rules, and rerun under AddressSanitizer.
Question numbers appear here only as test_q<N> and as NONNUMERIC keys, so that sources/interviews-3/renumber.py can move them.
"""
import heapq
import itertools
import math
import pathlib
import platform
import random
import statistics
import subprocess
import sys
from collections import OrderedDict
from fractions import Fraction

import pytest
from scipy import stats as scipy_stats

HERE = pathlib.Path(__file__).resolve().parents[1]
CPP = HERE / "cpp"
BUILD = HERE.parents[2] / "build" / "iv31"
BUILD.mkdir(parents=True, exist_ok=True)
STRICT = ["-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror"]
ASAN = ["-std=c++20", "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=undefined"]
sys.path.insert(0, str(HERE / "python"))

import iv_alias  # noqa: E402
import iv_alive  # noqa: E402
import iv_as_of  # noqa: E402
import iv_best_bid_history  # noqa: E402
import iv_best_mean  # noqa: E402
import iv_best_venue  # noqa: E402
import iv_bits  # noqa: E402
import iv_bloom  # noqa: E402
import iv_brackets  # noqa: E402
import iv_bst  # noqa: E402
import iv_clips  # noqa: E402
import iv_cycle  # noqa: E402
import iv_dijkstra  # noqa: E402
import iv_drawdown  # noqa: E402
import iv_edit  # noqa: E402
import iv_external_sort  # noqa: E402
import iv_fenwick_depth  # noqa: E402
import iv_first_unique  # noqa: E402
import iv_fx_cycle  # noqa: E402
import iv_gapped  # noqa: E402
import iv_grid  # noqa: E402
import iv_heap  # noqa: E402
import iv_heavy  # noqa: E402
import iv_histogram  # noqa: E402
import iv_intervals  # noqa: E402
import iv_k_distinct  # noqa: E402
import iv_k_trades  # noqa: E402
import iv_kadane  # noqa: E402
import iv_kendall  # noqa: E402
import iv_kmp  # noqa: E402
import iv_lfu  # noqa: E402
import iv_lis  # noqa: E402
import iv_lower_bound  # noqa: E402
import iv_matching  # noqa: E402
import iv_median_stream  # noqa: E402
import iv_merge_feeds  # noqa: E402
import iv_merge_runs  # noqa: E402
import iv_min_stack  # noqa: E402
import iv_min_window  # noqa: E402
import iv_missing  # noqa: E402
import iv_next_greater  # noqa: E402
import iv_pairing  # noqa: E402
import iv_product_except  # noqa: E402
import iv_queue_position  # noqa: E402
import iv_quickselect  # noqa: E402
import iv_random_set  # noqa: E402
import iv_range_sums  # noqa: E402
import iv_rate_limit  # noqa: E402
import iv_regex  # noqa: E402
import iv_reservoir  # noqa: E402
import iv_reverse_list  # noqa: E402
import iv_rolling_mean  # noqa: E402
import iv_settle  # noqa: E402
import iv_shortest_sum  # noqa: E402
import iv_shuffle  # noqa: E402
import iv_slicing  # noqa: E402
import iv_snapshot  # noqa: E402
import iv_split_days  # noqa: E402
import iv_subarray_sum  # noqa: E402
import iv_sum_mins  # noqa: E402
import iv_sweep  # noqa: E402
import iv_three_sum  # noqa: E402
import iv_ticks  # noqa: E402
import iv_top_k  # noqa: E402
import iv_topo  # noqa: E402
import iv_trade_fee  # noqa: E402
import iv_two_medians  # noqa: E402
import iv_two_singles  # noqa: E402
import iv_two_stack_queue  # noqa: E402
import iv_two_sum  # noqa: E402
import iv_union_find  # noqa: E402
import iv_varint  # noqa: E402
import iv_weighted_jobs  # noqa: E402
import iv_welford  # noqa: E402
import iv_window_max  # noqa: E402
import iv_window_median  # noqa: E402

NONNUMERIC = {}


def gxx(name, flags=STRICT, tag=""):
    exe = BUILD / f"{name}{tag}"
    r = subprocess.run(["g++", *flags, f"-I{CPP}", str(CPP / f"{name}.cpp"), "-o", str(exe)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return exe


def feed(exe, text):
    r = subprocess.run(["setarch", platform.machine(), "-R", str(exe)], input=text, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_q1():
    f = iv_drawdown.max_drawdown
    assert f([]) == 0 and f([5]) == 0 and f([1, 2, 3, 10]) == 0
    assert f([100, 120, 90, 110, 80, 130]) == 40
    wrong = 130 - 80  # highest minus lowest ignores the order, and 80 -> 130 is a rise
    assert wrong == 50
    assert max([1, 2, 3, 10]) - min([1, 2, 3, 10]) == 9
    rng = random.Random(1)
    for _ in range(300):
        xs = [rng.randint(1, 50) for _ in range(rng.randint(0, 12))]
        brute = max([xs[i] - xs[j] for i in range(len(xs)) for j in range(i, len(xs))], default=0)
        assert f(xs) == brute
        trade = max([xs[j] - xs[i] for i in range(len(xs)) for j in range(i, len(xs))], default=0)
        assert iv_drawdown.best_trade(xs) == trade
    # the worst fall in money and in per cent can be different falls
    xs = [Fraction(v) for v in (100, 50, 1000, 600)]
    assert f(xs) == 400 and iv_drawdown.max_relative_drawdown(xs) == Fraction(1, 2)


def test_q2():
    f = iv_two_sum.two_sum
    assert f([3, 4], 6) is None and f([3, 3], 6) == (0, 1) and f([], 1) is None
    assert f([2, 7, 11, 15], 9) == (0, 1)
    # the classic wrong version fills the dictionary first, and pairs an element with itself
    def wrong(xs, target):
        where = {x: i for i, x in enumerate(xs)}
        for i, x in enumerate(xs):
            if target - x in where:
                return i, where[target - x]
        return None
    assert wrong([3, 4], 6) == (0, 0)
    rng = random.Random(2)
    for _ in range(500):
        xs = [rng.randint(-9, 9) for _ in range(rng.randint(0, 10))]
        t = rng.randint(-12, 12)
        exists = any(xs[i] + xs[j] == t for i, j in itertools.combinations(range(len(xs)), 2))
        got = f(xs, t)
        assert (got is not None) == exists
        if got:
            assert got[0] != got[1] and xs[got[0]] + xs[got[1]] == t
        s = sorted(xs)
        got = iv_two_sum.two_sum_sorted(s, t)
        assert (got is not None) == exists
        if got:
            assert got[0] < got[1] and s[got[0]] + s[got[1]] == t


def test_q3():
    asks = [(100, 300), (101, 200), (103, 500)]
    fills, left, cost = iv_sweep.sweep(asks, 600)
    assert fills == [(100, 300), (101, 200), (103, 100)] and left == 0 and cost == 60500
    assert Fraction(cost, 600) == Fraction(605, 6)
    assert round(cost / 600, 2) == 100.83 and round(cost / 600 - 100, 2) == 0.83
    fills, left, cost = iv_sweep.sweep(asks, 1200)
    assert left == 200 and cost == 30000 + 20200 + 51500 and round(cost / 1000, 2) == 101.7
    assert round(cost / 1200, 2) == 84.75
    assert iv_sweep.sweep(asks, 0) == ([], 0, 0) and iv_sweep.sweep([], 5) == ([], 5, 0)
    assert iv_sweep.size_within(asks, 101) == 500 and iv_sweep.size_within(asks, 99) == 0
    rng = random.Random(3)
    for _ in range(300):
        book, price = [], 100
        for _ in range(rng.randint(0, 6)):
            price += rng.randint(1, 3)
            book.append((price, rng.randint(1, 9)))
        q = rng.randint(0, 30)
        units = [p for p, s in book for _ in range(s)]  # one share at a time, cheapest first
        fills, left, cost = iv_sweep.sweep(book, q)
        assert cost == sum(units[:q]) and left == max(0, q - len(units)) and sum(s for _, s in fills) == min(q, len(units))


def test_q4():
    rng = random.Random(4)
    for k in (1, 2, 5):
        r = iv_rolling_mean.RollingMean(k)
        xs = [rng.randint(-100, 100) for _ in range(60)]
        for i, x in enumerate(xs):
            w = xs[max(0, i - k + 1) : i + 1]
            assert r.update(x) == sum(w) / len(w)
    r = iv_rolling_mean.RollingMean(3)
    got = [r.update(x) for x in (1e16, 1.0, 1.0, 1.0)]
    assert got[-1] == pytest.approx(1 / 3) and statistics.mean([1.0, 1.0, 1.0]) == 1.0
    assert (1e16 + 1.0) == 1e16
    total = 1e16 + 1.0 + 1.0                   # the order the stem names decides it: adding first would give 0, not 1/3
    assert (total + 1.0 - 1e16) / 3 == 0.0 and (total - 1e16 + 1.0) / 3 == pytest.approx(1 / 3)
    r = iv_rolling_mean.RollingMean(3)  # the same stream as integers stays exact
    got = [r.update(x) for x in (10**16, 1, 1, 1)]
    assert got[-1] == 1.0
    # the drift of a long-lived running sum, on ordinary prices
    r = iv_rolling_mean.RollingMean(10)
    xs = [rng.uniform(90, 110) for _ in range(2_000_000)]
    for x in xs:
        r.update(x)
    assert r.total != sum(xs[-10:]) and abs(r.total - sum(xs[-10:])) < 1e-6


def test_q17():
    f = iv_window_max.window_max
    assert f([1, 3, 2, 5, 4, 1], 3) == [3, 5, 5, 5]
    assert f([5], 1) == [5] and f([2, 2, 2], 2) == [2, 2]
    # the wrong answer's lazy heap: on a rising list no stale entry reaches the root, so nothing is ever removed
    heap, peak = [], 0
    for i in range(10000):
        heapq.heappush(heap, (-i, i))
        peak = max(peak, len(heap))
        while heap[0][1] <= i - 5:
            heapq.heappop(heap)
    assert peak == 10000
    rng = random.Random(5)
    for _ in range(300):
        xs = [rng.randint(0, 9) for _ in range(rng.randint(1, 15))]
        k = rng.randint(1, len(xs))
        win = [xs[i : i + k] for i in range(len(xs) - k + 1)]
        assert f(xs, k) == [max(w) for w in win]
        assert iv_window_max.window_range(xs, k) == [max(w) - min(w) for w in win]
        t, ev = 0, []
        for x in xs:
            t += rng.randint(1, 3)
            ev.append((t, x))
        width = rng.randint(1, 6)
        assert iv_window_max.time_window_max(ev, width) == [max(v for u, v in ev[: i + 1] if u > ev[i][0] - width) for i in range(len(ev))]


def brute_count(xs, target):
    return sum(sum(xs[i:j]) == target for i in range(len(xs)) for j in range(i + 1, len(xs) + 1))


def test_q18():
    f = iv_subarray_sum.count_sum
    assert f([1, -1, 1], 1) == 3 and f([0, 0], 0) == 3 and f([], 0) == 0
    # two pointers that grow while below target and shrink while above, wrong once values can be negative
    def two_pointers(xs, t):
        i = s = n = 0
        for j, x in enumerate(xs):
            s += x
            while s > t and i <= j:
                s -= xs[i]
                i += 1
            n += s == t
        return n
    assert two_pointers([1, -1, 1], 1) == 2
    rng = random.Random(6)
    for _ in range(400):
        xs = [rng.randint(-4, 4) for _ in range(rng.randint(0, 12))]
        t = rng.randint(-6, 6)
        assert f(xs, t) == brute_count(xs, t)
        m = rng.randint(1, 7)
        assert iv_subarray_sum.count_divisible(xs, m) == sum(
            sum(xs[i:j]) % m == 0 for i in range(len(xs)) for j in range(i + 1, len(xs) + 1))


def test_q19():
    f = iv_alive.peak_alive
    assert f([(1, 2), (2, 3)]) == (1, 1)
    assert f([(0, 10), (2, 5), (4, 8), (5, 6)]) == (3, 4) and f([]) == (0, None)
    wrong = sorted([(1, 1), (2, -1), (2, 1), (3, -1)], key=lambda e: (e[0], -e[1]))  # opens first at equal times
    alive = peak = 0
    for _, d in wrong:
        alive += d
        peak = max(peak, alive)
    assert peak == 2
    rng = random.Random(7)
    for _ in range(400):
        orders = []
        for _ in range(rng.randint(0, 8)):
            a = rng.randint(0, 12)
            orders.append((a, a + rng.randint(1, 6)))
        counts = {t: sum(a <= t < b for a, b in orders) for t in range(0, 20)}
        peak = max(counts.values())
        when = min((t for t, c in counts.items() if c == peak), default=None) if peak else None
        assert f(orders) == (peak, when)
        assert iv_alive.peak_alive_heap(orders) == peak
        diff = [0] * (18 + 1)  # the small-range follow-up, R = 18: +1 at each open, -1 at each close, then a running sum
        for a, b in orders:
            diff[a] += 1
            diff[b] -= 1
        assert max(itertools.accumulate(diff), default=0) == peak


def test_q20():
    f = iv_top_k.top_k
    trades = [("AAA", 100, 3), ("BBB", 50, 10), ("CCC", 300, 1), ("AAA", 100, 2), ("DDD", 10, 1)]
    assert f(trades, 2) == [("BBB", 500), ("AAA", 500)][::-1]
    assert f(trades, 3) == [("AAA", 500), ("BBB", 500), ("CCC", 300)]
    rng = random.Random(8)
    for _ in range(300):
        tr = [(rng.choice("ABCDEFG"), rng.randint(1, 5), rng.randint(1, 5)) for _ in range(rng.randint(0, 20))]
        k = rng.randint(1, 5)
        tot = {}
        for s, p, q in tr:
            tot[s] = tot.get(s, 0) + p * q
        assert f(tr, k) == sorted(tot.items(), key=lambda kv: (-kv[1], kv[0]))[:k]


def test_q21():
    a = [(1, {"m": "a1"}), (3, {"m": "a3"})]
    b = [(1, {"m": "b1"}), (2, {"m": "b2"})]
    assert [m["m"] for _, m in iv_merge_feeds.merge_feeds([a, b])] == ["a1", "b1", "b2", "a3"]
    assert list(iv_merge_feeds.merge_feeds([])) == [] and list(iv_merge_feeds.merge_feeds([[], []])) == []
    with pytest.raises(TypeError):  # the classic wrong heap entry compares messages on a tie
        sorted([(1, {"m": "a"}), (1, {"m": "b"})])
    # lazy: it runs on endless generators and reads no further than it must
    def forever(step):
        t = 0
        while True:
            t += step
            yield t, {"step": step}
    assert [t for t, _ in itertools.islice(iv_merge_feeds.merge_feeds([forever(2), forever(3)]), 5)] == [2, 3, 4, 6, 6]
    rng = random.Random(9)
    for _ in range(200):
        feeds = []
        for n in range(rng.randint(1, 5)):
            times = sorted(rng.randint(0, 9) for _ in range(rng.randint(0, 6)))
            feeds.append([(t, {"feed": n, "pos": p}) for p, t in enumerate(times)])
        got = list(iv_merge_feeds.merge_feeds(feeds))
        want = sorted((x for f in feeds for x in f), key=lambda e: (e[0], e[1]["feed"], e[1]["pos"]))
        assert got == want


def test_q22():
    rng = random.Random(10)
    for _ in range(100):
        s = iv_median_stream.StreamMedian()
        xs = []
        for _ in range(rng.randint(1, 40)):
            x = rng.randint(-20, 20)
            xs.append(x)
            s.add(x)
            assert s.median() == statistics.median(xs)
            assert 0 <= len(s.high) - len(s.low) <= 1 and (not s.low or -s.low[0] <= s.high[0])
    s = iv_median_stream.StreamMedian()
    for x in (5, 1, 9, 3):
        s.add(x)
    assert s.median() == 4
    with pytest.raises(IndexError):  # no median before the first add: the answer says so
        iv_median_stream.StreamMedian().median()
    counts = [0] * 1001  # the bounded-range follow-up: one counter per tick, walked to the middle
    xs = [rng.randint(0, 1000) for _ in range(99)]
    for x in xs:
        counts[x] += 1
    assert next(v for v, c in enumerate(itertools.accumulate(counts)) if c >= 50) == statistics.median(xs)


class Scripted:
    def __init__(self, draws):
        self.draws = iter(draws)

    def randrange(self, _n):
        return next(self.draws)


def test_q23():
    n, k = 5, 2
    choices = [range(i + 1) for i in range(k, n)]  # every sequence of draws is equally likely: 3 * 4 * 5 = 60
    subsets = {}
    for draws in itertools.product(*choices):
        got = frozenset(iv_reservoir.reservoir(range(n), k, Scripted(draws)))
        subsets[got] = subsets.get(got, 0) + 1
    assert sum(subsets.values()) == 60 and len(subsets) == 10 and set(subsets.values()) == {6}
    keep = Fraction(sum(c for s, c in subsets.items() if 4 in s), 60)
    assert keep == Fraction(2, 5)
    # replace with probability 1/(i+1) instead of k/(i+1): the last item survives only 1/n of the time
    assert Fraction(1, n) != Fraction(k, n)
    # induction step, exact: k/i * (1 - k/(i+1) * 1/k) == k/(i+1)
    for i in range(k, 40):
        assert Fraction(k, i) * (1 - Fraction(k, i + 1) * Fraction(1, k)) == Fraction(k, i + 1)
    rng = random.Random(11)
    hits = [0] * 20
    for _ in range(40000):
        for x in iv_reservoir.reservoir(range(20), 5, rng):
            hits[x] += 1
    for h in hits:
        assert abs(h / 40000 - 0.25) < 0.012
    assert iv_reservoir.reservoir(range(2), 5, rng) == [0, 1]
    wins = [0, 0, 0]
    weights = [1, 2, 5]
    for _ in range(40000):
        keys = [iv_reservoir.weighted_key(rng, w) for w in weights]
        wins[keys.index(max(keys))] += 1
    for w, c in zip(weights, wins, strict=True):
        assert abs(c / 40000 - w / 8) < 0.012


def test_q24():
    exe = gxx("lru_main")
    san = gxx("lru_main", ASAN, tag="_asan")
    assert feed(exe, "2\np 1 10\np 2 20\ng 1\np 3 30\ng 2\ng 1\ng 3\n").split() == ["10", "-1", "10", "30"]
    assert feed(exe, "0\np 1 1\ng 1\n").split() == ["-1"]
    rng = random.Random(12)
    for _ in range(25):
        cap = rng.randint(1, 5)
        model, script, want = [], [str(cap)], []  # model: list of [key, value], most recent first
        for _ in range(400):
            key = rng.randint(0, 8)
            if rng.random() < 0.5:
                script.append(f"g {key}")
                hit = next((e for e in model if e[0] == key), None)
                want.append(str(hit[1]) if hit else "-1")
                if hit:
                    model.remove(hit)
                    model.insert(0, hit)
            else:
                value = rng.randint(0, 99)
                script.append(f"p {key} {value}")
                hit = next((e for e in model if e[0] == key), None)
                if hit:
                    model.remove(hit)
                model.insert(0, [key, value])
                del model[cap:]
        text = "\n".join(script) + "\n"
        assert feed(exe, text).split() == want
        assert feed(san, text).split() == want


def test_q49():
    exe = gxx("book_main")
    san = gxx("book_main", ASAN, tag="_asan")
    assert feed(exe, "a 1 b 100 5\na 2 b 100 7\na 3 a 103 4\nc 1\nc 1\nc 2\nc 3\n").splitlines() == [
        "1 100 5 -1 0", "1 100 12 -1 0", "1 100 12 103 4", "1 100 7 103 4", "0 100 7 103 4", "1 -1 0 103 4", "1 -1 0 -1 0"]
    rng = random.Random(13)
    for _ in range(25):
        live, script, want = {}, [], []
        for step in range(500):
            if live and rng.random() < 0.45:
                i = rng.choice(list(live)) if rng.random() < 0.9 else 10_000 + step
                script.append(f"c {i}")
                ok = live.pop(i, None) is not None
            else:
                i = rng.randint(1, 60)
                side, price, qty = rng.choice("ba"), rng.randint(95, 105), rng.randint(1, 9)
                script.append(f"a {i} {side} {price} {qty}")
                ok = i not in live
                if ok:
                    live[i] = (side, price, qty)
            bids = [p for s, p, _ in live.values() if s == "b"]
            asks = [p for s, p, _ in live.values() if s == "a"]
            bb, ba = max(bids, default=-1), min(asks, default=-1)
            bq = sum(q for s, p, q in live.values() if s == "b" and p == bb)
            aq = sum(q for s, p, q in live.values() if s == "a" and p == ba)
            want.append(f"{int(ok)} {bb} {bq} {ba} {aq}")
        text = "\n".join(script) + "\n"
        assert feed(exe, text).splitlines() == want
        assert feed(san, text).splitlines() == want


def simple_cycles(nodes, rates):
    for size in range(2, len(nodes) + 1):
        for chosen in itertools.combinations(nodes, size):
            first = chosen[0]
            for rest in itertools.permutations(chosen[1:]):
                path = (first, *rest, first)
                if all((a, b) in rates for a, b in zip(path, path[1:], strict=False)):
                    yield path


def gain(path, rates):
    out = Fraction(1)
    for a, b in zip(path, path[1:], strict=False):
        out *= rates[(a, b)]
    return out


def test_q50():
    f = iv_fx_cycle.find_arbitrage
    # no triangle pays, but a four-hop cycle does
    rates = {("A", "B"): Fraction(2), ("B", "C"): Fraction(2), ("C", "D"): Fraction(1, 2), ("D", "A"): Fraction(3, 5),
             ("B", "A"): Fraction(2, 5), ("C", "B"): Fraction(2, 5), ("D", "C"): Fraction(9, 5), ("A", "D"): Fraction(3, 2)}
    cycles = list(simple_cycles(list("ABCD"), rates))
    assert not any(gain(c, rates) > 1 for c in cycles if len(c) == 4)  # a path of 4 nodes is a triangle
    assert gain(("A", "B", "C", "D", "A"), rates) == Fraction(6, 5)
    got = f({k: float(v) for k, v in rates.items()})
    assert got is not None and got[0] == got[-1] and gain(tuple(got), rates) > 1
    # the printed table: the square and its diagonals, so triangles exist, and none of them pays
    square = {("A", "B"): Fraction(2), ("B", "C"): Fraction(2), ("C", "D"): Fraction(1, 2), ("D", "A"): Fraction(3, 5),
              ("A", "C"): Fraction(3), ("C", "A"): Fraction(1, 5), ("B", "D"): Fraction(4, 5), ("D", "B"): Fraction(4, 5)}
    triangles = {tuple(c): gain(c, square) for c in simple_cycles(list("ABCD"), square) if len(c) == 4}
    assert sorted(triangles.values()) == [Fraction(4, 5), Fraction(4, 5), Fraction(9, 10), Fraction(24, 25)]
    assert gain(("A", "B", "C", "D", "A"), square) == Fraction(6, 5)
    got = f({k: float(v) for k, v in square.items()})
    assert got is not None and len(got) == 5 and gain(tuple(got), square) == Fraction(6, 5)
    assert f({("A", "B"): 2.0, ("B", "A"): 0.5}) is None
    # round-off on a consistent set of rates must not look like a profit
    exact = {("A", "B"): 1 / 4, ("B", "C"): 4 / 9, ("C", "A"): 9.0}
    assert Fraction(1, 4) * Fraction(4, 9) * 9 == 1
    assert sum(-math.log(r) for r in exact.values()) == pytest.approx(-4.44e-16, abs=1e-18)
    assert f(exact) is None and f(exact, eps=0.0) is not None
    # a fee per hop: multiply each rate by 1 - f
    assert f({k: float(v) * 0.9 for k, v in rates.items()}) is None
    assert gain(("A", "B", "C", "D", "A"), rates) * Fraction(9, 10) ** 4 < 1
    rng = random.Random(14)
    found = 0
    for _ in range(600):
        names = list("ABCDE")[: rng.randint(2, 5)]
        value = {c: Fraction(rng.randint(1, 20)) for c in names}
        table = {}
        for a in names:
            for b in names:
                if a != b and rng.random() < 0.7:
                    table[(a, b)] = value[b] / value[a] * Fraction(rng.randint(90, 104), 100)
        cycles = list(simple_cycles(names, table))
        best = max((gain(c, table) for c in cycles), default=Fraction(0))
        got = f({k: float(v) for k, v in table.items()})
        if best <= 1:
            assert got is None
        elif best > Fraction(1001, 1000):
            assert got is not None
        if got is not None:
            found += 1
            assert got[0] == got[-1] and gain(tuple(got), table) > 1
    assert found > 50


def test_q51():
    f = iv_lis.longest_increasing
    assert f([]) == [] and f([3]) == [3] and f([2, 2, 2]) == [2]
    assert f([3, 4, 1]) == [3, 4] and f([3, 1, 4, 1, 5, 9, 2, 6]) in ([3, 4, 5, 6], [1, 4, 5, 6], [3, 4, 5, 9], [1, 4, 5, 9])
    tails = []  # the tails array alone is not a subsequence: 1 comes after 4
    from bisect import bisect_left
    for x in [3, 4, 1]:
        n = bisect_left(tails, x)
        if n == len(tails):
            tails.append(x)
        else:
            tails[n] = x
    assert tails == [1, 4]
    rng = random.Random(15)
    for _ in range(400):
        xs = [rng.randint(0, 12) for _ in range(rng.randint(0, 11))]
        best = 0
        for r in range(len(xs) + 1):
            for c in itertools.combinations(xs, r):
                if all(a < b for a, b in zip(c, c[1:], strict=False)):
                    best = max(best, r)
        got = f(xs)
        assert len(got) == best and all(a < b for a, b in zip(got, got[1:], strict=False))
        it = iter(xs)
        assert all(v in it for v in got)  # a subsequence of xs, in order
        boxes = [(rng.randint(1, 6), rng.randint(1, 6)) for _ in range(rng.randint(0, 7))]
        chain = 0
        for r in range(len(boxes) + 1):
            for c in itertools.permutations(boxes, r):
                if all(a[0] < b[0] and a[1] < b[1] for a, b in zip(c, c[1:], strict=False)):
                    chain = max(chain, r)
        assert iv_lis.nested_boxes(boxes) == chain


def test_q52():
    assert iv_kendall.sort_count([3, 1, 2])[1] == 2
    assert iv_kendall.kendall_tau([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(1 - 2 * 1 / 6)
    assert 10**5 * (10**5 - 1) // 2 == 4_999_950_000 and 4_999_950_000 > 2**31
    rng = random.Random(16)
    for _ in range(200):
        n = rng.randint(2, 30)
        xs, ys = rng.sample(range(100), n), rng.sample(range(100), n)
        conc = sum((xs[i] - xs[j]) * (ys[i] - ys[j]) > 0 for i, j in itertools.combinations(range(n), 2))
        disc = n * (n - 1) // 2 - conc
        tau = iv_kendall.kendall_tau(xs, ys)
        assert tau == pytest.approx((conc - disc) / (n * (n - 1) / 2))
        assert tau == pytest.approx(scipy_stats.kendalltau(xs, ys).statistic)
        xt, yt = [rng.randint(0, 5) for _ in range(n)], [rng.randint(0, 5) for _ in range(n)]
        if len(set(xt)) > 1 and len(set(yt)) > 1:
            assert iv_kendall.kendall_tau_b(xt, yt) == pytest.approx(scipy_stats.kendalltau(xt, yt).statistic)


def test_q53():
    f = iv_heavy.heavy_hitters
    assert f("aabab", 2) == {"a": 1}  # k = 2 is majority vote
    assert f("abcab", 3) == {"a": 1, "b": 1}
    assert f("abc", 2) == {"c": 1}  # a false positive: c occurs once in three, and is still a candidate
    rng = random.Random(17)
    for _ in range(500):
        n = rng.randint(1, 80)
        pool = "abcdefgh"[: rng.randint(1, 8)]
        xs = [rng.choice(pool) if rng.random() < 0.5 else pool[0] for _ in range(n)]
        rng.shuffle(xs)
        k = rng.randint(2, 6)
        got = f(xs, k)
        assert len(got) <= k - 1
        for s in set(xs):
            true = xs.count(s)
            est = got.get(s, 0)
            assert est <= true <= est + n // k
            assert true <= est + (n - sum(got.values())) // k  # rounds = (n - total of the counters) / k
            if true * k > n:
                assert s in got


def test_q69():
    f = iv_window_median.window_medians
    assert f([1, 3, 2, 5, 4], 3) == [2, 3, 4]
    assert f([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]
    assert f([7], 1) == [7] and f([2, 2, 2, 2], 3) == [2, 2]
    rng = random.Random(18)
    for _ in range(600):
        xs = [rng.randint(0, rng.choice([2, 5, 30])) for _ in range(rng.randint(1, 30))]
        k = rng.randint(1, len(xs))
        assert f(xs, k) == [statistics.median(xs[i : i + k]) for i in range(len(xs) - k + 1)]
    # stale entries pile up: on a rising series memory grows with n, not with k
    peak = [0]
    class Counting:
        heappop = staticmethod(heapq.heappop)
        @staticmethod
        def heappush(heap, item):
            heapq.heappush(heap, item)
            peak[0] = max(peak[0], len(heap))
    original = iv_window_median.heapq
    iv_window_median.heapq = Counting
    try:
        f(list(range(10000)), 5)
    finally:
        iv_window_median.heapq = original
    assert peak[0] >= 9990  # nearly all 10 000, as the answer says


def test_q70():
    f = iv_shortest_sum.shortest_at_least
    assert f([2, -1, 2], 3) == 3 and f([1, 2], 4) is None and f([], 1) is None and f([5], 5) == 1
    assert f([84, -37, 32, 40, 95], 167) == 3
    def sliding(xs, t):  # the shrink-from-the-left window, right only when no value is negative
        i = s = 0
        best = None
        for j, x in enumerate(xs):
            s += x
            while s >= t:
                best = j - i + 1 if best is None else min(best, j - i + 1)
                s -= xs[i]
                i += 1
        return best
    assert sliding([84, -37, 32, 40, 95], 167) != 3
    rng = random.Random(19)
    for _ in range(800):
        xs = [rng.randint(-8, 10) for _ in range(rng.randint(0, 14))]
        t = rng.randint(1, 20)
        spans = [j - i for i in range(len(xs)) for j in range(i + 1, len(xs) + 1) if sum(xs[i:j]) >= t]
        assert f(xs, t) == min(spans, default=None)


def test_q71():
    f = iv_two_medians.median_two
    assert f([1, 3], [2]) == 2 and f([1, 2], [3, 4]) == 2.5 and f([], [1]) == 1 and f([2], []) == 2
    assert f([1, 1, 1], [1, 1]) == 1
    assert f([1, 2, 3, 4], [5, 6, 7, 8]) == 4.5
    # averaging the two medians fails when lengths differ
    assert (statistics.median([1, 2, 3, 4, 5, 6, 7]) + statistics.median([100])) / 2 != f([1, 2, 3, 4, 5, 6, 7], [100])
    assert f([1, 2, 3, 4, 5, 6, 7], [100]) == 4.5
    assert (statistics.median([1, 2, 3, 4, 5, 6, 7]) + 100) / 2 == 52
    assert math.ceil(math.log2(10**9 + 1)) == 30
    rng = random.Random(20)
    for _ in range(1000):
        a = sorted(rng.randint(0, 20) for _ in range(rng.randint(0, 9)))
        b = sorted(rng.randint(0, 20) for _ in range(rng.randint(0, 9)))
        if not a and not b:
            continue
        both = sorted(a + b)
        assert f(a, b) == statistics.median(both)
        k = rng.randint(1, len(both))
        assert iv_two_medians.kth_of_two(a, b, k) == both[k - 1]
        parts = [a, b, sorted(rng.randint(0, 20) for _ in range(3))]
        allp = sorted(x for p in parts for x in p)
        assert iv_two_medians.median_of_partitions(parts, 0, 20) == allp[(len(allp) + 1) // 2 - 1]


def test_q5():
    f = iv_brackets.balanced
    assert f("([)]") is False and f("") is True and f("((") is False and f(")") is False and f("{[()]}") is True
    assert iv_brackets.counters_only("([)]") is True  # the classic wrong answer
    assert iv_brackets.longest_valid(")()())") == 4
    rng = random.Random(901)
    def valid_by_rewriting(s):
        while True:
            t = s.replace("()", "").replace("[]", "").replace("{}", "")
            if t == s:
                return not s
            s = t
    for _ in range(2000):
        s = "".join(rng.choice("()[]{}") for _ in range(rng.randint(0, 8)))
        assert f(s) == valid_by_rewriting(s)
    for _ in range(300):
        s = "".join(rng.choice("()") for _ in range(rng.randint(0, 10)))
        best = max([j - i for i in range(len(s) + 1) for j in range(i, len(s) + 1) if valid_by_rewriting(s[i:j])], default=0)
        assert iv_brackets.longest_valid(s) == best


def test_q6():
    xs = [1, 2, 2, 2, 3]
    f = iv_lower_bound.lower_bound
    assert f(xs, 2) == 1 and f(xs, 4) == 5 and f([], 1) == 0
    assert iv_lower_bound.upper_bound(xs, 2) - f(xs, 2) == 3 and iv_lower_bound.upper_bound(xs, 2) == 4
    rng = random.Random(902)
    for _ in range(500):
        s = sorted(rng.randint(0, 9) for _ in range(rng.randint(0, 12)))
        t = rng.randint(-1, 10)
        linear = next((i for i, v in enumerate(s) if v >= t), len(s))
        assert f(s, t) == linear
    assert 1_200_000_000 + 1_200_000_000 > 2**31 - 1  # (lo + hi) passes INT_MAX with positions past a billion
    assert 1_200_000_000 + (1_200_000_000 - 1_200_000_000) // 2 < 2**31


def test_q7():
    u = iv_first_unique.FirstUnique()
    assert u.first_unique() is None
    for s in "ABACB":
        u.add(s)
    assert u.first_unique() == "C"
    rng = random.Random(903)
    for _ in range(200):
        u, seen = iv_first_unique.FirstUnique(), []
        for _ in range(rng.randint(0, 20)):
            s = rng.choice("ABCDEF")
            u.add(s)
            seen.append(s)
            assert u.first_unique() == next((x for x in seen if seen.count(x) == 1), None)
    # a plain dict walks past its deleted entries, so first_unique would be O(n): the order must come from the links
    assert isinstance(iv_first_unique.FirstUnique().once, OrderedDict)


def test_q8():
    m = iv_reverse_list
    assert m.reverse(None) is None
    assert m.values(m.reverse(m.build([1, 2, 3]))) == [3, 2, 1]
    assert m.values(m.reverse_recursive(m.build([1, 2, 3]))) == [3, 2, 1]
    assert sys.getrecursionlimit() >= 1000
    big = m.build(range(100_000))
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)  # the default; pytest may have raised it
    try:
        with pytest.raises(RecursionError):
            m.reverse_recursive(big)
    finally:
        sys.setrecursionlimit(limit)
    big = m.build(range(100_000))
    assert m.values(m.reverse(big))[:2] == [99_999, 99_998]


def test_q9():
    m = iv_bits
    assert 12 & 11 == 8 and bin(12) == "0b1100" and bin(8) == "0b1000"
    assert m.next_power_of_two(1000) == 1024 and m.next_power_of_two(1024) == 1024 and m.next_power_of_two(1) == 1
    assert 0 & -1 == 0 and not m.is_power_of_two(0)
    for x in range(1, 5000):
        assert m.is_power_of_two(x) == (bin(x).count("1") == 1)
        assert m.count_set_bits(x) == bin(x).count("1")
        p = m.next_power_of_two(x)
        assert p >= x and p // 2 < x and m.is_power_of_two(p)
    # the mask agrees with the remainder, even across the wrap of a 64-bit counter
    size = 1024
    for i in (0, 5, 1023, 1024, 2**64 - 1):
        assert i & (size - 1) == i % size
    assert ((2**64 - 1 + 1) % 2**64) & (size - 1) == ((2**64 - 1) & (size - 1)) + 1 - size


def test_q10():
    f = iv_missing.missing
    assert f([3, 1, 5, 2], 5) == 4
    assert iv_missing.two_missing([3, 5, 2], 5) == (1, 4)
    rng = random.Random(906)
    for _ in range(300):
        n = rng.randint(2, 40)
        xs = list(range(1, n + 1))
        rng.shuffle(xs)
        assert f(xs[1:], n) == xs[0]
        assert iv_missing.two_missing(xs[2:], n) == tuple(sorted(xs[:2]))
        assert n * (n + 1) // 2 - sum(xs[1:]) == xs[0]
    n = 4_294_967_295  # the first n at which the triangular number passes 2^63 - 1, near 4.3e9
    assert n * (n + 1) // 2 <= 2**63 - 1 and (n + 1) * (n + 2) // 2 > 2**63 - 1
    assert round(n / 1e9, 1) == 4.3


def test_q11():
    s = iv_min_stack.MinStack()
    s.push(1)
    s.push(1)
    s.pop()
    assert s.min() == 1  # the case that needs <= and not <
    rng = random.Random(907)
    for _ in range(200):
        s, model = iv_min_stack.MinStack(), []
        for _ in range(40):
            if model and rng.random() < 0.45:
                assert s.pop() == model.pop()
            else:
                x = rng.randint(0, 5)
                s.push(x)
                model.append(x)
            if model:
                assert s.min() == min(model)


def test_q12():
    rng = random.Random(908)
    for _ in range(200):
        q, model, pushed = iv_two_stack_queue.Queue(), [], 0
        for _ in range(rng.randint(0, 100)):
            if model and rng.random() < 0.5:
                assert q.pop() == model.pop(0)
            else:
                q.push(pushed)
                model.append(pushed)
                pushed += 1
        assert q.moves <= pushed  # each element is moved at most once, whatever the sequence
    q = iv_two_stack_queue.Queue()
    for i in range(1_000):
        q.push(i)
    before = q.moves
    q.pop()
    assert q.moves - before == 1_000  # and one single pop can still do all of them


def test_q13():
    f = iv_ticks.to_ticks
    assert f("101.25") == 10125 and f("1.15") == 115 and f("-0.05") == -5 and f("7") == 700 and f("0.5") == 50
    assert int(float("1.15") * 100) == 114 and repr(float("1.15") * 100) == "114.99999999999999"
    assert round(float("1.15") * 100) == 115
    # the parser that loses the sign
    assert int("-0") * 100 + 5 == 5
    for bad in ("1.234", "abc", "1.2.3", "", "--1.50", "---7", "1-"):
        with pytest.raises(ValueError):
            f(bad)
    for t in range(-30000, 30000, 7):
        whole, frac = divmod(abs(t), 100)
        assert f(("-" if t < 0 else "") + f"{whole}.{frac:02d}") == t
    # a float loses the digit on a large enough price
    assert round(float("90071992547409.93") * 100) != 9007199254740993
    assert f("90071992547409.93") == 9007199254740993


def test_q14():
    f = iv_kadane.best_stretch
    assert f([-2, 3, -1, 4, -5]) == (6, 1, 3)
    assert f([-3, -1, -2]) == (-1, 1, 1)
    assert sum(x for x in [-2, 3, -1, 4, -5] if x > 0) == 7
    with pytest.raises(IndexError):  # no stretch to return: the answer says so
        f([])
    rng = random.Random(910)
    for _ in range(500):
        xs = [rng.randint(-9, 9) for _ in range(rng.randint(1, 12))]
        best, i, j = f(xs)
        assert best == sum(xs[i : j + 1]) and i <= j
        assert best == max(sum(xs[a : b + 1]) for a in range(len(xs)) for b in range(a, len(xs)))


def test_q15():
    f = iv_product_except.product_except_self
    assert f([2, 3, 0, 4]) == [0, 0, 24, 0]
    assert f([2, 3, 0, 0]) == [0, 0, 0, 0]
    rng = random.Random(911)
    for _ in range(300):
        xs = [rng.randint(-3, 3) for _ in range(rng.randint(1, 8))]
        assert f(xs) == [math.prod(xs[:i] + xs[i + 1 :]) for i in range(len(xs))]


def test_q16():
    assert -7 // 2 == -4 and -7 % 2 == 1
    assert -7 - -7 % 5 == -10
    exe = gxx("floor_snap", tag="_strict")
    assert feed(exe, "-7 2\n-7 5\n7 5\n-10 5\n0 5\n").split("\n")[:5] == ["-3 -1 -8", "-1 -2 -10", "1 2 5", "-2 0 -10", "0 0 0"]
    assert -4 * 2 + 1 == -7 and -3 * 2 - 1 == -7
    assert int(-7 / 5) * 5 == -5  # the truncating wrong answer, in C++'s terms
    pairs = [(x, t) for x in range(-40, 41) for t in (1, 2, 5, 7)]
    out = feed(exe, "".join(f"{x} {t}\n" for x, t in pairs)).splitlines()
    for (x, t), line in zip(pairs, out, strict=True):
        assert int(line.split()[2]) == x - x % t  # C++ against Python's floor


def test_q25():
    m = iv_reverse_list
    rng = random.Random(913)
    for _ in range(300):
        n = rng.randint(0, 30)
        nodes = [m.Node(i) for i in range(n)]
        for a, b in itertools.pairwise(nodes):
            a.next = b
        start = None
        if n and rng.random() < 0.7:
            start = rng.randrange(n)
            nodes[-1].next = nodes[start]
        got = iv_cycle.cycle_start(nodes[0] if n else None)
        assert got is (nodes[start] if start is not None else None)


def test_q26():
    halts = [(8, 10), (1, 3), (10, 12), (2, 6)]
    assert iv_intervals.merge(halts) == [(1, 6), (8, 12)]
    assert iv_intervals.covered(halts) == 9 and 5 + 4 == 9 and sum(b - a for a, b in halts) == 10
    assert iv_intervals.merge([(1, 6), (2, 3)]) == [(1, 6)]
    assert iv_intervals.merge([]) == []
    rng = random.Random(914)
    for _ in range(500):
        xs = [(a, a + rng.randint(0, 5)) for a in (rng.randint(0, 25) for _ in range(rng.randint(0, 8)))]
        units = set()
        for a, b in xs:
            units |= set(range(a, b))
        assert iv_intervals.covered(xs) == len(units)
        m = iv_intervals.merge(xs)
        assert all(m[i][1] < m[i + 1][0] for i in range(len(m) - 1))
    # sorting by end misses the long halt
    by_end = sorted([(1, 10), (2, 3), (4, 5)], key=lambda t: t[1])
    assert by_end[0] == (2, 3) and by_end[-1] == (1, 10)


def test_q27():
    f = iv_next_greater.days_until_higher
    assert f([100, 101, 103, 99, 97, 100, 104, 101]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert iv_next_greater.span([100, 80, 60, 70, 60, 75, 85]) == [1, 1, 1, 2, 1, 4, 6]
    rng = random.Random(915)
    for _ in range(300):
        xs = [rng.randint(0, 9) for _ in range(rng.randint(0, 14))]
        assert f(xs) == [next((j - i for j in range(i + 1, len(xs)) if xs[j] > xs[i]), 0) for i in range(len(xs))]


def test_q28():
    f = iv_clips.fewest_clips
    assert iv_clips.greedy([1, 3, 4], 6) == [4, 1, 1] and sorted(f([1, 3, 4], 6)) == [3, 3]
    assert f([2, 4], 5) is None
    assert iv_clips.greedy([3, 4], 6) is None and f([3, 4], 6) == [3, 3]
    assert iv_clips.ways([1, 3, 4], 6) == 4
    assert len(iv_clips.greedy([1, 5, 10, 25], 67)) == len(f([1, 5, 10, 25], 67))
    rng = random.Random(916)
    for _ in range(200):
        sizes = rng.sample(range(1, 12), rng.randint(1, 4))
        n = rng.randint(0, 40)
        # a second route: breadth-first search over quantities
        level, seen, depth, answer = {0}, {0}, 0, None
        while level:
            if n in level:
                answer = depth
                break
            level = {q + s for q in level for s in sizes if q + s <= n} - seen
            seen |= level
            depth += 1
        got = f(sizes, n)
        assert (got is None) == (answer is None)
        if got is not None:
            assert len(got) == answer and sum(got) == n and set(got) <= set(sizes)


def _brute_fee(prices, fee):
    best = 0
    for i in range(len(prices)):
        for j in range(i, len(prices)):
            best = max(best, prices[j] - prices[i] - fee + _brute_fee(prices[j + 1 :], fee))
    return best


def test_q29():
    f = iv_trade_fee.max_profit_with_fee
    xs = [10, 13, 12, 18, 14, 19]
    assert f(xs, 2) == 9 == (18 - 10 - 2) + (19 - 14 - 2)
    assert f(xs, 0) == 14 == sum(max(0, b - a) for a, b in itertools.pairwise(xs))
    assert f(xs, 1_000_000) == 0 and f([], 2) == 0
    assert (3 - 2) + (6 - 2) + (5 - 2) == 8
    rng = random.Random(917)
    for _ in range(300):
        ys = [rng.randint(1, 20) for _ in range(rng.randint(0, 7))]
        fee = rng.randint(0, 6)
        assert f(ys, fee) == _brute_fee(ys, fee)


def test_q30():
    f = iv_edit.edit_distance
    assert f("ABCD", "ACBD") == 2 and f("", "ABC") == 3 and f("ABC", "ABC") == 0
    def slow(a, b):
        if not a or not b:
            return len(a) + len(b)
        return min(slow(a[1:], b[1:]) + (a[0] != b[0]), slow(a[1:], b) + 1, slow(a, b[1:]) + 1)
    rng = random.Random(918)
    for _ in range(300):
        a = "".join(rng.choice("AB") for _ in range(rng.randint(0, 5)))
        b = "".join(rng.choice("AB") for _ in range(rng.randint(0, 5)))
        assert f(a, b) == f(b, a) == slow(a, b)
    def with_swaps(a, b):
        d = [[max(i, j) if not i * j else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                d[i][j] = min(d[i - 1][j - 1] + (a[i - 1] != b[j - 1]), d[i - 1][j] + 1, d[i][j - 1] + 1)
                if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                    d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
        return d[-1][-1]
    assert with_swaps("ABCD", "ACBD") == 1


def test_q31():
    rng = random.Random(919)
    for _ in range(200):
        n = rng.randint(1, 15)
        g = iv_union_find.Groups(n)
        adj = {i: set() for i in range(n)}
        for _ in range(rng.randint(0, 25)):
            a, b = rng.randrange(n), rng.randrange(n)
            g.link(a, b)
            adj[a].add(b)
            adj[b].add(a)
            comp, stack, seen = 0, [], set()
            for s in range(n):
                if s not in seen:
                    comp += 1
                    stack.append(s)
                    seen.add(s)
                    while stack:
                        for w in adj[stack.pop()]:
                            if w not in seen:
                                seen.add(w)
                                stack.append(w)
            assert g.count == comp
            x, y = rng.randrange(n), rng.randrange(n)
            reach, stack = {x}, [x]
            while stack:
                for w in adj[stack.pop()]:
                    if w not in reach:
                        reach.add(w)
                        stack.append(w)
            assert g.same(x, y) == (y in reach)
    # depth stays within log2 n with union by size, even on a chain of links
    n = 1024
    g = iv_union_find.Groups(n)
    for i in range(n - 1):
        g.link(i, i + 1)
    def depth(x):
        d = 0
        while g.parent[x] != x:
            x, d = g.parent[x], d + 1
        return d
    assert max(depth(i) for i in range(n)) <= 10


def test_q32():
    f = iv_topo.run_order
    assert f(2, [(0, 1), (1, 0)]) is None and f(0, []) == []
    a, b, c, d = 0, 1, 2, 3
    edges = [(a, b), (a, c), (b, d), (c, d)]
    assert iv_topo.finish_time([3, 2, 4, 1], edges) == 8 and 3 + 4 + 1 == 8 and 3 + 2 + 4 + 1 == 10
    assert iv_topo.finish_time([3, 1, 4, 1], edges) == 8  # a faster B changes nothing
    rng = random.Random(920)
    for _ in range(300):
        n = rng.randint(1, 6)
        es = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 8))]
        exists = any(all(p.index(x) < p.index(y) for x, y in es) for p in itertools.permutations(range(n)))
        got = f(n, es)
        assert (got is not None) == exists
        if got is not None:
            assert sorted(got) == list(range(n)) and all(got.index(x) < got.index(y) for x, y in es)


def test_q33():
    g = ["..#", ".#.", "..."]
    assert iv_grid.shortest_path(g, (0, 0), (2, 2)) == 4
    assert iv_grid.shortest_path(["#."], (0, 1), (0, 0)) is None
    rng = random.Random(921)
    for _ in range(300):
        r, c = rng.randint(1, 5), rng.randint(1, 5)
        grid = ["".join("#" if rng.random() < 0.3 else "." for _ in range(c)) for _ in range(r)]
        cells = [(i, j) for i in range(r) for j in range(c) if grid[i][j] != "#"]
        if not cells:
            continue
        s, t = rng.choice(cells), rng.choice(cells)
        # a second route: relax until nothing changes
        dist = {s: 0}
        changed = True
        while changed:
            changed = False
            for (i, j) in cells:
                for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                    if n in dist and dist[n] + 1 < dist.get((i, j), 10**9):
                        dist[i, j] = dist[n] + 1
                        changed = True
        assert iv_grid.shortest_path(grid, s, t) == dist.get(t)
    # marking on pop lets a cell into the queue more than once; marking on push never does
    grid = ["." * 6] * 6
    pushes, seen, queue = 0, set(), [(0, 0)]
    while queue:
        i, j = queue.pop(0)
        if (i, j) in seen:
            continue
        seen.add((i, j))
        for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= n[0] < 6 and 0 <= n[1] < 6 and n not in seen:
                queue.append(n)
                pushes += 1
    assert 35 < pushes <= 4 * 36


def test_q34():
    links = {"A": [("B", 5), ("C", 2)], "C": [("B", 1)], "B": [("D", 1)]}
    dist, before = iv_dijkstra.fastest(links, "A")
    assert dist["D"] == 4
    route, v = ["D"], "D"
    while v in before:
        v = before[v]
        route.append(v)
    assert route[::-1] == ["A", "C", "B", "D"]
    assert 5 + 1 == 6
    neg = {"A": [("B", 2), ("C", 3)], "C": [("B", -2)]}
    assert iv_dijkstra.closed_set_version(neg, "A")["B"] == 2
    assert iv_dijkstra.fastest(neg, "A")[0]["B"] == 1
    class StopsTheLoop(dict):  # a negative cycle: count the visits, since the lazy version never ends by itself
        visits = 0
        def get(self, *key):
            StopsTheLoop.visits += 1
            if StopsTheLoop.visits > 10000:
                raise TimeoutError
            return dict.get(self, *key)
    with pytest.raises(TimeoutError):
        iv_dijkstra.fastest(StopsTheLoop({"A": [("B", -1)], "B": [("A", 0)]}), "A")
    rng = random.Random(922)
    for _ in range(300):
        n = rng.randint(1, 8)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(0, 9)) for _ in range(rng.randint(0, 15))]
        g = {}
        for a, b, w in edges:
            g.setdefault(a, []).append((b, w))
        bf = {0: 0}
        for _ in range(n):
            for a, b, w in edges:
                if a in bf and bf[a] + w < bf.get(b, 10**9):
                    bf[b] = bf[a] + w
        assert iv_dijkstra.fastest(g, 0)[0] == bf


def test_q35():
    f = iv_split_days.smallest_largest_day
    assert f([4, 9, 3, 7, 8], 2) == 16 and f([4, 9, 3, 7, 8], 3) == 13
    def brute(xs, d):
        best = sum(xs)
        for cuts in itertools.combinations(range(1, len(xs)), min(d - 1, len(xs) - 1)):
            b = (0, *cuts, len(xs))
            best = min(best, max(sum(xs[b[i] : b[i + 1]]) for i in range(len(b) - 1)))
        return best
    rng = random.Random(923)
    for _ in range(400):
        xs = [rng.randint(1, 15) for _ in range(rng.randint(1, 8))]
        d = rng.randint(1, 5)
        assert f(xs, d) == brute(xs, d)
    assert f([5, 5], 1) == 10 and f([5, 5], 9) == 5  # one day takes everything; many days leave only the largest
    # the average-aiming cut of the wrong answer: stop before passing 15.5
    assert (4 + 9 + 3 + 7 + 8) / 2 == 15.5 and 4 + 9 == 13 and 3 + 7 + 8 == 18
    # with a negative slice the greedy count rises with the cap, though feasibility itself is monotone
    def greedy(xs, cap):
        used, load = 1, 0
        for s in xs:
            if load + s > cap:
                used, load = used + 1, 0
            load += s
        return used
    def fewest(xs, cap):
        for d in range(1, len(xs) + 1):
            for cuts in itertools.combinations(range(1, len(xs)), d - 1):
                b = (0, *cuts, len(xs))
                if all(sum(xs[b[i] : b[i + 1]]) <= cap for i in range(d)):
                    return d
    xs = [8, 2, -5, 8, -1, 4]
    assert [greedy(xs, c) for c in (8, 9, 10, 11)] == [2, 2, 3, 2]
    assert [fewest(xs, c) for c in (8, 9, 10, 11)] == [2, 2, 2, 2]
    assert brute([5, -5], 1) == 0 < max(5, -5)  # the largest slice is no longer a lower bound


def test_q36():
    f = iv_quickselect.kth_smallest
    rng = random.Random(924)
    for _ in range(300):
        xs = [rng.randint(0, 9) for _ in range(rng.randint(1, 30))]
        k = rng.randrange(len(xs))
        assert f(xs, k, rng) == sorted(xs)[k]
    assert iv_quickselect.comparisons_first_pivot(list(range(100)), 99) == 4950 == 100 * 99 // 2
    assert iv_quickselect.comparisons_first_pivot([7] * 100, 99) == 4950
    # three groups: all equal ends at once
    assert f([7] * 100, 99, rng) == 7


def test_q37():
    f = iv_three_sum.three_sum
    assert sorted(f([-2, 0, 1, 1, 2, -1, -1])) == [(-2, 0, 2), (-2, 1, 1), (-1, -1, 2), (-1, 0, 1)]
    rng = random.Random(925)
    for _ in range(400):
        xs = [rng.randint(-6, 6) for _ in range(rng.randint(0, 12))]
        brute = {tuple(sorted(t)) for t in itertools.combinations(xs, 3) if sum(t) == 0}
        got = f(xs)
        assert len(got) == len(set(got)) and set(got) == brute


def test_q38():
    tape = list("ABACCDDD")
    assert iv_k_distinct.longest_k_distinct(tape, 2) == 5
    assert iv_k_distinct.count_exactly(tape, 2) == 11
    rng = random.Random(926)
    for _ in range(300):
        t = [rng.choice("ABCD") for _ in range(rng.randint(0, 12))]
        k = rng.randint(1, 4)
        subs = [t[i:j] for i in range(len(t)) for j in range(i + 1, len(t) + 1)]
        assert iv_k_distinct.longest_k_distinct(t, k) == max((len(s) for s in subs if len(set(s)) <= k), default=0)
        assert iv_k_distinct.count_exactly(t, k) == sum(len(set(s)) == k for s in subs)


def test_q39():
    exe = gxx("flat_map_main", tag="_strict")
    asan = gxx("flat_map_main", flags=ASAN, tag="_asan")
    rng = random.Random(927)
    lines, want, model = [], [], {}
    for _ in range(6000):
        k = rng.randint(1, 300)
        op = rng.random()
        if op < 0.45 and len(model) < 500:
            v = rng.randint(0, 99)
            lines.append(f"p {k} {v}")
            model[k] = v
        elif op < 0.7:
            lines.append(f"e {k}")
            model.pop(k, None)
        else:
            lines.append(f"g {k}")
            want.append(str(model.get(k, "-")))
    text = "\n".join(lines) + "\n"
    assert feed(exe, text).split() == want
    assert feed(asan, text).split() == want
    # clearing a slot without a shift: a key that probed past it now looks absent
    table = [None] * 4
    for key in (0, 4):  # both have home slot 0
        i = key % 4
        while table[i] is not None:
            i = (i + 1) % 4
        table[i] = key
    table[0] = None
    assert table[0] is None and 4 in table  # get(4) starts at slot 0, sees empty, and stops
    # expected probes of an unsuccessful search, by simulation, against the formula
    def probes(load, size=1 << 16):
        r = random.Random(1000)
        t = [False] * size
        for _ in range(int(load * size)):
            i = r.randrange(size)
            while t[i]:
                i = (i + 1) % size
            t[i] = True
        total = 0
        for _ in range(20000):
            i, c = r.randrange(size), 1
            while t[i]:
                i, c = (i + 1) % size, c + 1
            total += c
        return total / 20000
    assert 0.5 * (1 + 1 / 0.5**2) == 2.5 and round(0.5 * (1 + 1 / 0.1**2), 1) == 50.5
    assert 2.2 < probes(0.5) < 2.8 and 30 < probes(0.9) < 75


def test_q40():
    rng = random.Random(928)
    for _ in range(200):
        xs = [rng.randint(0, 50) for _ in range(rng.randint(1, 40))]
        h = iv_heap.MinHeap(xs)
        assert [h.pop() for _ in xs] == sorted(xs)
        h = iv_heap.MinHeap()
        model = []
        for _ in range(60):
            if model and rng.random() < 0.4:
                assert h.pop() == heapq.heappop(model)
            else:
                x = rng.randint(0, 50)
                h.push(x)
                heapq.heappush(model, x)
    # swap counts on a descending list of 1024 items
    def count_pushes(n):
        a, swaps = [], 0
        for x in range(n, 0, -1):
            a.append(x)
            i = len(a) - 1
            while i and a[i] < a[(i - 1) // 2]:
                a[i], a[(i - 1) // 2] = a[(i - 1) // 2], a[i]
                i = (i - 1) // 2
                swaps += 1
        return swaps
    def count_build(n):
        a, swaps = list(range(n, 0, -1)), 0
        for s in range(n // 2 - 1, -1, -1):
            i = s
            while (c := 2 * i + 1) < n:
                if c + 1 < n and a[c + 1] < a[c]:
                    c += 1
                if a[i] <= a[c]:
                    break
                a[i], a[c] = a[c], a[i]
                i = c
                swaps += 1
        return swaps
    assert count_pushes(1024) == 8204 and count_build(1024) == 1015
    assert sum(h * Fraction(1, 2 ** (h + 1)) for h in range(1, 200)) < 1
    for n in range(1, 2000):  # the ceiling is needed, and the true total of heights is n minus its set bits
        height = [0] * n
        for i in range(n - 1, 0, -1):
            height[(i - 1) // 2] = max(height[(i - 1) // 2], height[i] + 1)
        for h in set(height):
            assert height.count(h) <= math.ceil(n / 2 ** (h + 1))
        assert sum(height) == n - bin(n).count("1") <= n
    assert 2 > 3 / 2 and [1, 1, 0] == [1, 1, 0]  # n = 3: two leaves, above n/2 = 1.5


def test_q41():
    f = iv_two_singles.two_singles
    assert set(f([4, 7, 4, 9, 7, 2])) == {9, 2}
    assert 9 ^ 2 == 11 == 0b1011 and 11 & -11 == 1
    assert iv_two_singles.single_among_triples([7, 7, 7, 5, 9, 9, 9]) == 5
    assert {a + b for a, b in ((1, 6), (2, 5), (3, 4))} == {7} and {a ^ b for a, b in ((1, 6), (2, 5), (3, 4))} == {7}
    rng = random.Random(929)
    for _ in range(300):
        vals = rng.sample(range(1, 1000), rng.randint(2, 12))
        xs = vals[2:] * 2 + vals[:2]
        rng.shuffle(xs)
        assert set(f(xs)) == set(vals[:2])
        ys = vals[1:] * 3 + vals[:1]
        rng.shuffle(ys)
        assert iv_two_singles.single_among_triples(ys) == vals[0]


def test_q42():
    lim = iv_rate_limit.Limiter(2, 10)
    assert [lim.allow(t) for t in (0, 1, 10, 10, 11)] == [True, True, True, False, True]
    fixed = iv_rate_limit.FixedBuckets(2, 10)
    assert all(fixed.allow(t) for t in (9, 9, 10, 10))  # four inside a span of two seconds, against a limit of 2
    rng = random.Random(930)
    for _ in range(200):
        n, t = rng.randint(1, 4), rng.randint(1, 8)
        lim, now, sent = iv_rate_limit.Limiter(n, t), 0, []
        for _ in range(40):
            now += rng.randint(0, 3)
            inside = sum(1 for s in sent if now - t < s <= now)
            ok = lim.allow(now)
            assert ok == (inside < n)  # exact: refuses only when the window is truly full
            if ok:
                sent.append(now)
        for i in range(len(sent) - n):
            assert sent[i + n] - sent[i] >= t  # never breaks the limit
    # a token bucket with capacity N and rate N/T sends a burst, then refills: near 2N in a window of T
    tb = iv_rate_limit.TokenBucket(10, 10)
    accepted = 0
    for i in range(1000):
        accepted += tb.allow(i / 100)
    assert 18 <= accepted <= 20
    half = iv_rate_limit.TokenBucket(5, 10)
    accepted = 0
    for i in range(1000):
        accepted += half.allow(i / 100)
    assert accepted <= 10


def test_q43():
    s = iv_as_of.AsOfStore()
    s.set("k", "a", 1)
    s.set("k", "b", 3)
    assert s.get("k", 0) is None and s.get("k", 1) == "a" and s.get("k", 2) == "a" and s.get("k", 3) == "b" and s.get("x", 9) is None
    assert set(s.times) == {"k"} and set(s.values) == {"k"}  # reads do not grow the store
    got = iv_as_of.as_of_join([(1, "t"), (2, "t"), (5, "t")], [(2, "q2"), (4, "q4")])
    assert [g[2] for g in got] == [None, "q2", "q4"]
    rng = random.Random(931)
    for _ in range(200):
        s, log, t = iv_as_of.AsOfStore(), [], 0
        for _ in range(30):
            t += rng.randint(1, 3)
            k = rng.choice("AB")
            s.set(k, t * 10, t)
            log.append((k, t * 10, t))
            q, qk = rng.randint(0, t), rng.choice("AB")
            want = [v for kk, v, tt in log if kk == qk and tt <= q]
            assert s.get(qk, q) == (want[-1] if want else None)


def test_q44():
    rng = random.Random(932)
    s, model = iv_random_set.RandomSet(), set()
    for _ in range(5000):
        x = rng.randint(0, 40)
        if rng.random() < 0.5:
            assert s.insert(x) == (x not in model)
            model.add(x)
        else:
            assert s.remove(x) == (x in model)
            model.discard(x)
        assert set(s.items) == model and all(s.items[s.where[v]] == v for v in model)
    s = iv_random_set.RandomSet()
    s.insert(1)
    assert s.remove(1) and s.items == [] and s.where == {}  # removing the last element
    for x in range(10):
        s.insert(x)
    for x in (3, 7):
        s.remove(x)
    counts = {x: 0 for x in s.items}
    for _ in range(40000):
        counts[s.pick(rng)] += 1
    assert scipy_stats.chisquare(list(counts.values())).pvalue > 0.001


def test_q45():
    counts = {}
    for draws in itertools.product(range(3), repeat=3):
        xs = [1, 2, 3]
        for i, j in enumerate(draws):
            xs[i], xs[j] = xs[j], xs[i]
        counts[tuple(xs)] = counts.get(tuple(xs), 0) + 1
    assert sum(counts.values()) == 27 and 27 % 6 != 0
    assert sorted(counts.values()) == [4, 4, 4, 5, 5, 5]
    assert counts[(1, 3, 2)] == counts[(2, 1, 3)] == counts[(2, 3, 1)] == 5
    assert counts[(1, 2, 3)] == counts[(3, 1, 2)] == counts[(3, 2, 1)] == 4
    for n in range(3, 40):
        assert n**n % math.factorial(n) != 0  # never divisible, so it is never fair
        assert math.gcd(n - 1, n**n) == 1
    # the fair version: exact, by enumerating its random choices
    outcomes = {}
    class Fixed:
        def __init__(self, seq):
            self.seq = iter(seq)
        def randrange(self, _n):
            return next(self.seq)
    for draws in itertools.product(*[range(i + 1) for i in range(3, 0, -1)]):
        xs = [1, 2, 3, 4]
        iv_shuffle.shuffle(xs, Fixed(draws))
        outcomes[tuple(xs)] = outcomes.get(tuple(xs), 0) + 1
    assert len(outcomes) == 24 and set(outcomes.values()) == {1}
    # and by simulation
    rng = random.Random(933)
    freq = {}
    for _ in range(24000):
        xs = [1, 2, 3, 4]
        iv_shuffle.shuffle(xs, rng)
        freq[tuple(xs)] = freq.get(tuple(xs), 0) + 1
    assert scipy_stats.chisquare(list(freq.values())).pvalue > 0.001
    assert math.factorial(21) > 2**64 > math.factorial(20)


def test_q46():
    bad = (5, (1, None, None), (6, (4, None, None), None))
    assert not iv_bst.is_bst(bad) and iv_bst.children_only(bad)
    rng = random.Random(934)
    def tree(depth):
        if depth == 0 or rng.random() < 0.25:
            return None
        return (rng.randint(0, 40), tree(depth - 1), tree(depth - 1))
    for _ in range(1000):
        t = tree(5)
        keys = iv_bst.in_order(t)
        if len(keys) == len(set(keys)):
            assert iv_bst.is_bst(t) == (keys == sorted(keys))
    deep = None
    for k in range(100_000, 0, -1):
        deep = (k, None, deep)
    assert iv_bst.is_bst(deep)  # no recursion error at 100 000 levels


def test_q47():
    xs = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    assert round(iv_welford.naive_variance(xs), 2) == -170.67
    s = iv_welford.RunningStats()
    for x in xs:
        s.add(x)
    assert s.variance() == 30.0 and s.mean == 1e9 + 10
    assert statistics.variance([Fraction(v) for v in (4, 7, 13, 16)]) == 30
    assert math.ulp(4e18) == 512
    rng = random.Random(935)
    for _ in range(200):
        ys = [rng.gauss(0, 10) for _ in range(rng.randint(2, 40))]
        s = iv_welford.RunningStats()
        for y in ys:
            s.add(y)
        assert math.isclose(s.variance(), statistics.variance(ys), rel_tol=1e-9, abs_tol=1e-9)
    s = iv_welford.RunningStats()
    for _ in range(1000):
        s.add(1e15 + 0.125)
    assert s.variance() == 0.0  # all values equal: exactly zero
    # the exponentially weighted update against the definition, with weights lam^(age)
    lam, ys = 0.9, [rng.gauss(0, 1) for _ in range(400)]
    mean, var = ys[0], 0.0
    for y in ys[1:]:
        d = y - mean
        mean += (1 - lam) * d
        var = lam * (var + (1 - lam) * d * d)
    w = [lam**i for i in range(len(ys))][::-1]
    total = sum(w)
    m2 = sum(a * b for a, b in zip(w, ys, strict=True)) / total
    v2 = sum(a * (b - m2) ** 2 for a, b in zip(w, ys, strict=True)) / total
    assert abs(mean - m2) < 1e-6 and abs(var - v2) < 1e-6


def test_q48():
    xs = [1000, 1001, 999, 1300]
    data = iv_varint.encode(xs)
    assert len(data) == 6 and iv_varint.decode(data) == xs and 4 * 8 == 32
    deltas = [1000, 1, -2, 301]
    zig = [2 * d if d >= 0 else -2 * d - 1 for d in deltas]
    assert zig == [2000, 2, 3, 602]
    assert [len(iv_varint.encode([z // 2 if z % 2 == 0 else -(z + 1) // 2])) for z in zig] == [2, 1, 1, 2]
    assert iv_varint.encode([]) == b"" and iv_varint.encode([0, 0]) == b"\x00\x00"
    assert ((-2) % 2**64).bit_length() == 64 and math.ceil(64 / 7) == 10  # plain varint of -2: ten bytes
    rng = random.Random(936)
    for _ in range(500):
        ys = [rng.randint(-(10**12), 10**12) for _ in range(rng.randint(0, 10))]
        assert iv_varint.decode(iv_varint.encode(ys)) == ys
    assert 128 <= 602 < 16384


def _brute_k(prices, k):
    if k == 0 or len(prices) < 2:
        return 0
    best = 0
    for i in range(len(prices)):
        for j in range(i + 1, len(prices)):
            best = max(best, prices[j] - prices[i] + _brute_k(prices[j + 1 :], k - 1))
    return best


def test_q54():
    f = iv_k_trades.max_profit_k
    xs = [4, 2, 7, 6, 1, 5]
    assert f(xs, 1) == 5 and f(xs, 2) == 9 and f(xs, 10**9) == 9 == sum(max(0, b - a) for a, b in itertools.pairwise(xs))
    assert f(xs, 0) == 0 and f([5, 4, 3], 2) == 0 and f([], 3) == 0
    assert f([1, 5, 4, 9], 1) == 8
    rng = random.Random(937)
    for _ in range(300):
        ys = [rng.randint(0, 15) for _ in range(rng.randint(0, 7))]
        k = rng.randint(0, 3)
        assert f(ys, k) == _brute_k(ys, k)
        assert f(ys, k + 1) >= f(ys, k)


def test_q55():
    f = iv_histogram.largest_rectangle
    assert f([2, 1, 4, 5, 1, 3, 3]) == 8 and f([3, 3]) == 6 and f([]) == 0
    rng = random.Random(938)
    for _ in range(500):
        xs = [rng.randint(0, 6) for _ in range(rng.randint(0, 10))]
        brute = max([min(xs[i:j]) * (j - i) for i in range(len(xs)) for j in range(i + 1, len(xs) + 1)], default=0)
        assert f(xs) == brute


def test_q56():
    c = iv_lfu.LFU(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)
    assert set(c.value) == {"a", "c"} and c.get("b") is None
    rng = random.Random(939)
    for _ in range(100):
        cap = rng.randint(1, 4)
        c = iv_lfu.LFU(cap)
        model, uses, last, clock = {}, {}, {}, 0
        for _ in range(60):
            clock += 1
            k = rng.randint(0, 6)
            if rng.random() < 0.5:
                got = c.get(k)
                assert got == model.get(k)
                if k in model:
                    uses[k] += 1
                    last[k] = clock
            else:
                if k not in model and len(model) == cap:
                    old = min(model, key=lambda x: (uses[x], last[x]))
                    del model[old], uses[old], last[old]
                uses[k] = uses.get(k, 0) + 1
                last[k] = clock
                model[k] = clock
                c.put(k, clock)
            assert c.value == model
            assert all(c.by_freq.values()) and len(c.by_freq) <= cap  # no empty group is kept
    c = iv_lfu.LFU(2)  # the memory stays bounded however often one key is read
    c.put("a", 1)
    for _ in range(1000):
        c.get("a")
    assert len(c.by_freq) == 1


def test_q57():
    e = iv_matching.Engine()
    assert e.submit(1, "S", 10, 100) == [] and e.submit(2, "S", 10, 50) == []
    assert e.submit(3, "B", 11, 120) == [(1, 3, 10, 100), (2, 3, 10, 20)]
    assert e.live[2][1] == 30 and 3 not in e.live and 1 not in e.live
    rng = random.Random(940)
    for _ in range(150):
        e, oid = iv_matching.Engine(), 0
        book = []  # the slow model: a list of [side, price, age, id, quantity]
        for _ in range(80):
            if book and rng.random() < 0.25:
                o = rng.choice(book)
                assert e.cancel(o[3])
                book.remove(o)
                continue
            oid += 1
            side, price, qty = rng.choice("BS"), rng.randint(8, 12), rng.randint(1, 9)
            want, left = [], qty
            while left:
                opp = [o for o in book if o[0] != side and (o[1] <= price if side == "B" else o[1] >= price)]
                if not opp:
                    break
                o = min(opp, key=lambda o: (o[1] if side == "B" else -o[1], o[2]))
                done = min(left, o[4])
                want.append((o[3], oid, o[1], done))
                left -= done
                o[4] -= done
                if o[4] == 0:
                    book.remove(o)
            assert e.submit(oid, side, price, qty) == want
            if left:
                book.append([side, price, oid, oid, left])
            assert {k: v[1] for k, v in e.live.items()} == {o[3]: o[4] for o in book}
    assert not iv_matching.Engine().cancel(99)
    # why the stem says the IDs are unique: a repeat overwrites the map, and a later fill raises
    e = iv_matching.Engine()
    e.submit("x", "S", 10, 5)
    e.submit("x", "S", 10, 5)
    with pytest.raises(KeyError):
        e.submit("y", "B", 10, 10)


def test_q58():
    f = iv_weighted_jobs.best_total
    assert f([(0, 3, 4), (2, 5, 7), (4, 7, 3), (6, 9, 5)]) == 12
    assert f([(0, 10, 10), (0, 4, 6), (5, 9, 6)]) == 12 and f([]) == 0
    assert f([(0, 3, 4), (3, 7, 3)]) == 7  # touching is allowed
    assert 4 + 3 == 7  # earliest finishers first on the example
    rng = random.Random(941)
    for _ in range(300):
        jobs = []
        for _ in range(rng.randint(0, 7)):
            s = rng.randint(0, 10)
            jobs.append((s, s + rng.randint(1, 5), rng.randint(1, 9)))
        best = 0
        for r in range(len(jobs) + 1):
            for sub in itertools.combinations(jobs, r):
                o = sorted(sub)
                if all(o[i][1] <= o[i + 1][0] for i in range(len(o) - 1)):
                    best = max(best, sum(j[2] for j in o))
        assert f(jobs) == best


def test_q59():
    lad = iv_fenwick_depth.Ladder(16)
    lad.update(4, 3)
    lad.update(7, 5)
    lad.update(9, 2)
    assert lad.depth(7) == 7 and lad.depth(5) == 7 and lad.depth(0) == 10 and lad.depth(10) == 0
    rng = random.Random(942)
    for _ in range(100):
        n = rng.randint(1, 40)
        lad, a = iv_fenwick_depth.Ladder(n), [0] * n
        for _ in range(100):
            p, d = rng.randrange(n), rng.randint(-3, 9)
            lad.update(p, d)
            a[p] += d
            q = rng.randrange(n + 1)
            assert lad.depth(q) == sum(a[q:])
    for _ in range(100):
        n = rng.randint(1, 40)
        lad, a = iv_fenwick_depth.Ladder(n), [0] * n
        for _ in range(30):
            p = rng.randrange(n)
            d = rng.randint(0, 9)
            lad.update(p, d)
            a[p] += d
        q = rng.randint(1, sum(a) + 2)
        want = max((p for p in range(n) if sum(a[p:]) >= q), default=None)
        assert iv_fenwick_depth.highest_with_depth(lad, q) == want
    # a touched-entry count stays within the bit length
    big = iv_fenwick_depth.Ladder(1 << 20)
    i, steps = 1, 0
    while i <= big.n:
        i += i & -i
        steps += 1
    assert steps <= 21


def test_q60():
    def run(pattern, stream):
        w = iv_kmp.Watcher(pattern)
        return [i + 1 for i, x in enumerate(stream) if w.push(x)]
    assert run("ABAB", "ABABAB") == [4, 6]
    assert run("AAB", "AAAB") == [4]
    # the restart-from-zero version misses that match
    def restart(pattern, stream):
        k, out = 0, []
        for i, x in enumerate(stream):
            if x == pattern[k]:
                k += 1
                if k == len(pattern):
                    out.append(i + 1)
                    k = 0
            else:
                k = int(x == pattern[0])
        return out
    assert restart("ABAB", "ABABAB") == [4] and restart("AAB", "AAAB") == []
    rng = random.Random(943)
    for _ in range(500):
        p = "".join(rng.choice("AB") for _ in range(rng.randint(1, 5)))
        s = "".join(rng.choice("AB") for _ in range(rng.randint(0, 30)))
        assert run(p, s) == [i + len(p) for i in range(len(s) - len(p) + 1) if s[i : i + len(p)] == p]


def test_q61():
    f = iv_min_window.smallest_window
    tape = list("XAYBZACB")
    assert f(tape, list("ABC")) == (5, 7)
    assert f(tape, list("AABC")) == (1, 6)
    assert f(list("AB"), list("C")) is None
    with pytest.raises(IndexError):  # the assumption the answer states: at least one required symbol
        f(list("ABC"), [])
    rng = random.Random(944)
    for _ in range(400):
        t = [rng.choice("ABCD") for _ in range(rng.randint(0, 12))]
        need = [rng.choice("ABC") for _ in range(rng.randint(1, 4))]
        def ok(s, need=need):
            return all(s.count(x) >= need.count(x) for x in need)
        lengths = [j - i for i in range(len(t)) for j in range(i + 1, len(t) + 1) if ok(t[i:j])]
        got = f(t, need)
        assert (got is None) == (not lengths)
        if got:
            assert got[1] - got[0] + 1 == min(lengths) and ok(t[got[0] : got[1] + 1])


def test_q62():
    m, h = iv_bloom.bloom_size(100_000_000, 0.01)
    assert round(m / 1e6, 1) == 958.5 and h == 7 and round(m / 8 / 1e6) == 120
    assert round(-math.log(0.01) / math.log(2) ** 2, 3) == 9.585 and round(9.585 * math.log(2), 2) == 6.64
    assert 100_000_000 * 16 / 1e9 == 1.6 and 1.6e9 / (m / 8) > 10
    b = iv_bloom.Bloom(20_000, 0.01)
    for i in range(20_000):
        b.add(i)
    assert all(b.might_contain(i) for i in range(20_000))  # no false negatives
    false = sum(b.might_contain(i) for i in range(10**7, 10**7 + 200_000))
    assert 0.006 < false / 200_000 < 0.014
    half = iv_bloom.Bloom(20_000, 0.01)
    half.m //= 2
    half.bits = bytearray(half.m // 8 + 1)
    for i in range(20_000):
        half.add(i)
    false = sum(half.might_contain(i) for i in range(10**7, 10**7 + 50_000))
    assert 0.11 < false / 50_000 < 0.21
    assert 0.11 < (1 - math.exp(-7 * 20_000 / half.m)) ** 7 < 0.21


def test_q63():
    rng = random.Random(946)
    for _ in range(100):
        n = rng.randint(1, 9)
        v, bids = iv_best_venue.BestBid(n), [0] * n
        for _ in range(200):
            x, p = rng.randrange(n), rng.randint(0, 30)
            v.update(x, p)
            bids[x] = p
            price, venue = v.best()
            assert price == max(bids) and bids[venue] == price
            assert all(v.heap[v.pos[i]] == i for i in range(n))


def test_q64():
    assert math.ceil(10_000 / 30) == 334 and 334 * 64 / 1000 < 22
    secs = 4 * 10**13 / (500 * 10**6)
    assert secs == 80_000 and round(secs / 3600, 1) == 22.2
    assert 10**13 / (5 * 10**8) == 20_000
    assert round(math.log2(334), 1) == 8.4 and round(2 * math.log2(334)) == 17
    class Counted:  # the compares per record of a real heap, on 334 runs
        calls = 0
        def __init__(self, v):
            self.v = v
        def __lt__(self, other):
            Counted.calls += 1
            return self.v < other.v
    draw = random.Random(946)
    runs = [sorted(draw.random() for _ in range(40)) for _ in range(334)]
    merged, per_record, before = heapq.merge(*(map(Counted, r) for r in runs)), [], 0
    for _ in merged:
        per_record.append(Counted.calls - before)
        before = Counted.calls
    assert 8.4 < max(per_record[334:]) <= 17  # above the loser tree's figure, within the bound
    assert round(math.log2(10**13 / (32 * 10**9))) == 8  # a quicksort's levels before a part fits in memory
    rng = random.Random(947)
    xs = [rng.randint(0, 10**6) for _ in range(5000)]
    assert list(iv_external_sort.external_sort(xs, 300)) == sorted(xs)
    assert list(iv_external_sort.external_sort([], 10)) == []


def test_q65():
    w = [Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)]
    prob, other = iv_alias.build(w)
    assert prob[0] == 1 and prob[1] == 1 and prob[2] == Fraction(1, 2) and other[2] == 0
    def exact(prob, other):
        n = len(prob)
        p = [Fraction(0)] * n
        for i in range(n):
            p[i] += Fraction(1, n) * prob[i]
            p[other[i]] += Fraction(1, n) * (1 - prob[i])
        return p
    assert exact(prob, other) == w
    pr, ot = iv_alias.build([1 / 2, 1 / 3, 1 / 6])  # floats build another table with the same probabilities
    assert pr[1] != 1 and ot[1] == 0 and ot[2] == 1
    n = 3
    got = [0.0] * n
    for i in range(n):
        got[i] += pr[i] / n
        got[ot[i]] += (1 - pr[i]) / n
    assert got == pytest.approx([1 / 2, 1 / 3, 1 / 6], abs=1e-14)
    rng = random.Random(948)
    for _ in range(200):
        ws = [rng.randint(1, 20) for _ in range(rng.randint(1, 8))]
        pr, ot = iv_alias.build([Fraction(x) for x in ws])
        assert exact(pr, ot) == [Fraction(x, sum(ws)) for x in ws]
    counts = [0, 0, 0]
    pf = [float(x) for x in prob]
    for _ in range(60000):
        counts[iv_alias.draw(pf, other, rng)] += 1
    assert scipy_stats.chisquare(counts, [30000, 20000, 10000]).pvalue > 0.001


def test_q66():
    lv = iv_queue_position.Level(10)
    lv.add("a", 100)
    lv.add("b", 200)
    lv.add("c", 300)
    lv.cancel("b")
    lv.execute(150)
    assert lv.ahead("c") == 0 and lv.size[2] == 250
    rng = random.Random(949)
    for _ in range(200):
        lv, model, n = iv_queue_position.Level(100), [], 0
        for _ in range(60):
            op = rng.random()
            if op < 0.45 or not model:
                q = rng.randint(1, 9)
                lv.add(n, q)
                model.append([n, q])
                n += 1
            elif op < 0.65:
                o = rng.choice(model)
                lv.cancel(o[0])
                model.remove(o)
            else:
                q = rng.randint(1, 12)
                lv.execute(q)
                while q and model:
                    done = min(q, model[0][1])
                    model[0][1] -= done
                    q -= done
                    if model[0][1] == 0:
                        model.pop(0)
            for i, (oid, _) in enumerate(model):
                assert lv.ahead(oid) == sum(s for _, s in model[:i])


def test_q67():
    rng = random.Random(950)
    for _ in range(200):
        history, book, seq = [], {}, 0  # the true stream, and each state of the true book
        snaps = {0: {}}
        for _ in range(60):
            seq += 1
            p, s = rng.randint(1, 6), rng.randint(0, 5)
            book[p] = s
            if s == 0:
                del book[p]
            history.append((seq, p, s))
            snaps[seq] = dict(book)
        r = iv_snapshot.Recovering()
        arrivals = list(history)
        for i in range(len(arrivals) - 1):
            if rng.random() < 0.05:
                arrivals[i], arrivals[i + 1] = arrivals[i + 1], arrivals[i]  # reordered
        high = 0
        for seq, p, s in arrivals:
            if rng.random() < 0.05:
                continue  # lost
            r.on_delta(seq, p, s)
            high = max(high, seq)
            if rng.random() < 0.05:
                r.on_delta(seq, p, s)  # a duplicate
            if rng.random() < (0.3 if r.book is None else 0.1):  # snapshots keep coming, live or not
                last = max(0, high - rng.randint(0, 6))
                was = None if r.book is None else (dict(r.book), r.seq)
                r.on_snapshot(last, snaps[last])
                assert was is None or was == (r.book, r.seq)  # a live book is not touched
            if r.book is not None:
                assert r.book == snaps[r.seq]  # never a wrong book
    # with no loss, once live, it stays live
    r = iv_snapshot.Recovering()
    r.on_snapshot(0, {})
    for i in range(1, 50):
        assert r.on_delta(i, 1, i) == "ok"
    assert r.book == {1: 49}
    # the wrong recipe: applying every buffered update over a snapshot restores a stale size
    book = {1: 7}
    stale = [(4, 1, 3)]  # already included in a snapshot at sequence 5
    for _, p, s in stale:
        book[p] = s
    assert book[1] == 3 != 7
    r = iv_snapshot.Recovering()
    r.on_delta(4, 1, 3)
    r.on_delta(6, 2, 9)
    assert r.on_snapshot(5, {1: 7}) and r.book == {1: 7, 2: 9}
    r = iv_snapshot.Recovering()
    r.on_delta(8, 1, 3)
    assert not r.on_snapshot(5, {1: 7}) and r.book is None and r.buffer  # too old: keep waiting
    # a stale snapshot must not rewind a live book, or the next update reports a false gap
    r = iv_snapshot.Recovering()
    r.on_snapshot(100, {10: 5})
    assert r.on_delta(101, 10, 7) == "ok"
    assert r.on_snapshot(100, {10: 5}) and r.seq == 101 and r.book == {10: 7}
    assert r.on_delta(102, 10, 8) == "ok"
    # updates buffered out of order still connect to the snapshot
    r = iv_snapshot.Recovering()
    r.on_delta(12, 1, 2)
    r.on_delta(11, 1, 1)
    assert r.on_snapshot(10, {}) and r.seq == 12 and r.book == {1: 2}


def test_q68():
    f = iv_merge_runs.merge_cost
    assert f([2, 3, 4, 10]) == 33 == 5 + 9 + 19
    assert 14 + 17 + 19 == 50
    def brute(sizes, k=2):
        if len(sizes) == 1:
            return 0
        best = None
        for c in itertools.combinations(range(len(sizes)), k):
            s = sum(sizes[i] for i in c)
            rest = [sizes[i] for i in range(len(sizes)) if i not in c]
            v = s + brute([*rest, s], k)
            best = v if best is None else min(best, v)
        return best
    rng = random.Random(951)
    for _ in range(100):
        xs = [rng.randint(1, 20) for _ in range(rng.randint(1, 6))]
        assert f(xs) == brute(xs)
    assert iv_merge_runs.merge_cost_k([2, 3, 4, 10], 3) == 24 == (0 + 2 + 3) + (4 + 5 + 10)
    for _ in range(30):
        xs = [rng.randint(1, 20) for _ in range(rng.choice([3, 5, 7]))]
        assert iv_merge_runs.merge_cost_k(xs, 3) == brute(xs, 3)


def test_q72():
    f = iv_best_bid_history.best_bid_changes
    assert f([(0, 5, 10), (1, 3, 12), (2, 4, 11), (6, 7, 9)]) == [(0, 10), (1, 12), (3, 11), (4, 10), (5, None), (6, 9), (7, None)]
    assert f([(0, 5, 10), (5, 8, 10)]) == [(0, 10), (8, None)]
    rng = random.Random(952)
    for _ in range(400):
        bids = []
        for _ in range(rng.randint(0, 8)):
            o = rng.randint(0, 12)
            bids.append((o, o + rng.randint(1, 6), rng.randint(1, 6)))
        want, last = [], "start"
        for t in range(0, 20):
            live = [p for o, c, p in bids if o <= t < c]
            best = max(live) if live else None
            if best != last and not (last == "start" and best is None):
                want.append((t, best))
            last = best
        assert f(bids) == want


def test_q73():
    f = iv_range_sums.count_in_range
    xs = [3, -2, 1, 4]
    assert f(xs, 1, 3) == sum(1 <= sum(xs[i:j]) <= 3 for i in range(4) for j in range(i + 1, 5)) == 5
    class Counted(int):
        calls = 0
        def __lt__(self, other):
            Counted.calls += 1
            return int.__lt__(self, other)
    left, right = sorted(random.Random(1).sample(range(10**6), 500)), sorted(random.Random(2).sample(range(10**6), 500))
    sorted([Counted(v) for v in left] + [Counted(v) for v in right])
    assert Counted.calls < 2100  # two ascending runs are merged, not sorted afresh
    assert sum(xs[1:3]) == -1 and sum(xs[2:4]) == 5 and sum(xs[1:4]) == 3
    assert {3, 1, 2, 6} | {0} == {0, 1, 2, 3, 6}
    rng = random.Random(953)
    for _ in range(400):
        ys = [rng.randint(-6, 6) for _ in range(rng.randint(0, 12))]
        lo = rng.randint(-5, 5)
        hi = lo + rng.randint(0, 6)
        assert f(ys, lo, hi) == sum(lo <= sum(ys[i:j]) <= hi for i in range(len(ys)) for j in range(i + 1, len(ys) + 1))


def test_q74():
    f = iv_slicing.cheapest_slicing
    assert f(5, [1, 3], [1, 1]) == (22, [3, 2])
    assert 1 * 3 + 3**2 == 12 and 3 * 2 + 2**2 == 10
    def brute(total, a, b, fee=0):
        best = None
        for split in itertools.product(range(total + 1), repeat=len(a)):
            if sum(split) == total:
                c = sum(a[t] * q + b[t] * q * q + (fee if q else 0) for t, q in enumerate(split))
                best = c if best is None else min(best, c)
        return best
    rng = random.Random(954)
    for _ in range(300):
        t = rng.randint(1, 4)
        a, b = [rng.randint(0, 6) for _ in range(t)], [rng.randint(0, 3) for _ in range(t)]
        x = rng.randint(0, 7)
        cost, sent = f(x, a, b)
        assert cost == brute(x, a, b) and sum(sent) == x
        assert cost == sum(a[i] * q + b[i] * q * q for i, q in enumerate(sent))
    assert f(2, [1, 2], [1, 1]) == (5, [1, 1]) == (brute(2, [1, 2], [1, 1]), [1, 1])  # periods differ, equal split still best
    assert f(5, [2, 1], [0, 0]) == (5, [0, 5])  # no impact: everything goes to the cheapest period
    assert f(4, [1, 1], [1, 10**6]) == (4 + 16, [4, 0])  # a huge impact: almost nothing there
    # a fixed fee breaks the method: it spreads and pays twice
    cost, sent = f(5, [1, 3], [1, 1])
    assert sent == [3, 2] and cost + 2 * 100 == 222
    assert brute(5, [1, 3], [1, 1], fee=100) == 1 * 5 + 25 + 100 == 130


def test_q75():
    f = iv_pairing.max_pairs
    n, part = f([1, 2], {1: ["A", "B"], 2: ["A"]})
    assert n == 2 and part == {"A": 2, "B": 1}
    # a long augmenting path: the recursion hits Python's limit, and the explicit stack does not
    chain = {i: ([i - 1, i] if i else [0]) for i in range(3000)}
    with pytest.raises(RecursionError):
        f(list(chain), chain)
    n, part = iv_pairing.max_pairs_stack(list(chain), chain)
    assert n == 3000 and all(s in chain[b] for s, b in part.items()) and len(set(part.values())) == 3000
    rng = random.Random(955)
    for _ in range(300):
        nb, ns = rng.randint(1, 5), rng.randint(1, 5)
        comp = {b: [s for s in range(ns) if rng.random() < 0.4] for b in range(nb)}
        n, part = f(list(range(nb)), comp)
        assert len(part) == n and all(s in comp[b] for s, b in part.items()) and len(set(part.values())) == n
        best = 0
        for sellers in itertools.product([None, *range(ns)], repeat=nb):
            used = [s for s in sellers if s is not None]
            if len(used) == len(set(used)) and all(s is None or s in comp[b] for b, s in enumerate(sellers)):
                best = max(best, len(used))
        assert n == best
        assert iv_pairing.max_pairs_stack(list(range(nb)), comp)[0] == best
        greedy, taken = 0, set()
        for b in range(nb):
            s = next((x for x in comp[b] if x not in taken), None)
            if s is not None:
                taken.add(s)
                greedy += 1
        assert 2 * greedy >= best  # greedy reaches at least half


def test_q76():
    import re
    f = iv_regex.matches
    assert not f("ba", "a*b*") and f("", "a*") and f("aab", "a*b") and f("xy", "..") and f("a", "a*a")
    rng = random.Random(956)
    for _ in range(3000):
        text = "".join(rng.choice("ab") for _ in range(rng.randint(0, 6)))
        pat = ""
        for _ in range(rng.randint(0, 4)):
            pat += rng.choice("ab.") + rng.choice(["", "*"])
        assert f(text, pat) == (re.fullmatch(pat, text) is not None)
    def backtrack(text, pat, i=0, j=0):
        nonlocal_calls[0] += 1
        if j == len(pat):
            return i == len(text)
        first = i < len(text) and pat[j] in (text[i], ".")
        if j + 1 < len(pat) and pat[j + 1] == "*":
            return backtrack(text, pat, i, j + 2) or (first and backtrack(text, pat, i + 1, j))
        return first and backtrack(text, pat, i + 1, j + 1)
    nonlocal_calls = [0]
    assert not backtrack("a" * 20, "a*a*a*a*b")
    assert 10_000 < nonlocal_calls[0]
    assert math.comb(24, 4) == 10626 and 21 * 11 == 231
    assert not f("a" * 20, "a*a*a*a*b")
    # the greedy wrong answer
    assert f("a", "a*a")


def test_q77():
    f = iv_settle.fewest_transfers
    assert f([5, -5, 3, -1, -2]) == 3 and f([]) == 0 and f([0, 0]) == 0
    assert f([6, 5, -4, -4, -3]) == 4
    assert f([8, 7, 2, -8, -9]) == 3
    def groups_brute(xs):
        if not xs:
            return 0
        head, rest = xs[0], xs[1:]
        best = 0
        for r in range(len(rest) + 1):
            for c in itertools.combinations(range(len(rest)), r):
                if head + sum(rest[i] for i in c) == 0:
                    left = [rest[i] for i in range(len(rest)) if i not in c]
                    best = max(best, 1 + groups_brute(left))
        return best
    def greedy(balances):
        xs, n = sorted(balances), 0
        xs = [x for x in xs if x]
        while xs:
            xs.sort()
            lo, hi = xs[0], xs[-1]
            amt = min(-lo, hi)
            xs[0] += amt
            xs[-1] -= amt
            xs = [x for x in xs if x]
            n += 1
        return n
    assert greedy([8, 7, 2, -8, -9]) == 4 and greedy([6, 5, -4, -4, -3]) == 4
    rng = random.Random(957)
    gaps = 0
    for _ in range(300):
        xs = [rng.randint(-6, 6) for _ in range(rng.randint(1, 6))]
        xs.append(-sum(xs))
        ys = [x for x in xs if x]
        assert f(xs) == len(ys) - groups_brute(ys)
        assert f(xs) <= greedy(xs)
        gaps += f(xs) < greedy(xs)
    assert gaps > 0  # the largest-to-largest rule really does lose sometimes


def test_q78():
    f = iv_gapped.best_gapped
    assert f([7, -2, -9, 4, 15], 2) == 24 == 7 - 2 + 4 + 15
    assert f([-3, -1, -2], 2) == -1
    assert 7 + 4 + 15 == 26
    def brute(xs, k):
        best = None
        for r in range(1, len(xs) + 1):
            for c in itertools.combinations(range(len(xs)), r):
                if all(b - a <= k for a, b in itertools.pairwise(c)):
                    s = sum(xs[i] for i in c)
                    best = s if best is None else max(best, s)
        return best
    rng = random.Random(958)
    for _ in range(400):
        xs = [rng.randint(-9, 9) for _ in range(rng.randint(1, 9))]
        k = rng.randint(1, 4)
        assert f(xs, k) == brute(xs, k)
        assert f(xs, 1) == iv_kadane.best_stretch(xs)[0]
        assert f(xs, len(xs)) == (sum(x for x in xs if x > 0) or max(xs))


def test_q79():
    f = iv_sum_mins.sum_of_minimums
    assert f([2, 4, 1, 3]) == 17 == 2 * 2 + 4 * 1 + 1 * 6 + 3 * 1
    assert f([2, 2]) == 6 and f([]) == 0
    def count(xs, left_strict, right_strict):
        total = 0
        n = len(xs)
        for j, v in enumerate(xs):
            lo = j - 1
            while lo >= 0 and (xs[lo] > v if not left_strict else xs[lo] >= v):
                lo -= 1
            hi = j + 1
            while hi < n and (xs[hi] > v if not right_strict else xs[hi] >= v):
                hi += 1
            total += v * (j - lo) * (hi - j)
        return total
    assert count([2, 2], True, True) == 8 and count([2, 2], False, False) == 4
    rng = random.Random(959)
    for _ in range(500):
        xs = [rng.randint(0, 3) for _ in range(rng.randint(0, 10))]
        brute = sum(min(xs[i:j]) for i in range(len(xs)) for j in range(i + 1, len(xs) + 1))
        assert f(xs) == brute


def test_q80():
    f = iv_best_mean.best_mean
    xs = [2, 10, -6, -5, 40, 4]
    assert abs(f(xs, 4) - 9.75) < 1e-6 and sum(xs[1:5]) == 39 and 39 / 4 == 9.75
    assert f([1, 2], 5) is None  # no stretch that long: not a silent number
    assert sum(xs) == 45 and sum(xs) / 6 == 7.5
    assert abs(f([9, 1, 9], 2) - Fraction(19, 3)) < 1e-6 and (9 + 1) / 2 == 5
    def exact(ys, k):
        return max(Fraction(sum(ys[i:j]), j - i) for i in range(len(ys)) for j in range(i + k, len(ys) + 1))
    def short_lengths(ys, k):
        return max(Fraction(sum(ys[i : i + w]), w) for w in range(k, min(2 * k, len(ys) + 1)) for i in range(len(ys) - w + 1))
    rng = random.Random(960)
    for _ in range(300):
        ys = [rng.randint(-9, 9) for _ in range(rng.randint(1, 10))]
        k = rng.randint(1, len(ys))
        assert abs(f(ys, k) - exact(ys, k)) < 1e-6
        assert short_lengths(ys, k) == exact(ys, k)
        assert abs(f(ys, 1) - max(ys)) < 1e-6
        assert abs(f(ys, len(ys)) - Fraction(sum(ys), len(ys))) < 1e-6
    # the smallest gap between two distinct means of integer lists
    a, b = Fraction(1, 9), Fraction(1, 10)
    assert a - b == Fraction(1, 90) >= Fraction(1, 10**2)
