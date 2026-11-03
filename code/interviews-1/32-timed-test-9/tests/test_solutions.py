"""Every number printed in the answers of "Timed Test 9": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F
from itertools import combinations, product

import numpy as np
from scipy import integrate, stats

NONNUMERIC = {}


def test_q1():
    assert F(4) - F(4, 3) == F(8, 3)
    assert (1 + F(1, 2) * 2) / F(3, 4) == F(8, 3)
    rng = np.random.default_rng(1)
    g = rng.geometric(0.5, (2, 3_000_000))
    assert abs(g.max(axis=0).mean() - 8 / 3) < 0.005


def test_q2():
    v = list(product([0, 1], repeat=3))
    n = 0
    for a, b, c in combinations(v, 3):
        d = [sum((x - y) ** 2 for x, y in zip(p, q, strict=True)) for p, q in ((a, b), (b, c), (a, c))]
        n += d[0] == d[1] == d[2]
    assert n == 8 and F(n, 56) == F(1, 7)
    assert math.comb(8, 3) == 56


def test_q3():
    for nv, mean, var in ((1, 1.0, 0.5), (4, 0.4, 0.8)):
        w = lambda t, nv=nv: stats.norm.pdf(t) * stats.norm.pdf(2, t, math.sqrt(nv))  # noqa: E731
        z = integrate.quad(w, -12, 12)[0]
        m = integrate.quad(lambda t, w=w: t * w(t), -12, 12)[0] / z
        s = integrate.quad(lambda t, w=w: t * t * w(t), -12, 12)[0] / z - m * m
        assert abs(m - mean) < 1e-7 and abs(s - var) < 1e-7


def test_q4():
    d = [i for i in range(1, 10**6 + 1) if 10**6 % i == 0]
    assert len(d) == 49
    assert F(sum(1 for x in d if x % 1000 == 0), 49) == F(16, 49)
    assert F(4, 7) ** 2 == F(16, 49)
    assert d[24] == 1000


def test_q5():
    assert round(stats.norm.cdf(0.71), 2) == 0.76
    assert round(1 / math.sqrt(2), 2) == 0.71
    rng = np.random.default_rng(5)
    x, y = rng.standard_normal((2, 4_000_000))
    assert abs((x > y + 1).mean() - 0.24) < 0.001
    k = np.abs(x + y - 2) < 0.01
    assert abs(x[k].mean() - 1) < 0.02
    assert abs(np.polyfit(x + y, x, 1)[0] - 0.5) < 0.002


def test_q6():
    rng = np.random.default_rng(6)
    x, y = rng.exponential(size=(2, 4_000_000))
    assert abs(np.minimum(x, y).mean() - 0.5) < 0.001
    assert abs(np.maximum(x, y).mean() - 1.5) < 0.002
    assert abs((x > y + 1).mean() - 1 / (2 * math.e)) < 0.001
    assert round(1 / (2 * math.e), 3) == 0.184


def test_q7():
    p = sum(math.exp(-1) / math.factorial(k) for k in range(0, 40, 2))
    assert abs(p - (1 + math.exp(-2)) / 2) < 1e-12
    assert round(p, 3) == 0.568
    assert round(math.exp(-3), 3) == 0.050
    assert abs(sum(math.exp(-6) * 6**k / math.factorial(k) * 2.0**-k for k in range(80)) - math.exp(-3)) < 1e-12
    rng = np.random.default_rng(7)
    n = rng.poisson(6, 4_000_000)
    assert abs((rng.binomial(n, 0.5) == 0).mean() - math.exp(-3)) < 0.0005


def test_q8():
    c = {"two": 0, "one": 0}
    for r in product(range(6), repeat=5):
        s = sorted(r.count(v) for v in set(r))
        if s == [1, 2, 2]:
            c["two"] += 1
        if s == [1, 1, 1, 2]:
            c["one"] += 1
    assert c["two"] == 1800 and F(1800, 7776) == F(25, 108)
    assert round(25 / 108, 3) == 0.231
    assert c["one"] == 3600 and round(3600 / 7776, 3) == 0.463
    assert 6 * math.comb(5, 3) * math.factorial(5) // 2 == 3600
    assert 6 * 5 * 4 * 30 == 3600


def test_q9():
    mu = np.array([0.05, 0.10])
    s = np.diag([0.01, 0.04])
    w = np.linalg.solve(s, mu)
    assert abs(w[0] / w[1] - 2) < 1e-12
    w = w / w.sum()
    assert np.allclose(w, [2 / 3, 1 / 3])
    r = w @ mu
    v = w @ s @ w
    assert round(r * 100, 2) == 6.67 and round(v * 1e4, 1) == 88.9
    assert round(math.sqrt(v) * 100, 2) == 9.43
    assert abs(r / math.sqrt(v) - math.sqrt(0.5)) < 1e-12
    x = np.linspace(0.01, 0.99, 981)
    sh = (x * 0.05 + (1 - x) * 0.1) / np.sqrt(x**2 * 0.01 + (1 - x) ** 2 * 0.04)
    assert abs(x[sh.argmax()] - 2 / 3) < 0.002


def test_q10():
    n = math.comb(13, 2) * 36 * 44
    assert n == 123552 and math.comb(52, 5) == 2598960
    assert round(n / 2598960, 4) == 0.0475
    assert round(2 * n / 2598960, 3) == 0.095
    assert 80 * 1600 == 128000 and 2598960 / 128000 > 20
    rng = np.random.default_rng(10)
    deck = np.repeat(np.arange(13), 4)
    c = 0
    m = 200_000
    for _ in range(m):
        s = rng.choice(deck, 5, replace=False)
        c += sorted(np.bincount(s).tolist())[-3:] == [1, 2, 2]
    assert abs(c / m - 0.0475) < 0.002


def test_q11():
    rng = np.random.default_rng(11)
    n = 10
    m = 200_000
    last = nine = 0
    for _ in range(m):
        free = list(range(n))
        free.remove(s := int(rng.integers(n)))
        for k in range(1, n):
            if k in free:
                free.remove(k)
                got = k
            else:
                got = free.pop(int(rng.integers(len(free))))
            if k == 8:
                nine += got != 8
            if k == 9:
                last += got == 9
        assert s >= 0
    assert abs(last / m - 0.5) < 0.004
    assert abs(nine / m - 1 / 3) < 0.004


def test_q12():
    assert len(str(math.factorial(100))) == 158
    assert str(math.factorial(100))[:2] == "93"
    a = 100 * math.log(100) - 100
    assert round(100 * math.log(100), 1) == 460.5 and round(a, 1) == 360.5
    assert round(0.5 * math.log(2 * math.pi * 100), 2) == 3.22
    assert round(a + 0.5 * math.log(2 * math.pi * 100), 1) == 363.7
    assert abs(math.lgamma(101) / math.log(10) - 157.97) < 0.01
    assert round(363.7 / 2.303, 1) == 157.9 and int(363.7 / 2.303) + 1 == 158
    assert round(360.5 / 2.303, 1) == 156.5
    n = 10**6
    assert abs(math.exp(math.lgamma(n + 1) / n) / n - 1 / math.e) < 1e-3
