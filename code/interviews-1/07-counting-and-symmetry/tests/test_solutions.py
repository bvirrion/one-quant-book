"""Every number printed in the answers of "Counting and Symmetry": a formula and an enumeration or a simulation."""
import itertools
import math
from fractions import Fraction as F

import numpy as np

C = math.comb
NONNUMERIC = {}


def test_q1():
    assert math.factorial(7) == 5040
    # Fix person 0 in chair 0; persons 0 and 1 must not be neighbours.
    good = 0
    for p in itertools.permutations(range(1, 8)):
        seats = (0, *p)
        where = seats.index(1)
        good += where not in (1, 7)
    assert good == 3600 == 5040 - 2 * math.factorial(6)
    # With three people everyone is next to everyone, so the same subtraction must give zero.
    assert math.factorial(2) - 2 * math.factorial(1) == 0


def test_q2():
    total = math.factorial(11) // (math.factorial(4) ** 2 * math.factorial(2))
    assert total == 34650
    others = math.factorial(7) // (math.factorial(4) * math.factorial(2))
    assert others == 105 and C(8, 4) == 70 and others * C(8, 4) == 7350
    # Enumerate S positions directly as a second route: choose non-adjacent places for S.
    good = sum(all(b - a > 1 for a, b in itertools.pairwise(s)) for s in itertools.combinations(range(11), 4))
    assert good == 70
    assert F(7350, 34650) == F(7, 33)


def test_q3():
    assert C(10, 5) == 252
    assert C(4, 2) * C(6, 3) == 120
    grid = [[0] * 6 for _ in range(6)]
    for x in range(6):
        for y in range(6):
            if (x, y) == (0, 0):
                grid[x][y] = 1
            elif (x, y) != (2, 2):
                grid[x][y] = (grid[x - 1][y] if x else 0) + (grid[x][y - 1] if y else 0)
    assert grid[5][5] == 132


def test_q4():
    assert C(13, 3) == 286 and C(9, 3) == 84
    assert sum(1 for t in itertools.product(range(11), repeat=4) if sum(t) == 10) == 286
    assert sum(1 for t in itertools.product(range(1, 11), repeat=4) if sum(t) == 10) == 84


def test_q5():
    assert C(11, 4) == 330 and C(6, 4) == 15 and 330 - 15 == 315
    people = list(range(11))  # 0..5 are men, 6..10 are women
    assert sum(any(x >= 6 for x in c) for c in itertools.combinations(people, 4)) == 315
    assert 5 * C(10, 3) == 600
    # The overcount: each committee is counted once per woman in it.
    assert sum(sum(x >= 6 for x in c) for c in itertools.combinations(people, 4)) == 600


def test_q6():
    outcomes = list(itertools.product(range(6), repeat=5))
    assert len({tuple(sorted(o)) for o in outcomes}) == 252 == C(10, 5)
    full = sum(sorted(np.bincount(o, minlength=6).tolist())[-2:] == [2, 3] for o in outcomes)
    assert full == 300 == 6 * 5 * C(5, 2)
    assert F(300, 7776) == F(25, 648)
    assert round(300 / 7776, 4) == 0.0386
    assert sum(len(set(o)) == 5 for o in outcomes) == 720
    assert sum(len(set(o)) == 1 for o in outcomes) == 6
    # A false answer: a uniform distribution over the 252 results.
    assert F(30, 252) != F(300, 7776)


def test_q7():
    arrangements = list(itertools.combinations(range(8), 3))  # places of the red balls
    assert F(sum(7 in a for a in arrangements), len(arrangements)) == F(3, 8)
    assert F(sum(1 in a for a in arrangements), len(arrangements)) == F(3, 8)


def test_q8():
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    total = 0
    for x, y, z in itertools.product(range(10), repeat=3):
        k = sum(v in (0, 9) for v in (x, y, z))
        counts[k] += 1
        total += k
    assert counts == {3: 8, 2: 96, 1: 384, 0: 512}
    assert total == 600
    assert F(total, 1000) == F(3, 5)
    assert 1000 - 8**3 == 488
    assert 6 * 10**2 == 600  # double counting from the outside


def test_q9():
    total = C(49, 6)
    assert total == 13_983_816
    exact = F(C(6, 3) * C(43, 3), total)
    assert C(6, 3) * C(43, 3) == 246_820
    assert round(float(exact), 4) == 0.0177
    at_least = sum(F(C(6, k) * C(43, 6 - k), total) for k in range(3, 7))
    assert round(float(at_least), 4) == 0.0186
    assert sum(F(C(6, k) * C(43, 6 - k), total) for k in range(7)) == 1
    assert round(total / (C(6, 3) * C(43, 3))) == 57 and round(float(1 / at_least)) == 54
    assert round(C(6, 3) * (6 / 49) ** 3 * (43 / 49) ** 3, 3) == 0.025  # the wrong binomial
    rng = np.random.default_rng(9)
    draws = rng.random((300_000, 49)).argsort(axis=1)[:, :6]
    hits = (draws < 6).sum(axis=1)
    assert abs((hits == 3).mean() - float(exact)) < 0.001
    assert abs((hits >= 3).mean() - float(at_least)) < 0.001


def test_q10():
    brute = sum(all(n % p for p in (2, 3, 5)) for n in range(1, 1001))
    assert brute == 266
    assert 1000 - 500 - 333 - 200 + 166 + 100 + 66 - 33 == 266
    # The density check: (1/2)(2/3)(4/5) = 4/15 of the numbers, which is about 266.7.
    assert F(1, 2) * F(2, 3) * F(4, 5) == F(4, 15)
    assert round(1000 * 4 / 15, 1) == 266.7
    assert sum(all(n % p for p in (2, 3, 5)) for n in range(1, 31)) == 8


def test_q11():
    assert 3**5 - 3 * 2**5 + 3 == 150
    assert sum(len(set(t)) == 3 for t in itertools.product(range(3), repeat=5)) == 150
    assert F(150, 243) == F(50, 81)
    assert round(50 / 81, 3) == 0.617
    # Too few balls: with two balls the formula must give zero.
    assert 3**2 - 3 * 2**2 + 3 == 0


def test_q12():
    perms = list(itertools.permutations(range(5)))
    fixed = [sum(p[i] == i for i in range(5)) for p in perms]
    assert fixed.count(0) == 44 and fixed.count(2) == 20 and fixed.count(1) == 45
    assert F(44, 120) == F(11, 30) and F(20, 120) == F(1, 6)
    assert sum((-1) ** k * C(5, k) * math.factorial(5 - k) for k in range(6)) == 44
    assert C(5, 2) * 2 == 20
    assert round(44 / 120, 3) == 0.367 and round(math.exp(-1), 3) == 0.368
    d = 1  # D_0
    for n in range(1, 21):
        d = n * d + (-1) ** n
    assert abs(d / math.factorial(20) - math.exp(-1)) < 1e-12
    assert abs(44 / 120 - math.exp(-1)) < 0.002
    # Four in the right place and one wrong is impossible.
    assert fixed.count(4) == 0


def test_q13():
    orders = []
    for places in itertools.combinations(range(10), 6):
        order = [-1] * 10
        for i in places:
            order[i] = 1
        orders.append(order)
    assert len(orders) == 210
    ahead = sum(all(s > 0 for s in itertools.accumulate(o)) for o in orders)
    assert ahead == 42
    assert F(ahead, 210) == F(1, 5) == F(6 - 4, 6 + 4)
    # The reflection count: 84 orders start with B; 84 bad orders start with A; 42 are left.
    assert C(9, 3) == 84 and C(9, 5) == 126 and 126 - 84 == 42
    # A tie leaves nothing: with equal votes, A cannot stay ahead at the end.
    assert F(5 - 5, 10) == 0
    # The follow-up, 60 votes against 40, by counting lattice paths that stay strictly ahead.
    ways = {(1, 0): 1}
    for a in range(1, 61):
        for b in range(41):
            if (a, b) != (1, 0) and a > b:
                ways[(a, b)] = ways.get((a - 1, b), 0) + ways.get((a, b - 1), 0)
    assert F(ways[(60, 40)], C(100, 40)) == F(1, 5)


def test_q14():
    def good(fives, tens):
        n = fives + tens
        ok = total = 0
        for places in itertools.combinations(range(n), fives):
            s = [-1] * n
            for i in places:
                s[i] = 1
            total += 1
            ok += all(v >= 0 for v in itertools.accumulate(s))
        return ok, total

    assert good(5, 5) == (42, 252)
    assert F(42, 252) == F(1, 6) == F(5 + 1 - 5, 5 + 1)
    assert good(6, 4) == (90, 210)
    assert F(90, 210) == F(3, 7) == F(6 + 1 - 4, 6 + 1)
    assert C(10, 5) - C(10, 4) == 42
    rng = np.random.default_rng(14)
    steps = np.tile(np.array([1] * 5 + [-1] * 5), (200_000, 1))
    rng.permuted(steps, axis=1, out=steps)
    assert abs((steps.cumsum(axis=1).min(axis=1) >= 0).mean() - 1 / 6) < 0.002


def test_q15():
    def p_more(n, p=F(1, 2)):
        pa = [C(n + 1, k) * p**k * (1 - p) ** (n + 1 - k) for k in range(n + 2)]
        pb = [C(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1)]
        return sum(pa[i] * pb[j] for i in range(n + 2) for j in range(n + 1) if i > j)

    assert p_more(10) == F(1, 2)
    # The symmetry needs a fair coin: a biased coin breaks it, so the answer is not a triviality of the count.
    assert p_more(10, F(7, 10)) > F(1, 2)
    assert p_more(10, F(3, 10)) < F(1, 2)
    rng = np.random.default_rng(15)
    a, b = rng.binomial(11, 0.5, 1_000_000), rng.binomial(10, 0.5, 1_000_000)
    assert abs((a > b).mean() - 0.5) < 0.002


def test_q16():
    # A small deck, exact: 2 aces, 4 others. Each named card should be next with chance 1/6.
    labels = ["A1", "A2", "x", "y", "z", "w"]
    next_a2 = next_x = 0
    for p in itertools.permutations(labels):
        i = min(p.index("A1"), p.index("A2"))
        if i < 5:
            next_a2 += p[i + 1] == "A2"
            next_x += p[i + 1] == "x"
    assert F(next_a2, 720) == F(1, 6) == F(next_x, 720)
    rng = np.random.default_rng(16)
    # Cards 0..3 are the aces, 0 is the ace of spades; card 4 is the two of clubs.
    deck = rng.random((200_000, 52)).argsort(axis=1)
    first = (deck < 4).argmax(axis=1)
    rows = np.flatnonzero(first < 51)
    nxt = deck[rows, first[rows] + 1]
    assert abs((nxt == 0).sum() / 200_000 - 1 / 52) < 0.001
    assert abs((nxt == 4).sum() / 200_000 - 1 / 52) < 0.001


def test_q17():
    exact = F(39 * 26 * 13, 51 * 50 * 49)
    assert exact == F(math.factorial(4) * C(48, 12) * C(36, 12) * C(24, 12), C(52, 13) * C(39, 13) * C(26, 13))
    assert round(float(exact), 3) == 0.105
    rng = np.random.default_rng(17)
    deck = rng.random((300_000, 52)).argsort(axis=1)
    hand = (deck[:, :4] // 13)  # where each of the four aces lies; positions are uniform
    all_differ = np.array([len(set(row)) == 4 for row in hand[:100_000]])
    assert abs(all_differ.mean() - float(exact)) < 0.004


def test_q18():
    sums = [sum(t) for t in itertools.product(range(1, 7), repeat=3)]
    assert sums.count(10) == 27 and sums.count(11) == 27
    assert sum(sum(t) == 14 for t in itertools.product(range(1, 7), repeat=4)) == 146
    assert C(13, 3) - 4 * C(7, 3) == 146
    assert C(13, 3) == 286 and 4 * C(7, 3) == 140


def test_q19():
    assert math.factorial(12) // (math.factorial(4) ** 3 * math.factorial(3)) == 5775
    assert C(11, 3) * C(7, 3) == 5775  # person 1's group, then person 5's
    together = C(10, 2) * C(7, 3)
    assert together == 1575
    assert F(together, 5775) == F(3, 11)
    rng = np.random.default_rng(19)
    p = rng.random((300_000, 12)).argsort(axis=1)
    same = (np.argmax(p == 0, axis=1) // 4) == (np.argmax(p == 1, axis=1) // 4)
    assert abs(same.mean() - 3 / 11) < 0.003


def test_q20():
    assert C(64, 2) == 2016
    assert F(63, 2016) == F(1, 32) == F(2, 64)
    assert F(32, 63) == F(32, 64 - 1)
    # With two players, they must meet. With four, 3 matches over 6 pairs.
    assert F(1, C(2, 2)) == F(2, 2)
    assert F(3, C(4, 2)) == F(2, 4)
    rng = np.random.default_rng(20)
    met = reach = 0
    runs = 20_000
    for _ in range(runs):
        field = rng.permutation(64)
        seen = False
        best = field.copy()
        while len(field) > 1:
            a, b = field[::2], field[1::2]
            if any({int(x), int(y)} == {0, 1} for x, y in zip(a, b, strict=True)):
                seen = True
            field = np.where(rng.random(len(a)) < 0.5, a, b)
        met += seen
        reach += (np.argmax(best == 0) < 32) != (np.argmax(best == 1) < 32)  # opposite halves of the draw
    assert abs(met / runs - 1 / 32) < 0.004
    assert abs(reach / runs - 32 / 63) < 0.012


def regions(n):
    return 1 + C(n, 2) + C(n, 4)


def test_q21():
    assert [regions(n) for n in (1, 2, 3, 4, 5, 6)] == [1, 2, 4, 8, 16, 31]
    assert regions(10) == 256
    assert C(10, 2) == 45 and C(10, 4) == 210
    # Euler's formula as a second route: V - E + F = 1 (not counting the outer face).
    for n in (4, 5, 6, 10):
        v = n + C(n, 4)
        e = n + C(n, 2) + 2 * C(n, 4)  # arcs, plus chords cut at each crossing
        assert e - v + 1 == regions(n)


def test_q22():
    ways = [1] + [0] * 100
    for coin in (1, 5, 10, 25, 50):
        for amount in range(coin, 101):
            ways[amount] += ways[amount - coin]
    assert ways[100] == 292
    brute = sum(
        1
        for h in range(3)
        for q in range((100 - 50 * h) // 25 + 1)
        for d in range((100 - 50 * h - 25 * q) // 10 + 1)
        for n in range((100 - 50 * h - 25 * q - 10 * d) // 5 + 1)
    )
    assert brute == 292
    assert sum(21 - 2 * d for d in range(11)) == 121


def test_q23():
    assert sum(1 for x in range(16) for y in range(16) if 0 <= 30 - x - y <= 15) == 136
    assert C(32, 2) == 496 and C(16, 2) == 120 and 496 - 3 * 120 == 136


def test_q24():
    assert F(1, C(8, 4)) == F(1, 70)
    assert F(math.factorial(4) ** 3, math.factorial(12)) == F(1, 34650)
    rng = np.random.default_rng(24)
    p = rng.random((400_000, 52)).argsort(axis=1)
    aces = p[:, :4].max(axis=1)
    kings = p[:, 4:8].min(axis=1)
    assert abs((aces < kings).mean() - 1 / 70) < 0.0008
    # With one ace and one king the same argument gives an even chance.
    assert F(1, C(2, 1)) == F(1, 2)


def test_q25():
    assert sum(C(10, k) ** 2 for k in range(11)) == C(20, 10) == 184_756
    assert 4**10 == 1_048_576
    assert round(184_756 / 4**10, 3) == 0.176
    rng = np.random.default_rng(25)
    a, b = rng.binomial(10, 0.5, 1_000_000), rng.binomial(10, 0.5, 1_000_000)
    assert abs((a == b).mean() - 184_756 / 4**10) < 0.002
    # The normal estimate, 1/sqrt(pi n), is near; the wrong one is 1/11.
    assert round(1 / math.sqrt(math.pi * 10), 3) == 0.178


def test_q26():
    for n in (1, 2, 3, 4):
        subsets = list(itertools.product((0, 1), repeat=n))
        pairs = list(itertools.product(subsets, repeat=2))
        contained = sum(all(x <= y for x, y in zip(a, b, strict=True)) for a, b in pairs)
        disjoint = sum(all(x * y == 0 for x, y in zip(a, b, strict=True)) for a, b in pairs)
        assert contained == disjoint == 3**n
        assert sum(a == b for a, b in pairs) == 2**n
    assert round(0.75**10, 3) == 0.056
    assert F(1, 2) ** 10 == F(1, 1024)


def test_q27():
    def no_adj(c, wrap=False, n=20):
        ok = all(b - a > 1 for a, b in itertools.pairwise(c))
        return ok and not (wrap and c[0] == 0 and c[-1] == n - 1)

    assert C(18, 3) == 816 == sum(no_adj(c) for c in itertools.combinations(range(20), 3))
    assert F(20, 17) * C(17, 3) == 800 == sum(no_adj(c, True) for c in itertools.combinations(range(20), 3))
    assert C(17, 3) == 680 and C(16, 2) == 120 and 680 + 120 == 800
    assert 816 - 800 == 16 == C(16, 1)


def test_q28():
    def formula(n):
        return sum((-1) ** k * C(n, k) * 2**k * math.factorial(2 * n - k) for k in range(n + 1))

    assert formula(5) == 1_263_360
    assert [C(5, k) * 2**k * math.factorial(10 - k) for k in range(6)] == [
        3_628_800, 3_628_800, 1_612_800, 403_200, 57_600, 3840]
    assert round(1_263_360 / 3_628_800, 3) == 0.348
    assert round(0.8**5, 3) == 0.328 and F(5 * 2, 10) == 1
    for n in (2, 3, 4):
        seats = list(range(2 * n))
        brute = sum(
            all(abs(p.index(2 * i) - p.index(2 * i + 1)) != 1 for i in range(n)) for p in itertools.permutations(seats)
        )
        assert brute == formula(n)
    assert formula(2) == 8 and formula(3) == 240
    rng = np.random.default_rng(28)
    p = rng.random((200_000, 10)).argsort(axis=1)
    apart = np.ones(200_000, bool)
    for i in range(5):
        apart &= np.abs(p[:, 2 * i] - p[:, 2 * i + 1]) != 1
    assert abs(apart.mean() - 0.348) < 0.003


def test_q29():
    n = sum(sum(c) % 5 == 0 for r in range(11) for c in itertools.combinations(range(1, 11), r))
    assert n == 208 == (1024 + 4 * 4) // 5
    w = np.exp(2j * np.pi / 5)
    product = np.prod([1 + w**k for k in range(1, 11)])
    assert abs(product - 4) < 1e-9
    assert abs(np.prod([1 + w**k for k in range(1, 5)]) - 1) < 1e-9
    # Filter for a fifth root of unity: all five values agree with the enumeration.
    filtered = sum(np.prod([1 + w ** (j * k) for k in range(1, 11)]) for j in range(5)) / 5
    assert abs(filtered - 208) < 1e-9
    # The other residues share the rest evenly.
    counts = [0] * 5
    for r in range(11):
        for c in itertools.combinations(range(1, 11), r):
            counts[sum(c) % 5] += 1
    assert counts == [208, 204, 204, 204, 204]
    five = sum(sum(c) % 5 == 0 for r in range(6) for c in itertools.combinations(range(1, 6), r))
    assert five == 8 == (32 + 4 * 2) // 5


def rings():
    all_rings = [c for c in itertools.product((0, 1), repeat=6) if sum(c) == 3]
    assert len(all_rings) == 20

    def rots(r):
        return {r[i:] + r[:i] for i in range(6)}

    neck = {min(rots(r)) for r in all_rings}
    brace = {min(min(rots(r)), min(rots(r[::-1]))) for r in all_rings}
    return len(neck), len(brace)


def test_q30():
    assert rings() == (4, 3)
    assert F(20 + 2 + 2, 6) == 4
    # Burnside with flips: 3 reflections through opposite beads fix 4 each; 3 through gaps fix none.
    assert F(20 + 2 + 2 + 3 * 4 + 3 * 0, 12) == 3


def cube_rotations():
    # Faces 0,1 top/bottom; 2,3 front/back; 4,5 left/right. Generated by two quarter turns.
    a = (0, 1, 4, 5, 3, 2)
    b = (2, 3, 1, 0, 4, 5)
    group = {tuple(range(6))}
    frontier = list(group)
    while frontier:
        g = frontier.pop()
        for h in (a, b):
            c = tuple(g[h[i]] for i in range(6))
            if c not in group:
                group.add(c)
                frontier.append(c)
    return group


def test_q31():
    group = cube_rotations()
    assert len(group) == 24

    def orbits(k):
        return len({min(tuple(c[g[i]] for i in range(6)) for g in group) for c in itertools.product(range(k), repeat=6)})

    assert orbits(2) == 10
    assert orbits(3) == 57
    for k, want in ((2, 10), (3, 57)):
        assert F(k**6 + 3 * k**4 + 12 * k**3 + 8 * k**2, 24) == want
    # Cycle structure of the group: 1 + 3 + 6 + 8 + 6.
    cycles = {}
    for g in group:
        seen, n = set(), 0
        for i in range(6):
            if i not in seen:
                n += 1
                j = i
                while j not in seen:
                    seen.add(j)
                    j = g[j]
        cycles[n] = cycles.get(n, 0) + 1
    assert cycles == {6: 1, 4: 3, 3: 12, 2: 8}
    assert math.factorial(6) // 24 == 30
    # One colour: exactly one cube.
    assert orbits(1) == 1


def test_q32():
    tris = list(itertools.combinations(range(12), 3))
    assert len(tris) == 220
    right = contains = 0
    for a, b, c in tris:
        gaps = (b - a, c - b, 12 - c + a)
        right += max(gaps) == 6
        contains += max(gaps) < 6
    assert right == 60 == 6 * 10
    assert contains == 40
    assert F(60, 220) == F(3, 11) and F(40, 220) == F(2, 11)
    assert 220 - 60 - 120 == 40 and 12 * C(5, 2) == 120
    assert F(40, 220) < F(1, 4)  # the continuous limit of the same question is 1/4
    # As the polygon gets finer the fraction rises toward 1/4: 240 corners.
    n = 240
    inside = F(C(n, 3) - n * C(n // 2 - 1, 2) - n // 2 * (n - 2), C(n, 3))
    assert abs(float(inside) - 0.25) < 0.01


def test_q33():
    assert sum(range(91, 101)) == 955
    assert 2**10 - 1 == 1023 > 955
    rng = np.random.default_rng(33)
    for _ in range(200):
        nums = [int(x) for x in rng.choice(np.arange(1, 101), 10, replace=False)]
        seen = {}
        found = False
        for r in range(1, 11):
            for c in itertools.combinations(nums, r):
                s = sum(c)
                if s in seen and not set(seen[s]) & set(c):
                    found = True
                    break
                seen.setdefault(s, c)
            if found:
                break
        assert found
    # Seven powers of two have all subset sums different.
    powers = [1, 2, 4, 8, 16, 32, 64]
    sums = [sum(c) for r in range(1, 8) for c in itertools.combinations(powers, r)]
    assert len(sums) == len(set(sums)) == 127
    assert sum(range(94, 101)) == 679 and 2**7 - 1 == 127 < 679
    # Removing common elements from two equal-sum groups leaves two disjoint ones of equal sum.
    a, b = {3, 7, 12}, {3, 19}
    assert sum(a) == 22 == sum(b) and sum(a - b) == sum(b - a)


def test_q34():
    paths = list(itertools.product((1, -1), repeat=10))
    hit = sum(max(itertools.accumulate(p)) >= 4 for p in paths)
    assert hit == 232
    # S_10 >= 4 means 7 or more up steps; S_10 > 4 means 8 or more.
    above = sum(C(10, k) for k in range(7, 11))
    beyond = sum(C(10, k) for k in range(8, 11))
    assert above == 176 and beyond == 56 and above + beyond == 232
    assert F(232, 1024) == F(29, 128)
    assert round(29 / 128, 3) == 0.227
    assert C(10, 7) == 120
    # A level beyond the number of steps is out of reach.
    assert sum(max(itertools.accumulate(p)) >= 11 for p in paths) == 0
    assert 2 * above == 352 != hit  # doubling S >= 4 double-counts the paths ending exactly on 4


def test_q35():
    brute = [0] * 28
    for t in itertools.product(range(10), repeat=3):
        brute[sum(t)] += 1
    assert sum(x * x for x in brute) == 55_252
    assert C(32, 5) == 201_376 and C(22, 5) == 26_334 and C(12, 5) == 792
    assert C(32, 5) - 6 * C(22, 5) + 15 * C(12, 5) == 55_252
    assert brute[27] == 1 and brute[13] == 75
    assert round(1e6 / 28) == 35_714 and round(1e6 / 55_252) == 18


def test_q36():
    def count(n):
        total = 0
        for cells in itertools.product((0, 1), repeat=n * n):
            rows = [cells[i * n : (i + 1) * n] for i in range(n)]
            total += all(sum(r) % 2 == 0 for r in rows) and all(sum(c) % 2 == 0 for c in zip(*rows, strict=True))
        return total

    assert count(2) == 2 and count(3) == 16 and count(4) == 2**9
    assert 2**16 == 65_536


def test_q37():
    for n, want in ((3, 4), (4, 11), (5, 26), (6, 57)):
        c = sum(sum(a < b for a, b in itertools.pairwise(p)) == 1 for p in itertools.permutations(range(n)))
        assert c == want == 2**n - n - 1


def test_q38():
    target = [0] * 13
    for a, b in itertools.product(range(1, 7), repeat=2):
        target[a + b] += 1

    def poly(die):
        out = [0] * (max(die) + 1)
        for f in die:
            out[f] += 1
        return out

    def times(a, b):
        out = [0] * (len(a) + len(b) - 1)
        for i, x in enumerate(a):
            for j, y in enumerate(b):
                out[i + j] += x * y
        return out

    found = []
    dice = [(1, *d) for d in itertools.combinations_with_replacement(range(1, 12), 5)]
    polys = {d: tuple(poly(d)) for d in dice}
    sums = {}
    for d in dice:
        sums.setdefault(sum(d), []).append(d)
    for d in dice:
        for e in sums.get(42 - sum(d), []):
            if d <= e:
                prod = times(polys[d], polys[e])
                if len(prod) == 13 and prod == target:
                    found.append((d, e))
    assert sorted(found) == [((1, 2, 2, 3, 3, 4), (1, 3, 4, 5, 6, 8)), ((1, 2, 3, 4, 5, 6), (1, 2, 3, 4, 5, 6))]
    assert sum((1, 2, 2, 3, 3, 4)) + sum((1, 3, 4, 5, 6, 8)) == 42
    # The printed factorisation: x(1+x)(1+x+x^2)(1-x+x^2) is the plain die.
    plain = times(times(times([0, 1], [1, 1]), [1, 1, 1]), [1, -1, 1])
    assert plain == poly((1, 2, 3, 4, 5, 6))
    assert times(times([0, 1], [1, 1]), [1, 1, 1]) == poly((1, 2, 2, 3, 3, 4))
    assert times(plain, [1, -1, 1]) == poly((1, 3, 4, 5, 6, 8))


def menage(n):
    return sum(
        (-1) ** k * F(2 * n, 2 * n - k) * C(2 * n - k, k) * math.factorial(n - k) for k in range(n + 1)
    )


def test_q39():
    count = 0
    # Fix man 0; men in even chairs, women in odd chairs; woman i is partner of man i.
    for men in itertools.permutations(range(1, 5)):
        order = (0, *men)
        for women in itertools.permutations(range(5)):
            count += all(women[i] != order[i] and women[i] != order[(i + 1) % 5] for i in range(5))
    assert count == 312 == math.factorial(4) * 13
    assert menage(5) == 13 and menage(6) == 80
    assert F(13, 120) == F(312, math.factorial(4) * math.factorial(5))
    assert round(13 / 120, 3) == 0.108
    assert round(0.6**5, 3) == 0.078 and round(math.exp(-2), 3) == 0.135
    # A check that the condition can fail: the same count with no restriction is the whole space.
    assert math.factorial(4) * math.factorial(5) == 2880


def test_q40():
    success = 1 - sum(F(1, k) for k in range(51, 101))
    assert round(float(success), 4) == 0.3118
    assert round(1 - math.log(2), 3) == 0.307
    rng = np.random.default_rng(40)
    wins, sim = 0, 20_000
    for _ in range(sim):
        box = rng.permutation(100)
        seen = np.zeros(100, bool)
        worst = 0
        for s in range(100):
            if not seen[s]:
                length, j = 0, s
                while not seen[j]:
                    seen[j] = True
                    j = box[j]
                    length += 1
                worst = max(worst, length)
        wins += worst <= 50
    assert abs(wins / sim - float(success)) < 0.012
    # With 100 boxes each they always succeed; with 1 each, only the identity works.
    assert 1 - sum(F(1, k) for k in range(101, 101)) == 1
    # With 2 prisoners and 1 box: 1/2, as enumeration confirms.
    assert 1 - sum(F(1, k) for k in range(2, 3)) == F(1, 2)
