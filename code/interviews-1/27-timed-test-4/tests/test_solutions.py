"""Every number printed in the answers of "Timed Test 4": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F

import numpy as np

NONNUMERIC = {}


def test_q1():
    assert F(8, 9) * F(6, 8) * F(4, 7) == F(8, 21)
    assert F(5 * math.comb(4, 2) * 4, math.comb(10, 4)) == F(4, 7)
    assert F(math.comb(5, 2), 210) == F(1, 21)
    assert F(8, 21) + F(4, 7) + F(1, 21) == 1
    rng = np.random.default_rng(1)
    c = {0: 0, 1: 0, 2: 0}
    n = 200_000
    for _ in range(n):
        s = rng.choice(10, 4, replace=False) // 2
        c[4 - len(set(s.tolist()))] += 1
    assert abs(c[0] / n - 8 / 21) < 0.004 and abs(c[1] / n - 4 / 7) < 0.004


def test_q2():
    rng = np.random.default_rng(2)
    x, y, z = rng.exponential(size=(3, 4_000_000))
    assert abs((x > y + z).mean() - 0.25) < 0.001
    assert abs((x > 2 * y).mean() - 1 / 3) < 0.001


def test_q3():
    x = np.array([0.0, 1, 2])
    y = np.array([0.0, 1, 1])
    b, a = np.polyfit(x, y, 1)
    assert abs(b - 0.5) < 1e-12 and abs(a - 1 / 6) < 1e-12
    e = y - a - b * x
    assert np.allclose(e, [-1 / 6, 1 / 3, -1 / 6])
    assert abs(e @ x) < 1e-12
    assert abs(1 - (e @ e) / ((y - y.mean()) @ (y - y.mean())) - 0.75) < 1e-12
    assert abs((x @ y) / (x @ x) - 0.6) < 1e-12


def test_q4():
    e = [F(0)] * 7
    for k in range(5, -1, -1):
        useful = sum(e[k + d] for d in range(1, 7) if k + d <= 6)
        n = 6 - k
        stay = 6 - n
        e[k] = (1 + useful * F(1, 6)) / (1 - F(stay, 6))
    assert e[:6] == [6] * 6
    rng = np.random.default_rng(4)
    t = []
    for _ in range(60_000):
        s = 0
        n = 0
        while s < 6:
            d = rng.integers(1, 7)
            n += 1
            if s + d <= 6:
                s += d
        t.append(n)
    assert abs(np.mean(t) - 6) < 0.06


def test_q5():
    rng = np.random.default_rng(5)
    t = rng.uniform(0, 2 * math.pi, 4_000_000)
    d = 2 * np.sin(t / 2)
    assert abs(d.mean() - 4 / math.pi) < 0.001
    assert round(4 / math.pi, 2) == 1.27
    assert abs((d * d).mean() - 2) < 0.002


def test_q6():
    assert (1 + F(1, 3) * F(3, 2)) / F(2, 3) == F(9, 4)
    # Count three-player outcomes: 0 rock, 1 paper, 2 scissors.
    c = {"tie": 0, "one": 0, "two": 0}
    for a in range(3):
        for b in range(3):
            for d in range(3):
                s = {a, b, d}
                if len(s) != 2:
                    c["tie"] += 1
                else:
                    w = [x for x in s if (x + 2) % 3 in s][0]
                    k = [a, b, d].count(w)
                    c["one" if k == 1 else "two"] += 1
    assert c == {"tie": 9, "one": 9, "two": 9}
    assert 3 * (2**4 - 2) == 42 and F(81 - 42, 81) == F(13, 27)
    rng = np.random.default_rng(6)
    t = []
    for _ in range(100_000):
        p = 3
        n = 0
        while p > 1:
            n += 1
            r = rng.integers(0, 3, p)
            s = set(r.tolist())
            if len(s) == 2:
                w = [x for x in s if (x + 2) % 3 in s][0]
                p = int((r == w).sum())
        t.append(n)
    assert abs(np.mean(t) - 2.25) < 0.015


def test_q7():
    h = F(4, 5)
    t = F(3, 5)
    u = h / 2
    assert h == F(1, 2) + t / 2 and t == h / 2 + u / 2
    assert (h + t) / 2 == F(7, 10)
    rng = np.random.default_rng(7)
    w = 0
    n = 300_000
    for _ in range(n):
        rh = rt = 0
        while True:
            if rng.random() < 0.5:
                rh += 1
                rt = 0
                if rh == 2:
                    w += 1
                    break
            else:
                rt += 1
                rh = 0
                if rt == 3:
                    break
    assert abs(w / n - 0.7) < 0.003


def test_q8():
    assert round(1 + math.log(2), 3) == 1.693
    rng = np.random.default_rng(8)
    t = []
    for _ in range(400_000):
        p = 1.0
        n = 0
        while p >= 0.5:
            p *= rng.random()
            n += 1
        t.append(n)
    assert abs(np.mean(t) - (1 + math.log(2))) < 0.004
    t5 = []
    for _ in range(100_000):
        p = 1.0
        n = 0
        while p >= math.exp(-5):
            p *= rng.random()
            n += 1
        t5.append(n)
    assert abs(np.mean(t5) - 6) < 0.03


def test_q9():
    def g(f):
        return 0.5 * np.log(1 + 2 * f) + 0.5 * np.log(1 - f)

    f = np.linspace(0, 0.99, 9901)
    assert abs(f[g(f).argmax()] - 0.25) < 1e-3
    assert round(float(g(0.25)), 4) == 0.0589
    assert abs(g(0.5)) < 1e-12
    assert abs(0.5 * math.log(1.125) - float(g(0.25))) < 1e-12


def test_q10():
    p = sum(math.comb(7, k) * 0.6**k * 0.4 ** (7 - k) for k in range(4, 8))
    assert round(p, 3) == 0.710
    assert [round(math.comb(7, k) * 0.6**k * 0.4 ** (7 - k), 4) for k in (4, 5, 6, 7)] == [0.2903, 0.2613, 0.1306, 0.028]
    q = {n: 2 * math.comb(n - 1, 3) * F(1, 2**n) for n in (4, 5, 6, 7)}
    assert q == {4: F(1, 8), 5: F(1, 4), 6: F(5, 16), 7: F(5, 16)}
    assert sum(n * v for n, v in q.items()) == F(93, 16)
    assert 93 / 16 == 5.8125


def test_q11():
    tot = F(0)
    em = F(0)
    en = F(0)
    for a in range(1, 7):
        for b in range(1, 7):
            tot += F(max(a, b) * min(a, b), 36)
            em += F(max(a, b), 36)
            en += F(min(a, b), 36)
    assert em == F(161, 36) and en == F(91, 36)
    assert tot == F(49, 4)
    assert tot - em * en == F(1225, 1296) == F(35, 36) ** 2


def test_q12():
    rng = np.random.default_rng(12)
    m = 1_000_000
    n = rng.poisson(10, m)
    s = rng.gamma(np.maximum(n, 1), 5.0) * (n > 0)
    assert abs(s.mean() - 50) < 0.1
    assert abs(s.var() - 500) < 3
    assert f"{math.exp(-10):.1e}" == "4.5e-05"
    assert round(math.sqrt(500), 1) == 22.4
