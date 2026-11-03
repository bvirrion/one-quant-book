"""Making a Market: every number printed in the answers, exactly where possible, then by a seeded simulation."""
import math
import pathlib
import sys
from fractions import Fraction as F
from itertools import permutations, product
from math import comb

import numpy as np
import sympy as sp
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import norm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import iv_market as m  # noqa: E402

NONNUMERIC = {}
DIE = range(1, 7)


def mean(xs):
    xs = list(xs)
    return sum(F(x) for x in xs) / len(xs)


def r2(x):
    return round(float(x), 2)


def test_q1():
    sums = [a + b + c for a, b, c in product(DIE, repeat=3)]
    assert mean(sums) == F(21, 2)
    var = mean(s * s for s in sums) - mean(sums) ** 2
    assert var == F(35, 4) and r2(math.sqrt(var)) == 2.96
    fair = F(21, 2)

    def edge(bid, ask):
        return (fair - bid + ask - fair) / 2

    assert edge(10, 11) == F(1, 2) == edge(11, 12)
    assert fair - 11 == F(-1, 2) and 12 - fair == F(3, 2)
    rng = np.random.default_rng(1)
    s = rng.integers(1, 7, (300_000, 3)).sum(axis=1)
    buy = rng.random(300_000) < 0.5
    assert abs(np.where(buy, s - 11, 12 - s).mean() - 0.5) < 0.03


def rank_loss(bid, ask):
    return mean((bid - r) if r < bid else (r - ask) if r > ask else 0 for r in range(1, 14))


def test_q2():
    assert rank_loss(6, 8) == F(30, 13) and r2(F(30, 13)) == 2.31
    grid = [F(i, 2) for i in range(0, 30)]
    assert min(rank_loss(b, b + 2) for b in grid) == F(30, 13)
    assert [b for b in grid if rank_loss(b, b + 2) == F(30, 13)] == [F(6)]

    def best(width):
        return min(rank_loss(b, b + width) for b in grid)

    assert [r2(best(w)) for w in (2, 4, 5, 6, 12)] == [2.31, 1.54, 1.23, 0.92, 0.0]
    assert best(5) >= 1 > best(6)
    assert rank_loss(4, 10) == F(12, 13)
    rng = np.random.default_rng(2)
    r = rng.integers(1, 14, 300_000)
    assert abs((np.maximum(6 - r, 0) + np.maximum(r - 8, 0)).mean() - float(F(30, 13))) < 0.02


def test_q3():
    v = mean(d * d for d in DIE)
    assert v == F(91, 6) and r2(v) == 15.17
    assert F(7, 2) ** 2 == F(49, 4) and r2(F(49, 4)) == 12.25
    assert 12.25 < 15.17 and r2(v - F(49, 4)) == 2.92
    assert r2(mean(F(d, 1) * d - 0 for d in DIE) - F(49, 4)) == r2(F(35, 12))
    assert r2(F(35, 12)) == 2.92
    inv = mean(F(1, d) for d in DIE)
    assert inv == F(49, 120) and r2(inv) == 0.41 and r2(F(2, 7)) == 0.29
    rng = np.random.default_rng(3)
    assert abs((rng.integers(1, 7, 300_000) ** 2).mean() - float(v)) < 0.1


def test_q4():
    deck = 4 * sum(range(1, 14))
    assert deck == 364 and deck - 100 == 264
    assert F(264, 42) == F(44, 7) and r2(F(44, 7)) == 6.29
    assert 42 * 7 == 294
    # nearest quarter to the centre is 6.25, so 5.75 and 6.75; the counterparty passes.
    assert F(23, 4) < F(44, 7) < F(27, 4)
    # A shuffle of what is left, for a sample deck whose first ten cards total 100.
    cards = [v for v in range(1, 14) for _ in range(4)]
    rng = np.random.default_rng(4)
    seen = [13, 13, 13, 12, 12, 11, 10, 9, 4, 3]
    assert sum(seen) == 100
    rest = list(cards)
    for x in seen:
        rest.remove(x)
    assert sum(rest) == 264 and len(rest) == 42
    sims = [int(rng.permutation(rest)[0]) for _ in range(40_000)]
    assert abs(np.mean(sims) - 44 / 7) < 0.05


def test_q5():
    bid_a, ask_a, bid_b, ask_b = F(55, 100), F(60, 100), F(50, 100), F(52, 100)
    for d in DIE:
        pay_a, pay_b = int(d >= 4), int(d <= 3)
        assert bid_a + bid_b - pay_a - pay_b == F(5, 100)
    assert bid_a + bid_b > 1 and ask_a + ask_b == F(112, 100) > 1
    # The follow-up: both asks below one.
    assert 1 - (F(45, 100) + F(45, 100)) == F(10, 100)


def test_q6():
    v0 = mean(max(a, b) for a, b in product(DIE, DIE))
    assert v0 == F(161, 36) and r2(v0) == 4.47
    after = {a: mean(max(a, b) for b in DIE) for a in DIE}
    assert after[3] == 4 and after[6] == 6
    assert [r2(after[a]) for a in DIE] == [3.5, 3.67, 4.0, 4.5, 5.17, 6.0]
    rng = np.random.default_rng(6)
    x = rng.integers(1, 7, (300_000, 2)).max(axis=1)
    assert abs(x.mean() - float(v0)) < 0.01


def test_q7():
    sieve = [True] * 1000
    sieve[0] = sieve[1] = False
    for i in range(2, 32):
        if sieve[i]:
            for j in range(i * i, 1000, i):
                sieve[j] = False
    primes = sum(sieve)
    assert primes == 168
    ln = math.log(1000)
    assert round(ln, 2) == 6.91
    assert round(3 * 2.303, 2) == 6.91
    assert round(1000 / ln) == 145
    assert round(1000 / (ln - 1)) == 169
    assert 159 <= primes <= 179
    assert primes - 155 == 13
    # The sieve estimate in the follow-up: numbers below 1,000 with no factor 2, 3, 5 or 7.
    assert sum(1 for n in range(1, 1000) if all(n % p for p in (2, 3, 5, 7))) == 228
    assert round(1000 * F(1, 2) * F(2, 3) * F(4, 5) * F(6, 7)) == 229


def test_q8():
    # Exact tail: P(T > n) = (5/6)^n.
    tail = lambda n: F(5, 6) ** n  # noqa: E731
    assert r2(tail(7)) == 0.28 and r2(tail(19)) == 0.03
    assert 20 - 7 == 13
    assert round(float(1 - tail(4)), 3) == 0.518
    assert r2(1 - tail(4)) == 0.52
    # Mean 6, variance 30, so the standard deviation is about 5.5; the median is 4.
    n = 2000
    probs = [F(5, 6) ** (k - 1) * F(1, 6) for k in range(1, n)]
    assert abs(float(sum(k * p for k, p in zip(range(1, n), probs, strict=True))) - 6) < 1e-9
    assert round(math.sqrt(30), 1) == 5.5
    assert 1 - tail(3) < F(1, 2) < 1 - tail(4)
    # Each side earns 1 on average; the long side can lose 4 at most.
    assert 6 - 5 == 1 and 7 - 6 == 1 and 5 - 1 == 4
    rng = np.random.default_rng(8)
    t = rng.geometric(1 / 6, 400_000)
    assert abs((t > 7).mean() - float(tail(7))) < 0.003
    assert abs((t < 5).mean() - float(1 - tail(4))) < 0.003
    assert abs((t - 5).mean() - 1) < 0.03


def test_q9():
    total = comb(52, 10)
    p = {k: F(comb(26, k) * comb(26, 10 - k), total) for k in range(11)}
    mu = sum(k * v for k, v in p.items())
    var = sum(k * k * v for k, v in p.items()) - mu**2
    assert mu == 5 and var == F(35, 17)
    assert r2(math.sqrt(var)) == 1.43 and r2(math.sqrt(2.5)) == 1.58
    outside = 1 - p[4] - p[5] - p[6]
    assert r2(outside) == 0.29
    after = 1 + 9 * F(25, 51)
    assert after == F(92, 17) and r2(after) == 5.41
    assert r2(9 * F(25, 51)) == 4.41 and r2(after - 5) == 0.41
    rng = np.random.default_rng(9)
    deck = np.array([1] * 26 + [0] * 26)
    red = np.array([rng.permutation(deck)[:10].sum() for _ in range(40_000)])
    assert abs(red.mean() - 5) < 0.03
    assert abs(((red < 4) | (red > 6)).mean() - float(outside)) < 0.01


def test_q10():
    def loss(k):
        return 2 * (norm.pdf(k) - k * norm.sf(k))

    # Numerical integral agrees with the closed form.
    for k in (0.5, 1.0, 1.645):
        integral = 2 * quad(lambda z, c=k: (z - c) * norm.pdf(z), k, 12)[0]
        assert abs(integral - loss(k)) < 1e-8
    assert round(loss(0), 2) == 0.8
    assert round(loss(1.0), 3) == 0.167
    assert round(loss(1.645), 3) == 0.042
    k5 = brentq(lambda k: loss(k) - 0.05, 0.5, 3)
    assert round(k5, 2) == 1.57 and round(2 * k5, 1) == 3.1
    rng = np.random.default_rng(10)
    z = rng.standard_normal(800_000)
    assert abs(np.maximum(np.abs(z) - 1.645, 0).mean() - loss(1.645)) < 0.001


def test_q11():
    s = math.log(2)
    centre = 200 * math.exp(s * s / 2)
    assert round(centre) == 254 and round(math.exp(s * s / 2), 2) == 1.27
    assert round(norm.sf(s / 2), 2) == 0.36
    assert round(200 * math.exp(-1.645 * s)) == 64 and round(200 * math.exp(1.645 * s)) == 625
    # Three factors, each uncertain by a factor of 1.5, give about a factor of 2 in all.
    assert round(math.exp(math.sqrt(3) * math.log(1.5)), 1) == 2.0
    rng = np.random.default_rng(11)
    x = 200 * np.exp(s * rng.standard_normal(1_000_000))
    assert abs(x.mean() - centre) < 1.5
    assert abs((x > centre).mean() - norm.sf(s / 2)) < 0.002
    assert abs(np.median(x) - 200) < 1


def test_q12():
    bid, ask = m.two_value_quote(F(80), F(120), F(1, 2), F(3, 10))
    assert (bid, ask) == (F(94), F(106))
    assert m.posterior(F(1, 2), F(65, 100), F(35, 100)) == F(65, 100)
    assert F(3, 10) * 120 + F(7, 10) * 100 == 106
    assert ask - bid == 12 == F(3, 10) * 40
    # Sharing of the follow-ups: no knowing traders, and only knowing traders.
    assert m.two_value_quote(F(80), F(120), F(1, 2), F(0)) == (F(100), F(100))
    assert m.two_value_quote(F(80), F(120), F(1, 2), F(1)) == (F(80), F(120))
    rng = np.random.default_rng(12)
    n = 400_000
    high = rng.random(n) < 0.5
    knows = rng.random(n) < 0.3
    buys = np.where(knows, high, rng.random(n) < 0.5)
    v = np.where(high, 120, 80)
    assert abs(v[buys].mean() - 106) < 0.1
    assert abs(v[~buys].mean() - 94) < 0.1


def test_q13():
    def quote(prior):
        return m.two_value_quote(F(0), F(100), prior, F(1, 5))

    path = "BBSB"
    p = F(1, 2)
    printed = []
    for i in range(5):
        bid, ask = quote(p)
        printed.append((r2(bid), r2(ask)))
        if i < 4:
            p = m.posterior(p, F(3, 5), F(2, 5)) if path[i] == "B" else m.posterior(p, F(2, 5), F(3, 5))
    assert printed == [(40.0, 60.0), (50.0, 69.23), (60.0, 77.14), (50.0, 69.23), (60.0, 77.14)]
    # Any order of the same trades.
    for order in set(permutations("BBSB")):
        q = F(1, 2)
        for t in order:
            q = m.posterior(q, F(3, 5), F(2, 5)) if t == "B" else m.posterior(q, F(2, 5), F(3, 5))
        assert q == p
    assert p == F(9, 13)
    # Uninformed traders who buy 70% of the time: the two ratios are no longer reciprocal.
    buy_h, buy_l = F(1, 5) + F(4, 5) * F(7, 10), F(4, 5) * F(7, 10)
    assert (buy_h, buy_l) == (F(76, 100), F(56, 100))
    assert r2(buy_h / buy_l) == 1.36
    assert r2((1 - buy_h) / (1 - buy_l)) == 0.55
    assert r2(buy_l / buy_h) == 0.74
    rng = np.random.default_rng(13)
    n = 200_000
    high = rng.random(n) < 0.5
    pattern = np.ones(n, dtype=bool)
    for t in path:
        knows = rng.random(n) < 0.2
        buys = np.where(knows, high, rng.random(n) < 0.5)
        pattern &= buys if t == "B" else ~buys
    assert abs(high[pattern].mean() - 9 / 13) < 0.01


def test_q14():
    def weights(event):
        out = {}
        for v in DIE:
            knows = {"S": v < 3, "B": v > 4, "P": 3 <= v <= 4}[event]
            noise = F(1, 2) if event in "SB" else F(0)
            out[v] = F(1, 2) * int(knows) + F(1, 2) * noise
        return out

    def fair(event):
        w = weights(event)
        return sum(v * x for v, x in w.items()) / sum(w.values())

    assert weights("S")[1] == F(3, 4) and weights("S")[3] == F(1, 4)
    assert sum(weights("S").values()) == F(5, 2)
    assert fair("S") == F(27, 10) and fair("B") == F(43, 10) and fair("P") == F(7, 2)
    # The next quote: 1 wide and centred on the new value, which already sits on the 0.1 grid.
    assert (fair("S") - F(1, 2), fair("S") + F(1, 2)) == (F(22, 10), F(32, 10))
    ps = {e: sum(weights(e).values()) / 6 for e in "SBP"}
    assert sum(ps.values()) == 1
    assert sum(ps[e] * fair(e) for e in "SBP") == F(7, 2)
    assert (ps["S"], ps["B"], ps["P"]) == (F(5, 12), F(5, 12), F(1, 6))
    assert mean([1, 2]) == F(3, 2)
    rng = np.random.default_rng(14)
    n = 500_000
    v = rng.integers(1, 7, n)
    looked = rng.random(n) < 0.5
    sell = np.where(looked, v < 3, rng.random(n) < 0.5)
    assert abs(v[sell].mean() - 2.7) < 0.01


def test_q15():
    a, big_i, big_n = F(1, 10), F(8, 10), F(5, 100)
    p100 = a * big_i / (a * big_i + (1 - a) * big_n)
    p1 = a * (1 - big_i) / (a * (1 - big_i) + (1 - a) * (1 - big_n))
    assert p100 == F(16, 25) and r2(p100) == 0.64
    assert p1 == F(4, 175) and round(float(p1), 3) == 0.023
    assert r2(100 + 10 * p100) == 106.4 and r2(100 + 10 * p1) == 100.23
    lots_i = a * ((1 - big_i) * 1 + big_i * 100)
    lots_n = (1 - a) * ((1 - big_n) * 1 + big_n * 100)
    assert r2(lots_i) == 8.02 and round(float(lots_n), 3) == 5.355
    share = lots_i / (lots_i + lots_n)
    assert r2(share) == 0.6 and round(float(100 + 10 * share), 1) == 106.0
    rng = np.random.default_rng(15)
    n = 1_000_000
    high = rng.random(n) < 0.5
    knows = rng.random(n) < 0.1
    big = np.where(knows, rng.random(n) < 0.8, rng.random(n) < 0.05)
    buys = np.where(knows, high, rng.random(n) < 0.5)
    v = np.where(high, 110, 90)
    assert abs(v[buys & big].mean() - 106.4) < 0.1
    assert abs(v[buys & ~big].mean() - float(100 + 10 * p1)) < 0.05


def test_q16():
    lam = F(1, 100)

    def ask_low(q):
        return 100 + lam * ((q - 1) ** 2 - q * q)

    def bid_high(q):
        return 100 + lam * (q * q - (q + 1) ** 2)

    assert ask_low(40) == F(9921, 100) and bid_high(40) == F(9919, 100)
    centre = (ask_low(40) + bid_high(40)) / 2
    assert centre == F(992, 10) and 100 - 2 * lam * 40 == centre
    assert (centre - 1, centre + 1) == (F(982, 10), F(1002, 10))
    assert ask_low(-40) == F(10081, 100) and bid_high(-40) == F(10079, 100)
    assert (ask_low(-40) + bid_high(-40)) / 2 == F(1008, 10)
    assert (ask_low(41) + bid_high(41)) / 2 == F(9918, 100)
    assert ask_low(0) == F(10001, 100) and bid_high(0) == F(9999, 100)
    assert ask_low(40) - bid_high(40) == F(2, 100)
    assert 2 * lam == F(2, 100)


def test_q17():
    def run(limit, rounds):
        dist = {0: F(1)}
        total = F(0)
        for _ in range(rounds):
            new = {}
            for q, w in dist.items():
                for step in (-1, 1):
                    if abs(q + step) <= limit:
                        total += w / 2
                        new[q + step] = new.get(q + step, 0) + w / 2
                    else:
                        new[q] = new.get(q, 0) + w / 2
            dist = new
        return total, dist

    total10, _ = run(3, 10)
    assert total10 == F(73, 8) and float(total10) == 9.125
    assert 10 - total10 == F(7, 8)
    # Stationary law is uniform: the transition matrix is doubly stochastic.
    size = 7
    t = np.zeros((size, size))
    for i in range(size):
        for s in (-1, 1):
            j = i + s
            if 0 <= j < size:
                t[i, j] += 0.5
            else:
                t[i, i] += 0.5
    assert np.allclose(t.sum(axis=0), 1) and np.allclose(t.sum(axis=1), 1)
    assert F(6, 7) == 1 - F(2, 7) / 2 and r2(F(6, 7)) == 0.86
    for lim in (1, 3, 5, 10):
        assert F(2 * lim, 2 * lim + 1) == 1 - F(2, 2 * lim + 1) / 2
    assert abs(float(run(3, 1500)[0]) / 1500 - 6 / 7) < 0.002
    rng = np.random.default_rng(17)
    q = np.zeros(20_000, dtype=int)
    done = np.zeros(20_000)
    for _ in range(10):
        step = rng.choice([-1, 1], 20_000)
        ok = np.abs(q + step) <= 3
        done += ok
        q = np.where(ok, q + step, q)
    assert abs(done.mean() - 9.125) < 0.03


def test_q18():
    bid, ask = F(34, 10), F(36, 10)
    assert 3 * bid == F(102, 10) and 3 * ask == F(108, 10)
    fair = F(21, 2)
    # Bids above 10.8: buy the pieces, sell to you. Asks below 10.2: buy from you, sell the pieces.
    assert F(109, 10) - 3 * ask == F(1, 10)
    assert 3 * bid - F(101, 10) == F(1, 10)
    assert F(107, 10) - 3 * ask == F(-1, 10)
    assert F(107, 10) - fair == F(2, 10)
    var = 3 * F(35, 12)
    assert r2(math.sqrt(var)) == 2.96
    rng = np.random.default_rng(18)
    s = rng.integers(1, 7, (300_000, 3)).sum(axis=1)
    assert abs((10.7 - s).mean() - 0.2) < 0.02
    assert round(float((10.7 - s < 0).mean()), 2) == round(float(mean(a + b + c > 10.7 for a, b, c in product(DIE, repeat=3))), 2)
    assert r2(mean(a + b + c >= 11 for a, b, c in product(DIE, repeat=3))) == 0.5


def test_q19():
    cases = [(x, y, z) for x, y, z in product(DIE, repeat=3) if x + y > F(15, 2)]
    a = [x + y for x, y, z in cases]
    b = [x + z for x, y, z in cases]
    assert mean(x + y > 7.5 for x, y in product(DIE, DIE)) == F(15, 36)
    ea, eb = mean(a), mean(b)
    assert ea == F(28, 3) and r2(ea) == 9.33
    assert eb == F(49, 6) and r2(eb) == 8.17
    assert eb - 7 == (ea - 7) / 2
    va = mean(v * v for v in a) - ea**2
    vb = mean(v * v for v in b) - eb**2
    cov = mean(p * q for p, q in zip(a, b, strict=True)) - ea * eb
    ratio = cov / vb
    assert va == F(14, 9) and r2(va) == 1.56
    assert vb == F(161, 36) and r2(vb) == 4.47
    assert cov == F(7, 9)
    assert ratio == F(4, 23) and r2(ratio) == 0.17
    assert r2(cov * cov / (va * vb) * 100) == 8.7
    # The unconditional ratio makes it worse now.
    assert r2(va + vb / 4 - cov) == 1.9
    assert 140 == 8 * 5 + 9 * 4 + 10 * 3 + 11 * 2 + 12 and F(140, 15) == ea
    # With no conditioning: ratio one half, a quarter of the variance goes.
    v = F(35, 12)
    assert v / (2 * v) == F(1, 2)
    assert (2 * v - v * v / (2 * v)) / (2 * v) == F(3, 4)
    rng = np.random.default_rng(19)
    d = rng.integers(1, 7, (800_000, 3))
    mask = d[:, 0] + d[:, 1] > 7.5
    assert abs((d[mask, 0] + d[mask, 1]).mean() - float(ea)) < 0.01
    assert abs((d[mask, 0] + d[mask, 2]).mean() - float(eb)) < 0.01
    assert abs(np.cov(d[mask, 0] + d[mask, 1], d[mask, 0] + d[mask, 2])[0, 1] - float(cov)) < 0.01


def test_q20():
    def h(n, p, move=F(2)):
        return p * move / (n + p)

    assert r2(h(10, F(8, 10))) == 0.15 and round(float(h(10, F(8, 10))), 3) == 0.148
    assert round(float(h(10, F(1, 2))), 3) == 0.095
    assert round(float(h(5, F(8, 10))), 3) == 0.276
    x = h(10, F(8, 10))
    assert 10 * x + F(8, 10) * (x - 2) == 0
    assert round(float(h(10, F(8, 10)) - h(10, F(1, 2))), 3) == 0.053
    rng = np.random.default_rng(20)
    hit = rng.random(1_000_000) < 0.8
    pnl = 10 * float(x) + np.where(hit, float(x) - 2, 0)
    assert abs(pnl.mean()) < 0.01


def test_q21():
    alpha = F(1, 10)

    def per_trade(h):
        return (1 - alpha) * h + alpha * (h - 2)

    assert per_trade(F(1)) == F(8, 10) and per_trade(F(1)) / 2 == F(4, 10)
    assert per_trade(F(1, 2)) == F(3, 10)
    assert per_trade(F(9, 10)) == F(7, 10)
    assert F(1, 2) + alpha == F(6, 10) and per_trade(F(6, 10)) == F(4, 10)
    assert per_trade(F(7, 10)) == F(5, 10)
    assert per_trade(F(2, 10)) == 0
    # Undercutting by one step beats sharing while h is above 0.4, and ties at 0.4.
    step = F(1, 10)
    assert per_trade(F(5, 10) - step) > per_trade(F(5, 10)) / 2
    assert per_trade(F(4, 10) - step) == per_trade(F(4, 10)) / 2
    assert per_trade(F(3, 10) - step) < per_trade(F(3, 10)) / 2
    assert per_trade(F(3, 10)) / 2 == F(5, 100) and per_trade(F(4, 10)) / 2 == F(1, 10)
    rng = np.random.default_rng(21)
    n = 500_000
    high = rng.random(n) < 0.5
    knows = rng.random(n) < 0.1
    buys = np.where(knows, high, rng.random(n) < 0.5)
    v = np.where(high, 102, 98)
    pnl = np.where(buys, 100.9 - v, v - 99.1)
    assert abs(pnl.mean() - 0.7) < 0.01


def test_q22():
    values = [d + 7 - F(21, 2) for d in DIE]

    def profit(h, a):
        loss = mean(max(abs(v) - h, 0) for v in values)
        return (1 - a) * h - a * loss

    assert profit(F(4, 5), F(1, 2)) == 0
    assert profit(F(3, 8), F(1, 4)) == 0
    assert profit(F(4, 3), F(3, 4)) == 0
    assert mean(max(abs(v) - F(4, 5), 0) for v in values) == F(4, 5)
    assert [float(v) for v in values] == [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
    # Checked against the whole 3-dice space, not just the conditional means.
    h = F(4, 5)
    total = F(0)
    for a, b, c in product(DIE, repeat=3):
        s = a + b + c
        v = a + 7
        if v < F(21, 2) - h:
            inf = s - (F(21, 2) - h)
        elif v > F(21, 2) + h:
            inf = F(21, 2) + h - s
        else:
            inf = F(0)
        noise = ((s - (F(21, 2) - h)) + (F(21, 2) + h - s)) / 2
        total += (inf + noise) / 2
    assert total == 0
    rng = np.random.default_rng(22)
    n = 800_000
    d = rng.integers(1, 7, (n, 3))
    s = d.sum(axis=1)
    v = d[:, 0] + 7
    pnl_inf = np.where(v < 9.7, s - 9.7, np.where(v > 11.3, 11.3 - s, 0))
    pnl_noise = np.where(rng.random(n) < 0.5, s - 9.7, 11.3 - s)
    pnl = np.where(rng.random(n) < 0.5, pnl_inf, pnl_noise)
    assert abs(pnl.mean()) < 0.015


def test_q23():
    def quote(n):
        p = F(1, 1 + 3**n)
        return m.two_value_quote(F(0), F(100), p, F(1, 2))

    printed = [(r2(a), r2(b)) for a, b in (quote(n) for n in range(5))]
    assert printed == [(25.0, 75.0), (10.0, 50.0), (3.57, 25.0), (1.22, 10.0), (0.41, 3.57)]
    widths = [r2(b - a) for a, b in (quote(n) for n in range(5))]
    assert widths == [50.0, 40.0, 21.43, 8.78, 3.16]
    # The ask after n sales equals the bid after n - 2.
    assert quote(3)[1] == quote(1)[0]
    assert F(1, 4) ** 4 == F(1, 256) and round(float(F(1, 256)) * 100, 1) == 0.4
    assert r2(F(3, 4) ** 4) == 0.32
    rng = np.random.default_rng(23)
    n = 300_000
    high = rng.random(n) < 0.5
    sells = np.ones(n, dtype=bool)
    for _ in range(4):
        knows = rng.random(n) < 0.5
        sale = np.where(knows, ~high, rng.random(n) < 0.5)
        sells &= sale
    assert abs(high[sells].mean() - 1 / 82) < 0.003


def test_q24():
    a, x = sp.symbols("alpha x", positive=True)
    num = sp.integrate(x * a, (x, sp.Symbol("t"), 1)) + (1 - a) / 4
    den = a * (1 - sp.Symbol("t")) + (1 - a) / 2
    t = sp.Symbol("t")
    eq = sp.simplify(num - t * den)
    roots = sp.solve(eq, t)
    want = ((1 + a) - sp.sqrt(1 - a**2)) / (2 * a)
    assert any(abs(sp.N((r - want).subs(a, sp.Rational(1, 3)))) < 1e-12 for r in roots)
    ask = lambda al: ((1 + al) - math.sqrt(1 - al * al)) / (2 * al)  # noqa: E731
    assert round(100 * ask(0.5), 1) == 63.4 and round(100 * (1 - ask(0.5)), 1) == 36.6
    assert round(100 * ask(0.1), 1) == 52.5
    assert round(100 * ask(0.99), 1) == 93.4
    assert abs(100 * ask(1e-6) - 50) < 1e-3
    assert abs((100 * ask(0.001) - 50) / 0.001 - 25) < 0.5
    rng = np.random.default_rng(24)
    n = 1_000_000
    v = rng.random(n) * 100
    a_ = 100 * ask(0.5)
    knows = rng.random(n) < 0.5
    buys = np.where(knows, v > a_, rng.random(n) < 0.5)
    assert abs(v[buys].mean() - a_) < 0.1


def test_q25():
    def profit(h, a=F(1, 5)):
        return (1 - a) * h * (1 - h / 20) - a * (50 - h) ** 2 / 100

    h = F(1) / F(84, 1000)
    assert r2(h) == 11.9
    assert r2(profit(h)) == 0.95
    # The derivative vanishes there.
    x = sp.Symbol("x")
    expr = sp.Rational(4, 5) * x * (1 - x / 20) - sp.Rational(1, 5) * (50 - x) ** 2 / 100
    assert sp.solve(sp.diff(expr, x), x)[0] == sp.Rational(250, 21)
    assert sp.Rational(250, 21) == sp.Rational(h.numerator, h.denominator)
    zero = sorted(float(r) for r in sp.solve(expr, x))
    assert round(zero[0], 2) == 7.14
    assert abs(zero[0] - 50 / 7) < 1e-9
    # At a share of a quarter the best quote just breaks even; above that nothing earns.
    a = F(1, 4)
    best = F(1) / ((1 - a) / 10 + a / 50)
    assert best == F(25, 2) and profit(best, a) == 0
    for a2 in (F(3, 10), F(2, 5)):
        hs = [F(i, 10) for i in range(0, 500)]
        assert max(profit(h2, a2) if h2 < 20 else -a2 * (50 - h2) ** 2 / 100 for h2 in hs) < 0
    # Informed loss by integration of the uniform.
    assert abs(quad(lambda v: max(v - 50 - 11.9, 0) / 100, 0, 100)[0] * 2 - (50 - 11.9) ** 2 / 100) < 1e-5
    rng = np.random.default_rng(25)
    n = 1_000_000
    v = rng.random(n) * 100
    hf = float(h)
    bid, ask = 50 - hf, 50 + hf
    knows = rng.random(n) < 0.2
    trades = rng.random(n) < 1 - hf / 20
    buy = rng.random(n) < 0.5
    inf = np.where(v > ask, ask - v, np.where(v < bid, v - bid, 0))
    noise = np.where(trades, np.where(buy, ask - v, v - bid), 0)
    assert abs(np.where(knows, inf, noise).mean() - float(profit(h))) < 0.06


def test_q26():
    lam, k = 0.01, 2.0

    def best(benefit):
        """Best delta >= 0 for profit (delta + benefit) * exp(-k delta)."""
        return max(0.0, 1 / k - benefit)

    # Flat: any trade costs 0.01 of penalty.
    assert round(best(-lam), 2) == 0.51
    # Long 40: a purchase costs 0.81, a sale saves 0.79.
    assert round(lam * (2 * 40 + 1), 2) == 0.81 and round(lam * (2 * 40 - 1), 2) == 0.79
    assert round(best(-0.81), 2) == 1.31
    assert best(0.79) == 0.0
    assert round(1 / k - 0.79, 2) == -0.29
    grid = np.linspace(0, 4, 400_001)
    for benefit, want in ((-0.81, 1.31), (0.79, 0.0), (-0.01, 0.51), (0.49, 0.01)):
        vals = (grid + benefit) * np.exp(-k * grid)
        assert abs(grid[np.argmax(vals)] - want) < 1e-4
    # Going below fair value gets you no more fills, and only lowers the price.
    assert round(0.79, 2) == 0.79
    assert round(1.31 - 0.81, 2) == 0.5
    assert round(0.5 * math.exp(-k * 1.31), 3) == 0.036
    # First position at which the ask reaches 100: lam (2q - 1) >= 1/k.
    assert lam * (2 * 25 - 1) < 0.5 <= lam * (2 * 26 - 1)
    # Expected change in score at the best quote against the flat quote, long 40.
    best_score = 0.5 * (0.5 * math.exp(-k * 1.31)) + 0.5 * 0.79
    naive = 0.5 * ((0.51 - 0.81) * math.exp(-k * 0.51)) + 0.5 * ((0.51 + 0.79) * math.exp(-k * 0.51))
    assert round(best_score, 2) == 0.41 and round(naive, 2) == 0.18
    rng = np.random.default_rng(26)
    n = 1_000_000
    u = rng.random(n)
    buy = rng.random(n) < 0.5
    res = np.where(buy, 0.79, np.where(u < math.exp(-k * 1.31), 0.5, 0.0))
    assert abs(res.mean() - best_score) < 0.003


def test_q27():
    def quote(prior):
        return m.two_value_quote(F(90), F(110), prior, F(3, 10))

    assert quote(F(1, 2)) == (F(97), F(103))
    bid, ask = quote(F(4, 5))
    assert r2(ask) == 107.63 and r2(bid) == 103.66
    assert r2(ask - bid) == 3.97
    assert r2((ask + bid) / 2) == 105.64
    assert 90 + 20 * F(4, 5) == 106
    assert r2(m.posterior(F(4, 5), F(65, 100), F(35, 100))) == 0.88
    b2, a2 = quote(F(3, 5))
    assert r2(a2) == 104.72 and r2(b2) == 98.94 and r2(a2 - b2) == 5.78
    # A perfect signal removes the width.
    assert quote(F(1)) == (F(110), F(110))
    rng = np.random.default_rng(27)
    n = 1_000_000
    high = rng.random(n) < 0.5
    sig = np.where(rng.random(n) < 0.8, high, ~high)
    knows = rng.random(n) < 0.3
    buys = np.where(knows, high, rng.random(n) < 0.5)
    v = np.where(high, 110, 90)
    assert abs(v[sig & buys].mean() - float(ask)) < 0.05
    assert abs(v[sig & ~buys].mean() - float(bid)) < 0.05


def test_q28():
    def two(mk):
        total = F(0)
        for a, b in product(DIE, DIE):
            share = F(1) if a < b else F(1, 2) if a == b else F(0)
            total += share * (a + F(7, 2) + mk - a - b)
        return total / 36

    assert two(F(1, 2)) == F(-17, 72) and round(float(two(F(1, 2))), 3) == -0.236
    assert two(F(35, 36)) == 0 and r2(F(35, 36)) == 0.97
    # Value given that you win.
    wins = [(a, b) for a, b in product(DIE, DIE) if a < b]
    assert mean(b for a, b in wins) == F(14, 3)

    def three(mk):
        total = F(0)
        for d in product(DIE, repeat=3):
            low = min(d)
            if d[0] == low:
                total += F(1, d.count(low)) * (d[0] + 7 + mk - sum(d))
        return total / 216

    assert three(F(35, 24)) == 0 and r2(F(35, 24)) == 1.46
    rng = np.random.default_rng(28)
    n = 1_000_000
    a = rng.integers(1, 7, n)
    b = rng.integers(1, 7, n)
    share = np.where(a < b, 1.0, np.where(a == b, 0.5, 0.0))
    assert abs((share * (4 - b)).mean() - float(two(F(1, 2)))) < 0.006


def test_q29():
    def start():
        return {(k, v): F(1, 4) for k in (True, False) for v in (0, 100)}

    def like(state, side):
        knows, v = state
        if knows:
            return F(1) if (side == "B") == (v == 100) else F(0)
        return F(1, 2)

    def update(w, side):
        new = {s: x * like(s, side) for s, x in w.items()}
        total = sum(new.values())
        return {s: x / total for s, x in new.items()}

    def value(w):
        return sum(x * s[1] for s, x in w.items())

    def quote(w):
        return value(update(w, "S")), value(update(w, "B"))

    w = start()
    assert quote(w) == (F(25), F(75))
    w1 = update(w, "B")
    assert quote(w1) == (F(50), F(250, 3)) and r2(F(250, 3)) == 83.33
    assert sum(x for s, x in w1.items() if s[0]) == F(1, 2)
    assert value(w1) == 75
    w2 = update(w1, "S")
    assert value(w2) == 50 and quote(w2) == (F(50), F(50))
    assert sum(x for s, x in w2.items() if s[0]) == 0
    # A new person each round.
    assert m.two_value_quote(F(0), F(100), F(3, 4), F(1, 2)) == (F(50), F(90))
    # Further buys: the ask climbs and the bid stays at 50.
    w3 = update(w1, "B")
    assert quote(w3) == (F(50), F(90))
    rng = np.random.default_rng(29)
    n = 400_000
    high = rng.random(n) < 0.5
    knows = rng.random(n) < 0.5
    t1 = np.where(knows, high, rng.random(n) < 0.5)
    t2 = np.where(knows, high, rng.random(n) < 0.5)
    v = np.where(high, 100, 0)
    assert abs(v[t1 & t2].mean() - 250 / 3) < 0.3
    assert abs(v[t1 & ~t2].mean() - 50) < 0.5


def test_q30():
    deals = list(permutations(range(1, 11), 3))
    assert mean(max(d) for d in deals) == F(33, 4)
    their = {c: mean(max(d) for d in deals if d[1] == c) for c in range(1, 11)}
    assert [r2(their[c]) for c in range(1, 11)] == [7.67, 7.67, 7.67, 7.69, 7.78, 7.94, 8.22, 8.64, 9.22, 10.0]

    def pnl(bid):
        total = F(0)
        for d in deals:
            v = their[d[1]]
            if bid > v:
                total += max(d) - bid
            elif bid + 2 < v:
                total += bid + 2 - max(d)
        return total / len(deals)

    bids = [F(24 + i, 4) for i in range(41)]
    best = max(bids, key=pnl)
    assert best == F(15, 2) and pnl(best) == F(-1, 20)
    assert pnl(F(29, 4)) == F(-3, 40) and float(pnl(F(29, 4))) == -0.075
    # At 7.5 to 9.5 only card 10 trades.
    assert [c for c in their if their[c] > F(19, 2)] == [10]
    assert [c for c in their if their[c] < F(15, 2)] == []
    rest = [d for d in deals if d[1] != 10]
    assert mean(max(d) for d in rest) == F(145, 18) and r2(F(145, 18)) == 8.06
    assert F(9, 10) * F(145, 18) + F(1, 10) * 10 == F(33, 4)
    # Quote 7.75 to 9.75 begins to sell to you on cards 1 to 4.
    assert [c for c in their if their[c] < F(31, 4)] == [1, 2, 3, 4]
    assert round(float(pnl(F(31, 4))), 3) == -0.056
    rng = np.random.default_rng(30)
    hands = np.array([rng.permutation(10)[:3] + 1 for _ in range(80_000)])
    assert abs(hands.max(axis=1).mean() - 8.25) < 0.02


def test_q31():
    cases = []
    lo, hi = F(13, 2), F(15, 2)
    for p, q, seen in product(DIE, DIE, "PQ"):
        s, d = p + q, p - q + 7
        vs = (p if seen == "P" else q) + F(7, 2)
        vd = p + F(7, 2) if seen == "P" else F(21, 2) - q
        ts = "S" if vs < lo else "B" if vs > hi else "N"
        td = "S" if vd < lo else "B" if vd > hi else "N"
        pnl = F(0)
        pnl += s - lo if ts == "S" else hi - s if ts == "B" else 0
        pnl += d - lo if td == "S" else hi - d if td == "B" else 0
        cases.append((p, q, seen, ts, td, s, d, pnl))
    assert mean(c[7] for c in cases) == -2

    def worth(pred):
        sel = [c for c in cases if pred(c)]
        return mean(c[5] for c in sel), mean(c[6] for c in sel), len(sel)

    assert worth(lambda c: c[3] == "B")[:2] == (F(9), F(7))
    assert worth(lambda c: c[3] == "B" and c[4] == "B")[:2] == (F(9), F(9))
    assert worth(lambda c: c[3] == "B" and c[4] == "S")[:2] == (F(9), F(5))
    assert {c[2] for c in cases if c[3] == "B" and c[4] == "B"} == {"P"}
    assert {c[2] for c in cases if c[3] == "B" and c[4] == "S"} == {"Q"}
    assert worth(lambda c: c[3] == "N")[:2] == (F(7), F(7))
    assert mean(c[3] == "N" for c in cases) == F(1, 3)
    rng = np.random.default_rng(31)
    n = 500_000
    p, q = rng.integers(1, 7, n), rng.integers(1, 7, n)
    seen_p = rng.random(n) < 0.5
    vs = np.where(seen_p, p, q) + 3.5
    vd = np.where(seen_p, p + 3.5, 10.5 - q)
    s, d = p + q, p - q + 7
    res = np.where(vs < 6.5, s - 6.5, np.where(vs > 7.5, 7.5 - s, 0.0)) + np.where(
        vd < 6.5, d - 6.5, np.where(vd > 7.5, 7.5 - d, 0.0)
    )
    assert abs(res.mean() + 2) < 0.02


def test_q32():
    v10, b10 = m.hidden_number_loss(range(1, 11))
    assert v10 == F(12, 5) and float(v10) == 2.4 and b10 == 5
    v16, b16 = m.hidden_number_loss(range(1, 17))
    assert v16 == F(19, 4) and float(v16) == 4.75 and b16 == 8
    # The path by hand, by true number.
    per = {1: 5, 2: 3, 3: 2, 4: 2, 5: 0, 6: 0, 7: 2, 8: 2, 9: 3, 10: 5}
    assert sum(per.values()) == 24
    # First quote alone.
    assert mean((5 - x) if x < 5 else (x - 6) if x > 6 else 0 for x in range(1, 11)) == 2
    assert F(24, 10) - 2 == F(2, 5)

    def walk(n):
        total = 0
        for x in range(1, n + 1):
            bid = 1
            while x > bid + 1:
                total += x - bid - 1
                bid += 2
        return F(total, n)

    assert walk(10) == 7
    rng = np.random.default_rng(32)
    x = rng.integers(1, 11, 200_000)
    table = np.array([0] + [per[i] for i in range(1, 11)])
    assert abs(table[x].mean() - 2.4) < 0.02


def test_q33():
    best, policy = m.penalty_game(10, F(1, 5))
    assert round(float(best), 2) == 8.41
    assert [policy[i] for i in range(1, 11)] == [2, 3, 3, 4, 4, 5, 5, 5, 6, 6]
    assert float(m.penalty_game(10, F(1, 5), limit=11)[0]) == 8.0
    fixed = {lim: float(m.penalty_game(10, F(1, 5), limit=lim)[0]) for lim in range(1, 8)}
    assert max(fixed, key=fixed.get) == 3 and round(fixed[3], 2) == 8.35
    # The last round by hand: a purchase at q gains 1 - 0.2 (2q + 1).
    assert 1 - F(1, 5) * (2 * 1 + 1) > 0 and 1 - F(1, 5) * (2 * 2 + 1) == 0
    # Two rounds left, by hand: the value of being at q with one round left.
    v0 = {q: -F(1, 5) * q * q for q in range(-6, 7)}
    v1 = {q: (max(1 + v0[q - 1], v0[q]) + max(1 + v0[q + 1], v0[q])) / 2 for q in range(-4, 5)}
    assert 1 + v1[3] - v1[2] > 0 and 1 + v1[4] - v1[3] <= 0
    rng = np.random.default_rng(33)
    n = 200_000
    q = np.zeros(n, dtype=int)
    score = np.zeros(n)
    limits = [policy[i] for i in range(10, 0, -1)]
    for lim in limits:
        step = rng.choice([-1, 1], n)
        ok = np.abs(q + step) <= lim
        ok |= np.abs(q + step) < np.abs(q)
        score += ok
        q = np.where(ok, q + step, q)
    score -= 0.2 * q * q
    assert abs(score.mean() - float(best)) < 0.02


def test_q34():
    sv, su = 2.0, 100.0
    lam, beta = sv / (2 * su), su / sv
    assert lam == 0.01 and beta == 50
    assert sv * su / 2 == 100
    assert sv**2 / 2 == 2
    assert lam * su**2 == 100
    # Symbolic: best response and zero-profit price give the fixed point.
    b, s_v, s_u, ell = sp.symbols("beta sigma_v sigma_u lambda", positive=True)
    v, x = sp.symbols("v x", real=True)
    br = sp.solve(sp.diff(x * (v - ell * x), x), x)[0]
    assert sp.simplify(br - v / (2 * ell)) == 0
    reg = b * s_v**2 / (b**2 * s_v**2 + s_u**2)
    sol = sp.solve([sp.Eq(b, 1 / (2 * ell)), sp.Eq(ell, reg)], [b, ell], dict=True)
    good = [s for s in sol if s[ell].subs({s_v: 2, s_u: 100}) > 0]
    assert sp.simplify(good[0][ell] - s_v / (2 * s_u)) == 0
    assert sp.simplify(good[0][b] - s_u / s_v) == 0
    # Variance after the price: Var(V | y) = sv^2 (1 - rho^2), rho^2 = 1/2.
    assert beta**2 * sv**2 / (beta**2 * sv**2 + su**2) == 0.5
    rng = np.random.default_rng(34)
    n = 2_000_000
    dv = sv * rng.standard_normal(n)
    u = su * rng.standard_normal(n)
    xs = beta * dv
    y = xs + u
    price = lam * y
    assert abs(np.cov(y, dv)[0, 1] / y.var() - lam) < 1e-4
    assert abs((xs * (dv - price)).mean() - 100) < 1.0
    assert abs((dv - price).var() - 2) < 0.01
    # A deviation earns less.
    assert (2 * beta * dv * (dv - lam * 2 * beta * dv)).mean() < (xs * (dv - lam * xs)).mean()


def test_q35():
    g, v, k, q = 0.1, 4.0, 1.5, 2
    d = math.log(1 + g / k) / g
    assert round(d, 3) == 0.645
    bid_depth = g * v * (2 * q + 1) / 2 + d
    ask_depth = g * v * (1 - 2 * q) / 2 + d
    assert round(bid_depth, 3) == 1.645 and round(ask_depth, 3) == 0.045
    assert round(100 - bid_depth, 2) == 98.35 and round(100 + ask_depth, 2) == 100.05
    assert round(g * v, 2) == 0.4 and round(2 * d, 2) == 1.29
    assert round(g * v + 2 * d, 2) == 1.69
    assert round(100 - g * v * q, 2) == 99.2
    assert round(1 / k, 3) == 0.667
    assert abs(d - 1 / k) < 0.03

    def u_gain(delta, inv):
        """Expected utility of a fill relative to no fill, in units of the no-fill utility."""
        f = math.exp(-k * delta)
        return (1 - f) + f * math.exp(-g * (delta - inv))

    grid = np.linspace(0, 5, 50_001)
    bvals = [u_gain(x, g * v * (2 * q + 1) / 2) for x in grid]
    avals = [u_gain(x, g * v * (1 - 2 * q) / 2) for x in grid]
    assert abs(grid[int(np.argmin(bvals))] - bid_depth) < 1e-3
    assert abs(grid[int(np.argmin(avals))] - ask_depth) < 1e-3
    # The closed form of the fill against a Monte Carlo of the utility.
    rng = np.random.default_rng(35)
    z = rng.standard_normal(1_000_000)
    end = 100 + 2 * z
    base = np.exp(-g * q * end).mean()
    fill = np.exp(-g * ((q + 1) * end - (100 - bid_depth))).mean()
    want = np.exp(-g * (q * 100 + bid_depth) + g**2 * v * (q + 1) ** 2 / 2)
    assert abs(fill / want - 1) < 0.01
    assert abs(base / np.exp(-g * q * 100 + g**2 * v * q**2 / 2) - 1) < 0.01
