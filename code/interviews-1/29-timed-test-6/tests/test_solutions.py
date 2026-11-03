"""Every number printed in the answers of "Timed Test 6": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F
from itertools import product

import numpy as np

NONNUMERIC = {}


def test_q1():
    sq = list(product(range(8), repeat=2))
    r = sum(1 for a in sq for b in sq if a != b and (a[0] == b[0] or a[1] == b[1]))
    k = sum(1 for a in sq for b in sq if a != b and max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1)
    assert F(r, 4032) == F(2, 9)
    assert k == 420 and F(k, 4032) == F(5, 48)
    assert 4 + 24 + 36 == 64 and 4 * 3 + 24 * 5 + 36 * 8 == 420
    # Neighbours the edge removes: 92 of 512, about a fifth, because 28 of the 64 squares have fewer than 8.
    assert 64 * 8 - k == 92 and round(92 / 512, 2) == 0.18
    assert sum(1 for a in sq if a[0] in (0, 7) or a[1] in (0, 7)) == 28 == 4 + 24


def test_q2():
    games = [(a, b) for a in range(4) for b in range(a + 1, 4)]
    both = some = 0
    for o in product([0, 1], repeat=6):
        w = [0] * 4
        for (a, b), x in zip(games, o, strict=True):
            w[a if x else b] += 1
        if 3 in w:
            some += 1
            if 0 in w:
                both += 1
    assert F(some, 64) == F(1, 2) and F(both, 64) == F(3, 8)


def test_q3():
    rng = np.random.default_rng(3)
    d = np.array([1] * 4 + [0] * 48)
    f = []
    for _ in range(200_000):
        f.append(int(rng.permutation(d).argmax()) + 1)
    assert abs(np.mean(f) - 10.6) < 0.05
    assert F(3, 51) == F(1, 17)
    assert F(53, 5) == F(106, 10)
    d2 = np.array([1] * 48 + [0] * 4)
    assert abs(np.mean([int(rng.permutation(d2).argmax()) + 1 for _ in range(100_000)]) - 53 / 49) < 0.005


def test_q4():
    d = F(15, 65 - 45)
    c = -45 * d
    assert d == F(3, 4) and c == F(-135, 4) and float(c) == -33.75
    assert 65 * d + c == 15 and 45 * d + c == 0
    value = 50 * d + c
    assert value == F(15, 4) and float(value) == 3.75
    p = F(50 - 45, 65 - 45)
    assert p == F(1, 4) and p * 15 == value
    assert 65 * p + 45 * (1 - p) == 50
    # The real probability enters nowhere: whatever it is, the replica pays the call in both states.
    assert F(9, 10) * 15 == F(27, 2) and float(F(27, 2)) == 13.5
    # Any other price leaves a sure profit, the same in both states.
    for price in (F(4), F(27, 2)):
        for stock, call in ((65, 15), (45, 0)):
            assert price - call + (d * stock + c) - value == price - value


def test_q5():
    rng = np.random.default_rng(5)
    c = np.array([0] * 26 + [1] * 26)
    v = [(lambda s: (s[1:] == s[:-1]).sum())(rng.permutation(c)) for _ in range(100_000)]
    assert abs(np.mean(v) - 25) < 0.03
    deck = np.repeat(np.arange(13), 4)
    h = []
    for _ in range(300_000):
        s = rng.choice(deck, 5, replace=False)
        h.append(sum(int(a == b) for i, a in enumerate(s) for b in s[i + 1 :]))
    assert abs(np.mean(h) - 10 / 17) < 0.004
    assert round(10 / 17, 3) == 0.588


def test_q6():
    lines = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
    tot = rows = none = 0
    for g in product([0, 1], repeat=9):
        k = sum(g[a] == g[b] == g[c] for a, b, c in lines)
        tot += k
        none += k == 0
        rows += any(g[a] == g[b] == g[c] for a, b, c in lines[:3])
    assert F(tot, 512) == 2 and F(rows, 512) == F(37, 64)
    assert none == 32


def test_q7():
    assert round(0.9**10, 3) == 0.349
    assert abs(10 * 45 * 362880 / 1e10 - 0.01633) < 1e-5
    assert round(10 / math.e, 2) == 3.68
    rng = np.random.default_rng(7)
    b = rng.integers(0, 10, (500_000, 10))
    b.sort(axis=1)
    full = 1 + (b[:, 1:] != b[:, :-1]).sum(axis=1)
    e = 10 - full
    assert abs(e.mean() - 3.487) < 0.005
    assert abs((e == 1).mean() - 0.01633) < 0.001


def test_q8():
    br = F(1, 36) + F(2, 45) + F(25, 396)
    assert F(3, 36) * F(3, 9) == F(1, 36)
    assert F(4, 36) * F(4, 10) == F(2, 45)
    assert F(5, 36) * F(5, 11) == F(25, 396)
    p = F(2, 9) + 2 * br
    assert p == F(244, 495)
    assert round(float(1 - 2 * p), 3) == 0.014
    rng = np.random.default_rng(8)
    w = 0
    n = 300_000
    for _ in range(n):
        s = rng.integers(1, 7) + rng.integers(1, 7)
        if s in (7, 11):
            w += 1
        elif s not in (2, 3, 12):
            while True:
                t = rng.integers(1, 7) + rng.integers(1, 7)
                if t == s:
                    w += 1
                    break
                if t == 7:
                    break
    assert abs(w / n - 244 / 495) < 0.003


def test_q9():
    n = 10
    s = np.full((n, n), 0.04 * 0.2)
    np.fill_diagonal(s, 0.04)
    w = np.full(n, 1 / n)
    v = w @ s @ w
    assert abs(v - 0.0112) < 1e-12
    assert round(math.sqrt(v), 3) == 0.106
    assert round(math.sqrt(0.008), 3) == 0.089
    assert round(0.2 / math.sqrt(10), 3) == 0.063


def test_q10():
    rng = np.random.default_rng(10)
    u = rng.random(4_000_000)
    for x, v in ((0.5, 0.75), (0.25, 0.6875), (0.0, 0.5)):
        assert abs(np.where(u < x, 1 - u, u).mean() - v) < 0.0005
        assert 0.5 + x - x * x == v
    assert F(11, 16) == 0.6875


def test_q11():
    rng = np.random.default_rng(11)
    n = 200_000
    ln = []
    same = 0
    for _ in range(n):
        p = rng.permutation(10)
        c = {0}
        x = int(p[0])
        while x != 0:
            c.add(x)
            x = int(p[x])
        ln.append(len(c))
        same += 1 in c
    ln = np.array(ln)
    assert abs(same / n - 0.5) < 0.004
    assert abs(ln.mean() - 5.5) < 0.03
    assert max(abs((ln == k).mean() - 0.1) for k in range(1, 11)) < 0.003
    prod = F(1)
    for k in range(1, 11):
        v = prod * F(1, 11 - k)
        assert v == F(1, 10)
        prod *= F(10 - k, 11 - k)


def test_q12():
    assert F(2 * 25, 21) == F(50, 21)
    assert round(50 / 21, 2) == 2.38
    assert round(math.log(7, 5), 2) == 1.21
    rng = np.random.default_rng(12)
    t = []
    c = [0] * 7
    for _ in range(300_000):
        n = 0
        while True:
            a, b = rng.integers(0, 5, 2)
            n += 2
            v = 5 * a + b
            if v < 21:
                c[v % 7] += 1
                break
        t.append(n)
    assert abs(np.mean(t) - 50 / 21) < 0.01
    assert max(c) - min(c) < 2500
