"""Every number printed in the answers of "Timed Test 10": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F
from itertools import product

import numpy as np
from scipy import integrate, stats

NONNUMERIC = {}


def test_q1():
    rng = np.random.default_rng(1)
    s = rng.random((4_000_000, 3)).sum(axis=1)
    assert abs(((s > 1) & (s < 2)).mean() - 2 / 3) < 0.001
    assert abs(s.std() - 0.5) < 0.001
    assert round(stats.norm.cdf(1) - stats.norm.cdf(-1), 2) == 0.68


def test_q2():
    n = sum(1 for b in product(range(3), repeat=5) if len(set(b)) == 3)
    assert n == 150 and 243 - 96 + 3 == 150 and F(150, 243) == F(50, 81)
    assert 3 * math.comb(5, 3) * 2 == 60 and 3 * math.comb(5, 2) * math.comb(3, 2) == 90
    assert 243 - 96 == 147
    assert round(50 / 81, 3) == 0.617


def test_q3():
    assert 4 / 25 == 0.16
    assert round(stats.norm.sf(2.5), 4) == 0.0062
    assert round(0.16 / 0.0124) == 13
    rng = np.random.default_rng(3)
    x = rng.normal(10, 2, 4_000_000)
    assert abs((np.abs(x - 10) >= 5).mean() - 0.0124) < 0.0005
    # A three-point law at +-5 and 0 attains the bound.
    assert 0.16 * 25 == 4


def test_q4():
    a, b, c = (2, 4, 9), (1, 6, 8), (3, 5, 7)
    assert sum(x > y for x, y in product(a, b)) == 5
    assert sum(x > y for x, y in product(b, c)) == 5
    assert sum(x > y for x, y in product(c, a)) == 5
    assert sum(a) == sum(b) == sum(c) == 15


def test_q5():
    rng = np.random.default_rng(5)
    u = rng.exponential(10, 4_000_000)
    w = rng.exponential(20, 4_000_000)
    m = np.minimum(u, w)
    assert abs((u < w).mean() - 2 / 3) < 0.001
    assert abs(m.mean() - 20 / 3) < 0.01
    assert abs(m[u < w].mean() - m[u >= w].mean()) < 0.03


def test_q6():
    p = F(1)
    r = {}
    for n in range(1, 8):
        p *= F(21 - n, 20)
        r[n] = p
    assert round(float(r[5]), 3) == 0.581 and round(float(r[6]), 3) == 0.436
    assert round(float(1 - r[5]), 3) == 0.419 and round(float(1 - r[6]), 3) == 0.564
    assert round(1.18 * math.sqrt(20), 1) == 5.3
    assert round(1.18 * math.sqrt(365), 1) == 22.5


def test_q7():
    y = 0.5
    a = integrate.quad(lambda x: x * (1 / x), y, 1)[0] / integrate.quad(lambda x: 1 / x, y, 1)[0]
    assert abs(a - 0.5 / math.log(2)) < 1e-9
    assert round(a, 3) == 0.721
    rng = np.random.default_rng(7)
    x = rng.random(8_000_000)
    v = x * rng.random(8_000_000)
    k = np.abs(v - 0.5) < 0.005
    assert abs(x[k].mean() - a) < 0.003


def test_q8():
    # Exact law of the total by repeated convolution.
    def law(n):
        p = {0: F(1)}
        for _ in range(n):
            q = {}
            for t, w in p.items():
                for x in range(1, 7):
                    q[t + x] = q.get(t + x, 0) + w * F(1, 6)
            p = q
        return p

    five, six = law(5), law(6)
    assert sum(w for t, w in five.items() if t >= 18) == F(1, 2)
    assert six[21] == F(4_332, 46_656) and 6**6 == 46_656
    v = sum(w for t, w in six.items() if t >= 21)
    assert v == F(1, 2) + F(1, 2) * F(4_332, 46_656)
    assert round(float(v), 3) == 0.546
    # The bijection itself, on every outcome: x -> 7 - x sends total >= 18 onto total <= 17.
    up = {o for o in product(range(1, 7), repeat=5) if sum(o) >= 18}
    down = {o for o in product(range(1, 7), repeat=5) if sum(o) <= 17}
    assert {tuple(7 - x for x in o) for o in up} == down
    assert not up & down and len(up) + len(down) == 6**5
    # Limit cases: one die has no centre on a face; two dice have one.
    assert sum(w for t, w in law(1).items() if t >= 4) == F(1, 2)
    assert sum(w for t, w in law(2).items() if t >= 7) == F(7, 12) == F(1, 2) + F(1, 2) * F(6, 36)
    rng = np.random.default_rng(8)
    r5 = rng.integers(1, 7, (2_000_000, 5)).sum(axis=1)
    r6 = rng.integers(1, 7, (2_000_000, 6)).sum(axis=1)
    assert abs((r5 >= 18).mean() - 0.5) < 0.001
    assert abs((r6 >= 21).mean() - float(v)) < 0.001


def test_q9():
    assert F(1, 3) * F(3, 4) * F(4, 5) == F(1, 5)
    rng = np.random.default_rng(9)
    m = 400_000
    u = rng.random((m, 5))
    keep = np.zeros(m, dtype=int)
    for i in range(1, 5):
        keep = np.where(u[:, i] < 1 / (i + 1), i, keep)
    c = np.bincount(keep, minlength=5) / m
    assert max(abs(c - 0.2)) < 0.003
    # Sample of 2 from 5.
    cnt = np.zeros(5)
    m = 200_000
    for _ in range(m):
        r = [0, 1]
        for i in range(2, 5):
            if rng.random() < 2 / (i + 1):
                r[rng.integers(2)] = i
        cnt[r] += 1
    assert max(abs(cnt / m - 0.4)) < 0.004


def test_q10():
    n = 13 * 4 * math.comb(12, 2) * 16
    assert n == 54912
    assert round(n / 2598960, 4) == 0.0211
    assert 13 * 4 * 12 * 6 == 3744 and round(3744 / 2598960, 5) == 0.00144
    rng = np.random.default_rng(10)
    deck = np.repeat(np.arange(13), 4)
    c = 0
    m = 200_000
    for _ in range(m):
        s = rng.choice(deck, 5, replace=False)
        c += sorted(np.bincount(s).tolist())[-3:] == [1, 1, 3]
    assert abs(c / m - 0.0211) < 0.0015


def test_q11():
    assert round(stats.norm.sf(1.9), 4) == 0.0287
    assert abs(2 * 0.0287 - 0.0574) < 1e-12
    ex = stats.binom.cdf(40, 100, 0.5) + stats.binom.sf(59, 100, 0.5)
    assert round(ex, 4) == 0.0569
    assert round(2 * stats.norm.sf(2), 4) == 0.0455
    assert round(1 - 0.0455 / 0.0569, 1) == 0.2


def test_q12():
    assert 10 - 100 + 105 == 15
    assert 14 + 100 - 10 == 104
    for s in (90.0, 105.0, 120.0):
        v = s + max(105 - s, 0) - max(s - 105, 0)
        assert v == 105
    assert 105 - 104 == 1
