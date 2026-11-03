"""Every number printed in the answers of "Timed Test 8": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F
from itertools import combinations, product

import numpy as np
from scipy import stats

NONNUMERIC = {}


def test_q1():
    a = 1 - F(5, 6) ** 4
    b = 1 - F(35, 36) ** 24
    assert a == 1 - F(625, 1296)
    assert round(float(a), 3) == 0.518 and round(float(b), 3) == 0.491
    assert round(float(F(35, 36) ** 24), 3) == 0.509
    assert round(1 - math.exp(-2 / 3), 3) == 0.487
    assert round(math.comb(24, 2) / 1296, 2) == 0.21 and round(math.comb(4, 2) / 36, 2) == 0.17
    rng = np.random.default_rng(1)
    d = rng.integers(1, 7, (1_000_000, 4))
    assert abs((d == 6).any(axis=1).mean() - float(a)) < 0.002
    d = rng.integers(1, 7, (200_000, 24, 2))
    assert abs((d == 6).all(axis=2).any(axis=1).mean() - float(b)) < 0.004
    # The 0.21 and the 0.17 are expected pairs of hits, not chances: the chance of two or more is far smaller.
    def expected_pairs(tries, p):
        return sum(math.comb(tries, h) * p**h * (1 - p) ** (tries - h) * math.comb(h, 2) for h in range(tries + 1))

    assert expected_pairs(24, F(1, 36)) == F(math.comb(24, 2), 1296)
    assert expected_pairs(4, F(1, 6)) == F(math.comb(4, 2), 36)
    two_plus = [1 - stats.binom.cdf(1, 24, 1 / 36), 1 - stats.binom.cdf(1, 4, 1 / 6)]
    assert round(two_plus[0], 3) == 0.143 and round(two_plus[1], 3) == 0.132
    # Taking the pairs off the linear count moves the two in the right order.
    assert F(2, 3) - F(276, 1296) < b < F(2, 3) and F(2, 3) - F(1, 6) < a < F(2, 3)


def test_q2():
    m = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    n = sum(1 for w in product(m, repeat=4) if sum(x for x, _ in w) == 0 and sum(y for _, y in w) == 0)
    assert n == 36 and F(n, 256) == F(9, 64)
    assert 2 * 6 + 24 == 36
    assert F(math.comb(4, 2), 16) ** 2 == F(9, 64)
    assert round(9 / 64, 3) == 0.141


def test_q3():
    assert abs(4 / 0.04 - 100) < 1e-9
    t = np.arange(0, 3000)
    assert abs((4 * 1.04**t / 1.08 ** (t + 1)).sum() - 100) < 1e-6
    assert round(4 / 0.03, 1) == 133.3


def test_q4():
    n = sum(1 for a in product(range(1, 7), repeat=3) if max(a) - min(a) == 5)
    assert n == 30 and 216 - 250 + 64 == 30 and F(30, 216) == F(5, 36)
    assert 2 * 3 + 4 * 6 == 30


def test_q5():
    rng = np.random.default_rng(5)
    x, y = rng.random((2, 4_000_000))
    k = x < 0.5
    assert abs((x[k] + y[k] < 1).mean() - 0.75) < 0.001
    a = 0.1
    k = x < a
    assert abs((x[k] + y[k] < 1).mean() - (1 - a / 2)) < 0.002


def test_q6():
    t = [(a, b) for a in range(7) for b in range(a, 7)]
    assert len(t) == 28
    n = sum(1 for s, u in combinations(t, 2) if set(s) & set(u))
    assert n == 147 and math.comb(28, 2) == 378 and F(n, 378) == F(7, 18)
    assert F(1, 4) * F(6, 27) + F(3, 4) * F(12, 27) == F(7, 18)
    assert F(12, 27) == F(4, 9)


def test_q7():
    rng = np.random.default_rng(7)
    t = []
    for _ in range(400_000):
        n = 1
        p = rng.random()
        while True:
            c = rng.random()
            n += 1
            if c < p:
                break
            p = c
        t.append(n)
    t = np.array(t)
    assert abs(t.mean() - math.e) < 0.005
    assert abs((t == 2).mean() - 0.5) < 0.003 and abs((t == 3).mean() - 1 / 3) < 0.003
    assert round(2 * 0.5 + 3 / 3, 6) == 2


def test_q8():
    def v(a, b, p):
        if a == 0:
            return 1.0
        if b == 0:
            return 0.0
        return p * v(a - 1, b, p) + (1 - p) * v(a, b - 1, p)

    assert abs(v(2, 3, 0.5) - 11 / 16) < 1e-12
    assert abs(v(2, 3, 0.6) - 0.8208) < 1e-12
    assert abs(0.4**4 + 4 * 0.6 * 0.4**3 - 0.1792) < 1e-12
    assert v(2, 2, 0.5) == 0.5


def test_q9():
    assert round(math.pi / 6, 3) == 0.524 and round(6 / math.pi, 2) == 1.91
    assert round(math.pi**5) == 306
    assert round(math.pi**5 / 120, 2) == 2.55
    r = math.pi**5 / 120 / 1024
    assert round(r, 4) == 0.0025 and 390 < 1 / r < 410
    rng = np.random.default_rng(9)
    p = rng.uniform(-1, 1, (2_000_000, 3))
    assert abs(((p**2).sum(axis=1) < 1).mean() - math.pi / 6) < 0.001
    p = rng.uniform(-1, 1, (2_000_000, 10))
    assert abs(((p**2).sum(axis=1) < 1).mean() - r) < 0.0002


def test_q10():
    rng = np.random.default_rng(10)
    d = np.array([1] * 4 + [2] * 4 + [0] * 44)
    t = []
    for _ in range(200_000):
        s = rng.permutation(d)
        a = int((s == 1).argmax())
        t.append(int((s[:a] == 2).sum()))
    assert abs(np.mean(t) - 0.8) < 0.006
    assert F(48, 5) * F(4, 48) == F(4, 5)


def test_q11():
    tot = stops = alld = 0
    for f in product(range(6), repeat=5):
        tot += 1
        stops += len(set(f))
        alld += len(set(f)) == 5
    assert tot == 7776
    assert F(stops, tot) == F(4651, 1296)
    assert round(4651 / 1296, 2) == 3.59
    assert F(alld, tot) == F(5, 54) and round(5 / 54, 3) == 0.093
    assert 6 * (1 - F(3125, 7776)) == F(4651, 1296)


def test_q12():
    r = np.array([[1, 0.5], [0.5, 1]])
    c = np.array([0.5, 0.5])
    b = np.linalg.solve(r, c)
    assert np.allclose(b, [1 / 3, 1 / 3])
    assert abs(c @ b - 1 / 3) < 1e-12
    assert F(1, 3) - F(1, 4) == F(1, 12)
    assert abs(c @ np.linalg.solve(np.eye(2), c) - 0.5) < 1e-12
