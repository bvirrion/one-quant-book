"""Every number printed in the answers of "Timed Test 3": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F
from itertools import combinations, permutations, product

import numpy as np

NONNUMERIC = {}


def test_q1():
    p = [F(1, 2), F(1, 3), F(1, 6)]
    v = sum(1 / a for a in p) - sum(1 / (a + b) for a, b in combinations(p, 2)) + 1
    assert v == F(73, 10)
    rng = np.random.default_rng(1)
    t = []
    for _ in range(100_000):
        seen = set()
        n = 0
        for d in rng.choice(3, 200, p=[0.5, 1 / 3, 1 / 6]):
            n += 1
            seen.add(d)
            if len(seen) == 3:
                break
        t.append(n)
    assert abs(np.mean(t) - 7.3) < 0.05
    assert 3 * (1 + F(1, 2) + F(1, 3)) == F(11, 2)


def test_q2():
    c = {}
    for a in product(range(1, 7), repeat=3):
        c[sum(a)] = c.get(sum(a), 0) + 1
    assert c[9] == 25 and c[10] == 27 and c[11] == 27 and c[12] == 25


def test_q3():
    p = [0.5, 0.25, 0.125, 0.125]
    assert sum(a * b for a, b in zip(p, [1, 2, 3, 3], strict=True)) == 1.75
    assert sum(-a * math.log2(a) for a in p) == 1.75
    assert round(-(0.9 * math.log2(0.9) + 0.1 * math.log2(0.1)), 2) == 0.47


def test_q4():
    v = 0.5 * (1 - math.log(2))
    assert round(v, 3) == 0.153
    rng = np.random.default_rng(4)
    x = rng.random(4_000_000)
    y = x * rng.random(4_000_000)
    assert abs((y > 0.5).mean() - v) < 0.001
    assert abs(y.mean() - 0.25) < 0.001


def test_q5():
    a = F(1, 6) / (1 - F(5, 6) * F(2, 3))
    assert a == F(3, 8)
    b = F(5, 6) * F(1, 3) / F(4, 9)
    assert b == F(5, 8)
    assert F(1, 6) / (1 - F(5, 6) ** 2) == F(6, 11)
    rng = np.random.default_rng(5)
    w = 0
    n = 200_000
    for _ in range(n):
        while True:
            if rng.integers(1, 7) == 6:
                w += 1
                break
            if rng.integers(1, 7) >= 5:
                break
    assert abs(w / n - 0.375) < 0.004


def test_q6():
    pts = [(math.cos(k * math.pi / 3), math.sin(k * math.pi / 3)) for k in range(6)]
    r, e, o = 0, 0, 0
    for t in combinations(pts, 3):
        s = sorted(math.dist(t[i], t[j]) ** 2 for i, j in ((0, 1), (0, 2), (1, 2)))
        if abs(s[0] + s[1] - s[2]) < 1e-9:
            r += 1
        elif abs(s[0] - s[2]) < 1e-9:
            e += 1
        else:
            o += 1
    assert (r, e, o) == (12, 2, 6)


def test_q7():
    n = 8
    assert F(7, 8) * F(6, 7) * F(1, 6) == F(1, 8)
    h = sum(F(1, k) for k in range(1, 9))
    assert h == F(761, 280)
    assert round(float(h), 2) == 2.72
    tot = cyc = hit = 0
    for p in permutations(range(n)):
        seen = set()
        c = 0
        for i in range(n):
            if i not in seen:
                c += 1
                j = i
                k = 0
                while j not in seen:
                    seen.add(j)
                    j = p[j]
                    k += 1
                if 7 in _orbit(p, i) and k == 3:
                    hit += 1
        tot += 1
        cyc += c
    assert F(cyc, tot) == h
    assert F(hit, tot) == F(1, 8)
    assert round(8 / float(h), 2) == 2.94


def _orbit(p, i):
    o = {i}
    j = p[i]
    while j != i:
        o.add(j)
        j = p[j]
    return o


def test_q8():
    def f(k, p=0.01):
        return 1 / k + 1 - (1 - p) ** k

    assert round(f(10), 4) == 0.1956
    assert abs(f(11) - f(10)) < 1e-3
    assert min(range(2, 50), key=f) in (10, 11)
    assert round(math.exp(-0.1), 3) == 0.905
    assert round(0.99**10, 3) == 0.904
    assert round(0.5 + 1 - 0.7**2, 2) == 1.01
    assert min(range(2, 30), key=lambda k: f(k, 0.3)) == 3
    assert round(f(3, 0.3), 2) == 0.99
    assert round(f(2, 0.3), 2) == 1.01
    rng = np.random.default_rng(8)
    x = rng.random((400_000, 10)) < 0.01
    tests = 1 + 10 * x.any(1)
    assert abs(tests.mean() / 10 - f(10)) < 0.002


def test_q9():
    p = [F(1)]
    for n in range(1, 200):
        p.append(sum(p[max(0, n - 6) : n]) * F(1, 6))
    assert p[6] == F(1, 6) * F(7, 6) ** 5
    assert round(float(p[6]), 3) == 0.360
    assert abs(float(p[150]) - 2 / 7) < 1e-9
    assert max(p[1:]) == p[6]
    rng = np.random.default_rng(9)
    n = 300_000
    h = 0
    for _ in range(n):
        s = 0
        while s < 6:
            s += rng.integers(1, 7)
        h += s == 6
    assert abs(h / n - float(p[6])) < 0.003


def test_q10():
    # Exact moments of the uniform break, and of the shorter piece, uniform on [0, 1/2].
    area = F(1, 2) - F(1, 3)
    assert area == F(1, 6)
    assert F(1, 4) * F(3, 4) == F(3, 16)
    var_s = F(1, 2) ** 2 / 12
    assert var_s == F(1, 48)
    assert F(3, 16) - var_s == area
    # The roots of x(1 - x) = 3/16 are the quartiles of the break.
    for x in (F(1, 4), F(3, 4)):
        assert x * (1 - x) == F(3, 16)
    assert F(1, 2) * (1 - F(1, 2)) == F(1, 4)
    rng = np.random.default_rng(10)
    u = rng.random(4_000_000)
    s = np.minimum(u, 1 - u)
    a = s * (1 - s)
    assert abs(a.mean() - 1 / 6) < 0.001
    assert abs((a > 3 / 16).mean() - 0.5) < 0.001
    assert abs(np.cov(s, 1 - s)[0, 1] + 1 / 48) < 0.001
    assert a.max() <= 0.25


def test_q11():
    assert round(0.4 * 100 * 0.16 * 0.5, 1) == 3.2
    assert round(16 / math.sqrt(252), 2) == 1.01
    from scipy.stats import norm

    call = 100 * (2 * norm.cdf(0.5 * 0.16 * 0.5) - 1)
    assert abs(call - 3.2) < 0.03
    assert abs(2 * norm.pdf(0) * 0.5 - 0.4) < 0.002
    assert round(6.4 * 2, 1) == 12.8
    assert abs(100 * (2 * norm.cdf(0.5 * 0.16) - 1) * 2 - 12.8) < 0.1


def test_q12():
    n = 10
    assert 8 * F(1, 3) + 1 == F(11, 3)
    for k in (4, 5, 6, 7):
        tot = 0
        cnt = 0
        for p in permutations(range(k)):
            tot += 1
            for i in range(k):
                left = i == 0 or p[i] > p[i - 1]
                right = i == k - 1 or p[i] > p[i + 1]
                cnt += left and right
        assert F(cnt, tot) == F(k + 1, 3)
    assert F(n + 1, 3) == F(11, 3)
    # Follow-up: ascents mean 4.5, runs 5.5.
    assert F(9, 2) + 1 == F(11, 2)
    # Runs are one more than the descents, by enumeration, so (n + 1) / 2 on average.
    for k in (4, 5, 6, 7):
        arrangements = list(permutations(range(k)))
        total = 0
        for p in arrangements:
            runs, i = 0, 0
            while i < k:  # walk over each maximal ascending run
                runs += 1
                while i + 1 < k and p[i + 1] > p[i]:
                    i += 1
                i += 1
            total += runs
            assert runs == sum(p[i] > p[i + 1] for i in range(k - 1)) + 1
        assert F(total, len(arrangements)) == F(k + 1, 2)
