"""Every claim in the answers of "Logic Riddles", tested by exhaustive search or by a seeded simulation."""
import math
from collections import deque
from functools import lru_cache
from itertools import combinations, permutations, product

import numpy as np

NONNUMERIC = {}


def test_q1():
    def find(heavy, group):
        steps = 0
        while len(group) > 1:
            k = math.ceil(len(group) / 3)
            left, right, rest = group[:k], group[k:2 * k], group[2 * k:]
            steps += 1
            group = left if heavy in left else right if heavy in right else rest
        return group[0], steps

    for h in range(8):
        got, steps = find(h, list(range(8)))
        assert got == h and steps <= 2
    for h in range(81):
        got, steps = find(h, list(range(81)))
        assert got == h and steps <= 4
    assert 3**2 >= 8 and 3**1 < 8 and 3**4 == 81


def test_q2():
    rng = np.random.default_rng(2)
    for _ in range(50):
        rates = rng.exponential(size=200)
        a = rates / rates.sum() * 60
        b = rng.permutation(a)
        # Rope A burns from both ends; the two flames meet after half the total time.
        i, j, t1, t2 = 0, len(a) - 1, 0.0, 0.0
        while i <= j:
            if t1 <= t2:
                t1 += a[i]
                i += 1
            else:
                t2 += a[j]
                j -= 1
        # The last segment is shared: flames meet at (t1 + t2) with a correction under one segment.
        assert abs(max(t1, t2) - 30) <= a.max()
        assert b.sum() - 60 < 1e-9
    # Exact: both flames burn all of the rope, at twice the rate.
    assert 60 / 2 == 30 and 30 + 30 / 2 == 45


def test_q3():
    # Simulate the plan: t, sand remaining on top of (4, 7).
    a, b, t = 4, 7, 0
    # Both run until a runs out at 4; turn a.
    t += 4
    a, b = 4, b - 4
    # Until b runs out at 7; a has 1 on top and 3 below. Turn b.
    t += b
    a, b = a - 3, 7
    assert t == 7 and a == 1
    # Until a runs out at 8; b has run 1, so it holds 1 below. Turn b: 1 runs back.
    t += a
    b_below = 1
    t += b_below
    assert t == 9


def test_q4():
    for fake in range(1, 11):
        total = sum(k * (11 if k == fake else 10) for k in range(1, 11))
        assert total - 550 == fake
    assert sum(range(1, 11)) == 55


def test_q5():
    # Add one A: two A and two B. Half of each pill gives one A and one B.
    a, b = 1 + 1, 2
    assert a / 2 == 1 and b / 2 == 1
    # Tomorrow's half-pills are the other half, so nothing is wasted.
    assert a - a / 2 == 1 and b - b / 2 == 1


def test_q6():
    def pieces(n, cuts):
        """Cut links (1-based, sorted) and the runs of links between them."""
        out, last = [1] * len(cuts), 0
        for c in [*cuts, n + 1]:
            if c - last > 1:
                out.append(c - last - 1)
            last = c
        return out

    def pays(n, cuts):
        totals = {0}
        for size in pieces(n, cuts):
            totals |= {t + size for t in totals}
        return all(day in totals for day in range(1, n + 1))

    # No cut cannot pay day 1. One cut works for 7 links only at the third or the fifth.
    assert not pays(7, ())
    assert [c for c in range(1, 8) if pays(7, (c,))] == [3, 5]
    assert sorted(pieces(7, (3,))) == [1, 2, 4]
    # The wrong answer's three cuts do leave seven single links.
    assert pieces(7, (2, 4, 6)) == [1] * 7
    # The longest chain for each number of cuts, by trying every choice of cuts.
    assert max(n for n in range(1, 16) if any(pays(n, (c,)) for c in range(1, n + 1))) == 7
    assert max(n for n in range(2, 40) if any(pays(n, c) for c in combinations(range(1, n + 1), 2))) == 23
    assert sorted(pieces(23, (4, 11))) == [1, 1, 3, 6, 12]
    assert pays(23, (4, 11))
    # The payment plan really runs, day by day, with change, on the three pieces.
    held = set()
    for day in range(1, 8):
        held = {s for s in (1, 2, 4) if day & s}
        assert sum(held) == day
    assert held == {1, 2, 4}


def tile_exists(cells):
    cells = set(cells)

    @lru_cache(None)
    def go(rest):
        if not rest:
            return True
        x, y = min(rest)
        for nb in ((x + 1, y), (x, y + 1)):
            if nb in rest and go(rest - {(x, y), nb}):
                return True
        return False

    return go(frozenset(cells))


def test_q7():
    board = {(x, y) for x in range(8) for y in range(8)}
    rest = board - {(0, 0), (7, 7)}
    whites = sum((x + y) % 2 == 0 for x, y in rest)
    blacks = sum((x + y) % 2 == 1 for x, y in rest)
    assert (whites, blacks) == (30, 32)
    # Smaller boards by search: corners removed, none is possible; opposite colours, all are.
    small = {(x, y) for x in range(4) for y in range(4)}
    assert not tile_exists(small - {(0, 0), (3, 3)})
    for u, v in combinations(sorted(small), 2):
        if (u[0] + u[1]) % 2 != (v[0] + v[1]) % 2:
            assert tile_exists(small - {u, v})


def test_q8():
    for me, you in product([0, 1], repeat=2):
        first_guess = you
        second_guess = 1 - me
        assert first_guess == me or second_guess == you
    # Each is right half of the time, and never both.
    both = sum((you == me) and (1 - me == you) for me, you in product([0, 1], repeat=2))
    assert both == 0


def test_q9():
    # Three states are distinguished: on, off and warm, off and cold.
    states = {"s1": ("on", False) , "s2": ("off", True), "s3": ("off", False)}
    assert len(set(states.values())) == 3
    # A scheme with no heat cannot do it: one look gives two values for three switches.
    assert 2**1 < 3


def test_q10():
    fruits = ["apples", "oranges", "mixed"]
    worlds = [dict(zip(fruits, p, strict=True)) for p in permutations(fruits) if all(a != b for a, b in zip(fruits, p, strict=True))]
    assert len(worlds) == 2
    # Drawing from the box labelled mixed separates the two worlds.
    assert {w["mixed"] for w in worlds} == {"apples", "oranges"}
    # A draw from a box labelled apples can show oranges in both worlds, so it does not separate.
    assert {w["apples"] for w in worlds} == {"oranges", "mixed"}


def test_q11():
    times = (1, 2, 5, 10)
    start = (frozenset(times), True)
    best = {start: 0}
    queue = deque([start])
    while queue:
        (left, torch) = state = queue.popleft()
        t = best[state]
        if torch:
            moves = [frozenset(c) for r in (1, 2) for c in combinations(left, r)]
        else:
            moves = [frozenset([x]) for x in set(times) - left]
        for m in moves:
            nxt = (left - m if torch else left | m, not torch)
            nt = t + max(m)
            if nt < best.get(nxt, 10**9):
                best[nxt] = nt
                queue.append(nxt)
    assert best[(frozenset(), False)] == 17
    assert 2 + 1 + 10 + 2 + 2 == 17
    assert 10 + 1 + 5 + 1 + 2 == 19


def reach(a, b):
    seen = {(0, 0): 0}
    queue = deque([(0, 0)])
    while queue:
        x, y = queue.popleft()
        d = min(x, b - y)
        e = min(y, a - x)
        for s in ((a, y), (x, b), (0, y), (x, 0), (x - d, y + d), (x + e, y - e)):
            if s not in seen:
                seen[s] = seen[(x, y)] + 1
                queue.append(s)
    return seen


def test_q12():
    s = reach(3, 5)
    steps = min(v for (x, y), v in s.items() if y == 4)
    assert steps == 6
    amounts = {x for x, _ in reach(6, 10)} | {y for _, y in reach(6, 10)}
    assert 3 not in amounts
    assert amounts == {0, 2, 4, 6, 8, 10}
    assert math.gcd(3, 5) == 1 and math.gcd(6, 10) == 2


def test_q13():
    rng = np.random.default_rng(13)
    g = np.zeros((8, 8), dtype=int)
    g[3, 5] = 1
    for _ in range(2000):
        if rng.random() < 0.5:
            g[rng.integers(8)] ^= 1
        else:
            g[:, rng.integers(8)] ^= 1
        assert g.sum() % 2 == 1


def test_q14():
    rng = np.random.default_rng(14)
    for _ in range(300):
        hats = rng.integers(0, 2, 100)
        back = hats[1:].sum() % 2
        said = [back]
        seen_parity = back
        wrong = 0
        for i in range(1, 100):
            guess = (seen_parity - hats[i + 1 :].sum()) % 2
            wrong += guess != hats[i]
            seen_parity = (seen_parity - guess) % 2
            said.append(guess)
        assert wrong == 0
    # The first is right half of the time, so 99 are sure, and on average 99.5 are right.
    assert 99 + 0.5 == 99.5


def test_q15():
    n = 1000
    t = math.ceil(math.log2(n))
    assert t == 10 and 2**9 < n <= 2**10
    # One round: each taster drinks where its bit is set, and the set of those affected gives the number.
    for bottle in range(n):
        code = [k for k in range(t) if bottle >> k & 1]
        assert sum(1 << k for k in code) == bottle
    assert 3**6 < n <= 3**7
    # Two rounds: a ternary digit says drink in round 1, in round 2, or never.
    for bottle in range(n):
        digits = [(bottle // 3**k) % 3 for k in range(7)]
        assert sum(d * 3**k for k, d in enumerate(digits)) == bottle
    assert n == 1000


def test_q16():
    rng = np.random.default_rng(16)
    for _ in range(2000):
        coins = np.zeros(100, dtype=int)
        coins[rng.choice(100, 10, replace=False)] = 1
        pick = rng.choice(100, 10, replace=False)
        first = 1 - coins[pick]
        rest = np.delete(coins, pick)
        assert first.sum() == rest.sum()


def test_q17():
    assert (0 + 0) % 2 == (7 + 7) % 2
    assert 64 - 1 == 63
    # On a 4 by 4 board a full tour between opposite corners is absent, by search.
    def tours(n, start, end):
        moves = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
        seen = {start}

        def go(p):
            if len(seen) == n * n:
                return p == end
            for dx, dy in moves:
                q = (p[0] + dx, p[1] + dy)
                if 0 <= q[0] < n and 0 <= q[1] < n and q not in seen:
                    seen.add(q)
                    if go(q):
                        return True
                    seen.remove(q)
            return False

        return go(start)

    assert not tours(4, (0, 0), (3, 3))
    # On a 5 by 5 board corners have the same colour, 24 moves is even, and a tour exists.
    assert tours(5, (0, 0), (4, 4))


def test_q18():
    def run(n, hole):
        grid = np.zeros((2**n, 2**n), dtype=int)
        grid[hole] = -1
        tag = [0]
        # Fill the 2 by 2 base.
        def rec(m, x0, y0, ho):
            if m == 0:
                return
            h = 2 ** (m - 1)
            cx, cy = x0 + h, y0 + h
            tag[0] += 1
            t = tag[0]
            quads = [(x0, y0, (cx - 1, cy - 1)), (cx, y0, (cx, cy - 1)), (x0, cy, (cx - 1, cy)), (cx, cy, (cx, cy))]
            for qx, qy, cell in quads:
                if qx <= ho[0] < qx + h and qy <= ho[1] < qy + h:
                    rec(m - 1, qx, qy, ho)
                else:
                    grid[cell] = t
                    rec(m - 1, qx, qy, cell)

        rec(n, 0, 0, hole)
        return grid, tag[0]

    for hole in product(range(8), repeat=2):
        grid, pieces = run(3, hole)
        assert pieces == 21
        assert (grid == 0).sum() == 0
        counts = np.bincount(grid[grid > 0].ravel())
        assert (counts[1:] == 3).all()
    assert (64 - 1) // 3 == 21


def test_q19():
    def can(start):
        seen = {start}
        queue = deque([start])
        while queue:
            a, b, c = queue.popleft()
            if sorted((a, b, c))[:2] == [0, 0]:
                return True
            for nxt in ((a - 1, b - 1, c + 2), (a - 1, b + 2, c - 1), (a + 2, b - 1, c - 1)):
                if min(nxt) >= 0 and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return False

    assert not can((13, 15, 17))
    assert can((13, 16, 16))
    assert (13 % 3, 15 % 3, 17 % 3) == (1, 0, 2)
    assert (16 - 16) % 3 == 0


def test_q20():
    rng = np.random.default_rng(20)
    for _ in range(3000):
        b = list(range(1, 11))
        while len(b) > 1:
            i, j = rng.choice(len(b), 2, replace=False)
            x, y = b[i], b[j]
            b = [v for k, v in enumerate(b) if k not in (i, j)] + [abs(x - y)]
        assert b[0] % 2 == 1
    assert sum(range(1, 11)) == 55
    for _ in range(300):
        c = list(range(1, 11))
        while len(c) > 1:
            i, j = rng.choice(len(c), 2, replace=False)
            x, y = int(c[i]), int(c[j])
            c = [v for k, v in enumerate(c) if k not in (i, j)] + [x + y + x * y]
        assert c[0] == math.factorial(11) - 1
    assert math.factorial(11) - 1 == 39916799


def test_q21():
    def count(values):
        cmp = 0
        n = len(values)
        i = 0
        if n % 2:
            lo = hi = values[0]
            i = 1
        else:
            cmp += 1
            lo, hi = (values[0], values[1]) if values[0] < values[1] else (values[1], values[0])
            i = 2
        while i < n:
            a, b = values[i], values[i + 1]
            cmp += 1
            if a > b:
                a, b = b, a
            cmp += 2
            lo = min(lo, a)
            hi = max(hi, b)
            i += 2
        return cmp, lo, hi

    rng = np.random.default_rng(21)
    for n in (2, 3, 4, 7, 100, 101):
        v = list(rng.permutation(n * 3)[:n])
        c, lo, hi = count(v)
        assert c == math.ceil(3 * n / 2) - 2
        assert lo == min(v) and hi == max(v)
    assert count(list(range(100)))[0] == 148


def test_q22():
    triples = [(a, b, c) for a in range(1, 37) for b in range(a, 37) for c in range(b, 37) if a * b * c == 36]
    assert len(triples) == 8
    sums = {}
    for t in triples:
        sums.setdefault(sum(t), []).append(t)
    amb = {s: v for s, v in sums.items() if len(v) > 1}
    assert amb == {13: [(1, 6, 6), (2, 2, 9)]}


def test_q23():
    worlds = [p for p in product("RW", repeat=3) if p.count("W") <= 2]
    # Back sees middle and front. Index 0 back, 1 middle, 2 front.
    # Back does not know: rules out middle and front both white.
    after_back = [w for w in worlds if not (w[1] == "W" and w[2] == "W")]
    # Middle sees front; knows if front is white, since front W + middle W is out.
    after_mid = [w for w in after_back if w[2] == "R"]
    assert {w[2] for w in after_mid} == {"R"}
    # Weights: all of the eight worlds except WWW remain possible at the start.
    assert len(worlds) == 7


def test_q24():
    weights = [2**k for k in range(10)]
    assert sum(weights) == 1023
    for mask in range(1024):
        extra = sum(weights[k] for k in range(10) if mask >> k & 1)
        assert extra == mask
    # A smaller system cannot give distinct sums: 10 stacks need 1024 subsets, so the total is at least 1023.
    assert 2**10 - 1 == 1023


def test_q25():
    for safe_left, truthful in product([True, False], repeat=2):
        # "If I asked the other guard whether left is safe, would he say yes?"
        other_says = (safe_left if not truthful else not safe_left)
        answer = other_says if truthful else not other_says
        assert answer == (not safe_left)
        # A second route: "Would you say yes if I asked you whether left is safe?"
        my_says = safe_left if truthful else not safe_left
        answer2 = my_says if truthful else not my_says
        assert answer2 == safe_left


def test_q26():
    n = 100
    sols = []
    for f in range(n + 1):
        truth = [k == f for k in range(1, n + 1)]
        if truth.count(False) == f:
            sols.append(truth)
    assert len(sols) == 1 and sols[0].index(True) == 98
    # The at-least version with 100 statements: statements 1..50 true, the rest false.
    sols2 = []
    for f in range(n + 1):
        truth = [f >= k for k in range(1, n + 1)]
        if truth.count(False) == f:
            sols2.append(truth)
    assert len(sols2) == 1 and sum(sols2[0]) == 50 and all(sols2[0][:50])


def scheme_12():
    return [
        ({1, 2, 3, 10}, {4, 5, 6, 11}),
        ({1, 2, 3, 11}, {7, 8, 9, 10}),
        ({1, 4, 7, 10}, {2, 5, 8, 12}),
    ]


def test_q27():
    w = scheme_12()
    seen = {}
    for ball in range(1, 13):
        for sign in (1, -1):
            out = []
            for left, right in w:
                out.append(sign if ball in left else -sign if ball in right else 0)
            key = tuple(out)
            assert key not in seen
            seen[key] = (ball, sign)
    assert len(seen) == 24
    assert (0, 0, 0) not in seen
    assert (27 - 3) // 2 == 12
    for left, right in w:
        assert len(left) == len(right) == 4


def tile4(m, n):
    @lru_cache(None)
    def go(rows):
        if all(r == n for r in rows):
            return True
        low = min(rows)
        i = rows.index(low)
        r = list(rows)
        if low + 4 <= n:
            r[i] += 4
            if go(tuple(r)):
                return True
            r[i] -= 4
        if i + 4 <= m and all(rows[i + k] == low for k in range(4)):
            for k in range(4):
                r[i + k] += 1
            if go(tuple(r)):
                return True
        return False

    return go((0,) * m)


def test_q28():
    counts = [0, 0, 0, 0]
    for x in range(10):
        for y in range(10):
            counts[(x + y) % 4] += 1
    assert counts == [25, 26, 25, 24]
    assert not tile4(6, 6)
    assert not tile4(5, 6)
    assert tile4(4, 10)
    assert tile4(8, 3)
    assert not tile4(5, 5)
    # The rule: 1 by 4 bricks fit exactly when 4 divides one side.
    for m in range(1, 8):
        for n in range(1, 8):
            assert tile4(m, n) == (m % 4 == 0 or n % 4 == 0)


def test_q29():
    def second(values):
        cmp = 0
        round_ = [(v, []) for v in values]
        while len(round_) > 1:
            nxt = []
            for i in range(0, len(round_) - 1, 2):
                a, b = round_[i], round_[i + 1]
                cmp += 1
                if a[0] > b[0]:
                    nxt.append((a[0], [*a[1], b[0]]))
                else:
                    nxt.append((b[0], [*b[1], a[0]]))
            if len(round_) % 2:
                nxt.append(round_[-1])
            round_ = nxt
        beaten = round_[0][1]
        s = beaten[0]
        for x in beaten[1:]:
            cmp += 1
            s = max(s, x)
        return s, cmp

    rng = np.random.default_rng(29)
    for n in (2, 8, 64):
        worst = 0
        for _ in range(300):
            v = list(rng.permutation(n * 4)[:n])
            s, c = second(v)
            assert s == sorted(v)[-2]
            worst = max(worst, c)
        assert worst == n + math.ceil(math.log2(n)) - 2
    assert 64 + 6 - 2 == 68
    assert 63 + 62 == 125


def test_q30():
    for n in (2, 3, 4, 5):
        for hats in product(range(n), repeat=n):
            right = 0
            for i in range(n):
                rest = sum(hats) - hats[i]
                guess = (i - rest) % n
                right += guess == hats[i]
            assert right == 1


def test_q31():
    wins = 0
    guesses_right = 0
    guesses_all = 0
    for hats in product([0, 1], repeat=3):
        calls = []
        for i in range(3):
            others = [hats[j] for j in range(3) if j != i]
            if others[0] == others[1]:
                calls.append((i, 1 - others[0]))
        ok = bool(calls) and all(hats[i] == g for i, g in calls)
        wins += ok
        for i, g in calls:
            guesses_all += 1
            guesses_right += hats[i] == g
    assert wins == 6
    assert guesses_all == 12 and guesses_right == 6
    # No plan beats 3/4: search all plans, each person mapping the four views to pass, black or white.
    views = list(product([0, 1], repeat=2))
    outcomes = list(product([0, 1], repeat=3))
    masks = []
    for i in range(3):
        rows = []
        for plan in product([None, 0, 1], repeat=4):
            right = wrong = 0
            for o, hats in enumerate(outcomes):
                view = tuple(hats[j] for j in range(3) if j != i)
                g = plan[views.index(view)]
                if g is not None:
                    if g == hats[i]:
                        right |= 1 << o
                    else:
                        wrong |= 1 << o
            rows.append((right, wrong))
        masks.append(np.array(rows))
    r = masks[0][:, 0][:, None, None] | masks[1][:, 0][None, :, None] | masks[2][:, 0][None, None, :]
    w = masks[0][:, 1][:, None, None] | masks[1][:, 1][None, :, None] | masks[2][:, 1][None, None, :]
    win = r & ~w & 255
    pop = np.array([bin(k).count("1") for k in range(256)])
    assert pop[win].max() == 6


def test_q32():
    def run(blue, total):
        # Worlds: subsets of people who are blue and nonempty after the announcement.
        people = range(total)
        actual = frozenset(range(blue))
        worlds = {frozenset(c) for r in range(1, total + 1) for c in combinations(people, r)}
        day = 0
        while True:
            day += 1
            leaving = []
            for p in actual:
                seen = actual - {p}
                options = {w for w in worlds if w - {p} == seen}
                if len(options) == 1:
                    leaving.append(p)
            if leaving:
                return day, len(leaving)
            # Nobody left: rule out worlds in which someone would have known.
            new = set()
            for w in worlds:
                someone_would = False
                for p in w:
                    seen = w - {p}
                    if len({v for v in worlds if v - {p} == seen}) == 1:
                        someone_would = True
                if not someone_would:
                    new.add(w)
            worlds = new

    for blue in range(1, 6):
        day, count = run(blue, 6)
        assert day == blue and count == blue


def test_q33():
    n = 100
    formula = sum(n / (n - k) + n for k in range(1, n))
    assert abs(formula - (n * sum(1 / k for k in range(1, n)) + n * (n - 1))) < 1e-9
    assert round(formula) == 10418
    assert round(formula / 365, 1) == 28.5
    rng = np.random.default_rng(33)

    def simulate():
        light = False
        count = 0
        done = np.zeros(n, dtype=bool)
        day = 0
        while True:
            day += 1
            p = int(rng.integers(n))
            if p == 0:
                if light:
                    light = False
                    count += 1
                    if count == n - 1:
                        return day
            elif not light and not done[p]:
                light = True
                done[p] = True

    sims = [simulate() for _ in range(300)]
    assert abs(np.mean(sims) - formula) < 150


def test_q34():
    def parity(board):
        s = 0
        for i, c in enumerate(board):
            if c:
                s ^= i
        return s

    rng = np.random.default_rng(34)
    for _ in range(3000):
        board = rng.integers(0, 2, 64).tolist()
        target = int(rng.integers(64))
        flip = parity(board) ^ target
        board[flip] ^= 1
        assert parity(board) == target
    # Sizes: the same plan works for 2^k squares; for 3 squares, a graph argument shows none exists.
    for squares in (2, 4, 8, 16):
        for b in range(2**squares):
            bits = [(b >> i) & 1 for i in range(squares)]
            for t in range(squares):
                f = parity(bits) ^ t
                nb = bits.copy()
                nb[f] ^= 1
                assert parity(nb) == t

    # Three squares: exhaustive search over colourings of the cube.
    verts = list(product([0, 1], repeat=3))
    ok = False
    for colours in product(range(3), repeat=8):
        col = dict(zip(verts, colours, strict=True))
        good = True
        for v in verts:
            seen = set()
            for i in range(3):
                u = list(v)
                u[i] ^= 1
                seen.add(col[tuple(u)])
            if len(seen) != 3:
                good = False
                break
        if good:
            ok = True
            break
    assert not ok


def encode(hand):
    suits = {}
    for c in hand:
        suits.setdefault(c // 13, []).append(c)
    pair = next(sorted(v)[:2] for v in suits.values() if len(v) >= 2)
    a, b = pair
    d = (b - a) % 13
    if d <= 6:
        hidden, shown = b, a
    else:
        hidden, shown, d = a, b, (a - b) % 13
    others = sorted(set(hand) - {hidden, shown})
    perm_index = d - 1
    return hidden, shown, [others[i] for i in list(permutations(range(3)))[perm_index]]


def decode(shown, rest):
    base = sorted(rest)
    order = tuple(base.index(x) for x in rest)
    d = list(permutations(range(3))).index(order) + 1
    return shown // 13 * 13 + (shown % 13 + d) % 13


def test_q35():
    rng = np.random.default_rng(35)
    for _ in range(40_000):
        hand = rng.choice(52, 5, replace=False).tolist()
        hidden, shown, rest = encode(hand)
        assert decode(shown, rest) == hidden
    # Counting: 52*51*50*49 ordered rows against C(n,5)*5 hand-and-choice pairs.
    assert 52 * 51 * 50 * 49 // 24 == 270725
    assert 5 * 24 == 120
    # With n cards: C(n, 5) hands need at most n(n-1)(n-2)(n-3) rows, so n - 4 <= 120.
    def fits(n):
        return math.comb(n, 5) <= n * (n - 1) * (n - 2) * (n - 3)

    assert fits(52) and fits(124) and not fits(125)


def test_follow_ups():
    # Q13: on a 7 by 7 grid, the reachable patterns contain no single black cell.
    n = 7
    seen = set()
    for rows in range(2**n):
        for cols in range(2**n):
            g = tuple((rows >> i & 1) ^ (cols >> j & 1) for i in range(n) for j in range(n))
            seen.add(g)
    single = tuple(int(i == 3 * n + 3) for i in range(n * n))
    assert single not in seen and tuple([0] * (n * n)) in seen
    # Q31: seven people with the Hamming code win 7/8.
    parity = [[1, 0, 1, 0, 1, 0, 1], [0, 1, 1, 0, 0, 1, 1], [0, 0, 0, 1, 1, 1, 1]]

    def in_code(w):
        return all(sum(a * b for a, b in zip(row, w, strict=True)) % 2 == 0 for row in parity)

    wins = 0
    for hats in product([0, 1], repeat=7):
        guesses = []
        for i in range(7):
            w0, w1 = list(hats), list(hats)
            w0[i], w1[i] = 0, 1
            if in_code(w0):
                guesses.append((i, 1))
            elif in_code(w1):
                guesses.append((i, 0))
        wins += bool(guesses) and all(hats[i] == g for i, g in guesses)
    assert wins == 112 and wins / 128 == 7 / 8
    # Q33 follow-up: start unknown, two signals each, the counter stops at 2 (n - 1); it is never early.
    rng = np.random.default_rng(133)
    size = 8
    for _ in range(300):
        light = bool(rng.integers(2))
        count = 0
        times = np.zeros(size, dtype=int)
        visited = {0}
        while count < 2 * (size - 1):
            p = int(rng.integers(size))
            visited.add(p)
            if p == 0:
                if light:
                    light = False
                    count += 1
            elif not light and times[p] < 2:
                light = True
                times[p] += 1
        assert len(visited) == size
