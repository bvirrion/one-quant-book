"""Every number printed in the answers of "Expectation and Indicators": exact value, then a seeded simulation."""
import itertools
import math
from fractions import Fraction as F

import numpy as np

NONNUMERIC = {}


def harmonic(n):
    return sum(F(1, k) for k in range(1, n + 1))


def test_q1():
    # Higher of two dice, by enumeration and by the tail sum.
    pairs = list(itertools.product(range(1, 7), repeat=2))
    exact = F(sum(max(p) for p in pairs), 36)
    tail = sum(1 - F(k - 1, 6) ** 2 for k in range(1, 7))
    assert exact == tail == F(161, 36)
    assert round(float(exact), 2) == 4.47
    three = sum(1 - F(k - 1, 6) ** 3 for k in range(1, 7))
    assert three == F(119, 24) and round(float(three), 2) == 4.96
    # The absolute difference follows from max + min = sum of the dice.
    diff = F(sum(abs(a - b) for a, b in pairs), 36)
    assert diff == 2 * exact - 7 == F(35, 18)
    rng = np.random.default_rng(1)
    d = rng.integers(1, 7, (400_000, 2))
    assert abs(d.max(axis=1).mean() - float(exact)) < 0.01
    assert abs(np.abs(d[:, 0] - d[:, 1]).mean() - float(diff)) < 0.01


def test_q2():
    # First step: S = (1/6) 6 + (5/6)(3 + S).
    assert (F(1, 6) * 6 + F(5, 6) * 3) / (1 - F(5, 6)) == 21
    assert F(6) * F(7, 2) == 21
    assert 5 * F(3) + 6 == 21
    # Number of rolls of each other face before the six: 1.
    assert F(1, 6) / F(1, 6) == 1
    rng = np.random.default_rng(2)
    totals = []
    ones = []
    for _ in range(100_000):
        s, c = 0, 0
        while True:
            r = rng.integers(1, 7)
            s += r
            if r == 6:
                break
            c += r == 1
        totals.append(s)
        ones.append(c)
    assert abs(np.mean(totals) - 21) < 0.2
    assert abs(np.mean(ones) - 1) < 0.02


def small_deck_adjacent(ranks, suits):
    deck = [r for r in range(ranks) for _ in range(suits)]
    vals = []
    for perm in set(itertools.permutations(deck)):
        vals.append(sum(perm[i] == perm[i + 1] for i in range(len(perm) - 1)))
    return F(sum(vals), len(vals)), F(sum(v * v for v in vals), len(vals))


def adjacency_moments(ranks, suits):
    n = ranks * suits
    p = F(suits - 1, n - 1)
    mean = (n - 1) * p
    over = p * F(suits - 2, n - 2)
    # Non-overlapping pair: same rank again, or a different rank.
    second = F(suits - 2, n - 2) * F(suits - 3, n - 3) + F(n - suits, n - 2) * F(suits - 1, n - 3)
    non = p * second
    n_over = n - 2
    n_non = (n - 1) * (n - 2) // 2 - n_over
    second_moment = mean + 2 * n_over * over + 2 * n_non * non
    return mean, second_moment - mean**2


def test_q3():
    mean, var = adjacency_moments(13, 4)
    assert mean == 3
    assert var == F(48, 17) and round(float(var), 2) == 2.82
    assert F(3, 51) * F(2, 50) == F(1, 425)
    assert F(2, 50) * F(1, 49) + F(48, 50) * F(3, 49) == F(146, 2450)
    assert 3 + 2 * 50 * F(1, 425) + 2 * 1225 * F(3, 51) * F(146, 2450) - 9 == var
    assert round(math.exp(-3), 2) == 0.05
    # The moment formula agrees with brute force on a small deck.
    m1, m2 = small_deck_adjacent(3, 3)
    a, b = adjacency_moments(3, 3)
    assert m1 == a and m2 - m1**2 == b
    rng = np.random.default_rng(3)
    deck = np.repeat(np.arange(13), 4)
    samples = []
    for _ in range(60_000):
        p = rng.permutation(deck)
        samples.append((p[1:] == p[:-1]).sum())
    samples = np.array(samples)
    assert abs(samples.mean() - 3) < 0.02
    assert abs(samples.var() - float(var)) < 0.05
    assert abs((samples == 0).mean() - 0.045) < 0.005


def test_q4():
    for n in range(2, 8):
        vals = [sum(p[i] == i for i in range(n)) for p in itertools.permutations(range(n))]
        assert F(sum(vals), len(vals)) == 1
        assert F(sum(v * v for v in vals), len(vals)) == 2  # variance 1
    # Pair of positions: both fixed with probability 1/(n(n-1)).
    n = 52
    assert n * F(1, n) == 1
    assert n * F(1, n) + n * (n - 1) * F(1, n * (n - 1)) == 2  # E[X^2]
    rng = np.random.default_rng(4)
    s = np.array([(rng.permutation(52) == np.arange(52)).sum() for _ in range(100_000)])
    assert abs(s.mean() - 1) < 0.01
    assert abs(s.var() - 1) < 0.02
    assert abs((s == 0).mean() - math.exp(-1)) < 0.005


def test_q5():
    e = sum(F(6, k) for k in range(1, 7))
    assert e == F(147, 10)
    var = sum((1 - F(k, 6)) / F(k, 6) ** 2 for k in range(1, 7))
    assert round(float(var), 2) == 38.99
    assert e * F(7, 2) == F(1029, 20) and float(e * F(7, 2)) == 51.45
    assert e / 6 == F(49, 20)
    assert round(float(52 * harmonic(52))) == 236
    assert round(float(1000 * harmonic(1000)), -2) == 7500
    assert round(math.sqrt(float(var)), 1) == 6.2
    rng = np.random.default_rng(5)
    t, s = [], []
    for _ in range(50_000):
        seen, count, total = set(), 0, 0
        while len(seen) < 6:
            r = int(rng.integers(1, 7))
            seen.add(r)
            count += 1
            total += r
        t.append(count)
        s.append(total)
    assert abs(np.mean(t) - 14.7) < 0.1
    assert abs(np.var(t) - 38.99) < 1.2
    assert abs(np.mean(s) - 51.45) < 0.4


def test_q6():
    n = 21
    assert 1 + F(n - 1, 2) == 11
    assert F(n - 1, 4) == 5
    assert 1 + F(251, 2) == F(253, 2) and round(math.sqrt(251) / 2, 1) == 7.9
    assert round(126.5 - 2 * math.sqrt(251) / 2) == 111
    # Enumerate a shorter sequence: changes are independent fair bits.
    m = 12
    vals = []
    for seq in itertools.product((0, 1), repeat=m):
        vals.append(1 + sum(seq[i] != seq[i + 1] for i in range(m - 1)))
    assert F(sum(vals), len(vals)) == 1 + F(m - 1, 2)
    mean = F(sum(vals), len(vals))
    assert F(sum(v * v for v in vals), len(vals)) - mean**2 == F(m - 1, 4)
    # Runs of exactly three heads in 100 tosses.
    exact3 = 2 * F(1, 16) + 96 * F(1, 32)
    assert exact3 == F(25, 8) and float(exact3) == 3.125
    # Check that formula against enumeration for 12 tosses.
    tot = 0
    for seq in itertools.product("HT", repeat=m):
        s = "T" + "".join(seq) + "T"
        tot += sum(s[i : i + 5] == "THHHT" for i in range(len(s) - 4))
    assert F(tot, 2**m) == 2 * F(1, 16) + (m - 4) * F(1, 32)
    rng = np.random.default_rng(6)
    x = rng.integers(0, 2, (200_000, 21))
    runs = 1 + (x[:, 1:] != x[:, :-1]).sum(axis=1)
    assert abs(runs.mean() - 11) < 0.02 and abs(runs.var() - 5) < 0.06
    count = 0
    for row in rng.integers(0, 2, (5_000, 100)):
        s = "T" + "".join("H" if v else "T" for v in row) + "T"
        count += sum(s[i : i + 5] == "THHHT" for i in range(len(s) - 4))
    assert abs(count / 5_000 - 3.125) < 0.05


def test_q7():
    # Distribution of the position m of the second ace.
    total = math.comb(52, 4)
    pmf = {m: F((m - 1) * math.comb(52 - m, 2), total) for m in range(2, 51)}
    assert sum(pmf.values()) == 1
    exact = sum(m * p for m, p in pmf.items())
    assert exact == F(106, 5) and float(exact) == 21.2
    assert 2 * F(48, 5) + 2 == F(106, 5)
    assert F(48, 5) == F(96, 10)
    assert 4 * F(53, 5) == F(212, 5) and float(F(212, 5)) == 42.4
    assert 2 * F(52, 5) == F(104, 5) and float(F(104, 5)) == 20.8
    rng = np.random.default_rng(7)
    pos = [np.sort(rng.choice(52, 4, replace=False))[1] + 1 for _ in range(100_000)]
    assert abs(np.mean(pos) - 21.2) < 0.08


def test_q8():
    exact = sum(F(101 - k, 100) ** 3 for k in range(1, 101))
    assert exact == F(255025, 10000) and float(exact) == 25.5025
    assert exact == F((100 * 101 // 2) ** 2, 100**3)
    assert 101 - exact == F(754975, 10000)
    assert F(1, 4) * 100 == 25
    rng = np.random.default_rng(8)
    d = rng.integers(1, 101, (400_000, 3))
    assert abs(d.min(axis=1).mean() - 25.5025) < 0.1
    assert abs(d.max(axis=1).mean() - 75.4975) < 0.1


def first_repeat(n):
    e, p = F(0), F(1)
    for k in range(0, n + 1):
        e += p  # P(T > k)
        p *= F(n - k, n)
    return e


def test_q9():
    exact = first_repeat(6)
    assert exact == F(1223, 324) and round(float(exact), 2) == 3.77
    terms = [F(1), F(1), F(5, 6), F(5, 9), F(5, 18), F(5, 54), F(5, 324)]
    assert sum(terms) == exact
    n = 1024
    e, p = 0.0, 1.0
    for k in range(n + 1):
        e += p
        p *= (n - k) / n
    assert round(e, 1) == 40.8
    assert round(math.sqrt(math.pi * n / 2) + 2 / 3, 1) == 40.8
    # 32-bit identifiers: first expected collision.
    assert round(math.sqrt(math.pi * 2**32 / 2) + 2 / 3, -3) == 82000
    rng = np.random.default_rng(9)
    vals = []
    for _ in range(100_000):
        seen, c = set(), 0
        while True:
            r = int(rng.integers(6))
            c += 1
            if r in seen:
                break
            seen.add(r)
        vals.append(c)
    assert abs(np.mean(vals) - float(exact)) < 0.01


def test_q10():
    e = sum(1 / math.factorial(n) for n in range(30))
    assert abs(e - math.e) < 1e-12
    second = sum((2 * n + 1) / math.factorial(n) for n in range(30))
    assert abs(second - 3 * math.e) < 1e-12
    assert round(3 * math.e - math.e**2, 3) == 0.766
    assert round(math.e / 2, 3) == 1.359
    rng = np.random.default_rng(10)
    u = rng.random((400_000, 16))
    s = u.cumsum(axis=1)
    n = (s > 1).argmax(axis=1) + 1
    assert abs(n.mean() - math.e) < 0.005
    assert abs(n.var() - (3 * math.e - math.e**2)) < 0.01
    stop = s[np.arange(len(n)), n - 1]
    assert abs(stop.mean() - math.e / 2) < 0.003


def test_q11():
    # P(T > k) = 1/(k+1): the first draw is the largest of the first k+1.
    for k in range(1, 7):
        count = sum(1 for p in itertools.permutations(range(k + 1)) if p[0] == k)
        assert F(count, math.factorial(k + 1)) == F(1, k + 1)
    assert F(1, 2) + F(1, 6) + F(1, 12) == F(3, 4)  # P(T<=3)
    capped = float(harmonic(1000))
    assert round(capped, 2) == 7.49
    assert round(float(harmonic(10)), 2) == 2.93
    rng = np.random.default_rng(11)
    first = rng.random(200_000)
    t = rng.geometric(1 - first)
    assert abs((t == 1).mean() - 0.5) < 0.005
    assert abs((t <= 3).mean() - 0.75) < 0.005
    # The running mean does not settle: a larger sample has a far larger mean.
    assert t.mean() > float(harmonic(1000))
    capped_mean = np.minimum(t, 1000).mean()
    assert abs(capped_mean - capped) < 0.1


def test_q12():
    h, h2 = harmonic(100), sum(F(1, k * k) for k in range(1, 101))
    assert round(float(h), 3) == 5.187
    assert round(float(h - h2), 2) == 3.55
    assert round(math.log(100) + 0.577, 2) == 5.18
    assert round(float(harmonic(252)), 1) == 6.1
    # Indicators are independent: check on all permutations of 6 values.
    n = 6
    perms = list(itertools.permutations(range(n)))

    def recs(p):
        best, out = -1, []
        for v in p:
            out.append(v > best)
            best = max(best, v)
        return out

    r = [recs(p) for p in perms]
    for i in range(n):
        assert F(sum(x[i] for x in r), len(perms)) == F(1, i + 1)
        for j in range(i + 1, n):
            assert F(sum(x[i] and x[j] for x in r), len(perms)) == F(1, (i + 1) * (j + 1))
    rng = np.random.default_rng(12)
    u = rng.random((100_000, 100))
    records = (u == np.maximum.accumulate(u, axis=1)).sum(axis=1)
    assert abs(records.mean() - float(h)) < 0.02
    assert abs(records.var() - float(h - h2)) < 0.06


def test_q13():
    n = 60
    cov = -F(n, 36)
    var = n * F(1, 6) * F(5, 6)
    assert cov == -F(5, 3) and var == F(25, 3)
    assert cov / var == -F(1, 5)
    assert 2 * var + 2 * cov == F(40, 3) == n * F(1, 3) * F(2, 3)
    # Enumeration of 6 rolls for the general formula.
    m = 6
    tot1, tot2, tot12 = 0, 0, 0
    for seq in itertools.product(range(6), repeat=m):
        a, b = seq.count(0), seq.count(1)
        tot1 += a
        tot2 += b
        tot12 += a * b
    cnt = 6**m
    assert F(tot12, cnt) - F(tot1, cnt) * F(tot2, cnt) == -F(m, 36)
    rng = np.random.default_rng(13)
    counts = rng.multinomial(60, [1 / 6] * 6, 300_000)
    assert abs(np.cov(counts[:, 0], counts[:, 1])[0, 1] + 5 / 3) < 0.03
    assert abs(np.corrcoef(counts[:, 0], counts[:, 1])[0, 1] + 0.2) < 0.005


def test_q14():
    # Exact: P(N = k and all even) = (1/3)^(k-1) (1/6).
    p = F(1, 6) / (1 - F(1, 3))
    assert p == F(1, 4)
    num = F(1, 6) / (1 - F(1, 3)) ** 2
    assert num / p == F(3, 2)
    # Series check.
    s0 = sum(F(1, 3) ** (k - 1) * F(1, 6) for k in range(1, 60))
    s1 = sum(k * F(1, 3) ** (k - 1) * F(1, 6) for k in range(1, 60))
    assert abs(float(s1 / s0) - 1.5) < 1e-12 and abs(float(s0) - 0.25) < 1e-12
    assert num == F(3, 8)
    assert 1 / F(1, 3) == 3  # the classic wrong answer
    assert 1 / F(2, 6) == 3  # the follow-up: no ones, stop on {1, 6}
    # Stop on {1,3,5,6}: geometric with p = 2/3.
    assert 1 / F(4, 6) == F(3, 2)
    # The stop-and-target walk quoted in the answer: stop 10 below, target 5 above.
    size = 15
    pts = list(range(1, size))
    # h[x] = P(reach top from x) = x/size; g[x] = E[T; top] solves g[x] = h[x] + (g[x-1]+g[x+1])/2.
    h = {x: F(x, size) for x in range(size + 1)}
    from sympy import Rational, linsolve, symbols

    syms = {x: symbols(f"g{x}") for x in pts}
    get = lambda x: syms[x] if x in syms else 0  # noqa: E731
    eqs = [syms[x] - Rational(h[x].numerator, h[x].denominator) - (get(x - 1) + get(x + 1)) / 2 for x in pts]
    sol = next(iter(linsolve(eqs, [syms[x] for x in pts])))
    g10 = sol[pts.index(10)]
    wins = g10 / Rational(2, 3)
    assert wins == Rational(125, 3) and round(float(wins), 1) == 41.7
    assert (Rational(50) - g10) / Rational(1, 3) == Rational(200, 3) and round(200 / 3, 1) == 66.7
    rng = np.random.default_rng(14)
    win_t, lose_t = [], []
    for _ in range(4_000):
        x, t = 0, 0
        while -10 < x < 5:
            x += 2 * int(rng.integers(0, 2)) - 1
            t += 1
        (win_t if x == 5 else lose_t).append(t)
    assert abs(np.mean(win_t) - 125 / 3) < 2.5
    assert abs(np.mean(lose_t) - 200 / 3) < 5
    kept = []
    for _ in range(200_000):
        c = 0
        while True:
            r = rng.integers(1, 7)
            c += 1
            if r in (1, 3, 5):
                c = 0
                break
            if r == 6:
                break
        if c:
            kept.append(c)
    assert abs(len(kept) / 200_000 - 0.25) < 0.005
    assert abs(np.mean(kept) - 1.5) < 0.01


def noodle_exact(n):
    return sum(F(1, 2 * k - 1) for k in range(1, n + 1))


def test_q15():
    assert noodle_exact(1) == 1
    assert noodle_exact(2) == F(4, 3)
    val = float(noodle_exact(100))
    assert round(val, 2) == 3.28
    assert round(0.5 * math.log(100) + 0.98, 2) == 3.28
    one = F(1)
    for k in range(1, 101):
        one *= F(2 * k - 2, 2 * k - 1) if k > 1 else 1
    assert round(float(one), 3) == 0.089
    rng = np.random.default_rng(15)

    def simulate(n):
        ends = rng.permutation(2 * n)
        parent = list(range(n))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        loops = 0
        for i in range(0, 2 * n, 2):
            a, b = find(ends[i] // 2), find(ends[i + 1] // 2)
            if a == b:
                loops += 1
            else:
                parent[a] = b
        return loops

    loops = [simulate(100) for _ in range(6_000)]
    assert abs(np.mean(loops) - val) < 0.05
    assert abs(np.mean(np.array(loops) == 1) - float(one)) < 0.015


def bounce_run(rng, n):
    """Event-driven bouncing ants; returns last fall time and number of collisions."""
    pos = np.sort(rng.random(n))
    vel = rng.choice([-1.0, 1.0], n)
    # Ghost answer computed before the run.
    ghost_time = float(np.max(np.where(vel > 0, 1 - pos, pos)))
    ghost_cross = sum(
        1 for i in range(n) for j in range(i + 1, n) if vel[i] > 0 and vel[j] < 0
    )
    ghost_falls = sorted(np.where(vel > 0, 1 - pos, pos).tolist())
    t, collisions = 0.0, 0
    pos, vel = pos.tolist(), vel.tolist()
    alive = list(range(n))
    falls, order_left, order_right = [], [], []
    while alive:
        next_t, event = math.inf, None
        for a in (alive[0], alive[-1]):
            dt = (1 - pos[a]) if vel[a] > 0 else pos[a]
            if (a == alive[0] and vel[a] < 0) or (a == alive[-1] and vel[a] > 0):
                if dt < next_t:
                    next_t, event = dt, ("fall", a)
        for a, b in zip(alive, alive[1:], strict=False):
            if vel[a] > 0 and vel[b] < 0:
                dt = (pos[b] - pos[a]) / 2
                if dt < next_t:
                    next_t, event = dt, ("hit", a, b)
        for a in alive:
            pos[a] += vel[a] * next_t
        t += next_t
        if event[0] == "fall":
            alive.remove(event[1])
            falls.append(t)
            (order_right if vel[event[1]] > 0 else order_left).append(event[1])
        else:
            collisions += 1
            vel[event[1]], vel[event[2]] = -1.0, 1.0
    assert all(abs(u - v) < 1e-9 for u, v in zip(sorted(falls), ghost_falls, strict=True))
    assert order_left == sorted(order_left) and order_right == sorted(order_right, reverse=True)
    return t, collisions, ghost_time, ghost_cross


def test_q16():
    assert round(100 / 101, 3) == 0.990
    assert F(100 * 99, 2) * F(1, 4) == F(2475, 2) and float(F(2475, 2)) == 1237.5
    rng = np.random.default_rng(16)
    # Real bouncing ants give the same last fall time and collision count as the ghost picture.
    for _ in range(300):
        t, c, gt, gc = bounce_run(rng, 7)
        assert abs(t - gt) < 1e-9
        assert c == gc
    # And the mean follows n/(n+1).
    vals = [bounce_run(rng, 7) for _ in range(5_000)]
    assert abs(np.mean([v[0] for v in vals]) - 7 / 8) < 0.005
    assert abs(np.mean([v[1] for v in vals]) - 21 / 4) < 0.1
    pos = rng.random((200_000, 100))
    v = rng.integers(0, 2, (200_000, 100))
    d = np.where(v == 1, 1 - pos, pos).max(axis=1)
    assert abs(d.mean() - 100 / 101) < 0.0005


def test_q17():
    assert 2 * F(53, 5) - F(53, 9) == F(689, 45)
    assert round(689 / 45, 2) == 15.31
    # Small deck check of max = a + b - min, and the (n+1)/(k+1) rule.
    n, deck = 7, list(range(7))
    tot_max, tot_a, tot_min = 0, 0, 0
    count = 0
    for p in itertools.permutations(deck):
        # Cards 0, 1 are aces, cards 2, 3 kings, the rest other.
        a = min(p.index(0), p.index(1)) + 1
        k = min(p.index(2), p.index(3)) + 1
        tot_max += max(a, k)
        tot_min += min(a, k)
        tot_a += a
        count += 1
    assert F(tot_a, count) == F(n + 1, 3)
    assert F(tot_min, count) == F(n + 1, 5)
    assert F(tot_max, count) == 2 * F(n + 1, 3) - F(n + 1, 5)
    # Unequal coupons by inclusion-exclusion.
    probs = [F(1, 2), F(1, 3), F(1, 6)]
    e = F(0)
    for r in range(1, 4):
        for sub in itertools.combinations(probs, r):
            e += (-1) ** (r + 1) / sum(sub)
    assert e == F(73, 10)
    assert 2 + 3 + 6 - F(6, 5) - F(3, 2) - 2 + 1 == F(73, 10)
    assert 10 + 10 - 1 / (F(1, 10) + F(1, 10)) == 15
    rng = np.random.default_rng(17)
    deck = np.array([0] * 4 + [1] * 4 + [2] * 44)
    vals = []
    for _ in range(100_000):
        p = rng.permutation(deck)
        vals.append(max(np.argmax(p == 0), np.argmax(p == 1)) + 1)
    assert abs(np.mean(vals) - 689 / 45) < 0.05
    vals = []
    for _ in range(100_000):
        seen = set()
        c = 0
        while len(seen) < 3:
            seen.add(int(rng.choice(3, p=[0.5, 1 / 3, 1 / 6])))
            c += 1
        vals.append(c)
    assert abs(np.mean(vals) - 7.3) < 0.05


def socks(n):
    return sum(F(2**k * math.comb(n, k), math.comb(2 * n, k)) for k in range(0, n + 1))


def test_q18():
    assert socks(5) == F(256, 63) and round(256 / 63, 2) == 4.06
    terms = [F(2**k * math.comb(5, k), math.comb(10, k)) for k in range(6)]
    assert terms == [F(1), F(1), F(8, 9), F(2, 3), F(8, 21), F(8, 63)]
    for n in range(1, 12):
        assert socks(n) == F(4**n, math.comb(2 * n, n))
    assert round(4**10 / math.comb(20, 10), 2) == 5.68
    assert round(math.sqrt(math.pi * 5), 2) == 3.96
    # The classic wrong answer: birthday formula with five types.
    wrong = sum(math.prod(F(5 - j, 5) for j in range(k)) for k in range(0, 6))
    assert round(float(wrong), 2) == 3.51
    rng = np.random.default_rng(18)
    socks_arr = np.repeat(np.arange(5), 2)
    vals = []
    for _ in range(100_000):
        p = rng.permutation(socks_arr)
        seen = set()
        for i, v in enumerate(p):
            if v in seen:
                vals.append(i + 1)
                break
            seen.add(v)
    assert abs(np.mean(vals) - 256 / 63) < 0.01


def remaining(r, b):
    return F(r, b + 1) + F(b, r + 1)


def test_q19():
    assert remaining(6, 4) == F(62, 35) and round(62 / 35, 2) == 1.77
    assert 10 - F(62, 35) == F(288, 35) and round(288 / 35, 2) == 8.23
    # Enumeration of all colour orders.
    total, tot_rem, last_red = 0, 0, 0
    for reds in itertools.combinations(range(10), 6):
        seq = [1 if i in reds else 0 for i in range(10)]
        last = seq[-1]
        rem = 0
        for v in reversed(seq):
            if v != last:
                break
            rem += 1
        tot_rem += rem
        last_red += last
        total += 1
    assert F(tot_rem, total) == F(62, 35)
    assert F(last_red, total) == F(3, 5)
    rng = np.random.default_rng(19)
    arr = np.array([1] * 6 + [0] * 4)
    vals = []
    for _ in range(100_000):
        p = rng.permutation(arr)
        last = p[-1]
        k = 0
        while k < 10 and p[9 - k] == last:
            k += 1
        vals.append(k)
    assert abs(np.mean(vals) - 62 / 35) < 0.01


def test_q20():
    n = 100
    q1, q2 = F(99, 100) ** 100, F(98, 100) ** 100
    mean = n * q1
    var = n * q1 + n * (n - 1) * q2 - mean**2
    assert round(float(mean), 2) == 36.60
    assert round(float(var), 2) == 9.74
    assert round(float(n * q1 * (1 - q1)), 1) == 23.2
    assert round(100 * (math.exp(-1) - 2 * math.exp(-2)), 2) == 9.72
    assert round(float(q2 - q1**2), 5) == -0.00136
    # Enumeration of the formula for small m and n.
    k, m = 4, 5
    tot, tot2 = 0, 0
    for seq in itertools.product(range(k), repeat=m):
        e = k - len(set(seq))
        tot += e
        tot2 += e * e
    cnt = k**m
    a, b = F(k - 1, k) ** m, F(k - 2, k) ** m
    assert F(tot, cnt) == k * a
    assert F(tot2, cnt) - F(tot, cnt) ** 2 == k * a + k * (k - 1) * b - (k * a) ** 2
    rng = np.random.default_rng(20)
    empties = np.array([100 - len(np.unique(rng.integers(0, 100, 100))) for _ in range(100_000)])
    assert abs(empties.mean() - float(mean)) < 0.05
    assert abs(empties.var() - float(var)) < 0.2
    assert round(math.sqrt(float(var)), 1) == 3.1
    assert round((50 - float(mean)) / math.sqrt(float(var)), 1) == 4.3
    # Under the binomial variance the same count would be under 3 standard deviations.
    assert (50 - float(mean)) / math.sqrt(float(n * q1 * (1 - q1))) < 3
    assert n * (n - 1) == 9900


def test_q21():
    # Pair formula against the recursion, exactly.
    def formula(n):
        return 2 * (n + 1) * harmonic(n) - 4 * n

    rec = [F(0), F(0)]
    for n in range(2, 60):
        rec.append(n - 1 + F(2, n) * sum(rec))
    for n in range(2, 60):
        assert rec[n] == formula(n)
    pair = sum(F(2, j - i + 1) for i in range(1, 11) for j in range(i + 1, 11))
    assert pair == formula(10)
    assert round(float(formula(10)), 2) == 24.44
    assert round(float(formula(1000))) == 10986
    assert 1000 * 999 // 2 == 499500
    assert round(2 * math.log(2), 2) == 1.39
    assert abs(2 * 1000 * math.log(1000) - 2.85 * 1000 - float(formula(1000))) < 30

    rng = np.random.default_rng(21)

    def comparisons(a):
        if len(a) < 2:
            return 0
        p = a[rng.integers(len(a))]
        return len(a) - 1 + comparisons([v for v in a if v < p]) + comparisons([v for v in a if v > p])

    vals = [comparisons(list(range(10))) for _ in range(40_000)]
    assert abs(np.mean(vals) - float(formula(10))) < 0.08
    # Follow-up: worst case n(n-1)/2.
    assert 10 * 9 // 2 == 45


def derangements(n):
    d = [1, 0]
    for k in range(2, n + 1):
        d.append((k - 1) * (d[-1] + d[-2]))
    return d


def test_q22():
    size = 12
    d = derangements(size)

    def p_fixed(n, k):
        return F(math.comb(n, k) * d[n - k], math.factorial(n))

    rounds = [F(0)]
    deals = [F(0)]
    for n in range(1, size + 1):
        p0 = p_fixed(n, 0)
        rounds.append((1 + sum(p_fixed(n, k) * rounds[n - k] for k in range(1, n + 1))) / (1 - p0))
        deals.append((n + sum(p_fixed(n, k) * deals[n - k] for k in range(1, n + 1))) / (1 - p0))
    assert rounds[1] == 1
    for n in range(2, size + 1):
        assert rounds[n] == n
    # Total cards dealt: n + n(n-1)/2 + ... = n^2/2 + n.
    for n in range(2, size + 1):
        assert deals[n] == F(n * n, 2) + n
    assert deals[10] == 60
    rng = np.random.default_rng(22)
    r_vals, d_vals = [], []
    for _ in range(40_000):
        n, r, c = 10, 0, 0
        while n:
            r += 1
            c += n
            n -= (rng.permutation(n) == np.arange(n)).sum()
        r_vals.append(r)
        d_vals.append(c)
    assert abs(np.mean(r_vals) - 10) < 0.05
    assert abs(np.mean(d_vals) - 60) < 0.4


def test_q23():
    # E[final draw] = Sum_{n>=1} integral_0^1 y (1-y^n) dy / n!.
    final = sum((0.5 - 1 / (n + 2)) / math.factorial(n) for n in range(1, 30))
    assert abs(final - (math.e / 2 - 1)) < 1e-12
    assert round(math.e / 2 - 1, 3) == 0.359
    peak = sum(1 / (math.factorial(n - 1) * (n + 2)) for n in range(1, 30))
    assert abs(peak - (math.e - 2)) < 1e-12
    assert round(math.e - 2, 3) == 0.718
    assert abs(sum(1 / (math.factorial(n) * (n + 2)) for n in range(0, 30)) - 1) < 1e-12
    rng = np.random.default_rng(23)
    last, top, count, total = [], [], [], []
    for _ in range(300_000):
        prev = rng.random()
        c, s = 1, prev
        while True:
            x = rng.random()
            c += 1
            s += x
            if x < prev:
                break
            prev = x
        last.append(x)
        top.append(prev)
        count.append(c)
        total.append(s)
    assert abs(np.mean(last) - (math.e / 2 - 1)) < 0.002
    assert abs(np.mean(top) - (math.e - 2)) < 0.002
    assert abs(np.mean(count) - math.e) < 0.005
    assert abs(np.mean(total) - math.e / 2) < 0.005


def singleton_dp(n):
    """Exact expected number of faces seen exactly once, by dynamic programming on (seen, singles)."""
    memo = {}

    def e(seen, singles):
        if seen == n:
            return F(singles)
        key = (seen, singles)
        if key in memo:
            return memo[key]
        new, back_single = F(n - seen, n), F(singles, n)
        rest = F(seen - singles, n)
        val = new * e(seen + 1, singles + 1)
        if singles:
            val += back_single * e(seen, singles - 1)
        memo[key] = val / (1 - rest)
        return memo[key]

    return e(0, 0)


def test_q24():
    for n in range(1, 12):
        assert singleton_dp(n) == harmonic(n)
    assert harmonic(6) == F(49, 20) and float(harmonic(6)) == 2.45
    assert round(float(harmonic(52)), 2) == 4.54
    # The naive Poisson answer that the stopping rule invalidates.
    assert round(14.7 * math.exp(-14.7 / 6), 2) == 1.27
    rng = np.random.default_rng(24)
    vals = []
    for _ in range(100_000):
        counts = [0] * 6
        while min(counts) == 0:
            counts[int(rng.integers(6))] += 1
        vals.append(counts.count(1))
    assert abs(np.mean(vals) - 2.45) < 0.01


def two_of_each(n):
    memo = {}

    def e(zero, one):
        if zero == 0 and one == 0:
            return F(0)
        key = (zero, one)
        if key in memo:
            return memo[key]
        val = F(n, zero + one)
        if zero:
            val += F(zero, zero + one) * e(zero - 1, one + 1)
        if one:
            val += F(one, zero + one) * e(zero, one - 1)
        memo[key] = val
        return val

    return e(n, 0)


def _integral(k):
    # Integral of e^{-ku}(1+u)^k over the positive axis, as (numerator, denominator).
    val = sum(F(math.comb(k, j) * math.factorial(j), k ** (j + 1)) for j in range(k + 1))
    return val.numerator, val.denominator


def test_q25():
    from sympy import Integer, Rational, exp, integrate, oo, symbols

    exact = two_of_each(6)
    assert round(float(exact), 2) == 24.13
    u = symbols("u", positive=True)
    # 6 * integral of 1 - (1 - e^{-u}(1+u))^6, expanded term by term.
    total = Integer(0)
    for k in range(1, 7):
        total += (-1) ** (k + 1) * math.comb(6, k) * integrate(exp(-k * u) * (1 + u) ** k, (u, 0, oo))
    assert 6 * total == Rational(exact.numerator, exact.denominator)
    # The first terms quoted in the answer.
    assert integrate(exp(-u) * (1 + u), (u, 0, oo)) == 2
    assert integrate(exp(-2 * u) * (1 + u) ** 2, (u, 0, oo)) == Rational(5, 4)
    assert round(float(exact) - 14.7, 2) == 9.43
    assert 2 * 14.7 == 29.4
    assert exact == 6 * sum((-1) ** (k + 1) * math.comb(6, k) * F(*_integral(k)) for k in range(1, 7))
    rng = np.random.default_rng(25)
    vals = []
    for _ in range(50_000):
        counts = [0] * 6
        c = 0
        while min(counts) < 2:
            counts[int(rng.integers(6))] += 1
            c += 1
        vals.append(c)
    assert abs(np.mean(vals) - float(exact)) < 0.08
