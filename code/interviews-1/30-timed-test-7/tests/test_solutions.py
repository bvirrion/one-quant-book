"""Every number printed in the answers of "Timed Test 7": exact value, then a seeded simulation or second route."""
import math
from fractions import Fraction as F
from itertools import combinations, permutations, product

import numpy as np
from scipy import integrate, stats

NONNUMERIC = {}


def test_q1():
    assert F(6, 2) + 6 == 9
    assert F(6, 3) + F(6, 2) + 6 == 11
    assert 6 + 6 - 3 == 9
    rng = np.random.default_rng(1)
    t2 = []
    t3 = []
    for _ in range(100_000):
        s = set()
        n = 0
        while len(s) < 2:
            n += 1
            d = rng.integers(1, 7)
            if d in (1, 2):
                s.add(int(d))
        t2.append(n)
        s = set()
        n = 0
        while len(s) < 3:
            n += 1
            d = rng.integers(1, 7)
            if d % 2 == 0:
                s.add(int(d))
        t3.append(n)
    assert abs(np.mean(t2) - 9) < 0.06 and abs(np.mean(t3) - 11) < 0.07
    # The last face's share is 1 / H_k: above a half up to three faces, below it from four, but always the largest stage.
    for wanted, more_than_half in ((2, True), (3, True), (4, False), (5, False), (6, False)):
        stages = [F(6, j) for j in range(1, wanted + 1)]
        assert (stages[0] / sum(stages) > F(1, 2)) == more_than_half
        assert stages[0] == max(stages)


def test_q2():
    p = sum(math.comb(10, k) * 0.1**k * 0.9 ** (10 - k) for k in range(0, 11, 2))
    assert abs(p - (1 + 0.8**10) / 2) < 1e-12
    assert round(p, 4) == 0.5537
    assert round(0.8**10, 3) == 0.107
    two = sum(math.comb(10, k) * 0.1**k * 0.9 ** (10 - k) for k in (0, 2))
    assert round(two, 2) == 0.54


def test_q3():
    s = np.array([[1, 0.5], [0.5, 1]])
    assert np.array([1, 2]) @ s @ np.array([1, 2]) == 7
    for rho in (-0.5, 0, 0.5, 0.9):
        s = np.array([[1, rho], [rho, 1]])
        i = np.array([1, 1])
        assert abs((np.array([0, 1]) @ s @ i) / (i @ s @ i) - 0.5) < 1e-12
    rng = np.random.default_rng(3)
    z = rng.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 2_000_000)
    assert abs(np.polyfit(z.sum(axis=1), z[:, 1], 1)[0] - 0.5) < 0.002
    assert abs((z[:, 0] + 2 * z[:, 1]).var() - 7) < 0.03


def test_q4():
    v = sum(F(max(a - b, 0), 36) for a, b in product(range(1, 7), repeat=2))
    assert v == F(35, 36)
    assert round(35 / 36, 2) == 0.97
    assert 10 + 16 + 18 + 16 + 10 == 70


def test_q5():
    o = list(product(range(1, 7), repeat=2))
    al = [x for x in o if 6 in x]
    assert len(al) == 11 and F(sum(x == (6, 6) for x in al), len(al)) == F(1, 11)
    fi = [x for x in o if x[0] == 6]
    assert F(sum(x == (6, 6) for x in fi), len(fi)) == F(1, 6)


def test_q6():
    m = list(product([0, 1], repeat=4))
    z = [x for x in m if x[0] * x[3] == x[1] * x[2]]
    assert len(z) == 10
    both0 = sum(1 for x in m if x[0] * x[3] == 0 and x[1] * x[2] == 0)
    assert both0 == 9
    assert F(16 - len(z), 16) == F(3, 8)
    good = [x for x in m if (x[0] * x[3]) + (x[1] * x[2]) == 1]
    assert len(good) == 6


def test_q7():
    w = np.array([0.25, 1.0, 9 / 16])
    assert F(4 * 1, 2) + 16 + 9 * F(3, 4) == F(99, 4)
    assert F(99, 4) / 29 == F(99, 116)
    assert round(99 / 116, 3) == 0.853
    assert (0.5 + 1 + 0.75) / 3 == 0.75
    assert (F(4) * F(1, 2) + 3 * F(3, 4)) / 7 == F(17, 28)
    assert F(1, 4) / F(3, 16) == F(4, 3)
    assert F(1, 2) * F(1, 2) == F(1, 4) and F(3, 4) * F(1, 4) == F(3, 16)
    rng = np.random.default_rng(7)
    n = 4_000_000
    p = np.array([0.5, 1, 0.75])[rng.integers(0, 3, n)]
    f = rng.random((3, n)) < p
    k = f[0] & f[1]
    assert abs(f[2][k].mean() - 99 / 116) < 0.001
    assert w.sum() > 0


def test_q8():
    rng = np.random.default_rng(8)
    ln = rng.uniform(0, 2, 4_000_000)
    e = np.cumsum(ln)
    t = rng.uniform(1000, e[-1] - 1000, 2_000_000)
    i = np.searchsorted(e, t)
    age = t - (e[i] - ln[i])
    assert abs(age.mean() - 2 / 3) < 0.002
    assert abs(ln[i].mean() - 4 / 3) < 0.002


def test_q9():
    assert round(stats.norm.pdf(1), 3) == 0.242
    assert round(stats.norm.sf(1), 3) == 0.159
    assert round(0.242 / 0.159, 2) == 1.52
    v = integrate.quad(lambda z: z * stats.norm.pdf(z), 1, 12)[0] / stats.norm.sf(1)
    assert abs(v - 1.525) < 0.001
    q = stats.norm.ppf(0.99)
    assert round(q, 3) == 2.326 and round(stats.norm.pdf(q), 4) == 0.0267
    es = integrate.quad(lambda z: z * stats.norm.pdf(z), q, 14)[0] / 0.01
    assert abs(es - 2.665) < 0.001
    assert round(es / q - 1, 2) == 0.15
    assert round(stats.norm.pdf(0) / 0.5, 2) == 0.80


def test_q10():
    inv = [sum(p[i] > p[j] for i, j in combinations(range(4), 2)) for p in permutations(range(4))]
    m = F(sum(inv), 24)
    assert m == 3
    assert F(sum(x * x for x in inv), 24) - m * m == F(13, 6)
    assert F(4 * 3 * 13, 72) == F(13, 6)
    assert F(0 + 3 + 8 + 15, 12) == F(13, 6)


def test_q11():
    rng = np.random.default_rng(11)
    z = rng.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 4_000_000)
    assert abs(z.max(axis=1).mean() - math.sqrt(0.5 / math.pi)) < 0.002
    assert round(math.sqrt(0.5 / math.pi), 3) == 0.399
    assert round(1 / math.sqrt(math.pi), 3) == 0.564
    assert round(0.564 * 0.5, 3) == 0.282
    w = rng.standard_normal((2, 4_000_000))
    assert abs(w.max(axis=0).mean() - 1 / math.sqrt(math.pi)) < 0.002


def test_q12():
    d = np.ones(1)
    for _ in range(100):
        d = np.convolve(d, np.ones(6) / 6)
    exact = d[380 - 100 :].sum()
    assert abs(exact - 0.042) < 0.001
    v = 100 * 35 / 12
    assert round(v, 1) == 291.7 and round(math.sqrt(v), 1) == 17.1
    assert round(29.5 / 17.1, 2) == 1.73
    assert round(stats.norm.sf(1.73), 3) == 0.042
    assert round(30 / 17.1, 2) == 1.75
    assert round(stats.norm.sf(1.75), 3) == 0.040
