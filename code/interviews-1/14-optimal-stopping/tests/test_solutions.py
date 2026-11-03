"""Every number printed in the answers of "Optimal Stopping": backward induction, then a seeded simulation."""
import math
from fractions import Fraction as Fr
from functools import lru_cache
from itertools import product

import numpy as np

NONNUMERIC = {}


def die_value(k, sides=6):
    """Value of a die with k re-rolls left."""
    v = Fr(sides + 1, 2)
    for _ in range(k):
        v = sum(max(Fr(x), v) for x in range(1, sides + 1)) / sides
    return v


def test_q1():
    assert die_value(1) == Fr(17, 4)
    assert die_value(2) == Fr(14, 3)
    # With many re-rolls the value tends to 6, the top face.
    assert abs(float(die_value(60)) - 6) < 1e-3
    rng = np.random.default_rng(1)
    d = rng.integers(1, 7, (1_000_000, 2))
    pay = np.where(d[:, 0] >= 4, d[:, 0], d[:, 1])
    assert abs(pay.mean() - 4.25) < 0.005


def test_q2():
    v = [Fr(1, 2)]
    for _ in range(3):
        v.append((1 + v[-1] ** 2) / 2)
    assert v[1:] == [Fr(5, 8), Fr(89, 128), Fr(24305, 32768)]
    assert round(float(v[2]), 3) == 0.695
    assert round(float(v[3]), 3) == 0.742
    rng = np.random.default_rng(2)
    u = rng.random((1_000_000, 2))
    assert abs(np.where(u[:, 0] >= 0.5, u[:, 0], u[:, 1]).mean() - 0.625) < 0.001
    # Fixed point of v = (1 + v^2) / 2 is 1, the top of the range.
    assert (1 + 1**2) / 2 == 1


def test_q3():
    n = 100
    total = n * (n + 1) // 2
    keep = [x for x in range(1, n + 1) if x >= Fr(total - x, n - 1)]
    assert keep[0] == 51
    val = sum(max(Fr(x), Fr(total - x, n - 1)) for x in range(1, n + 1)) / n
    assert round(float(val), 2) == 63.13
    assert abs(float(val) - (3775 + 252500 / 99 - 1275 / 99) / 100) < 1e-9
    rng = np.random.default_rng(3)
    order = np.argsort(rng.random((200_000, n)), axis=1)[:, :2] + 1
    assert abs(np.where(order[:, 0] >= 51, order[:, 0], order[:, 1]).mean() - float(val)) < 0.05


def test_q4():
    @lru_cache(None)
    def win(r, b):
        if r + b == 1:
            return Fr(r)
        stop = Fr(r, r + b)
        go = Fr(r, r + b) * win(r - 1, b) if r else Fr(0)
        go += Fr(b, r + b) * win(r, b - 1) if b else 0
        return max(stop, go)

    assert win(26, 26) == Fr(1, 2)
    # Every state is indifferent: stopping and continuing agree.
    for r, b in ((26, 1), (1, 26), (5, 9), (13, 2)):
        assert win(r, b) == Fr(r, r + b)
    # A skewed start keeps the same value as its red fraction.
    assert win(10, 30) == Fr(1, 4)


def test_q5():
    def win(n, skip):
        if skip == 0:
            return Fr(1, n)
        return Fr(skip, n) * sum(Fr(1, k) for k in range(skip, n))

    assert win(3, 1) == Fr(1, 2)
    assert win(3, 0) == win(3, 2) == Fr(1, 3)
    best = max(range(10), key=lambda s: win(10, s))
    assert best == 3
    assert round(float(win(10, 3)), 3) == 0.399
    best1000 = max(range(1, 1000), key=lambda s: win(1000, s))
    assert abs(best1000 / 1000 - 1 / math.e) < 0.002
    assert abs(float(win(1000, best1000)) - 1 / math.e) < 0.001
    # Backward induction, with no assumption about the rule's form.
    n = 10
    v = Fr(0)
    for k in range(n, 0, -1):
        v = Fr(1, k) * max(Fr(k, n), v) + Fr(k - 1, k) * v
    assert v == win(10, 3)
    rng = np.random.default_rng(5)
    x = rng.random((400_000, 10))
    bar = x[:, :3].max(axis=1)
    later = x[:, 3:]
    above = later > bar[:, None]
    first = above.argmax(axis=1)
    has = above.any(axis=1)
    chosen = later[np.arange(len(x)), first]
    assert abs((has & (chosen == x.max(axis=1))).mean() - float(win(10, 3))) < 0.003


def test_q6():
    c = 0.02
    t = 1 - math.sqrt(2 * c)
    assert abs(t - 0.8) < 1e-12
    assert abs((1 - t) ** 2 / 2 - c) < 1e-12
    assert abs(1 / (1 - t) - 5) < 1e-9
    assert abs((1 + t) / 2 - 5 * c - t) < 1e-12
    rng = np.random.default_rng(6)
    draws = rng.geometric(0.2, 400_000)
    pay = 0.8 + 0.2 * rng.random(400_000) - c * draws
    assert abs(pay.mean() - 0.8) < 0.002
    # Cost 1/2 is the point where the game is worth nothing; cost 0 gives threshold 1.
    assert 1 - math.sqrt(2 * 0.5) == 0
    assert 1 - math.sqrt(0) == 1
    # Grid search on the threshold agrees.
    grid = np.linspace(0, 0.99, 991)
    val = (1 + grid) / 2 - c / (1 - grid)
    assert abs(grid[val.argmax()] - 0.8) < 0.002


def test_q7():
    vals = {t: Fr(sum(range(t, 21)), 21 - t) - (Fr(20, 21 - t) - 1) for t in range(1, 21)}
    best = max(vals, key=vals.get)
    assert best == 15
    assert vals[15] == Fr(91, 6)
    assert round(float(vals[15]), 2) == 15.17
    # Value iteration: w = E max(k, w - 1).
    w = 10.0
    for _ in range(500):
        w = sum(max(k, w - 1) for k in range(1, 21)) / 20
    assert abs(w - 91 / 6) < 1e-9
    # Limit: a free re-roll gets the top face, and a huge cost keeps the first roll.
    assert vals[20] == 20 - 19
    assert vals[1] == Fr(21, 2)
    rng = np.random.default_rng(7)
    rolls = rng.geometric(6 / 20, 400_000)
    pay = rng.integers(15, 21, 400_000) - (rolls - 1)
    assert abs(pay.mean() - 91 / 6) < 0.02


def test_q8():
    d = 0.8
    v = (1 - math.sqrt(1 - d**2)) / d**2
    assert abs(v - 0.625) < 1e-12
    assert abs(d * v - 0.5) < 1e-12
    assert abs((1 + (d * v) ** 2) / 2 - v) < 1e-12
    assert abs(1 / (1 - d * v) - 2) < 1e-9
    x = 0.3
    for _ in range(300):
        x = (1 + (d * x) ** 2) / 2
    assert abs(x - 0.625) < 1e-9
    # Limits: delta 0 takes the first offer, value one half; delta 1 waits for the top.
    assert (1 + 0) / 2 == 0.5
    assert (1 - math.sqrt(1 - 1)) / 1 == 1
    rng = np.random.default_rng(8)
    days = rng.geometric(0.5, 500_000)
    pay = (0.5 + 0.5 * rng.random(500_000)) * d ** (days - 1)
    assert abs(pay.mean() - 0.625) < 0.001
    # Waiting for the value itself: a threshold of 0.625 is worth only 0.609.
    def worth(t):
        return (1 - t * t) / 2 / (1 - t * d)

    assert abs(worth(0.625) - 0.609375) < 1e-12 and worth(0.625) < worth(0.5)
    assert abs(worth(0.5) - 0.625) < 1e-12
    # The threshold equals the mean offer only at this delta.
    for other in (0.6, 0.9):
        assert abs(other * (1 - math.sqrt(1 - other**2)) / other**2 - 0.5) > 0.1


def test_q9():
    @lru_cache(None)
    def val(s):
        if s >= 40:
            return Fr(s)
        go = sum(val(s + k) for k in range(1, 6)) / 6
        return max(Fr(s), go)

    v0 = float(val(0))
    assert round(v0, 2) == 6.15
    for s in range(1, 40):
        stops = val(s) == s
        if s < 15:
            assert not stops
        if s > 15:
            assert stops
    assert Fr(5, 6) * 15 + Fr(15, 6) == 15
    rng = np.random.default_rng(9)
    pay = np.zeros(300_000)
    alive = np.ones(300_000, dtype=bool)
    total = np.zeros(300_000)
    for _ in range(40):
        go = alive & (total < 15)
        if not go.any():
            break
        r = rng.integers(1, 7, go.sum())
        idx = np.nonzero(go)[0]
        alive[idx[r == 6]] = False
        total[idx] += np.where(r == 6, 0, r)
    pay = np.where(alive, total, 0)
    assert abs(pay.mean() - v0) < 0.03
    # The rule reaches 15 about 38% of the time, and every other path ends at 0.
    @lru_cache(None)
    def reach(s):
        return Fr(1) if s >= 15 else sum(reach(s + k) for k in range(1, 6)) / 6

    assert round(float(reach(0)), 3) == 0.378
    assert abs((total[alive] >= 15).mean() - 1) < 1e-12
    assert abs(alive.mean() - float(reach(0))) < 0.003
    assert (pay[~alive] == 0).all()


def test_q10():
    @lru_cache(None)
    def plain(n, s):
        if n == 0:
            return Fr(s)
        return max(Fr(s), (plain(n - 1, s + 1) + plain(n - 1, s - 1)) / 2)

    @lru_cache(None)
    def floored(n, s):
        if n == 0:
            return Fr(max(s, 0))
        return max(Fr(max(s, 0)), (floored(n - 1, s + 1) + floored(n - 1, s - 1)) / 2)

    assert plain(4, 0) == 0
    assert floored(4, 0) == Fr(3, 4)
    # Never stops early at a positive position: continuing gives the same value.
    for n, s in ((3, 1), (2, 2), (1, 3)):
        assert floored(n, s) == (floored(n - 1, s + 1) + floored(n - 1, s - 1)) / 2
    # Second route: E[S_4^+] from the binomial law.
    assert sum(Fr(math.comb(4, h), 16) * max(2 * h - 4, 0) for h in range(5)) == Fr(3, 4)
    # With many flips it grows like sqrt(n / (2 pi)).
    n = 400
    exact = sum(math.exp(math.lgamma(n + 1) - math.lgamma(h + 1) - math.lgamma(n - h + 1) - n * math.log(2)) * max(2 * h - n, 0) for h in range(n + 1))
    assert abs(exact / math.sqrt(n / (2 * math.pi)) - 1) < 0.01
    # Every rule scored on all 16 paths, with the floor: stopping at 2 costs nothing, and stopping at 1 costs 1/8.
    def rule_value(stop_at):
        total = Fr(0)
        for path in product((1, -1), repeat=4):
            s = 0
            for step in path:
                s += step
                if s >= stop_at:
                    break
            total += max(s, 0)
        return total / 16

    assert rule_value(99) == rule_value(2) == Fr(3, 4) and rule_value(1) == Fr(5, 8)
    assert floored(3, 1) == Fr(5, 4) and floored(2, 2) == 2


def test_q11():
    no_report = 0.5 * 100 - 40
    assert no_report == 10
    post_yes = 0.8 * 0.5 / (0.8 * 0.5 + 0.2 * 0.5)
    assert abs(post_yes - 0.8) < 1e-12
    v_yes = post_yes * 100 - 40
    v_no = max(0.2 * 100 - 40, 0)
    assert abs(v_yes - 40) < 1e-9 and v_no == 0
    v_report = 0.5 * v_yes + 0.5 * v_no
    assert abs(v_report - 20) < 1e-9
    assert abs(v_report - no_report - 10) < 1e-9
    assert 0.5 * 60 - no_report == 20
    # A report that would not change the decision is worth nothing, right or not.
    for acc, worth in ((0.5, 0.0), (0.6, 0.0), (0.7, 5.0), (0.9, 15.0), (1.0, 20.0)):
        vy = acc * 100 - 40
        vn = max((1 - acc) * 100 - 40, 0)
        assert abs(0.5 * max(vy, 0) + 0.5 * vn - 10 - worth) < 1e-9


def test_q12():
    @lru_cache(None)
    def val(h, t, left):
        if left == 0:
            return Fr(0)
        p = Fr(h + 1, h + t + 2)
        b = p * (1 + val(h + 1, t, left - 1)) + (1 - p) * val(h, t + 1, left - 1)
        a = Fr(1, 2) + val(h, t, left - 1)
        return max(a, b)

    assert val(0, 0, 2) == Fr(13, 12)
    assert val(0, 0, 3) == Fr(5, 3)
    assert val(0, 0, 1) == Fr(1, 2)
    rng = np.random.default_rng(12)
    p = rng.random(1_000_000)
    first = rng.random(1_000_000) < p
    second = np.where(first, rng.random(1_000_000) < p, rng.random(1_000_000) < 0.5)
    assert abs((first.astype(float) + second).mean() - 13 / 12) < 0.003


def test_q13():
    t = math.sqrt(2) - 1
    assert abs((1 - t**2) / 2 - t) < 1e-12
    v0 = t * math.exp(t)
    assert round(v0, 3) == 0.627
    assert round(t, 3) == 0.414
    rng = np.random.default_rng(13)
    n = 1_000_000
    total = np.zeros(n)
    live = np.ones(n, dtype=bool)
    for _ in range(40):
        go = live & (total < t)
        if not go.any():
            break
        total[go] += rng.random(go.sum())
        live &= total <= 1
    assert abs(np.where(live, total, 0).mean() - v0) < 0.002
    grid = np.linspace(0.01, 0.99, 981)
    # Value of threshold s: e^s times the worth at the boundary, which averages over x in [s, 1].
    worth = np.exp(grid) * (1 - grid**2) / 2
    assert abs(grid[worth.argmax()] - t) < 0.002
    assert abs(worth.max() - v0) < 1e-4


def test_q14():
    @lru_cache(None)
    def val(r, b):
        if r == 0:
            return Fr(0)
        if b == 0:
            return Fr(r)
        go = Fr(r, r + b) * (1 + val(r - 1, b)) + Fr(b, r + b) * (val(r, b - 1) - 1)
        return max(Fr(0), go)

    assert val(1, 1) == Fr(1, 2)
    assert val(2, 2) == Fr(2, 3)
    assert round(float(val(26, 26)), 2) == 2.62
    assert val(1, 0) == 1 and val(0, 3) == 0
    assert val(2, 1) == Fr(4, 3)
    assert val(1, 2) == 0
    assert Fr(1, 2) * (1 + val(1, 2)) + Fr(1, 2) * (val(2, 1) - 1) == Fr(2, 3)
    # A prophet stops at the walk's top: about 4.5 on a full deck, and it matches sqrt(pi n / 8).
    rng = np.random.default_rng(14)
    deck = np.argsort(rng.random((100_000, 52)), axis=1) < 26
    walk = np.cumsum(2 * deck.astype(np.int8) - 1, axis=1)
    top = np.maximum(walk.max(axis=1), 0).mean()
    assert abs(top - 4.0) < 0.1
    # A simulation of the backward-induction rule agrees with the exact value.
    stop_at = {(r, b): val(r, b) == 0 for r in range(27) for b in range(27)}
    pay = np.zeros(20_000)
    for i in range(20_000):
        r, b, s = 26, 26, 0
        for card in deck[i]:
            if stop_at[(r, b)]:
                break
            s += 1 if card else -1
            r -= int(card)
            b -= int(not card)
        pay[i] = s
    assert abs(pay.mean() - float(val(26, 26))) < 0.06


def test_q15():
    def by_induction(p, xmax=80):
        """Backward induction with no assumed rule: the value at each x and the spaces worth taking."""
        q = 1 - p
        v = [q / p]
        take = [True]
        for x in range(1, xmax + 1):
            take.append(x <= v[x - 1])
            v.append(p * min(x, v[x - 1]) + q * v[x - 1])
        return v, take

    p, q = Fr(1, 10), Fr(9, 10)
    v, take = by_induction(p)
    # The rule: exactly the spaces within 6 units are taken, and that is q^x >= 1/2.
    assert [x for x, t in enumerate(take) if t] == list(range(7))
    assert all(t == (q**x >= Fr(1, 2)) for x, t in enumerate(take) if x)
    # Before the limit the walk has settled: being further away changes nothing.
    assert v[6] == v[80]
    assert round(float(v[6]), 2) == 6.57
    assert round(0.9**6, 3) == 0.531 and round(0.9**7, 3) == 0.478

    # The closed form with limit r, against the printed values of other limits.
    def limit_value(r, pp=p):
        qq = 1 - pp
        return r + (2 * qq ** (r + 1) - qq) / pp

    assert limit_value(6) == v[6]
    assert round(float(limit_value(5)), 2) == 6.63
    assert round(float(limit_value(7)), 2) == 6.61
    assert round(float(limit_value(10)), 2) == 7.28
    assert limit_value(0) == q / p == 9
    assert min(range(0, 40), key=limit_value) == 6

    # Limit cases and other chances: the rule matches the induction.
    for pp in (Fr(1, 4), Fr(1, 3), Fr(1, 20)):
        w, t = by_induction(pp, 200)
        rule = [x for x in range(1, 201) if (1 - pp) ** x >= Fr(1, 2)]
        assert [x for x in range(1, 201) if t[x]] == rule
        assert w[200] == limit_value(rule[-1] if rule else 0, pp)
    # A certain space: you drive to the restaurant and walk nothing.
    assert limit_value(0, Fr(1)) == 0

    # A simulation of the rule on a long street.
    rng = np.random.default_rng(15)
    n = 400_000
    free = rng.random((n, 7)) < 0.1  # the spaces at 6, 5, ..., 0 units before
    first = np.where(free.any(axis=1), free.argmax(axis=1), -1)
    walk = np.where(first >= 0, 6.0 - first, rng.geometric(0.1, n).astype(float))
    assert abs(walk.mean() - float(v[6])) < 0.05


def test_q16():
    def value(n):
        return sum(Fr(1, n + 1) * abs(Fr(2 * (k + 1), n + 2) - 1) for k in range(n + 1))

    assert [value(n) for n in range(5)] == [0, Fr(1, 3), Fr(1, 3), Fr(2, 5), Fr(2, 5)]
    for n in range(1, 41, 2):
        assert value(n) == Fr(n + 1, 2 * (n + 2))
        assert value(n + 1) == value(n)
    assert abs(float(value(2001)) - 0.5) < 0.001
    # Limit: E|2p - 1| for p uniform.
    rng = np.random.default_rng(16)
    p = rng.random(2_000_000)
    assert abs(np.abs(2 * p - 1).mean() - 0.5) < 0.001
    first = rng.random(2_000_000) < p
    nxt = rng.random(2_000_000) < p
    assert abs(2 * (first == nxt).mean() - 1 - 1 / 3) < 0.002


def test_q17():
    t = 1 / math.sqrt(3)
    w = (1 + t - t**3) / 3
    assert round(t, 3) == 0.577
    assert round(w, 3) == 0.462
    rng = np.random.default_rng(17)
    n = 3_000_000
    a1, a2 = rng.random(n), rng.random(n)
    a = np.where(a1 >= t, a1, a2)
    b1, b2 = rng.random(n), rng.random(n)
    b = np.where(b1 > a, b1, b2)
    assert abs((a > b).mean() - w) < 0.001
    grid = np.linspace(0, 1, 1001)
    win = (1 + grid - grid**3) / 3
    assert abs(grid[win.argmax()] - t) < 0.001
    assert abs((1 + 0 - 0) / 3 - 1 / 3) < 1e-12
    # A sure 1 wins: x^2 at x = 1 is 1. No redraw allowed for B would change x^2 to x.


def test_q18():
    p = 0.1
    n = 30
    q = 1 - p
    # Backward induction on v = best win chance from trial k on.
    v = 0.0
    for k in range(n, 0, -1):
        v = p * max(q ** (n - k), v) + q * v
    assert abs(v - q**9) < 1e-12
    assert round(v, 3) == 0.387
    # Win chance when you accept any success in the last s trials: s p q^(s-1).
    win_last = {s: s * p * q ** (s - 1) for s in (8, 9, 10, 11)}
    assert abs(win_last[9] - win_last[10]) < 1e-12
    assert win_last[8] < win_last[9] and win_last[11] < win_last[9]
    assert round(win_last[8], 3) == 0.383
    # Odds rule: the last s trials with odds sum reaching 1.
    assert abs(9 * (p / q) - 1) < 1e-12
    rng = np.random.default_rng(18)
    x = rng.random((500_000, n)) < p
    last = x[:, -9:]
    win = last.sum(axis=1) == 1
    assert abs(win.mean() - v) < 0.002
    # Secretary: trial k succeeds (a new record) with p_k = 1/k; odds 1/(k-1).
    s = 0.0
    k = 10
    while s < 1:
        s += 1 / (k - 1)
        k -= 1
    assert k == 3


def sum_first_lead(terms):
    total = 0.0
    prob = 0.5
    for m in range(terms):
        total += prob
        prob *= (2 * m + 1) / (2 * m + 4)
    return total


def test_q19():
    # Stopping as soon as heads lead: first lead at flip 2m + 1 has chance C_m / 2^(2m+1).
    v = 0.0
    prob = 0.5
    for m in range(0, 200_000):
        v += prob * (m + 1) / (2 * m + 1)
        prob *= (2 * m + 1) / (2 * m + 4)
    remaining = 1 - sum_first_lead(200_000)
    assert abs(v + 0.5 * remaining - math.pi / 4) < 1e-4
    # Lower bound: a head on the first flip pays 1, and from any state you can get back to about 1/2.
    assert 0.5 * 1 + 0.5 * 0.5 == 0.75

    # Backward induction from a far horizon, with a low and a high terminal guess.
    def solve(horizon, extra):
        val = np.maximum(np.arange(horizon + 1) / horizon, 0.5 + extra / math.sqrt(horizon))
        table = {}
        for n in range(horizon - 1, 0, -1):
            stop = np.arange(n + 1) / n
            go = 0.5 * (val[: n + 1] + val[1: n + 2])
            if n <= 6:
                table[n] = go.copy()
            if n == 1000:
                table["lead"] = 2 * np.nonzero(stop >= go)[0][np.nonzero(stop >= go)[0] >= n / 2][0] - n
            val = np.maximum(stop, go)
        return 0.5 * (val[0] + val[1]), table

    low, table = solve(5000, 0.0)
    high, _ = solve(5000, 0.42)
    assert 0.7925 < low <= high < 0.7936
    assert round(low, 3) == 0.793 and round(high, 3) == 0.793
    assert low > math.pi / 4
    assert abs(table["lead"] / math.sqrt(1000) - 0.84) < 0.06
    # After 3 flips with 2 heads, going on beats stopping at 2/3, by a hair.
    assert round(table[3][2], 3) == 0.669 and table[3][2] > 2 / 3
    # Level at 2 flips and behind are always continued, and the first head is taken.
    assert table[2][1] > 1 / 2 and table[1][1] < 1


def test_q20():
    # The bad example: 1 for sure, then 1/eps with chance eps.
    eps = 1e-3
    prophet = eps * (1 / eps) + (1 - eps) * 1
    assert abs(prophet - (2 - eps)) < 1e-12
    gambler = max(1.0, eps * (1 / eps))
    assert abs(gambler - 1.0) < 1e-12
    # The guarantee, on random instances: threshold E[max]/2 earns at least half.
    rng = np.random.default_rng(20)
    for _ in range(30):
        n = rng.integers(2, 7)
        vals = rng.exponential(5, n) ** 2
        probs = rng.random(n)
        draws = (rng.random((200_000, n)) < probs) * vals
        emax = draws.max(axis=1).mean()
        t = emax / 2
        hit = draws >= t
        first = hit.argmax(axis=1)
        pay = np.where(hit.any(axis=1), draws[np.arange(len(draws)), first], 0)
        assert pay.mean() >= 0.5 * emax - 0.02 * emax
    # Median threshold works too, on a continuous example.
    x = rng.exponential(size=(500_000, 5))
    mx = x.max(axis=1)
    t = np.median(mx)
    hit = x >= t
    pay = np.where(hit.any(axis=1), x[np.arange(len(x)), hit.argmax(axis=1)], 0)
    assert pay.mean() >= 0.5 * mx.mean()
