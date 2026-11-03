"""Every number printed in the answers of "Games": game tables, LP solutions and seeded simulations."""
import math
from fractions import Fraction as Fr
from functools import lru_cache
from itertools import product

import numpy as np
from scipy.optimize import linprog

NONNUMERIC = {}


def lp_value(a):
    """Value and row mix of the matrix game with payoffs a to the row player."""
    a = np.asarray(a, float)
    m, n = a.shape
    c = np.zeros(m + 1)
    c[-1] = -1
    a_ub = np.hstack([-a.T, np.ones((n, 1))])
    b_ub = np.zeros(n)
    a_eq = np.ones((1, m + 1))
    a_eq[0, -1] = 0
    r = linprog(c, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=[1], bounds=[(0, None)] * m + [(None, None)])
    return r.x[-1], r.x[:-1]


def test_q1():
    def wins(n, moves, last_wins):
        table = [False] * (n + 1)
        table[0] = not last_wins
        for s in range(1, n + 1):
            table[s] = any(m <= s and not table[s - m] for m in moves)
        return table

    t = wins(97, range(1, 7), True)
    assert t[97] and not t[91]
    assert 97 % 7 == 6
    assert all(t[s] == (s % 7 != 0) for s in range(98))
    m = wins(97, range(1, 7), False)
    assert m[97] and not m[92]
    assert (97 - 1) % 7 == 5
    assert all(m[s] == ((s - 1) % 7 != 0) for s in range(1, 98))


def test_q2():
    @lru_cache(None)
    def win(a, b):
        return any(not win(x, b) for x in range(a)) or any(not win(a, y) for y in range(b))

    assert win(5, 8) and not win(5, 5)
    assert all(win(a, b) == (a != b) for a in range(10) for b in range(10))


def test_q3():
    v, p = lp_value([[3, -2], [-2, 1]])
    assert abs(v + 1 / 8) < 1e-9
    assert abs(p[0] - 3 / 8) < 1e-9
    v2, q = lp_value([[-3, 2], [2, -1]])
    assert abs(v2 - 1 / 8) < 1e-9
    assert abs(q[0] - 3 / 8) < 1e-9
    # Second route: sum over the four outcomes under the two mixes.
    q0 = Fr(3, 8)
    assert q0**2 * 3 + (1 - q0) ** 2 - 2 * 2 * q0 * (1 - q0) == Fr(-1, 8)
    # The payoffs add up to zero, yet the game is not fair.
    assert 3 + 1 - 2 - 2 == 0


def test_q4():
    x = 100.0
    seq = []
    for _ in range(6):
        x *= 2 / 3
        seq.append(round(x))
    assert seq[0] == 67
    start = 50.0
    assert round(start * 2 / 3) == 33 and round(start * 4 / 9) == 22 and round(start * 8 / 27) == 15
    # 0 is the fixed point of the best reply.
    assert 2 / 3 * 0 == 0
    # With whole numbers, all at 1 is stable too: the target is 2/3, nearer to 1 than to 0.
    assert abs(0 - 2 / 3) > abs(1 - 2 / 3)
    # In a room of 100, one player moving from 1 to 0 hardly moves the target, and 1 still wins.
    assert abs(1 - 2 / 3 * 99 / 100) < abs(0 - 2 / 3 * 99 / 100)
    # Whole-number steps down from 100: 67, 45, 30, and so on to 1, where it sticks.
    tops = [100]
    while round(tops[-1] * 2 / 3) != tops[-1]:
        tops.append(round(tops[-1] * 2 / 3))
    assert tops[1:4] == [67, 45, 30] and tops[-1] == 1

    def share(me, others):
        """My share of the win, ties split."""
        everyone = [me, *others]
        target = Fr(2, 3) * Fr(sum(everyone), len(everyone))
        gaps = [abs(v - target) for v in everyone]
        best = min(gaps)
        return Fr(1, gaps.count(best)) if gaps[0] == best else Fr(0)

    # A number above 67 can win, but 67 never does worse, in every room of three.
    assert share(68, [100, 100, 100, 100]) == 1
    assert all(share(x, [a, b]) <= share(67, [a, b]) for x in range(68, 101, 4) for a in range(0, 101, 3) for b in range(0, 101, 3))
    # All at 1: moving to 0 wins outright up to a room of 3, ties at 4, and loses from 5.
    assert share(0, [1, 1]) == 1 and share(0, [1, 1, 1]) == Fr(1, 4) and share(0, [1] * 4) == 0 and share(0, [1] * 99) == 0


def test_q5():
    a = [[0, -2, 1], [2, 0, -3], [-1, 3, 0]]
    v, p = lp_value(a)
    assert abs(v) < 1e-9
    assert np.allclose(p, [1 / 2, 1 / 6, 1 / 3], atol=1e-8)
    # Indifference by hand.
    r, pa, s = Fr(1, 2), Fr(1, 6), Fr(1, 3)
    assert -2 * pa + s == 0 and 2 * r - 3 * s == 0 and -r + 3 * pa == 0


def nim_win(state):
    @lru_cache(None)
    def win(st):
        for i, h in enumerate(st):
            for x in range(h):
                nxt = tuple(sorted(st[:i] + (x,) + st[i + 1:]))
                if not win(nxt):
                    return True
        return False

    return win(tuple(sorted(state)))


def test_q6():
    assert 3 ^ 5 ^ 7 == 1
    assert nim_win((3, 5, 7))
    moves = []
    base = (3, 5, 7)
    for i in range(3):
        for x in range(base[i]):
            nxt = base[:i] + (x,) + base[i + 1:]
            if not nim_win(nxt):
                moves.append(nxt)
    assert sorted(moves) == [(2, 5, 7), (3, 4, 7), (3, 5, 6)]
    # The rule agrees with brute force on a whole box of positions.
    for s in product(range(6), repeat=3):
        assert nim_win(s) == ((s[0] ^ s[1] ^ s[2]) != 0)


def test_q7():
    g = [0] * 30
    for n in range(1, 30):
        reach = {g[n - m] for m in (1, 3, 4) if m <= n}
        k = 0
        while k in reach:
            k += 1
        g[n] = k
    assert g[:9] == [0, 1, 0, 1, 2, 3, 2, 0, 1]
    assert all(g[n] == g[n % 7] for n in range(30))
    assert g[10] == 1 and g[6] == 2 and (g[10] ^ g[6]) == 3

    @lru_cache(None)
    def win(a, b):
        return any(m <= a and not win(a - m, b) for m in (1, 3, 4)) or any(m <= b and not win(a, b - m) for m in (1, 3, 4))

    assert win(10, 6) and not win(6, 6)
    good = [m for m in (1, 3, 4) if not win(10 - m, 6)] + [m for m in (1, 3, 4) if m <= 6 and not win(10, 6 - m)]
    assert good == [4, 3]
    assert g[3] == g[10]


def pirates(n, coins, need):
    """Backward induction; each voter says yes only if strictly better off. Returns the split, proposer first."""
    alloc = [coins]
    for k in range(2, n + 1):
        votes = need(k)
        # prior[i] is what the pirate who is i-th in the next round gets; the proposer now would be dead.
        order = sorted(range(k - 1), key=lambda i: (alloc[i], i))
        pick = order[: votes - 1]
        cost = sum(alloc[i] + 1 for i in pick)
        new = [0] * k
        if cost > coins:
            raise ValueError(k)
        for i in pick:
            new[i + 1] = alloc[i] + 1
        new[0] = coins - cost
        alloc = new
    return alloc


def test_q8():
    half = lambda k: math.ceil(k / 2)  # noqa: E731
    assert pirates(5, 100, half) == [98, 0, 1, 0, 1]
    assert pirates(4, 100, half) == [99, 0, 1, 0]
    assert pirates(3, 100, half) == [99, 0, 1]
    assert pirates(2, 100, half) == [100, 0]
    # More than half needed: at 2 pirates, the last rejects and takes all, so the fourth must back any plan.
    # With D doomed, C needs one more vote and D gives it for free.
    three = [100, 0, 0]
    # B needs 3 of 4 votes: their own and two of C, D, E. D and E get 0 under C, so one coin each.
    four = [98, 0, 1, 1]
    assert 100 - 2 == four[0] and three[1] + 1 == four[2] and three[2] + 1 == four[3]
    # A needs 3 of 5: their own, C (0 -> 1), and D or E (1 -> 2).
    five = [97, 0, 1, 2, 0]
    assert sum(five) == 100 and five[2] == four[1] + 1 and five[3] == four[2] + 1


def test_q9():
    d = 0.9
    a = 1 - d * (1 - d)
    assert abs(a - 0.91) < 1e-12
    assert abs(1 / (1 + d) - 10 / 19) < 1e-12
    assert round(1 / (1 + d), 3) == 0.526
    # Backward induction with many rounds tends to the formula, and to one half as d goes to 1.
    share = 1.0
    for _ in range(1000):
        share = 1 - d * share
    assert abs(share - 1 / (1 + d)) < 1e-9
    assert abs(1 / (1 + 0.9999) - 0.5) < 1e-3
    # d = 0 limit: the first proposer takes all.
    assert 1 / (1 + 0) == 1


def test_q10():
    v, p = lp_value([[0.6, 0.95], [0.9, 0.5]])
    assert abs(p[0] - 8 / 15) < 1e-8
    assert abs(v - 0.74) < 1e-9
    w, k = lp_value([[-0.6, -0.9], [-0.95, -0.5]])
    assert abs(w + 0.74) < 1e-9
    assert abs(k[0] - 0.6) < 1e-8
    v2, p2 = lp_value([[0.6, 0.95], [0.95, 0.5]])
    assert abs(p2[0] - 9 / 16) < 1e-8
    assert abs(1 - p2[0] - 7 / 16) < 1e-8
    assert abs(1 - p[0] - 7 / 15) < 1e-8
    assert 7 / 16 < 7 / 15
    assert abs(v2 - 0.75 - 0.0) < 0.01
    assert abs(v2 - (0.6 * 9 / 16 + 0.95 * 7 / 16)) < 1e-9
    assert round(v2, 3) == 0.753


def test_q11():
    for n in (2, 3, 5):
        # Deviation check for the first-price bid at v = 0.9.
        v = 0.9
        grid = np.linspace(0, v, 9001)
        pay = (v - grid) * np.minimum(grid * n / (n - 1), 1) ** (n - 1)
        assert abs(grid[pay.argmax()] - (n - 1) / n * v) < 1e-3
    rng = np.random.default_rng(11)
    for n in (2, 3, 5):
        x = np.sort(rng.random((600_000, n)), axis=1)
        second = x[:, -2].mean()
        first = ((n - 1) / n * x[:, -1]).mean()
        assert abs(second - (n - 1) / (n + 1)) < 0.001
        assert abs(first - (n - 1) / (n + 1)) < 0.001
        # Same mean but a lower variance for the first-price revenue.
        assert ((n - 1) / n * x[:, -1]).var() < x[:, -2].var()


def test_q12():
    def p_star(n, cost=Fr(1), worth=Fr(4)):
        """Each person's probability, from the indifference condition."""
        return 1 - float(cost / worth) ** (1 / (n - 1))

    assert abs(p_star(2) - 3 / 4) < 1e-12
    assert abs(p_star(3) - 1 / 2) < 1e-12
    # Exact indifference at the printed mixes, and exact chances that nobody does it.
    for n, p, nobody in ((2, Fr(3, 4), Fr(1, 16)), (3, Fr(1, 2), Fr(1, 8))):
        assert 4 * (1 - (1 - p) ** (n - 1)) == 3
        assert (1 - p) ** n == nobody
    # As n grows the probability falls to 0 and the chance of nobody rises to 1/4, from below.
    chances = [(1 - p_star(n)) ** n for n in (2, 3, 5, 10, 100, 10_000)]
    assert chances == sorted(chances) and abs(chances[-1] - 0.25) < 0.001 and chances[-1] < 0.25
    assert p_star(10_000) < 0.001
    # Limit cases: a free task is always done, and a task worth no more than its cost never is.
    assert p_star(3, Fr(0)) == 1
    assert p_star(3, Fr(4)) == 0
    # Simulate one person against the others: both choices pay the same, and a different mix is not an equilibrium.
    rng = np.random.default_rng(12)
    others = rng.random((2_000_000, 2)) < 0.5
    some = others.any(axis=1)
    assert abs((4 * some).mean() - 3) < 0.005
    assert abs((4 * (rng.random((2_000_000, 2)) < 0.3).any(axis=1)).mean() - 3) > 0.5
    # The chance that nobody does it, simulated at n = 3 and at n = 2.
    assert abs((rng.random((2_000_000, 3)) >= 0.5).all(axis=1).mean() - 1 / 8) < 0.001
    assert abs((rng.random((2_000_000, 2)) >= 0.75).all(axis=1).mean() - 1 / 16) < 0.001

    # The pure equilibrium: if exactly one person does it, nobody gains by changing.
    def pay(me, others_do):
        return (4 if me or others_do else 0) - (1 if me else 0)

    assert pay(True, False) > pay(False, False)
    assert pay(False, True) > pay(True, True)


def test_q13():
    # Smallest case by brute force: the first player wins every rectangle except 1 x 1.
    @lru_cache(None)
    def win(rows):
        if rows == (0,) * len(rows):
            return True
        for r, cols in enumerate(rows):
            for c in range(cols):
                new = tuple(min(h, c) if i >= r else h for i, h in enumerate(rows))
                if new[0] == 0:
                    continue
                if not win(new):
                    return True
        return False

    for m in range(1, 6):
        for n in range(1, 6):
            if m * n == 1:
                assert not win((1,))
            else:
                assert win((n,) * m)


def test_q14():
    # Above 200, a proposer has their own vote, the doomed proposers before them and 100 bought votes.
    survivors = [201, 202]
    while survivors[-1] < 1000:
        m = survivors[-1]
        n = m + 1
        while (n - m) + 100 < math.ceil(n / 2):
            n += 1
        survivors.append(n)
    assert survivors[:7] == [201, 202, 204, 208, 216, 232, 264]
    assert survivors[7] == 328
    # At 203: needs 102 votes, and the proposer has their own plus 100.
    assert math.ceil(203 / 2) == 102
    assert math.ceil(204 / 2) == 102
    # 300 pirates: thrown overboard until 264 are left.
    assert 300 - 264 == 36
    assert all(s == 200 + 2**k for k, s in enumerate(survivors))
    # At 200, the proposer needs 100 votes and pays 99, so he keeps a coin.
    half = lambda k: math.ceil(k / 2)  # noqa: E731
    assert pirates(200, 100, half)[0] == 1
    assert pirates(199, 100, half)[0] == 1


def akq_matrix():
    rank = {"A": 2, "K": 1, "Q": 0}
    cards = list(rank)
    xs = list(product([0, 1], repeat=3))
    ys = list(product([0, 1], repeat=3))
    m = np.zeros((8, 8))
    for i, bet in enumerate(xs):
        for j, call in enumerate(ys):
            tot = 0.0
            for cx in range(3):
                for cy in range(3):
                    if cx == cy:
                        continue
                    sign = 1 if rank[cards[cx]] > rank[cards[cy]] else -1
                    if not bet[cx]:
                        tot += sign
                    elif not call[cy]:
                        tot += 1
                    else:
                        tot += 2 * sign
            m[i, j] = tot / 6
    return m


def test_q15():
    v, _ = lp_value(akq_matrix())
    assert abs(v - 1 / 18) < 1e-8
    # The stated strategies, checked by best responses at each information set.
    b = Fr(1, 3)
    c = Fr(1, 3)
    # Y with a king facing a bet: X has an ace, or a queen that bluffs b of the time.
    call_ev = (Fr(1) * (-2) + b * 2) / (1 + b)
    fold_ev = Fr(-1)
    assert call_ev == fold_ev
    # X with a queen: a check loses 1 and a bet earns 1 when the king folds, -2 when called, -2 against an ace.
    check = Fr(-1)
    bet = Fr(1, 2) * ((1 - c) * 1 + c * (-2)) + Fr(1, 2) * (-2)
    assert check == bet
    # The value by direct sum over the six deals.
    rng = np.random.default_rng(15)
    n = 2_000_000
    pair = np.argsort(rng.random((n, 3)), axis=1)[:, :2]
    x, y = pair[:, 0], pair[:, 1]  # 0 ace, 1 king, 2 queen
    bets = (x == 0) | ((x == 2) & (rng.random(n) < 1 / 3))
    calls = (y == 0) | ((y == 1) & (rng.random(n) < 1 / 3))
    sign = np.where(x < y, 1, -1)
    pay = np.where(~bets, sign, np.where(calls, 2 * sign, 1))
    assert abs(pay.mean() - 1 / 18) < 0.003
    assert round(1 / 18, 3) == 0.056


def test_q16():
    def rev(r):
        return 1 / 3 + r**2 - 4 / 3 * r**3

    grid = np.linspace(0, 1, 100_001)
    assert abs(grid[rev(grid).argmax()] - 0.5) < 1e-4
    assert abs(rev(0.5) - 5 / 12) < 1e-12
    rng = np.random.default_rng(16)
    x = np.sort(rng.random((1_000_000, 2)), axis=1)
    r = 0.5
    pay = np.where(x[:, 1] >= r, np.maximum(x[:, 0], r), 0)
    assert abs(pay.mean() - 5 / 12) < 0.001
    # Efficiency loss: nobody trades in a quarter of the auctions, and the surplus is lower.
    assert (x[:, 1] < r).mean() - 0.25 < 0.002
    surplus = np.where(x[:, 1] >= r, x[:, 1], 0).mean()
    assert abs(surplus - 7 / 12) < 0.001
    assert abs(x[:, 1].mean() - 2 / 3) < 0.001
    # Other n: simulation says the reserve is still one half.
    y = np.sort(rng.random((600_000, 4)), axis=1)
    vals = []
    for rr in (0.4, 0.45, 0.5, 0.55, 0.6):
        vals.append(np.where(y[:, 3] >= rr, np.maximum(y[:, 2], rr), 0).mean())
    assert int(np.argmax(vals)) == 2
    # One bidder: price r, revenue r(1-r), a quarter at r = 1/2.
    assert 0.5 * 0.5 == 0.25


def test_q17():
    @lru_cache(None)
    def win(st):
        for i, c in enumerate(st):
            for t in range(1, c + 1):
                nxt = list(st)
                nxt[i] -= t
                if i > 0:
                    nxt[i - 1] += t
                if not win(tuple(nxt)):
                    return True
        return False

    start = (3, 1, 4, 1, 5)
    assert 3 ^ 4 ^ 5 == 2
    assert win(start)
    good = []
    for i, c in enumerate(start):
        for t in range(1, c + 1):
            nxt = list(start)
            nxt[i] -= t
            if i > 0:
                nxt[i - 1] += t
            if not win(tuple(nxt)):
                good.append((i + 1, t))
    assert good == [(1, 2)]
    # The rule against brute force on small staircases.
    for st in product(range(3), repeat=4):
        assert win(st) == ((st[0] ^ st[2]) != 0)


def test_q18():
    @lru_cache(None)
    def win(a, b):
        for x in range(a):
            if not win(x, b):
                return True
        for y in range(b):
            if not win(a, y):
                return True
        for s in range(1, min(a, b) + 1):
            if not win(a - s, b - s):
                return True
        return False

    lose = sorted((a, b) for a in range(16) for b in range(a, 26) if not win(a, b))
    assert lose[:7] == [(0, 0), (1, 2), (3, 5), (4, 7), (6, 10), (8, 13), (9, 15)]
    assert not win(9, 15) and win(10, 15)
    phi = (1 + math.sqrt(5)) / 2
    for k in range(1, 25):
        a, b = math.floor(k * phi), math.floor(k * phi * phi)
        assert b == a + k
        if b < 40:
            assert not win(a, b)
    # Each whole number appears in exactly one pair: Beatty.
    seen = sorted([math.floor(k * phi) for k in range(1, 200)] + [math.floor(k * phi**2) for k in range(1, 200)])
    assert seen[:100] == list(range(1, 101))


def kuhn_matrix():
    # Player 1 pure: for each of J, Q, K: 0 check-fold, 1 check-call, 2 bet.
    # Player 2 pure: for each card: after check (0 check, 1 bet) and after bet (0 fold, 1 call).
    p1 = list(product([0, 1, 2], repeat=3))
    p2 = list(product(product([0, 1], [0, 1]), repeat=3))
    m = np.zeros((len(p1), len(p2)))
    for i, s1 in enumerate(p1):
        for j, s2 in enumerate(p2):
            tot = 0.0
            for c1 in range(3):
                for c2 in range(3):
                    if c1 == c2:
                        continue
                    sign = 1 if c1 > c2 else -1
                    a = s1[c1]
                    after_check, after_bet = s2[c2]
                    if a == 2:
                        tot += 2 * sign if after_bet else 1
                    elif after_check == 0:
                        tot += sign
                    elif a == 1:
                        tot += 2 * sign
                    else:
                        tot -= 1
            m[i, j] = tot / 6
    return m


def test_q19():
    v, _ = lp_value(kuhn_matrix())
    assert abs(v + 1 / 18) < 1e-8
    # The stated family, for several alpha, against all of Player 2's pure replies.
    m = kuhn_matrix()
    p1 = list(product([0, 1, 2], repeat=3))
    for alpha in (0.0, 0.1, 0.2, 1 / 3):
        j = (1 - alpha, 0.0, alpha)
        q = (2 / 3 - alpha, 1 / 3 + alpha, 0.0)
        k = (0.0, 1 - 3 * alpha, 3 * alpha)
        mix = np.array([j[a] * q[b] * k[c] for a, b, c in p1])
        assert abs(mix.sum() - 1) < 1e-12
        assert (mix @ m).min() > -1 / 18 - 1e-9
    # Player 2's strategy: with a king, bet and call; with a queen, check and call a third; with a jack, bluff a third and fold.
    p2 = list(product(product([0, 1], [0, 1]), repeat=3))
    y = np.zeros(len(p2))
    for idx, ((jc, jb), (qc, qb), (kc, kb)) in enumerate(p2):
        pj = (1 / 3 if jc else 2 / 3) * (0 if jb else 1)
        pq = (0 if qc else 1) * (1 / 3 if qb else 2 / 3)
        pk = (1 if kc else 0) * (1 if kb else 0)
        y[idx] = pj * pq * pk
    assert abs(y.sum() - 1) < 1e-12
    assert (m @ y).max() < -1 / 18 + 1e-9


def test_q20():
    a, c, b = 0.1, 0.4, 0.7

    def bet_pay(x, call):
        fold = call
        if x < call:
            return fold - (1 - call) * 2
        return fold + 2 * ((x - call) - (1 - x))

    def check_pay(x):
        return 2 * x - 1

    # X's best reply to c = 0.4 is exactly the range [0, a] and [b, 1].
    xs = np.linspace(0, 1, 2001)
    bet = np.array([bet_pay(x, c) for x in xs])
    chk = check_pay(xs)
    choice = bet > chk + 1e-12
    assert choice[xs < 0.0995].all() and choice[xs > 0.7005].all()
    assert not choice[(xs > 0.1005) & (xs < 0.6995)].any()
    # Y at c is indifferent between folding (-1) and calling: value bets 0.3 against bluffs 0.1.
    assert abs((2 * a - 2 * (1 - b)) / (a + 1 - b) + 1) < 1e-12

    def value(call):
        total = 0.0
        step = 1 / 200_000
        grid = (np.arange(200_000) + 0.5) * step
        fold = call
        pay = np.where(grid < call, fold - (1 - call) * 2, fold + 2 * ((grid - call) - (1 - grid)))
        pay = np.where((grid < a) | (grid > b), pay, 2 * grid - 1)
        total = pay.mean()
        return total

    assert abs(value(c) - 0.1) < 1e-4
    # Against X's fixed range, every call threshold other than c is no worse for X.
    for other in (0.2, 0.3, 0.35, 0.45, 0.5, 0.6):
        assert value(other) > value(c) - 1e-6
    # Formula for bet size B, against numeric solutions.
    for bb in (0.5, 1.0, 2.0, 4.0):
        aa = bb / ((bb + 1) * (bb + 4))
        cc = bb * (bb + 3) / ((bb + 1) * (bb + 4))
        tt = (bb**2 + 4 * bb + 2) / ((bb + 1) * (bb + 4))
        # Y indifferent at the threshold.
        assert abs(((1 + bb) * aa - (1 + bb) * (1 - tt)) / (aa + 1 - tt) + 1) < 1e-12
        # X indifferent at the two edges.
        assert abs(2 * aa - 1 - (cc - (1 - cc) * (1 + bb))) < 1e-12
        assert abs(2 * tt - 1 - (cc + (1 + bb) * (2 * tt - cc - 1))) < 1e-12
    # The value equals a(B): numeric integral of X's best reply against the call threshold.
    for bb in (0.5, 1.0, 2.0, 4.0):
        aa = bb / ((bb + 1) * (bb + 4))
        cc = bb * (bb + 3) / ((bb + 1) * (bb + 4))
        g = (np.arange(400_000) + 0.5) / 400_000
        bet_val = np.where(g < cc, cc - (1 - cc) * (1 + bb), cc + (1 + bb) * (2 * g - cc - 1))
        assert abs(np.maximum(bet_val, 2 * g - 1).mean() - aa) < 1e-4
    # The value in the formula a(B) peaks at a bet of 2.
    g = np.linspace(0.01, 10, 10_000)
    assert abs(g[(g / ((g + 1) * (g + 4))).argmax()] - 2) < 0.002
    assert abs(2 / (3 * 6) - 1 / 9) < 1e-12
    # Simulation of the two rules.
    rng = np.random.default_rng(20)
    n = 2_000_000
    x, y = rng.random(n), rng.random(n)
    bets = (x < a) | (x > b)
    calls = y > c
    sign = np.where(x > y, 1, -1)
    pay = np.where(~bets, sign, np.where(calls, 2 * sign, 1))
    assert abs(pay.mean() - 0.1) < 0.002
