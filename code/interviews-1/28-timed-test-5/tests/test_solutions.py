"""Every number printed in the answers of "Timed Test 5": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F
from itertools import combinations, product

import numpy as np
from scipy import integrate, stats

NONNUMERIC = {}


def test_q1():
    assert round(5 * math.exp(-2), 3) == 0.677
    rng = np.random.default_rng(1)
    t = rng.gamma(3, 0.5, 4_000_000)
    assert abs(t.mean() - 1.5) < 0.002 and abs(t.var() - 0.75) < 0.003
    assert abs((t > 1).mean() - 5 * math.exp(-2)) < 0.001
    assert round(1 - stats.norm.cdf((1 - 1.5) / math.sqrt(0.75)), 2) == 0.72


def test_q2():
    assert 2 * F(35, 12) + 2 * F(7, 2) ** 2 == F(91, 3)
    rng = np.random.default_rng(2)
    s = []
    for n in rng.geometric(0.5, 400_000):
        s.append(rng.integers(1, 7, n).sum())
    s = np.array(s)
    assert abs(s.mean() - 7) < 0.03 and abs(s.var() - 91 / 3) < 0.3


def test_q3():
    assert F(4, 6) * F(5, 7) == F(10, 21)
    c = integrate.quad(lambda p: p**3 * (1 - p), 0, 1)[0]
    m = integrate.quad(lambda p: p**4 * (1 - p), 0, 1)[0] / c
    v = integrate.quad(lambda p: p**5 * (1 - p), 0, 1)[0] / c
    assert abs(m - 2 / 3) < 1e-9 and abs(v - 10 / 21) < 1e-9
    assert round(4 / 9, 3) == 0.444 and round(10 / 21, 3) == 0.476


def test_q4():
    runs = []
    for c in combinations(range(10), 5):
        s = [i in c for i in range(10)]
        runs.append(1 + sum(a != b for a, b in zip(s, s[1:], strict=False)))
    assert len(runs) == 252 and F(sum(runs), 252) == 6
    assert F(runs.count(2), 252) == F(1, 126)
    assert 1 + 9 * F(1, 2) == F(11, 2)
    assert 2 * F(5, 10) * F(5, 9) == F(5, 9)

def test_q5():
    n = sum(1 for a in product(range(1, 7), repeat=3) if (a[0] * a[1] * a[2]) % 6 == 0)
    assert n == 133
    assert 27 + 64 - 8 == 83


def test_q6():
    assert round(1 - math.exp(-0.5), 3) == 0.393
    assert round(math.sqrt(2 * math.log(2)), 2) == 1.18
    rng = np.random.default_rng(6)
    x, y = rng.standard_normal((2, 4_000_000))
    r = np.hypot(x, y)
    assert abs((r < 1).mean() - 0.3935) < 0.001
    assert abs(np.median(r) - 1.1774) < 0.002
    assert abs(r.mean() - math.sqrt(math.pi / 2)) < 0.001
    assert round(math.sqrt(math.pi / 2), 2) == 1.25


def test_q7():
    good = 0
    tot = 0
    for c in combinations(range(10), 3):
        a = b = 0
        ok = True
        for i in range(10):
            if i in c:
                b += 1
            else:
                a += 1
            ok &= a > b
        good += ok
        tot += 1
    assert tot == 120 and good == 48 and F(good, tot) == F(2, 5)
    assert 2 * math.comb(9, 2) == 72


def test_q8():
    assert 120 * F(7, 64) == F(105, 8)
    assert F(120 * 3 * 7, 64) == F(315, 8)
    assert 105 / 8 + 315 / 8 == 52.5
    rng = np.random.default_rng(8)
    t = []
    for _ in range(60_000):
        u = np.triu(rng.random((10, 10)) < 0.5, 1).astype(np.int64)
        a = u + u.T
        t.append(np.trace(a @ a @ a) / 6)
    assert abs(np.mean(t) - 15) < 0.1
    assert abs(np.var(t) - 52.5) < 1.5
    assert 39.375 / 13.125 == 3
    assert 0.0625 / 3.9e-5 > 1000


def test_q9():
    n = 2**1000
    s = str(n)
    assert len(s) == 302 and s[:4] == "1071"
    assert round(math.exp(0.069), 2) == 1.07
    x = 0.0
    c = 0
    for _ in range(200_000):
        x = (x + math.log10(2)) % 1
        c += x < math.log10(2)
    assert abs(c / 200_000 - 0.30103) < 0.001


def test_q10():
    v = integrate.quad(lambda t: (1 - t / 10) * (1 - t / 15), 0, 10)[0]
    assert abs(v - 35 / 9) < 1e-9
    assert abs(1 / (0.1 + 1 / 15) - 6) < 1e-9
    rng = np.random.default_rng(10)
    u = rng.uniform(0, 10, 4_000_000)
    w = rng.uniform(0, 15, 4_000_000)
    assert abs(np.minimum(u, w).mean() - 35 / 9) < 0.005


def test_q11():
    assert F(4, 5) / 3 == F(4, 15)
    assert F(1, 5) + 3 * F(4, 15) == 1
    assert F(3 - 1, 3 * (3 - 2)) == F(2, 3)
    assert F(5 - 1, 5 * (5 - 2)) == F(4, 15)
    rng = np.random.default_rng(11)
    n = 500_000
    win = 0
    for _ in range(n):
        p = rng.integers(5)
        c = rng.integers(5)
        opts = [d for d in range(5) if d not in (p, c)]
        o = opts[rng.integers(len(opts))]
        rest = [d for d in range(5) if d not in (c, o)]
        win += rest[rng.integers(3)] == p
    assert abs(win / n - 4 / 15) < 0.002


def test_q12():
    assert f"{math.exp(-8):.1e}" == "3.4e-04"
    assert 25 / 400 == 0.0625
    z = 1 - stats.norm.cdf(3.9)
    assert f"{z:.1e}" == "4.8e-05"
    ex = stats.binom.sf(69, 100, 0.5)
    assert f"{ex:.1e}" == "3.9e-05"
    assert round(math.exp(-8) / ex) == 9
