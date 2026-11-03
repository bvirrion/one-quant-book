"""Every number printed in the answers of "Waiting Times and Markov Chains": exact value, then a seeded simulation."""
import itertools
import math
from fractions import Fraction as F

import numpy as np
import sympy as sp

NONNUMERIC = {}
HALF = sp.Rational(1, 2)


def race(patterns, p=HALF, alphabet=None):
    """Exact (expected end time, win probabilities) when coin or die patterns race; solves the prefix automaton."""
    alphabet = alphabet or {"H": p, "T": 1 - p}
    prefixes = {""}
    for s in patterns:
        for i in range(len(s) + 1):
            prefixes.add(s[:i])
    prefixes = sorted(prefixes, key=lambda s: (len(s), s))

    def step(state, c):
        t = state + c
        if t in patterns:
            return t
        while t not in prefixes:
            t = t[1:]
        return t

    idx = {s: i for i, s in enumerate(s for s in prefixes if s not in patterns)}
    n = len(idx)
    a, rhs = sp.zeros(n, n), {s: sp.zeros(n, 1) for s in patterns}
    for s, i in idx.items():
        a[i, i] += 1
        for c, q in alphabet.items():
            t = step(s, c)
            if t in patterns:
                rhs[t][i] += q
            else:
                a[i, idx[t]] -= q
    time = a.LUsolve(sp.ones(n, 1))[idx[""]]
    return time, {s: a.LUsolve(rhs[s])[idx[""]] for s in patterns}


def simulate_race(rng, patterns, runs, letters="HT"):
    wins, total = dict.fromkeys(patterns, 0), 0
    for _ in range(runs):
        hist = ""
        while True:
            hist = (hist + letters[int(rng.integers(len(letters)))])[-8:]
            total += 1
            hit = [p for p in patterns if hist.endswith(p)]
            if hit:
                wins[hit[0]] += 1
                break
    return {k: v / runs for k, v in wins.items()}, total / runs


def lead(x, y):
    """Conway's leading number: sum of 2^(k-1) over k with the last k letters of x equal to the first k of y."""
    return sum(2 ** (k - 1) for k in range(1, min(len(x), len(y)) + 1) if x[-k:] == y[:k])


def self_time(s, size=2):
    """Expected wait from the overlaps of a pattern with itself."""
    return sum(size**k for k in range(1, len(s) + 1) if s[-k:] == s[:k])


def test_q1():
    assert race(["HH"])[0] == 6 and race(["HT"])[0] == 4
    # First-step equations printed in the answer.
    x, y = sp.symbols("x y")
    sol = sp.solve([x - (1 + x / 2 + y / 2), y - (1 + x / 2)], [x, y])
    assert sol[x] == 6 and sol[y] == 4
    rng = np.random.default_rng(1)
    assert abs(simulate_race(rng, ["HH"], 40_000)[1] - 6) < 0.1
    assert abs(simulate_race(rng, ["HT"], 40_000)[1] - 4) < 0.05
    # The follow-up: pairs of flips in blocks.


def test_q2():
    six = {str(d): sp.Rational(1, 6) for d in range(1, 7)}
    assert race(["66"], alphabet=six)[0] == 42
    assert race(["HHH"])[0] == 14
    for k in range(1, 6):
        assert race(["6" * k], alphabet=six)[0] == sp.Rational(6 * (6**k - 1), 5)
    assert 6 + 36 == 42
    assert (42 + 1) * 6 == 258 == race(["666"], alphabet=six)[0]
    assert 2 * 3 == 6 and (6 + 1) * 2 == 14
    rng = np.random.default_rng(2)
    assert abs(simulate_race(rng, ["66"], 10_000, "123456")[1] - 42) < 1.5


def test_q3():
    assert F(1, 6) / (1 - F(5, 6) ** 2) == F(6, 11)
    a, b = F(1, 6), F(1, 3)
    assert a / (1 - (1 - a) * (1 - b)) == F(3, 8)
    rng = np.random.default_rng(3)
    wins = np.sum(rng.geometric(1 / 6, 400_000) % 2 == 1) / 400_000
    assert abs(wins - 6 / 11) < 0.003
    you, opp = rng.geometric(1 / 6, 400_000), rng.geometric(1 / 3, 400_000)
    assert abs(np.mean(you <= opp) - 3 / 8) < 0.003


def test_q4():
    p, q = F(3, 5), F(2, 5)
    win = p**2 / (p**2 + q**2)
    assert win == F(9, 13) and round(float(win), 3) == 0.692
    length = 2 / (p**2 + q**2)
    assert length == F(50, 13) and round(float(length), 2) == 3.85
    rng = np.random.default_rng(4)
    wins, total = 0, 0
    for _ in range(100_000):
        lead_, t = 0, 0
        while abs(lead_) < 2:
            lead_ += 1 if rng.random() < 0.6 else -1
            t += 1
        wins += lead_ == 2
        total += t
    assert abs(wins / 100_000 - float(win)) < 0.005
    assert abs(total / 100_000 - float(length)) < 0.02


def test_q5():
    m = sp.Matrix([[sp.Rational(9, 10), sp.Rational(1, 10)], [sp.Rational(3, 10), sp.Rational(7, 10)]])
    pi = sp.Matrix([[sp.Rational(3, 4), sp.Rational(1, 4)]])
    assert pi * m == pi
    assert 1 / sp.Rational(3, 10) == sp.Rational(10, 3)
    assert 1 / sp.Rational(1, 10) == 10
    assert sorted(m.eigenvals()) == [sp.Rational(3, 5), 1]
    # Correlation at lag n is 0.6^n.
    for n in range(1, 5):
        mn = m**n
        p11 = pi[1] * mn[1, 1]
        cov = p11 - pi[1] ** 2
        assert cov / (pi[1] * pi[0]) == sp.Rational(3, 5) ** n
    # Half-life of the decay: little over one step.
    assert round(math.log(2) / -math.log(0.6), 2) == 1.36
    # Noisy copying.
    assert round(0.5 * (1 + 0.8**10), 3) == 0.554
    rng = np.random.default_rng(5)
    s, seq = 0, np.empty(400_000, dtype=int)
    u = rng.random(400_000)
    for i in range(400_000):
        s = (0 if u[i] < 0.9 else 1) if s == 0 else (1 if u[i] < 0.7 else 0)
        seq[i] = s
    assert abs(seq.mean() - 0.25) < 0.01
    assert abs(np.corrcoef(seq[:-2], seq[2:])[0, 1] - 0.36) < 0.02
    runs = np.diff(np.flatnonzero(np.diff(np.concatenate(([0], seq, [0])))))[::2]
    assert abs(runs.mean() - 10 / 3) < 0.1
    bits = rng.random((200_000, 10)) < 0.1
    assert abs((bits.sum(axis=1) % 2 == 0).mean() - 0.554) < 0.004


def test_q6():
    t, w = race(["HHT", "THH"])
    assert w["HHT"] == sp.Rational(1, 4) and w["THH"] == sp.Rational(3, 4)
    assert t == sp.Rational(13, 2)
    # Biased coin: HHT wins only by opening HH.
    p = sp.Rational(2, 3)
    assert race(["HHT", "THH"], p=p)[1]["HHT"] == p**2 == sp.Rational(4, 9)
    rng = np.random.default_rng(6)
    wins, mean_t = simulate_race(rng, ["HHT", "THH"], 60_000)
    assert abs(wins["HHT"] - 0.25) < 0.006 and abs(mean_t - 6.5) < 0.05


def test_q7():
    assert self_time("HTHTH") == 2 + 8 + 32 == 42 == race(["HTHTH"])[0]
    assert self_time("HHHTT") == 32 == race(["HHHTT"])[0]
    six = {str(d): sp.Rational(1, 6) for d in range(1, 7)}
    assert self_time("45", 6) == 36 == race(["45"], alphabet=six)[0]
    assert self_time("44", 6) == 42 == race(["44"], alphabet=six)[0]
    assert self_time("HTH") == 10 == race(["HTH"])[0]
    assert self_time("HHT") == 8 == race(["HHT"])[0]
    assert self_time("ABRACADABRA", 26) == 26**11 + 26**4 + 26
    rng = np.random.default_rng(7)
    assert abs(simulate_race(rng, ["HTHTH"], 6_000)[1] - 42) < 2
    assert abs(simulate_race(rng, ["HHHTT"], 6_000)[1] - 32) < 1.2


def cube_hit(d):
    """Expected steps to the opposite corner of a d-cube, by the distance chain."""
    e = {0: sp.Integer(0)}
    syms = sp.symbols(f"e1:{d + 1}")
    get = lambda k: 0 if k == 0 else syms[k - 1]  # noqa: E731
    eqs = []
    for k in range(1, d + 1):
        down = sp.Rational(k, d)
        up = 1 - down
        eqs.append(get(k) - 1 - down * get(k - 1) - (up * get(k + 1) if k < d else 0))
    sol = sp.solve(eqs, syms)
    e = {k: sol[syms[k - 1]] for k in range(1, d + 1)}
    return e[d]


def test_q8():
    assert cube_hit(3) == 10
    assert cube_hit(4) == sp.Rational(64, 3) and round(64 / 3, 2) == 21.33
    assert cube_hit(2) == 4
    # Equations in the answer: a = 1 + b, b = 1 + a/3 + 2c/3 with c = 1 + 2b/3.
    a, b, c = sp.symbols("a b c")
    s = sp.solve([a - 1 - b, b - 1 - a / 3 - 2 * c / 3, c - 1 - 2 * b / 3], [a, b, c])
    assert s == {a: 10, b: 9, c: 7}
    # Return time 8, time to a given adjacent corner 7, commute through resistance 5/6.
    assert 2 * 12 * sp.Rational(5, 6) == 20
    assert 2 * 12 * sp.Rational(7, 12) == 14
    rng = np.random.default_rng(8)

    def walk(target, start=0):
        v, t = start, 0
        while True:
            v ^= 1 << int(rng.integers(3))
            t += 1
            if v == target:
                return t

    assert abs(np.mean([walk(7) for _ in range(60_000)]) - 10) < 0.15
    assert abs(np.mean([walk(0) for _ in range(60_000)]) - 8) < 0.12
    assert abs(np.mean([walk(1) for _ in range(60_000)]) - 7) < 0.12


def test_q9():
    # Residues of the running sum, mod 6: uniform after every roll.
    r = {k: F(0) for k in range(6)}
    for d in range(1, 7):
        r[d % 6] += F(1, 6)
    assert all(v == F(1, 6) for v in r.values())
    x = sp.symbols("x0:6")
    eqs = [x[k] - 1 - sum(x[(k + d) % 6] for d in range(1, 7) if (k + d) % 6 != 0) / 6 for k in range(6)]
    assert sp.solve(eqs, x)[x[0]] == 6
    y = sp.symbols("y0:7")
    eqs = [y[k] - 1 - sum(y[(k + d) % 7] for d in range(1, 7) if (k + d) % 7 != 0) / 6 for k in range(7)]
    assert sp.solve(eqs, y)[y[0]] == 7
    rng = np.random.default_rng(9)
    u = rng.integers(1, 7, (200_000, 80)).cumsum(axis=1)
    t6 = (u % 6 == 0).argmax(axis=1) + 1
    t7 = (u % 7 == 0).argmax(axis=1) + 1
    assert abs(t6.mean() - 6) < 0.05 and abs(t7.mean() - 7) < 0.05


def reach(n, memo={}):  # noqa: B006
    if n <= 0:
        return F(0)
    if n not in memo:
        memo[n] = 1 + sum(reach(n - k) for k in range(1, 7)) / 6
    return memo[n]


def test_q10():
    assert round(float(reach(10)), 2) == 3.32
    assert reach(1) == 1 and reach(2) == F(7, 6) and reach(3) == F(49, 36)
    assert round(10 / 3.5, 2) == 2.86
    assert round((10 + 5 / 3) / 3.5, 2) == 3.33
    assert round(float(reach(100)), 2) == 29.05
    assert round((100 + 5 / 3) / 3.5, 2) == 29.05
    # Mean overshoot of the renewal limit.
    assert F(91, 6) / (2 * F(7, 2)) - F(1, 2) == F(5, 3)
    rng = np.random.default_rng(10)
    s = rng.integers(1, 7, (400_000, 12)).cumsum(axis=1)
    t = (s >= 10).argmax(axis=1) + 1
    assert abs(t.mean() - float(reach(10))) < 0.005
    # Wald: E[S_T] = 3.5 E[T].
    assert abs(s[np.arange(len(t)), t - 1].mean() - 3.5 * float(reach(10))) < 0.02


def test_q11():
    a, b = sp.symbols("a b")
    r = sp.Rational
    sol = sp.solve([a - r(1, 36) - b / 6 - r(29, 36) * a, b - r(1, 36) - r(29, 36) * a], [a, b])
    assert sol[a] == r(7, 13)
    assert r(1, 36) + r(1, 6) + r(29, 36) == 1
    rng = np.random.default_rng(11)
    wins = 0
    for _ in range(50_000):
        last = False
        while True:
            s = rng.integers(1, 7) + rng.integers(1, 7)
            if s == 12:
                wins += 1
                break
            if s == 7:
                if last:
                    break
                last = True
            else:
                last = False
    assert abs(wins / 50_000 - 7 / 13) < 0.007
    # The answer's step: multiply through by 216.
    assert sp.solve(42 * a - 7 - 29 * a, a)[0] == r(7, 13)


def test_q12():
    gaps = [(F(1, 2), 5), (F(1, 2), 15)]
    mean = sum(p * g for p, g in gaps)
    second = sum(p * g * g for p, g in gaps)
    assert second / (2 * mean) == F(25, 4) and float(second / (2 * mean)) == 6.25
    assert F(3, 4) * F(15, 2) + F(1, 4) * F(5, 2) == F(25, 4)
    assert F(15, 20) == F(3, 4)
    # Length-biased run length: E[L^2]/E[L] with L geometric(1/2).
    assert F(6) / F(2) == 3
    rng = np.random.default_rng(12)
    g = rng.choice([5, 15], 200_000)
    ends = g.cumsum()
    arrive = rng.random(100_000) * ends[-1]
    idx = np.searchsorted(ends, arrive)
    assert abs((ends[idx] - arrive).mean() - 6.25) < 0.05
    e = rng.exponential(10, 200_000)
    ends = e.cumsum()
    arrive = rng.random(100_000) * ends[-1]
    idx = np.searchsorted(ends, arrive)
    assert abs((ends[idx] - arrive).mean() - 10) < 0.15
    assert abs(e[idx].mean() - 20) < 0.3
    flips = rng.integers(0, 2, (200_000, 41))
    lengths = 1 + (flips[:, 21:] == flips[:, [20]]).cumprod(axis=1).sum(axis=1)
    lengths += (flips[:, :20] == flips[:, [20]])[:, ::-1].cumprod(axis=1).sum(axis=1)
    assert abs(lengths.mean() - 3) < 0.02


def test_q13():
    q = sp.symbols("q")
    roots = sp.solve(q - (sp.Rational(1, 4) + q / 4 + q**2 / 2), q)
    assert sorted(roots) == [sp.Rational(1, 2), 1]
    assert sp.Rational(1, 4) + 2 * sp.Rational(1, 2) == sp.Rational(5, 4)
    assert sp.Rational(1, 2) ** 3 == sp.Rational(1, 8)
    # Subcritical total progeny.
    assert F(1) / (1 - F(3, 4)) == 4
    rng = np.random.default_rng(13)
    dead = 0
    for _ in range(40_000):
        pop = 1
        for _ in range(300):
            if pop == 0 or pop > 60:
                break
            draws = rng.random(pop)
            pop = int((draws >= 0.25).sum() + (draws >= 0.5).sum())
        dead += pop == 0
    assert abs(dead / 40_000 - 0.5) < 0.01


def test_q14():
    u = [1.0]
    for n in range(1, 1020):
        u.append(sum(u[n - k] for k in range(1, 7) if n >= k) / 6)
    assert abs(u[1000] - 2 / 7) < 1e-10
    final = {k: sum(u[1000 + k - d] / 6 for d in range(k + 1, 7)) for k in range(6)}
    for k in range(6):
        assert abs(final[k] - (6 - k) / 21) < 1e-10
    assert sum(F(6 - k, 21) * k for k in range(6)) == F(5, 3)
    assert 1 / F(7, 2) == F(2, 7)
    assert round(2 / 7, 3) == 0.286
    assert F(2, 7) * F(1, 6) * 2 == F(2, 21)
    rng = np.random.default_rng(14)
    # Long enough to pass 1000 in every run, in short rows to save memory.
    finals, lasts = [], []
    for _ in range(4_000):
        s = rng.integers(1, 7, 420).cumsum()
        i = int(np.argmax(s >= 1000))
        finals.append(s[i])
        lasts.append(s[i] - (s[i - 1] if i else 0))
    finals, lasts = np.array(finals), np.array(lasts)
    assert abs((finals == 1000).mean() - 2 / 7) < 0.02
    assert abs((finals == 1005).mean() - 1 / 21) < 0.012
    assert abs((lasts == 2).mean() - 2 / 21) < 0.012
    assert abs((lasts == 6).mean() - 6 / 21) < 0.02


def test_q15():
    pats = ["".join(x) for x in itertools.product("HT", repeat=3)]
    best = {}
    for a in pats:
        best[a] = max((race([a, b])[1][b], b) for b in pats if b != a)
    assert best["HHH"] == (sp.Rational(7, 8), "THH")
    assert best["HHT"] == (sp.Rational(3, 4), "THH")
    assert best["HTH"] == (sp.Rational(2, 3), "HHT")
    assert best["HTT"] == (sp.Rational(2, 3), "HHT")
    assert best["TTT"] == (sp.Rational(7, 8), "HTT")
    assert best["TTH"] == (sp.Rational(3, 4), "HTT")
    assert best["THT"] == (sp.Rational(2, 3), "TTH")
    assert best["THH"] == (sp.Rational(2, 3), "TTH")
    assert min(v[0] for v in best.values()) == sp.Rational(2, 3)
    # Conway's odds for every pair.
    for a, b in itertools.permutations(pats, 2):
        p = race([a, b])[1][b]
        n, d = lead(a, a) - lead(a, b), lead(b, b) - lead(b, a)
        assert p == sp.Rational(n, n + d)
    # The numbers in the answer.
    a, b = "HTH", "HHT"
    assert (lead(a, a), lead(a, b), lead(b, b), lead(b, a)) == (5, 1, 4, 2)
    assert (5 - 1, 4 - 2) == (4, 2)
    # The cycle.
    for x, y in [("THH", "HHT"), ("HHT", "HTT"), ("HTT", "TTH"), ("TTH", "THH")]:
        assert race([x, y])[1][x] > sp.Rational(1, 2)
    rng = np.random.default_rng(15)
    assert abs(simulate_race(rng, ["HTH", "HHT"], 40_000)[0]["HHT"] - 2 / 3) < 0.01
    assert abs(simulate_race(rng, ["HHH", "THH"], 40_000)[0]["THH"] - 7 / 8) < 0.01


def clock_last(n):
    """Exact P(each vertex is visited last) on the n-cycle, from the arc of visited vertices."""
    # State: (left arm a, right arm b, at the right end?). With L = a + b edges in the arc, gambler's ruin from an end gives
    # the near new vertex w.p. (L+1)/(L+2) and the far one w.p. 1/(L+2).
    dist = {(0, 0, True): F(1)}
    last = {}
    for size in range(0, n - 2):
        new = {}
        for (a, b, right), p in dist.items():
            if a + b != size:
                new[(a, b, right)] = p
                continue
            near, far = F(size + 1, size + 2), F(1, size + 2)
            if right:
                moves = [((a, b + 1, True), near), ((a + 1, b, False), far)]
            else:
                moves = [((a + 1, b, False), near), ((a, b + 1, True), far)]
            for st, q in moves:
                new[st] = new.get(st, F(0)) + p * q
        dist = new
    for (a, b, _right), p in dist.items():
        assert a + b == n - 2
        last[(b + 1) % n] = last.get((b + 1) % n, F(0)) + p
    return last


def test_q16():
    last = clock_last(12)
    assert len(last) == 11 and all(v == F(1, 11) for v in last.values())
    assert sum(F(12, k) * F(k, 12) for k in range(1, 12)) == 11
    assert 6 * (12 - 6) == 36
    assert 12 * 11 // 2 == 66
    # The walk on j + 2 positions started next to an end takes 1 * j steps.
    assert sum(range(1, 12)) == 66
    rng = np.random.default_rng(16)
    counts = np.zeros(12)
    covers, hits = [], []
    for _ in range(20_000):
        pos, seen, t, t6 = 0, {0}, 0, None
        while len(seen) < 12:
            pos = (pos + (1 if rng.random() < 0.5 else -1)) % 12
            t += 1
            if pos == 6 and t6 is None:
                t6 = t
            if pos not in seen:
                seen.add(pos)
                lastv = pos
        counts[lastv] += 1
        covers.append(t)
        if t6 is not None:
            hits.append(t6)
    assert abs(counts[6] / 20_000 - 1 / 11) < 0.008
    assert counts[0] == 0
    assert abs(np.mean(covers) - 66) < 1


def knight_degrees():
    deg = {}
    moves = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
    for x, y in itertools.product(range(8), repeat=2):
        deg[(x, y)] = [(x + a, y + b) for a, b in moves if 0 <= x + a < 8 and 0 <= y + b < 8]
    return deg


def test_q17():
    nb = knight_degrees()
    total = sum(len(v) for v in nb.values())
    assert total == 336 == 8 * 7 * 6
    assert len(nb[(0, 0)]) == 2 and len(nb[(3, 3)]) == 8
    assert F(total, 2) == 168 and F(total, 8) == 42
    king = sum(
        sum(1 for a, b in itertools.product((-1, 0, 1), repeat=2) if (a or b) and 0 <= x + a < 8 and 0 <= y + b < 8)
        for x, y in itertools.product(range(8), repeat=2)
    )
    assert king == 420 and F(king, 3) == 140
    assert total // 2 == 168  # edges
    # Stationary check with the exact matrix.
    squares = sorted(nb)
    pos = {s: i for i, s in enumerate(squares)}
    m = np.zeros((64, 64))
    for s, ns in nb.items():
        for t in ns:
            m[pos[s], pos[t]] = 1 / len(ns)
    pi = np.array([len(nb[s]) / total for s in squares])
    assert np.allclose(pi @ m, pi)
    # Return time from the linear system on the other 63 squares.
    keep = [i for i in range(64) if i != pos[(0, 0)]]
    h = np.linalg.solve(np.eye(63) - m[np.ix_(keep, keep)], np.ones(63))
    assert abs(1 + m[pos[(0, 0)], keep] @ h - 168) < 1e-8
    rng = np.random.default_rng(17)
    cur, ret, returns = (0, 0), 0, []
    while len(returns) < 2_500:
        opts = nb[cur]
        cur = opts[int(rng.integers(len(opts)))]
        ret += 1
        if cur == (0, 0):
            returns.append(ret)
            ret = 0
    assert abs(np.mean(returns) - 168) < 12


def grid_values():
    nodes = [(i, j) for i in range(3) for j in range(3)]
    target = (2, 2)
    syms = {n: sp.Symbol(f"h{n[0]}{n[1]}") for n in nodes if n != target}
    get = lambda n: 0 if n == target else syms[n]  # noqa: E731

    def nbrs(n):
        return [(n[0] + a, n[1] + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= n[0] + a < 3 and 0 <= n[1] + b < 3]

    eqs = [get(n) - 1 - sum(get(m) for m in nbrs(n)) / len(nbrs(n)) for n in syms]
    sol = sp.solve(eqs, list(syms.values()))
    return {n: sol[syms[n]] for n in syms}, nbrs


def hit_time(src, dst, nbrs):
    nodes = [(i, j) for i in range(3) for j in range(3)]
    syms = {n: sp.Symbol(f"z{n[0]}{n[1]}") for n in nodes if n != dst}
    get = lambda n: 0 if n == dst else syms[n]  # noqa: E731
    eqs = [get(n) - 1 - sum(get(m) for m in nbrs(n)) / len(nbrs(n)) for n in syms]
    return sp.solve(eqs, list(syms.values()))[syms[src]]


def test_q18():
    vals, nbrs = grid_values()
    assert vals[(0, 0)] == 18
    # The values marked on the figure.
    assert vals[(0, 1)] == vals[(1, 0)] == 17
    assert vals[(1, 1)] == 15
    assert vals[(0, 2)] == vals[(2, 0)] == 15
    assert vals[(1, 2)] == vals[(2, 1)] == 11
    # The lumped equations printed in the answer.
    v, w, x, y, z = sp.symbols("s a m c b")
    sol = sp.solve([v - 1 - w, w - 1 - (v + x + y) / 3, x - 1 - (2 * w + 2 * z) / 4, y - 1 - (w + z) / 2, z - 1 - (x + y) / 3], [v, w, x, y, z])
    assert (sol[v], sol[w], sol[x], sol[y], sol[z]) == (18, 17, 15, 15, 11)
    # Commute time identity.
    assert 2 * 12 * sp.Rational(3, 2) == 36
    assert hit_time((1, 1), (0, 0), nbrs) == 15
    assert hit_time((0, 0), (1, 1), nbrs) == 6
    assert 2 * 12 * sp.Rational(7, 8) == 21
    rng = np.random.default_rng(18)

    def walk(src, dst):
        cur, t = src, 0
        while cur != dst:
            o = nbrs(cur)
            cur = o[int(rng.integers(len(o)))]
            t += 1
        return t

    assert abs(np.mean([walk((0, 0), (2, 2)) for _ in range(30_000)]) - 18) < 0.3
    assert abs(np.mean([walk((1, 1), (0, 0)) for _ in range(30_000)]) - 15) < 0.3
    assert abs(np.mean([walk((0, 0), (1, 1)) for _ in range(30_000)]) - 6) < 0.15


def second_moment(pattern):
    """Mean and variance of the wait for a coin pattern, from first-step equations on the prefix automaton."""
    prefixes = [pattern[:i] for i in range(len(pattern))]

    def step(s, c):
        t = s + c
        if t == pattern:
            return None
        while t not in prefixes:
            t = t[1:]
        return t

    n = len(prefixes)
    idx = {s: i for i, s in enumerate(prefixes)}
    a = sp.eye(n)
    for s, i in idx.items():
        for c in "HT":
            t = step(s, c)
            if t is not None:
                a[i, idx[t]] -= sp.Rational(1, 2)
    m = a.LUsolve(sp.ones(n, 1))
    b = sp.Matrix([1 + sum(sp.Rational(1, 2) * 2 * (m[idx[step(s, c)]] if step(s, c) is not None else 0) for c in "HT") for s in prefixes])
    s2 = a.LUsolve(b)
    return m[0], s2[0] - m[0] ** 2, s2[0]


def test_q19():
    assert second_moment("HH") == (6, 22, 58)
    assert second_moment("HT") == (4, 4, 20)
    assert second_moment("HHH")[:2] == (14, 142)
    a, b = sp.symbols("a b")
    s = sp.solve([a - 11 - a / 2 - b / 2, b - 7 - a / 2], [a, b])
    assert s == {a: 58, b: 36}
    assert a.subs(s) - 36 == 22
    assert round(math.sqrt(22), 1) == 4.7
    rng = np.random.default_rng(19)
    vals = []
    for _ in range(100_000):
        run, t = 0, 0
        while run < 2:
            run = run + 1 if rng.random() < 0.5 else 0
            t += 1
        vals.append(t)
    assert abs(np.var(vals) - 22) < 0.8
    assert abs(np.mean(vals) - 6) < 0.05


def test_q20():
    h = lambda n: sum(F(1, k) for k in range(1, n + 1))  # noqa: E731
    assert round(float(52 * h(52))) == 236
    assert 52 * h(51) + 1 == 52 * h(52)
    assert round(float(h(52)), 2) == 4.54
    rng = np.random.default_rng(20)
    # The stopping time on a full deck.
    n = 52
    times = []
    for _ in range(3_000):
        below, t = 0, 0
        while below < n - 1:
            t += 1
            if rng.random() < (below + 1) / n:
                below += 1
        times.append(t + 1)
    assert abs(np.mean(times) - float(52 * h(52))) < 4
    # On a 4-card deck the order at the stopping time is uniform over 24 orders (chi-square style check).
    counts = {}
    for _ in range(96_000):
        deck = [0, 1, 2, 3]
        bottom = 3
        while True:
            c = deck.pop(0)
            deck.insert(int(rng.integers(0, 4)), c)
            if c == bottom:
                break
        key = tuple(deck)
        counts[key] = counts.get(key, 0) + 1
    assert len(counts) == 24
    assert max(abs(v / 96_000 - 1 / 24) for v in counts.values()) < 0.005


def coin_time(n):
    e = {n: F(1)}
    for k in range(n - 1, 0, -1):
        e[k] = F(n, k) + F(n - k, k) * e[k + 1]
    return sum(e.values()), e


def test_q21():
    total, e = coin_time(10)
    assert total == F(74752, 63) and round(float(total), 1) == 1186.5
    assert 2**10 == 1024
    assert e[10] == 1
    assert e[1] == 10 + 9 * e[2]
    assert coin_time(3)[0] == 10
    # The lumped chain really is the 10-cube distance chain: check 4 coins against the cube solver.
    assert coin_time(4)[0] == F(64, 3)
    rng = np.random.default_rng(21)
    times, rets = [], []
    for _ in range(1_500):
        tails, t = 10, 0
        while tails:
            tails += -1 if rng.random() < tails / 10 else 1
            t += 1
        times.append(t)
    for _ in range(3_000):
        tails, t = 10, 0
        while True:
            tails += -1 if rng.random() < tails / 10 else 1
            t += 1
            if tails == 10:
                break
        rets.append(t)
    assert abs(np.mean(times) - float(total)) < 60
    assert abs(np.mean(rets) - 1024) < 80


def test_q22():
    pats = ["".join(x) for x in itertools.product("HT", repeat=4)]
    a = "HTHH"
    res = sorted(((race([a, b])[1][b], b) for b in pats if b != a), reverse=True)
    assert res[0] == (sp.Rational(9, 14), "THTH")
    assert res[1] == (sp.Rational(3, 5), "HHTH")
    # For every four-flip pattern, a best response is one letter followed by the pattern's first three.
    for x in pats:
        scored = {y: race([x, y])[1][y] for y in pats if y != x}
        top = max(scored.values())
        assert any(y[1:] == x[:3] for y, v in scored.items() if v == top)
    b = "THTH"
    assert (lead(a, a), lead(a, b), lead(b, b), lead(b, a)) == (9, 0, 10, 5)
    assert sp.Rational(9, 14) == sp.Rational(9 - 0, (9 - 0) + (10 - 5))
    t = race([a, b])[0]
    assert t == sp.Rational(90, 7) and round(90 / 7, 2) == 12.86
    assert sp.Rational(2 * (9 * 10 - 0 * 5), 9 + 10 - 0 - 5) == t
    assert self_time(a) == 18 and self_time(b) == 20
    # HHTH.
    assert (lead("HTHH", "HHTH"), lead("HHTH", "HHTH"), lead("HHTH", "HTHH")) == (3, 9, 5)
    assert sp.Rational(9 - 3, (9 - 3) + (9 - 5)) == sp.Rational(3, 5)
    rng = np.random.default_rng(22)
    wins, mean_t = simulate_race(rng, [a, b], 30_000)
    assert abs(wins[b] - 9 / 14) < 0.01 and abs(mean_t - 90 / 7) < 0.15
    # The three-flip recipe applied here: the opposite of the second letter of A, then its first three letters.
    recipe = {"H": "T", "T": "H"}[a[1]] + a[:3]
    assert recipe == "HHTH" and race([a, recipe])[1][recipe] < race([a, b])[1][b]


def distinct(k):
    e = {}
    for j in range(1, k):
        s, coef = F(0), F(0)
        for i in range(1, j + 1):
            coef += F(1, k)
            s += F(1, k) * sum(e[m] for m in range(i, j))
        e[j] = (1 + s) / (1 - coef)
    return 1 + sum(e.values()), e


def test_q23():
    total, e = distinct(6)
    assert total == F(416, 5) and float(total) == 83.2
    assert e == {1: F(6, 5), 2: F(9, 5), 3: F(18, 5), 4: F(54, 5), 5: F(324, 5)}
    # The compact recursion printed in the answer: e_j (6-j) = 6 + sum_{i<j} i e_i.
    for j in range(1, 6):
        assert e[j] * (6 - j) == 6 + sum(i * e[i] for i in range(1, j))
    assert distinct(3)[0] == 7
    assert distinct(2)[0] == 3
    # Exact check against a linear solve on the states 1..6.
    x = sp.symbols("x1:7")
    get = lambda j: 0 if j == 6 else x[j - 1]  # noqa: E731
    eqs = [get(j) - 1 - sp.Rational(6 - j, 6) * get(j + 1) - sum(get(i) for i in range(1, j + 1)) / 6 for j in range(1, 6)]
    sol = sp.solve(eqs, x[:5])
    assert 1 + sol[x[0]] == sp.Rational(416, 5)
    rng = np.random.default_rng(23)
    vals = []
    for _ in range(15_000):
        window, t = [], 0
        while len(window) < 6:
            r = int(rng.integers(6))
            t += 1
            if r in window:
                window = window[window.index(r) + 1 :]
            window.append(r)
        vals.append(t)
    assert abs(np.mean(vals) - 83.2) < 1.5


def test_q24():
    q = sp.symbols("q")
    assert sorted(sp.solve(q - sp.Rational(1, 3) - sp.Rational(2, 3) * q**2, q)) == [sp.Rational(1, 2), 1]
    d, s = F(1, 3) / F(1, 2), F(2, 3) * F(1, 2) ** 2 / F(1, 2)
    assert d == F(2, 3) and s == F(1, 3)
    mean = 2 * s
    assert mean == F(2, 3)
    assert 1 / (1 - mean) == 3
    # Series over total progeny 2k+1 with Catalan counts, conditional on extinction.
    num, den = 0.0, 0.0
    term = 1 / 3
    for k in range(0, 400):
        # term = C_k (1/3)^(k+1) (2/3)^k
        den += term
        num += (2 * k + 1) * term
        term *= (2 * (2 * k + 1) / (k + 2)) * (1 / 3) * (2 / 3)
    assert abs(den - 0.5) < 1e-9
    assert abs(num / den - 3) < 1e-9
    assert sp.Rational(1, 2) ** 3 == sp.Rational(1, 8)
    rng = np.random.default_rng(24)
    totals = []
    for _ in range(60_000):
        pop, total = 1, 1
        while 0 < pop < 80:
            draws = rng.random(pop)
            kids = 2 * int((draws < 2 / 3).sum())
            pop = kids
            total += kids
        if pop == 0:
            totals.append(total)
    assert abs(len(totals) / 60_000 - 0.5) < 0.008
    assert abs(np.mean(totals) - 3) < 0.15


def test_q25():
    s = sp.symbols("s")
    f = 1 / (2 - s)
    assert sp.simplify(1 / (1 - f) - (1 + 1 / (1 - s))) == 0
    p = F(0)
    for n in range(1, 21):
        p = 1 / (2 - p)
        assert p == F(n, n + 1)
    assert round(10 / 11, 3) == 0.909
    assert F(1, 10) * F(1, 11) == F(1, 110)
    # Given survival to generation n: mean n + 1 since E[X_n] = 1.
    assert 1 / (1 - F(10, 11)) == 11
    # Offspring mean is 1 and the distribution is geometric.
    assert abs(sum(k * 0.5 ** (k + 1) for k in range(200)) - 1) < 1e-12
    # P(extinction after generation n) = 1/(n+1): its tail sum, the mean extinction time, is the harmonic series.
    assert sum(F(1, n + 1) for n in range(0, 2001)) > 8
    rng = np.random.default_rng(25)
    alive, sizes = 0, []
    runs = 60_000
    for _ in range(runs):
        pop = 1
        for _ in range(10):
            if pop == 0:
                break
            pop = int(rng.negative_binomial(pop, 0.5))
        if pop:
            alive += 1
            sizes.append(pop)
    assert abs(1 - alive / runs - 10 / 11) < 0.005
    assert abs(np.mean(sizes) - 11) < 0.5
