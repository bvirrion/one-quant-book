"""Every number printed in the answers of "Timed Test 1": exact value, then a seeded simulation."""
import math
from fractions import Fraction as F
from itertools import product

import numpy as np
import scipy.stats as st

NONNUMERIC = {}


def test_q1():
    # Strings of length n with no two adjacent heads: a Fibonacci recurrence.
    a, b = 2, 3
    for _ in range(8):
        a, b = b, a + b
    assert b == 144
    assert sum("HH" not in "".join(s) for s in product("HT", repeat=10)) == 144
    assert F(144, 1024) == F(9, 64)
    assert round(float(F(9, 64)), 3) == 0.141
    flips = np.random.default_rng(1).integers(0, 2, (400_000, 10))
    hit = ((flips[:, 1:] & flips[:, :-1]).sum(axis=1) == 0).mean()
    assert abs(hit - 9 / 64) < 0.002


def test_q2():
    # y: the mover wins, previous flip heads. x: the mover wins, otherwise.
    y = F(2, 3)
    assert y == F(1, 2) + F(1, 2) * (1 - y)
    x = F(4, 9)
    assert x == F(1, 2) * (1 - y) + F(1, 2) * (1 - x)
    rng = np.random.default_rng(2)
    first = 0
    reps = 200_000
    for _ in range(reps):
        prev, turn = 0, 0
        while True:
            c = rng.random() < 0.5  # True is heads
            if prev and not c:
                first += turn == 0
                break
            prev, turn = c, 1 - turn
    assert abs(first / reps - 4 / 9) < 0.004


def test_q3():
    def worst(eggs, floors):
        best = [[0] * (floors + 1) for _ in range(eggs + 1)]
        for f in range(1, floors + 1):
            best[1][f] = f
        for e in range(2, eggs + 1):
            for f in range(1, floors + 1):
                best[e][f] = 1 + min(max(best[e - 1][k - 1], best[e][f - k]) for k in range(1, f + 1))
        return best[eggs][floors]

    assert worst(2, 100) == 14
    assert worst(3, 100) == 9
    assert 10 + 9 == 19  # equal steps of 10: ten first-egg drops, then nine more
    assert 13 * 14 // 2 == 91 and 14 * 15 // 2 == 105
    # The plan: drop from 14, 27, 39, ...
    floors, step, now = [], 14, 0
    while now + step <= 100 and step > 0:
        now += step
        floors.append(now)
        step -= 1
    assert floors[:3] == [14, 27, 39]
    assert floors == [14, 27, 39, 50, 60, 69, 77, 84, 90, 95, 99]
    # Check the plan on every possible highest safe floor: at most 14 drops, and always the right answer.
    worst_seen = 0
    for safe in range(0, 101):
        drops, low, top = 0, 0, 101
        for f in floors + [100]:
            drops += 1
            if f > safe:
                top = f
                break
            low = f
        found = low
        for f in range(low + 1, top):
            drops += 1
            if f > safe:
                break
            found = f
        assert found == safe
        worst_seen = max(worst_seen, drops)
    assert worst_seen == 14


def test_q4():
    assert F(3, 4) ** 2 - F(1, 2) ** 2 == F(5, 16)
    u = np.random.default_rng(4).random((2, 2_000_000))
    d = np.abs(u[0] - u[1])
    assert abs(((d > 0.25) & (d < 0.5)).mean() - 5 / 16) < 0.001


def test_q5():
    z = 1 / math.sqrt(12)
    assert round(z, 2) == 0.29
    assert round(st.norm.cdf(-z), 3) == 0.386
    assert round(0.5 - 0.29 * 0.4, 3) == 0.384
    # A monthly Sharpe of 1/sqrt(12) annualises to 1: mean 12 z over standard deviation sqrt(12).
    assert abs(12 * z / math.sqrt(12) - 1) < 1e-12
    r = np.random.default_rng(5).normal(z, 1, 2_000_000)
    assert abs((r < 0).mean() - st.norm.cdf(-z)) < 0.001


def test_q6():
    m = 0.75 * np.eye(5) + 0.25 * np.ones((5, 5))
    w = np.linalg.eigvalsh(m)
    assert np.allclose(w, [0.75, 0.75, 0.75, 0.75, 2.0])
    assert abs(np.linalg.det(m) - 81 / 128) < 1e-12
    assert F(3, 4) ** 4 * 2 == F(81, 128)
    assert round(81 / 128, 3) == 0.633
    # Lowest common off-diagonal entry for a correlation matrix of size 5.
    assert np.linalg.eigvalsh(1.25 * np.eye(5) - 0.25 * np.ones((5, 5))).min() > -1e-12
    assert np.linalg.eigvalsh(1.26 * np.eye(5) - 0.26 * np.ones((5, 5))).min() < 0


def test_q7():
    # Exact chain on the number of hits after each shot, from 1 hit in 2 shots.
    dist = {1: F(1)}
    for shots in range(2, 100):
        new = {}
        for h, p in dist.items():
            new[h + 1] = new.get(h + 1, 0) + p * F(h, shots)
            new[h] = new.get(h, 0) + p * (1 - F(h, shots))
        dist = new
    assert set(dist) == set(range(1, 100))
    assert all(v == F(1, 99) for v in dist.values())
    rng = np.random.default_rng(7)
    reps = 200_000
    h = np.ones(reps)
    for shots in range(2, 100):
        h += rng.random(reps) < h / shots
    assert abs((h == 50).mean() - 1 / 99) < 0.001
    assert abs(h.mean() - 50) < 0.2


def test_q8():
    # P(L > x) = 3(1-x)^2 - 3(1-2x)^2 + (1-3x)^2, each squared term counted while its base is positive.
    assert 1 - F(1, 2) + F(1, 9) == F(11, 18)
    assert F(1, 3) * (1 + F(1, 2) + F(1, 3)) == F(11, 18)
    assert round(11 / 18, 3) == 0.611
    cuts = np.sort(np.random.default_rng(8).random((2, 2_000_000)), axis=0)
    pieces = np.stack([cuts[0], cuts[1] - cuts[0], 1 - cuts[1]])
    assert abs(pieces.max(axis=0).mean() - 11 / 18) < 0.0005
    assert abs(pieces.min(axis=0).mean() - 1 / 9) < 0.0005
    # With n pieces the mean of the longest is H_n / n: check n = 4.
    four = np.diff(np.sort(np.random.default_rng(88).random((3, 1_000_000)), axis=0), axis=0, prepend=0, append=1)
    assert abs(four.max(axis=0).mean() - float(sum(F(1, k) for k in range(1, 5)) / 4)) < 0.0005
    for x in (0.2, 0.4, 0.7):
        exact = 3 * (1 - x) ** 2 - 3 * max(0, 1 - 2 * x) ** 2 + max(0, 1 - 3 * x) ** 2
        assert abs((pieces.max(axis=0) > x).mean() - exact) < 0.001


def test_q9():
    assert 3**6 == 729 and 3**7 == 2187
    assert 2**9 < 1000 <= 2**10
    # The count of distinguishable bottles with s strips and two rounds, adaptive or not.
    for s in range(1, 9):
        total = sum(math.comb(s, k) * 2 ** (s - k) for k in range(s + 1))
        assert total == 3**s

    # The ternary plan works for 1000 bottles and 7 strips: every bottle gets a distinct outcome.
    def digits(b, s=7):
        return [(b // 3**i) % 3 for i in range(s)]

    seen = set()
    for bottle in range(1000):
        d = digits(bottle)
        # Digit 0: first round. Digit 1: second round. Digit 2: never.
        first = tuple(i for i in range(7) if d[i] == 0)
        second = tuple(i for i in range(7) if d[i] == 1)
        seen.add((first, second))
    assert len(seen) == 1000


def test_q10():
    p, q, r = F(3, 10), F(7, 10), 3
    # Chain on the number of umbrellas where you are. States 0..r.
    m = np.zeros((r + 1, r + 1))
    m[0, r] = 1.0
    for i in range(1, r + 1):
        m[i, r - i] = float(q)
        m[i, r - i + 1] = float(p)
    vals, vecs = np.linalg.eig(m.T)
    pi = np.real(vecs[:, np.argmin(np.abs(vals - 1))])
    pi = pi / pi.sum()
    assert abs(pi[0] - float(q / (r + q))) < 1e-12
    for i in range(1, r + 1):
        assert abs(pi[i] - float(1 / (r + q))) < 1e-12
    wet = p * q / (r + q)
    assert wet == F(21, 370)
    assert p * F(1, 4) == F(75, 1000)  # the uniform guess
    assert round(float(wet), 4) == 0.0568
    assert round(float(q / (r + q)), 3) == 0.189
    rng = np.random.default_rng(10)
    here, wetc, trips = 3, 0, 1_000_000
    rain = rng.random(trips) < 0.3
    for t in range(trips):
        if rain[t]:
            if here == 0:
                wetc += 1
                here = 3
            else:
                here = 3 - here + 1
        else:
            here = 3 - here
    assert abs(wetc / trips - float(wet)) < 0.001


def test_q11():
    a, b = F(1, 3), F(2, 3)
    # Duel values for A, with A shooting first and second.
    duel_first = a / (1 - (1 - a) * (1 - b))
    assert duel_first == F(3, 7)
    duel_second = (1 - b) * duel_first
    assert duel_second == F(1, 7)
    # All three alive, A fires in the air.
    air = b * duel_first + (1 - b) * a
    assert air == F(25, 63)
    # Alternatives for A, with the others' replies below.
    aim_c = a * duel_second + (1 - a) * air
    aim_b = a * 0 + (1 - a) * air
    assert aim_c == F(59, 189) and aim_b == F(50, 189)
    assert air > aim_c > aim_b
    assert round(float(air), 3) == 0.397
    # B's choice: aiming at C gives survival 8/21, the rest gives 0 because C then kills B.
    assert b * (1 - duel_first) == F(8, 21)
    # C's choice when B has missed: shooting B leaves C to face A's single shot, 2/3. Shooting A leaves B's shot, 1/3.
    assert 1 - a == F(2, 3) and 1 - b == F(1, 3)
    # Others' total: A + B + C survivals sum to 1 under this play.
    c_wins = (1 - b) * (1 - a)
    assert air + b * (1 - duel_first) + c_wins == 1
    assert c_wins == F(2, 9)

    rng = np.random.default_rng(11)
    wins = 0
    reps = 300_000
    for _ in range(reps):
        # A in the air. B fires at C.
        if rng.random() < 2 / 3:
            while True:  # duel, A first
                if rng.random() < 1 / 3:
                    wins += 1
                    break
                if rng.random() < 2 / 3:
                    break
        else:  # C kills B, A fires once at C, and if that misses C kills A
            wins += rng.random() < 1 / 3
    assert abs(wins / reps - 25 / 63) < 0.003


def test_q12():
    z_a, z_b = 1.96, 0.84
    assert round(st.norm.ppf(0.975), 2) == z_a and round(st.norm.ppf(0.8), 2) == z_b
    n = ((z_a * 0.5 + z_b * math.sqrt(0.24)) / 0.1) ** 2
    assert round(n) == 194
    assert round(math.sqrt(0.24), 2) == 0.49
    assert round(z_a * 0.5, 2) == 0.98 and round(z_b * 0.49, 2) == 0.41
    assert round((0.98 + 0.41) ** 2 * 100) == 193
    # The one-sided test, and the usual shortcut of using 0.5 for both standard deviations.
    assert round(((1.645 * 0.5 + z_b * math.sqrt(0.24)) / 0.1) ** 2) == 152
    assert round(((z_a + z_b) * 0.5 / 0.1) ** 2) == 196

    # Exact binomial power, using the two-sided normal cut-off rule.
    def power(m):
        half = z_a * 0.5 * math.sqrt(m)
        lo, hi = m / 2 - half, m / 2 + half
        return st.binom.sf(math.floor(hi), m, 0.6) + st.binom.cdf(math.ceil(lo) - 1, m, 0.6)

    assert 0.77 < power(194) < 0.83
    assert power(100) < 0.6
    assert power(400) > 0.97

    def level(m):
        half = z_a * 0.5 * math.sqrt(m)
        lo, hi = m / 2 - half, m / 2 + half
        return st.binom.sf(math.floor(hi), m, 0.5) + st.binom.cdf(math.ceil(lo) - 1, m, 0.5)

    assert 0.03 < level(194) < 0.07
    assert round(power(194), 2) == 0.81
    heads = np.random.default_rng(12).binomial(194, 0.6, 500_000)
    half = z_a * 0.5 * math.sqrt(194)
    assert abs((np.abs(heads - 97) > half).mean() - power(194)) < 0.002
