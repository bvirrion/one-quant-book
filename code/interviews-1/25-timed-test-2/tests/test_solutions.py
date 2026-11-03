"""Every number printed in the answers of "Timed Test 2": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F
from itertools import combinations, permutations

import numpy as np

NONNUMERIC = {}


def test_q1():
    assert 5 * F(1, 4) + 3 * F(1, 6) == F(7, 4)
    rng = np.random.default_rng(1)
    bag = np.array([0] * 5 + [1] * 3)
    left = []
    for _ in range(100_000):
        o = rng.permutation(bag)
        r = np.cumsum(o == 0)
        b = np.cumsum(o == 1)
        i = np.argmax((r == 5) | (b == 3))
        left.append(7 - i)
    assert abs(np.mean(left) - 1.75) < 0.01


def test_q2():
    assert 6 + 18 - 1 / (F(1, 6) + F(1, 18)) == F(39, 2)
    rng = np.random.default_rng(2)
    t = []
    for _ in range(40_000):
        a = b = False
        n = 0
        while not (a and b):
            s = rng.integers(1, 7) + rng.integers(1, 7)
            a |= s == 7
            b |= s == 11
            n += 1
        t.append(n)
    assert abs(np.mean(t) - 19.5) < 0.2


def test_q3():
    d = F(20, 30)
    assert d == F(2, 3)
    assert d * 90 - 60 == 0 and d * 120 - 60 == 20
    assert d * 100 - 60 == F(20, 3)
    q = F(100 - 90, 30)
    assert q == F(1, 3) and q * 20 == F(20, 3)
    assert round(7 - 20 / 3, 2) == 0.33


def test_q4():
    # Exact area under the curve, term by term.
    area = F(1) - F(4, 3) + F(1, 2)
    assert area == F(1, 6)
    # Second route: density 2u for each square root, over the triangle u + v < 1 (on a fine lattice).
    m = 2000
    u = (np.arange(m) + 0.5) / m
    uu, vv = np.meshgrid(u, u)
    lattice = (4 * uu * vv * (uu + vv < 1)).sum() / m**2
    assert abs(lattice - 1 / 6) < 1e-3
    assert F(1, 24) * 4 == area
    rng = np.random.default_rng(4)
    x, y = rng.random((2, 4_000_000))
    assert abs((np.sqrt(x) + np.sqrt(y) < 1).mean() - 1 / 6) < 0.001
    # The event lies inside the triangle of the straight-line wrong answer.
    inside = np.sqrt(x) + np.sqrt(y) < 1
    assert (x + y < 1)[inside].all()
    assert abs((x + y < 1).mean() - 0.5) < 0.001


def test_q5():
    v = F(math.comb(10, 5) ** 2, math.comb(20, 10))
    assert math.comb(10, 5) ** 2 == 63_504 and math.comb(20, 10) == 184_756
    assert round(float(v), 3) == 0.344
    # A second route: list every placement of 10 heads in 20 flips.
    hits = sum(sum(p < 10 for p in c) == 5 for c in combinations(range(20), 10))
    assert F(hits, math.comb(20, 10)) == v
    # The placements over all first-half counts sum to one (Vandermonde).
    assert sum(math.comb(10, k) ** 2 for k in range(11)) == math.comb(20, 10)
    assert round(math.sqrt(10 * math.pi) / (5 * math.pi), 3) == 0.357
    # A simulation of the condition itself.
    rng = np.random.default_rng(5)
    flips = rng.random((1_000_000, 20)) < 0.5
    ten = flips.sum(axis=1) == 10
    assert abs((flips[ten, :10].sum(axis=1) == 5).mean() - float(v)) < 0.003
    # The wrong answer, and the factor of the follow-up with its large-sample limit.
    free = F(math.comb(10, 5), 2**10)
    assert round(float(free), 3) == 0.246
    assert round(float(v / free), 2) == 1.40
    n = 2000
    ratio = math.exp(4 * math.lgamma(2 * n + 1) - 4 * math.lgamma(n + 1) - math.lgamma(4 * n + 1))
    wide = math.exp(math.lgamma(2 * n + 1) - 2 * math.lgamma(n + 1) - 2 * n * math.log(2))
    assert abs(ratio / wide - math.sqrt(2)) < 0.001
    # Conditional variance of the count in the first half is half of the free one.
    mean = sum(k * math.comb(10, k) ** 2 for k in range(11)) / math.comb(20, 10)
    var = sum((k - mean) ** 2 * math.comb(10, k) ** 2 for k in range(11)) / math.comb(20, 10)
    assert abs(mean - 5) < 1e-12 and abs(var - 2.5 * 10 / 19) < 1e-12


def test_q6():
    # Exact sums over even counts, truncated far beyond any printed digit.
    t = sum(F(1, 4) ** j for j in range(1, 200))
    s = sum(2 * j * F(1, 4) ** j for j in range(1, 200))
    assert abs(float(t) - 1 / 3) < 1e-12
    assert abs(float(s) - 8 / 9) < 1e-12
    assert abs(float(s / t) - 8 / 3) < 1e-12

    # The conditional law of N / 2 is geometric with success chance 3/4, mean 4/3.
    assert abs(sum(j * 3 * F(1, 4) ** j for j in range(1, 200)) - F(4, 3)) < F(1, 10**12)

    # Any coin: the formula against a direct sum, then the limit case.
    def even_mean(p):
        q = 1 - p
        w = [q ** (2 * j - 1) * p for j in range(1, 3000)]
        return sum(2 * j * x for j, x in enumerate(w, 1)) / sum(w)

    for p in (0.5, 0.25, 0.9):
        assert abs(even_mean(p) - 2 / (1 - (1 - p) ** 2)) < 1e-9
    assert abs(even_mean(0.999) - 2) < 0.01

    rng = np.random.default_rng(6)
    n = rng.geometric(0.5, 3_000_000)
    assert abs((n % 2 == 0).mean() - 1 / 3) < 0.001
    assert abs(n[n % 2 == 0].mean() - 8 / 3) < 0.005


def test_q7():
    v = F(12, 38)
    assert v == F(6, 19) and round(float(v), 3) == 0.316
    # Second route: pairs of slots.
    assert math.comb(39, 2) == 741 and 3 * math.comb(13, 2) == 234
    assert F(234, 741) == v

    # The general formula against a listing of every pair of slots, then its two limits.
    def together(h):
        slots = [i // h for i in range(3 * h)]
        pairs = list(combinations(slots, 2))
        return F(sum(a == b for a, b in pairs), len(pairs))

    for h in (1, 2, 3, 13):
        assert together(h) == F(h - 1, 3 * h - 1)
    assert together(1) == 0
    assert abs(float(F(10**6 - 1, 3 * 10**6 - 1)) - 1 / 3) < 1e-6

    # A simulation of the whole deal, conditioning on your hand.
    rng = np.random.default_rng(7)
    n = 200_000
    positions = rng.permuted(np.tile(np.arange(52), (n, 1)), axis=1)[:, :4] // 13
    two = (positions == 0).sum(axis=1) == 2
    rest = np.sort(positions[two], axis=1)[:, 2:]
    assert abs((rest[:, 0] == rest[:, 1]).mean() - float(v)) < 0.01


def test_q8():
    assert 10 * F(2, 19) == F(20, 19)
    rng = np.random.default_rng(8)
    c = []
    for _ in range(100_000):
        p = rng.permutation(20)
        a = p // 2
        c.append((a == np.roll(a, 1)).sum())
    assert abs(np.mean(c) - 20 / 19) < 0.01
    # The general mean, by enumeration, and its limit of validity: with one couple the two are simply adjacent.
    for couples in (2, 3, 4):
        seats = 2 * couples
        arrangements = list(permutations(range(1, seats)))
        total = sum(sum(((0, *p)[i] // 2 == (0, *p)[(i + 1) % seats] // 2) for i in range(seats)) for p in arrangements)
        assert F(total, len(arrangements)) == F(2 * couples, 2 * couples - 1)
    # One couple is the exception: the two are simply adjacent, a count of 1, where the formula would say 2.
    assert F(2 * 1, 2 * 1 - 1) == 2


def test_q9():
    assert round(0.24 / 0.99, 3) == 0.242
    n = 100
    r = 0.24 / 0.99
    w = np.ones(n) / n
    c = 0.09 * ((1 - r) * np.eye(n) + r * np.ones((n, n)))
    assert abs(math.sqrt(w @ c @ w) - 0.15) < 1e-12
    assert abs(0.3 * math.sqrt(0.01 + 0.99 * 1) - 0.3) < 1e-12
    assert round(0.3 * math.sqrt(0.01), 2) == 0.03
    assert round(0.3 * math.sqrt(0.01 + 0.99 * 0.15), 3) == 0.119


def test_q10():
    v = (5 - math.pi) / 4
    assert round(v, 4) == 0.4646
    assert round(1 - 0.25 - 1 / 3, 2) == 0.42
    rng = np.random.default_rng(10)
    x, y = rng.random((2, 8_000_000))
    q = np.rint(x / y)
    assert abs((q % 2 == 0).mean() - v) < 0.001
    s = 0.25 + sum(1 / (4 * k - 1) - 1 / (4 * k + 1) for k in range(1, 400_000))
    assert abs(s - v) < 1e-5


def test_q11():
    p, q = 0.6, 0.4
    a = p**4 * (1 + 4 * q + 10 * q * q)
    assert round(a, 3) == 0.544
    b = 20 * p**3 * q**3
    assert round(b, 3) == 0.276
    d = p * p / (p * p + q * q)
    assert round(d, 3) == 0.692
    assert round(a + b * d, 3) == 0.736

    def f(i, j, memo={}):  # noqa: B006
        if i >= 4 and i - j >= 2:
            return 1.0
        if j >= 4 and j - i >= 2:
            return 0.0
        if i == j and i >= 3:
            return d
        if (i, j) not in memo:
            memo[(i, j)] = p * f(i + 1, j) + q * f(i, j + 1)
        return memo[(i, j)]

    assert abs(f(0, 0) - (a + b * d)) < 1e-12


def test_q12():
    s = sum(n * n * F(1, 2**n) for n in range(1, 300))
    assert abs(float(s) - 6) < 1e-12
    x = F(1, 2)
    assert x * (1 + x) / (1 - x) ** 3 == 6
    assert x * (1 + 4 * x + x * x) / (1 - x) ** 4 == 26
    assert abs(float(sum(n**3 * F(1, 2**n) for n in range(1, 300))) - 26) < 1e-12
