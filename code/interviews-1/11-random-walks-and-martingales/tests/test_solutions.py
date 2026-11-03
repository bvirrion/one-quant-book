"""Every number printed in the answers of "Random Walks and Martingales": a linear system, a formula and a simulation."""
import math
from fractions import Fraction as F

import numpy as np

C = math.comb
NONNUMERIC = {}


def solve_chain(states, moves, reward=None):
    """Expected reward until absorption by a state outside `states`. moves(s) lists (next state, probability)."""
    idx = {s: i for i, s in enumerate(states)}
    a = np.eye(len(states))
    b = np.zeros(len(states))
    for s in states:
        i = idx[s]
        for t, p in moves(s):
            if t in idx:
                a[i, idx[t]] -= p
            elif reward is not None:
                b[i] += p * reward(t)
        if reward is None:
            b[i] = 1.0
    return dict(zip(states, np.linalg.solve(a, b), strict=True))


def walk(p):
    return lambda s: ((s + 1, p), (s - 1, 1 - p))


def sim_exit(rng, p, start, low, high, runs):
    """Seeded simulation of an exit from (low, high): chance of the top, mean duration."""
    tops = total = 0
    for _ in range(runs):
        s, t = start, 0
        while low < s < high:
            s += 1 if rng.random() < p else -1
            t += 1
        tops += s >= high
        total += t
    return tops / runs, total / runs


def test_q1():
    assert F(3, 10) == F(3, 10)
    time = solve_chain(list(range(1, 10)), walk(0.5))
    top = solve_chain(list(range(1, 10)), walk(0.5), lambda t: t == 10)
    assert abs(time[3] - 21) < 1e-9 and abs(top[3] - 0.3) < 1e-9
    a, t = sim_exit(np.random.default_rng(1), 0.5, 3, 0, 10, 30_000)
    assert abs(a - 0.3) < 0.01 and abs(t - 21) < 0.4
    # Start at an end and nothing happens.
    assert 0 * (10 - 0) == 0 and 10 * (10 - 10) == 0


def test_q2():
    r = F(2, 3)
    p = (1 - r**5) / (1 - r**10)
    assert p == 1 / (1 + r**5)
    assert round(float(p), 4) == 0.8836
    duration = (10 * p - 5) / F(1, 5)
    assert round(float(duration), 1) == 19.2
    top = solve_chain(list(range(1, 10)), walk(0.6), lambda t: t == 10)
    time = solve_chain(list(range(1, 10)), walk(0.6))
    assert abs(top[5] - float(p)) < 1e-9 and abs(time[5] - float(duration)) < 1e-9
    a, t = sim_exit(np.random.default_rng(2), 0.6, 5, 0, 10, 30_000)
    assert abs(a - float(p)) < 0.008 and abs(t - float(duration)) < 0.3
    # A fair coin brings this back to one half.
    assert (5 - 0) / (10 - 0) == 0.5


def test_q3():
    assert F(9, 9 + 1) == F(9, 10)
    assert F(9, 10) * 1 + F(1, 10) * (-9) == 0
    assert 1 * 9 == 9
    time = solve_chain(list(range(-8, 1)), walk(0.5))
    assert abs(time[0] - 9) < 1e-9
    a, t = sim_exit(np.random.default_rng(3), 0.5, 0, -9, 1, 30_000)
    assert abs(a - 0.9) < 0.006 and abs(t - 9) < 0.4


def test_q4():
    assert C(10, 5) == 252
    assert round(252 / 1024, 3) == 0.246
    u100 = F(C(100, 50), 2**100)
    assert round(float(u100), 4) == 0.0796
    exact = sum(F(C(100, k), 2**100) * abs(2 * k - 100) for k in range(101))
    assert exact == 100 * u100
    assert round(float(exact), 2) == 7.96
    assert round(math.sqrt(2 * 100 / math.pi), 2) == 7.98
    rng = np.random.default_rng(4)
    steps = rng.binomial(100, 0.5, 1_000_000) * 2 - 100
    assert abs(np.abs(steps).mean() - 7.96) < 0.02
    assert abs((rng.binomial(10, 0.5, 1_000_000) == 5).mean() - 252 / 1024) < 0.002
    # Variance N = 100 steps, not n = 50: sigma * sqrt(2 / pi) is the 7.98.
    assert abs(math.sqrt(100) * math.sqrt(2 / math.pi) - math.sqrt(2 * 100 / math.pi)) < 1e-12
    assert (exact - 7.98) ** 2 < (exact - math.sqrt(2 * 50 / math.pi)) ** 2


def test_q5():
    assert F(10) / F(1, 5) == 50
    rng = np.random.default_rng(5)
    total = 0
    for _ in range(10_000):
        s = t = 0
        while s < 10:
            s += 1 if rng.random() < 0.6 else -1
            t += 1
        total += t
    assert abs(total / 10_000 - 50) < 0.8
    # Second route: the time per level is a first-step sum, x = 1 + 0.4 * 2x, so x = 5.
    assert F(1) / (1 - F(2, 5) * 2) == 5
    # At zero drift the time is infinite; just above it, huge.
    assert 10 / 0.0002 == 50_000


def test_q6():
    r = F(2, 3)
    assert round(float(r**10), 4) == 0.0173
    # P(ever +1) from a first-step equation: x = 0.4 + 0.6 x^2, whose small root is 2/3.
    assert F(2, 5) + F(3, 5) * r**2 == r
    assert r / (1 - r) == 2
    rng = np.random.default_rng(6)
    runs = 20_000
    hits = high = 0
    for _ in range(runs):
        s = best = 0
        while s > -40:
            s += 1 if rng.random() < 0.4 else -1
            best = max(best, s)
        hits += best >= 10
        high += best
    assert abs(hits / runs - float(r**10)) < 0.005
    assert abs(high / runs - 2) < 0.07
    # From the other side: with an edge, the deepest loss below the start stays near 2 however long you trade,
    # while the maximum drawdown, measured from each new peak, keeps growing.
    means = []
    for steps, reps in ((1_000, 300), (10_000, 150), (100_000, 40)):
        moves = rng.choice([1, -1], (reps, steps), p=[0.6, 0.4])
        path = np.concatenate([np.zeros((reps, 1), dtype=np.int64), np.cumsum(moves, axis=1)], axis=1)
        below = -path.min(axis=1)
        drawdown = (np.maximum.accumulate(path, axis=1) - path).max(axis=1)
        means.append((below.mean(), drawdown.mean()))
        assert abs(below.mean() - 2) < 0.8
    assert means[0][1] + 3 < means[1][1] and means[1][1] + 3 < means[2][1]


def test_q7():
    assert sum(2**k for k in range(10)) == 1023
    lose = F(1, 2**10)
    assert (1 - lose) * 1 + lose * (-1023) == 0
    bets = sum(F(k, 2**k) for k in range(1, 11)) + 10 * lose
    assert bets == 2 - F(2, 2**10)
    assert round(float(bets), 3) == 1.998
    rng = np.random.default_rng(7)
    wins = rng.random((1_000_000, 10)) < 0.5
    first = wins.argmax(axis=1)
    alive = wins.any(axis=1)
    profit = np.where(alive, 1, -1023)
    assert abs(alive.mean() - (1 - float(lose))) < 0.001
    assert abs(profit.mean()) < 0.1
    assert abs(np.where(alive, first + 1, 10).mean() - float(bets)) < 0.003


def test_q8():
    # P(T > 2n) = u_2n: a path that has not reached +1 by time 2n, by reflection.
    n = 20
    prob = {0: F(1)}
    for _ in range(2 * n):
        new = {}
        for s, p in prob.items():
            if s - 1 <= 0:
                new[s - 1] = new.get(s - 1, 0) + p / 2
            if s + 1 <= 0:
                new[s + 1] = new.get(s + 1, 0) + p / 2
        prob = new
    assert sum(prob.values()) == F(C(40, 20), 2**40)
    u100 = C(100, 50) / 2**100
    assert round(1 - u100, 2) == 0.92
    assert 1 - C(2, 1) / 4 == 0.5  # T = 1 with probability one half, so the median is 1
    # The mean diverges: the tail decays like 1/sqrt(pi n), and the truncated mean keeps growing.
    truncated = [sum(C(2 * k, k) / 4**k for k in range(0, m)) for m in (50, 200, 800)]
    assert truncated[1] > 1.9 * truncated[0] and truncated[2] > 1.9 * truncated[1]
    # At any fixed horizon the stopped game is fair.
    rng = np.random.default_rng(8)
    s = np.cumsum(rng.choice((-1, 1), (300_000, 200)), axis=1)
    reached = (s >= 1).any(axis=1)
    final = np.where(reached, 1, s[:, -1])
    assert abs(final.mean()) < 0.1
    assert final[~reached].mean() < -10


def test_q9():
    def moves(s):
        return ((1, 1.0),) if s == 0 else ((s + 1, 0.5), (s - 1, 0.5))

    time = solve_chain(list(range(10)), moves)
    assert abs(time[0] - 100) < 1e-9
    assert abs(time[4] - 84) < 1e-9
    assert 10**2 - 4**2 == 84
    rng = np.random.default_rng(9)
    total = 0
    for _ in range(5_000):
        s = t = 0
        while s < 10:
            s = 1 if s == 0 else s + (1 if rng.random() < 0.5 else -1)
            t += 1
        total += t
    assert abs(total / 5_000 - 100) < 3


def test_q10():
    def moves(s):
        return ((s + 1, 0.5), (s - 1, 0.3), (s, 0.2))

    states = list(range(-4, 5))
    top = solve_chain(states, moves, lambda t: t == 5)
    time = solve_chain(states, moves)
    assert round(top[0], 4) == 0.9279
    assert abs(top[0] - 1 / (1 + 0.6**5)) < 1e-9
    assert round(time[0], 1) == 21.4
    assert abs(time[0] - (5 * top[0] - 5 * (1 - top[0])) / 0.2) < 1e-9
    assert round(5 * top[0] - 5 * (1 - top[0]), 3) == 4.279
    # Removing the lazy steps leaves the same exit probabilities with p = 5/8.
    assert abs(top[0] - solve_chain(states, walk(5 / 8), lambda t: t == 5)[0]) < 1e-9


def test_q11():
    r = 9 / 11
    p = (1 - r**10) / (1 - r**30)
    assert round(p, 4) == 0.8677
    states = list(range(-9, 20))
    top = solve_chain(states, walk(0.55), lambda t: t == 20)
    time = solve_chain(states, walk(0.55))
    assert abs(top[0] - p) < 1e-9
    profit = 30 * p - 10
    assert round(profit, 2) == 16.03
    assert round(time[0], 1) == 160.3
    assert abs(time[0] - profit / 0.1) < 1e-9
    assert F(10, 30) == F(1, 3)
    fair = F(1, 3) * 20 + F(2, 3) * (-10)
    assert fair == 0
    assert F(1, 3) * 0 == 0
    assert 10 * 20 == 200
    a, t = sim_exit(np.random.default_rng(11), 0.55, 0, -10, 20, 8_000)
    assert abs(a - p) < 0.012 and abs(t - time[0]) < 4
    # The fair walk from a linear system, against the product of the two distances.
    fair = solve_chain(states, walk(0.5))[0]
    assert abs(fair - 200) < 1e-8


def test_q12():
    r = 9 / 11
    assert f"{r**100:.1e}" == "1.9e-09"
    assert round(r**10, 3) == 0.134
    assert round(r**2, 3) == 0.669
    # The formula from a simulated ruin against a far-off ceiling.
    rng = np.random.default_rng(12)
    runs = 5_000
    ruined = 0
    for _ in range(runs):
        s = 10
        while 0 < s < 60:
            s += 1 if rng.random() < 0.55 else -1
        ruined += s == 0
    assert abs(ruined / runs - r**10) < 0.015
    # A fair coin is ruined for certain, whatever the stake.
    assert (0.45 / 0.45) ** 100 == 1


def test_q13():
    u = lambda n: F(C(n, n // 2), 2**n)  # noqa: E731
    assert F(1, 2) * u(20) == F(C(20, 10), 2**21)
    assert round(float(F(1, 2) * u(20)), 4) == 0.0881
    assert round(float(u(20)), 3) == 0.176
    # First returns: f_2n = u_2n / (2n - 1).
    assert u(2) == F(1, 2) and u(4) / 3 == F(1, 8) and u(6) / 5 == F(1, 16)
    # Enumerate.
    import itertools

    def first_return(n):
        total = 0
        for p in itertools.product((1, -1), repeat=n):
            s = list(itertools.accumulate(p))
            total += s[-1] == 0 and all(v != 0 for v in s[:-1])
        return F(total, 2**n)

    assert first_return(2) == F(1, 2) and first_return(4) == F(1, 8) and first_return(6) == F(1, 16)
    positive = sum(all(v > 0 for v in itertools.accumulate(p)) for p in itertools.product((1, -1), repeat=12))
    assert F(positive, 2**12) == F(1, 2) * u(12)


def test_q14():
    assert F(1, 3) / F(8, 9) == F(3, 8)
    # Odds run 1/2, 1, 2, 4, 8. Chance the walk in log2 odds reaches +3 from -1, with the news reliable or not.
    rng = np.random.default_rng(14)
    # News doubles the odds with probability a if true and b if false, with a / b = 2 and (1-a)/(1-b) = 1/2.
    a, b = 2 / 3, 1 / 3
    reached = 0
    runs = 40_000
    for _ in range(runs):
        true = rng.random() < 1 / 3
        k = -1
        while -14 < k < 3:
            up = rng.random() < (a if true else b)
            k += 1 if up else -1
        reached += k == 3
    assert abs(reached / runs - 3 / 8) < 0.008
    # A belief at one half with a target of one: certain only half the time.
    assert F(1, 2) / 1 == F(1, 2)


def test_q15():
    # Distance in steps of 2 on a ring of six, with a lazy walk.
    def moves(d):
        return (((d + 1) % 6, 0.25), ((d - 1) % 6, 0.25), (d, 0.5))

    time = solve_chain([1, 2, 3, 4, 5], moves)
    assert abs(time[2] - 16) < 1e-9
    assert 2 * (6 - 2) * 2 == 16
    rng = np.random.default_rng(15)
    total = 0
    for _ in range(20_000):
        a, b, t = 0, 4, 0
        while a != b:
            a = (a + (1 if rng.random() < 0.5 else -1)) % 12
            b = (b + (1 if rng.random() < 0.5 else -1)) % 12
            t += 1
        total += t
    assert abs(total / 20_000 - 16) < 0.3


def test_q16():
    u = [F(C(2 * k, k), 4**k) for k in range(11)]
    last = [u[k] * u[10 - k] for k in range(11)]
    assert sum(last) == 1
    assert last[0] == last[10] == u[10]
    assert round(float(u[10]), 3) == 0.176
    assert round(float(last[5]), 3) == 0.061
    assert max(last) == last[0] == last[10] and min(last) == last[5]
    assert abs(2 / math.pi * math.asin(math.sqrt(0.25)) - 1 / 3) < 1e-12
    assert abs(1 - 2 / math.pi * math.asin(math.sqrt(0.75)) - 1 / 3) < 1e-12
    rng = np.random.default_rng(16)
    s = np.cumsum(rng.choice((-1, 1), (400_000, 20)), axis=1)
    zeros = s == 0
    pos = 20 - np.argmax(zeros[:, ::-1], axis=1)
    pos[~zeros.any(axis=1)] = 0
    assert abs((pos == 0).mean() - float(last[0])) < 0.002
    assert abs((pos == 10).mean() - float(last[5])) < 0.002
    # Longer run for the limit: the last zero in the first quarter of 2,000 steps.
    s = np.cumsum(rng.integers(0, 2, (6_000, 2000), dtype=np.int16) * 2 - 1, axis=1, dtype=np.int16)
    zeros = s == 0
    pos = 2000 - np.argmax(zeros[:, ::-1], axis=1)
    pos[~zeros.any(axis=1)] = 0
    assert abs((pos <= 500).mean() - 1 / 3) < 0.02


def three_players(a, b, c):
    """Mean time until someone is at zero, and until one holds everything, solved exactly."""
    n = a + b + c
    states = [(i, j, n - i - j) for i in range(n + 1) for j in range(n + 1 - i)]
    interior = [s for s in states if min(s) > 0]

    def moves3(s):
        out = []
        for x in range(3):
            for y in range(3):
                if x != y:
                    t = list(s)
                    t[x] -= 1
                    t[y] += 1
                    out.append((tuple(t), 1 / 6))
        return out

    first = solve_chain(interior, moves3)

    def moves_all(s):
        alive = [k for k in range(3) if s[k] > 0]
        pairs = [(x, y) for x in alive for y in alive if x != y]
        out = []
        for x, y in pairs:
            t = list(s)
            t[x] -= 1
            t[y] += 1
            out.append((tuple(t), 1 / len(pairs)))
        return out

    live = [s for s in states if sum(v > 0 for v in s) >= 2]
    full = solve_chain(live, moves_all)
    return first[(a, b, c)], full[(a, b, c)]


def test_q17():
    first, full = three_players(2, 3, 4)
    assert abs(first - 3 * 2 * 3 * 4 / 9) < 1e-9
    assert abs(full - (2 * 3 + 3 * 4 + 2 * 4)) < 1e-9
    first, full = three_players(1, 2, 3)
    assert abs(first - 3) < 1e-9 and abs(full - 11) < 1e-9
    assert F(3 * 10 * 20 * 30, 60) == 300
    assert 10 * 20 + 20 * 30 + 10 * 30 == 1100
    rng = np.random.default_rng(17)
    runs, total = 1_500, 0
    pairs = [(x, y) for x in range(3) for y in range(3) if x != y]
    for _ in range(runs):
        s = [10, 20, 30]
        t = 0
        while min(s) > 0:
            x, y = pairs[rng.integers(6)]
            s[x] -= 1
            s[y] += 1
            t += 1
        total += t
    assert abs(total / runs - 300) < 16


def test_q18():
    # The fraction is a martingale, exactly.
    for r, b in ((1, 1), (3, 2), (7, 11)):
        f = F(r, r + b)
        assert f * F(r + 1, r + b + 1) + (1 - f) * F(r, r + b + 1) == f
    assert F(1, 2) / F(3, 4) == F(2, 3)
    assert 1 - F(3, 4) == F(1, 4)
    # The first two draws red already reach 3/4, so 1/3 is a floor.
    assert F(1, 2) * F(2, 3) == F(1, 3)
    # Dynamic programme on the urn's states, to 4,000 balls.
    limit = 4000
    p = np.zeros(limit + 3)
    p[1] = 1.0
    hit = 0.0
    index = np.arange(limit + 3)
    for tot in range(2, limit):
        f = index / tot
        reach = f >= 0.75
        hit += p[reach].sum()
        p = np.where(reach, 0.0, p)
        new = p * (1 - f)
        new[1:] += (p * f)[:-1]
        p = new
    assert round(hit, 2) == 0.44
    rng = np.random.default_rng(18)
    runs = 30_000
    count = 0
    for _ in range(runs):
        r, b = 1, 1
        while r + b < 500:
            if rng.random() < r / (r + b):
                r += 1
            else:
                b += 1
            if r >= 3 * b:
                count += 1
                break
    assert abs(count / runs - hit) < 0.01


def test_q19():
    n = 100

    def tail(a, m=n):
        return F(sum(C(m, k) for k in range(m + 1) if 2 * k - m >= a)
                 + sum(C(m, k) for k in range(m + 1) if 2 * k - m > a), 2**m)

    mean = sum(tail(a) for a in range(1, n + 1))
    assert round(float(mean), 2) == 7.50
    assert round(math.sqrt(2 * n / math.pi), 2) == 7.98
    assert round(math.sqrt(2 * n / math.pi) - 0.5, 2) == 7.48
    # Enumerate a short walk to test the reflection itself.
    import itertools

    m = 14
    brute = F(sum(max(0, *itertools.accumulate(p)) for p in itertools.product((1, -1), repeat=m)), 2**m)
    assert brute == sum(tail(a, m) for a in range(1, m + 1))
    rng = np.random.default_rng(19)
    s = np.cumsum(rng.integers(0, 2, (300_000, n), dtype=np.int16) * 2 - 1, axis=1, dtype=np.int16)
    assert abs(np.maximum(s.max(axis=1), 0).mean() - float(mean)) < 0.03


def test_q20():
    mu, var = 0.2, 0.96
    assert abs(1 - mu**2 - var) < 1e-12
    v = 10 * var / mu**3
    assert round(v) == 1200
    assert round(math.sqrt(v), 1) == 34.6
    rng = np.random.default_rng(20)
    runs = 20_000
    times = np.zeros(runs)
    for i in range(runs):
        s = t = 0
        while s < 10:
            s += 1 if rng.random() < 0.6 else -1
            t += 1
        times[i] = t
    assert abs(times.mean() - 50) < 0.8
    assert abs(times.var() - 1200) < 60
    # Doubling the distance doubles the mean and the variance; a stronger drift shrinks both.
    assert round(20 * var / mu**3) == 2400


def test_q21():
    # Exact: return probabilities by convolution in two dimensions match the square of 1-d.
    u = [C(2 * n, n) / 4**n for n in range(12)]
    for n in range(1, 12):
        two = sum(math.factorial(2 * n) / (math.factorial(k) ** 2 * math.factorial(n - k) ** 2) for k in range(n + 1))
        assert abs(two / 16**n - u[n] ** 2) < 1e-12
    # The sums: one and two dimensions diverge, three converges.
    m = 200_000
    u1 = np.ones(m)
    for n in range(1, m):
        u1[n] = u1[n - 1] * (2 * n - 1) / (2 * n)
    assert u1[:1000].sum() > 30
    assert (u1[1:] ** 2).sum() > 3
    # Three dimensions, by a midpoint grid of the Fourier form 1 / (1 - average of cosines).
    k = 200
    t = (np.arange(k) + 0.5) * 2 * np.pi / k
    c = np.cos(t)
    grid = c[:, None, None] + c[None, :, None] + c[None, None, :]
    total = (1 / (1 - grid / 3)).mean()
    assert abs(total - 1.516) < 0.005
    assert round(1 - 1 / total, 2) == 0.34
    # Four dimensions, with a coarser grid.
    k = 48
    t = (np.arange(k) + 0.5) * 2 * np.pi / k
    c = np.cos(t)
    grid = c[:, None, None, None] + c[None, :, None, None] + c[None, None, :, None] + c[None, None, None, :]
    assert round(1 - 1 / (1 / (1 - grid / 4)).mean(), 2) == 0.19
    rng = np.random.default_rng(21)
    runs = 6_000
    back = 0
    for _ in range(runs):
        pos = [0, 0, 0]
        for _ in range(2000):
            d = rng.integers(3)
            pos[d] += 1 if rng.random() < 0.5 else -1
            if pos == [0, 0, 0]:
                back += 1
                break
    assert abs(back / runs - 0.34) < 0.03


def test_q22():
    lo, hi = -5, 10
    states = list(range(lo + 1, hi))

    def moves(s):
        return ((s + 2, 1 / 3), (s - 1, 2 / 3))

    top10 = solve_chain(states, moves, lambda t: t == 10)[0]
    top11 = solve_chain(states, moves, lambda t: t == 11)[0]
    time = solve_chain(states, moves)[0]
    assert round(top10 + top11, 3) == 0.326
    assert round(top10, 3) == 0.218 and round(top11, 3) == 0.108
    assert round(time, 1) == 25.9
    # Optional stopping: the mean of the final value is 0, the mean of its square is 2 * E[T].
    assert abs(10 * top10 + 11 * top11 - 5 * (1 - top10 - top11)) < 1e-9
    assert abs(100 * top10 + 121 * top11 + 25 * (1 - top10 - top11) - 2 * time) < 1e-9
    assert F(5, 15) == F(1, 3) and F(5 * 10, 2) == 25
    assert abs(15 * top10 + 16 * top11 - 5) < 1e-9
    assert abs((1 / 3 - top10 - top11) / (top10 + top11) - 0.02) < 0.005
    rng = np.random.default_rng(22)
    runs, ups, total = 30_000, 0, 0
    for _ in range(runs):
        s = t = 0
        while lo < s < hi:
            s += 2 if rng.random() < 1 / 3 else -1
            t += 1
        ups += s >= hi
        total += t
    assert abs(ups / runs - (top10 + top11)) < 0.008
    assert abs(total / runs - time) < 0.4
    # A fair walk with unit steps: chance 1/3 and 50 steps. The 25 is this walk's variance with no overshoot.
    unit = list(range(-4, 10))
    assert abs(solve_chain(unit, walk(0.5), lambda t: t == 10)[0] - 1 / 3) < 1e-9
    assert abs(solve_chain(unit, walk(0.5))[0] - 50) < 1e-9


def test_q23():
    def var(n):
        states = list(range(-n + 1, n))
        t = solve_chain(states, walk(0.5))
        idx = {s: i for i, s in enumerate(states)}
        a = np.eye(len(states))
        b = np.zeros(len(states))
        for s in states:
            i = idx[s]
            b[i] = 1
            for x in (s + 1, s - 1):
                if x in idx:
                    a[i, idx[x]] -= 0.5
                    b[i] += 2 * 0.5 * t[x]
        second = np.linalg.solve(a, b)[idx[0]]
        return second - t[0] ** 2

    for n in (1, 2, 3, 5, 10):
        assert abs(var(n) - F(2, 3) * n**2 * (n**2 - 1)) < 1e-6
    assert F(2, 3) * 100 * 99 == 6600
    assert round(math.sqrt(6600), 1) == 81.2
    assert var(1) < 1e-9  # one step, no variance
    rng = np.random.default_rng(23)
    times = np.zeros(8_000)
    for i in range(8_000):
        s = t = 0
        while abs(s) < 10:
            s += 1 if rng.random() < 0.5 else -1
            t += 1
        times[i] = t
    assert abs(times.mean() - 100) < 3
    assert abs(times.var() - 6600) < 600
    # The martingale itself: S^4 - 6 t S^2 + 3 t^2 + 2 t is fair over one step.
    for s, t in ((3, 5), (0, 7), (-2, 11)):
        now = s**4 - 6 * t * s**2 + 3 * t**2 + 2 * t
        up = (s + 1) ** 4 - 6 * (t + 1) * (s + 1) ** 2 + 3 * (t + 1) ** 2 + 2 * (t + 1)
        down = (s - 1) ** 4 - 6 * (t + 1) * (s - 1) ** 2 + 3 * (t + 1) ** 2 + 2 * (t + 1)
        assert (up + down) / 2 == now


def test_q24():
    for k in (1, 2, 5, 100):
        assert F(1, 2) * F(1, k) * (2 * k) == 1
    # On a finite ring the same quantity is exactly one, by the uniform stationary law.
    size = 40
    for k in (1, 7, 19):
        def moves(s, size=size):
            return (((s + 1) % size, 0.5), ((s - 1) % size, 0.5))

        states = [s for s in range(size) if s != 0]
        # Expected visits to k from each state, before hitting 0.
        idx = {s: i for i, s in enumerate(states)}
        a = np.eye(len(states))
        b = np.zeros(len(states))
        for s in states:
            for t, p in moves(s):
                if t in idx:
                    a[idx[s], idx[t]] -= p
            b[idx[s]] = 1.0 if s == k else 0.0
        v = np.linalg.solve(a, b)
        assert abs(0.5 * v[idx[1]] + 0.5 * v[idx[size - 1]] - 1) < 1e-9

    # Simulation on the line: long excursions make it slow, so cap and count only the mean to the cap.
    rng = np.random.default_rng(24)
    k, runs, total = 3, 200_000, 0
    for _ in range(runs):
        s = 1 if rng.random() < 0.5 else -1
        steps = 0
        while s != 0 and steps < 5000:
            total += s == k
            s += 1 if rng.random() < 0.5 else -1
            steps += 1
    assert abs(total / runs - 1) < 0.05


def test_q25():
    timid = (1.5**25 - 1) / (1.5**100 - 1)
    assert f"{timid:.1e}" == "6.2e-14"
    # Bold play: 25 -> 50 -> 100.
    assert F(2, 5) ** 2 == F(4, 25)
    assert float(F(4, 25)) == 0.16
    # Value iteration over every stake rule on whole dollars confirms bold play is best.
    def best(p, n=100, sweeps=150):
        v = np.zeros(n + 1)
        v[n] = 1.0
        for _ in range(sweeps):
            for x in range(1, n):
                stakes = np.arange(1, min(x, n - x) + 1)
                v[x] = (p * v[x + stakes] + (1 - p) * v[x - stakes]).max()
        return v

    v = best(0.4)
    assert abs(v[25] - 0.16) < 1e-9
    assert abs(v[50] - 0.4) < 1e-9
    # At a fair bet every plan gives one quarter.
    assert abs(best(0.5)[25] - 0.25) < 1e-9
    assert (1 - 25 / 100) == 0.75
    # At a good bet, small stakes win.
    r = 2 / 3
    favourable = (1 - r**25) / (1 - r**100)
    assert round(favourable, 5) == 0.99996
    assert F(3, 5) ** 2 == F(9, 25)
    assert abs(best(0.6, sweeps=2000)[25] - favourable) < 1e-5
    rng = np.random.default_rng(25)
    n = 1_000_000
    assert abs(((rng.random(n) < 0.4) & (rng.random(n) < 0.4)).mean() - 0.16) < 0.001
