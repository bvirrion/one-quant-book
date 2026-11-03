"""Played Games: every number printed in the scripts, by exact enumeration, then a seeded simulation."""
import math
import pathlib
import re
import sys
from fractions import Fraction as F
from itertools import permutations, product

import numpy as np
import sympy as sp

ROOT = pathlib.Path(__file__).resolve().parents[4]
GEN = ROOT / "parts" / "interviews-2" / "generated"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import gen_lookup  # noqa: E402

NONNUMERIC = {}

CARDS = range(1, 11)
DEALS = list(permutations(CARDS, 3))  # (A, B, C): 720 equally likely ordered deals


def value_b(c):
    """The other player's value of the sum at the start, having seen only card B = c."""
    return c + 2 * F(55 - c, 9)


def round2(x):
    return round(float(x), 2)


def mean(xs):
    xs = list(xs)
    return F(sum(xs), len(xs))


def test_q1():
    # The opening fair value, and the table of the other player's values.
    assert mean(a + b + c for a, b, c in DEALS) == F(33, 2)
    table = {c: round2(value_b(c)) for c in CARDS}
    assert table == {1: 13.0, 2: 13.78, 3: 14.56, 4: 15.33, 5: 16.11, 6: 16.89, 7: 17.67, 8: 18.44, 9: 19.22, 10: 20.0}
    assert all(value_b(c) == F(7 * c + 110, 9) for c in CARDS)

    # Round 1: quote 15.5-17.5 and get hit, so B is 1 to 4, and the sum's value falls to 14.17.
    bid, ask = F(31, 2), F(35, 2)
    sells = [c for c in CARDS if value_b(c) < bid]
    assert sells == [1, 2, 3, 4]
    assert [c for c in CARDS if value_b(c) > ask] == [7, 8, 9, 10]
    fv1 = mean(a + b + c for a, b, c in DEALS if b in sells)
    assert fv1 == mean(value_b(c) for c in sells)
    assert round2(fv1) == 14.17

    # On average, over all deals, that first quote loses to a player who knows one card.
    pnl = []
    for a, b, c in DEALS:
        s = a + b + c
        if value_b(b) < bid:
            pnl.append(s - bid)
        elif value_b(b) > ask:
            pnl.append(ask - s)
        else:
            pnl.append(F(0))
    assert round2(mean(pnl)) == -1.07
    assert round2(fv1 - bid) == -1.33
    assert F(8, 10) * (fv1 - bid) == mean(pnl)

    # Round 2: quote 13-15; no trade rules out card 4 only. Fair value 13.78.
    left = [c for c in sells if F(13) <= value_b(c) <= F(15)]
    assert left == [1, 2, 3]
    assert round2(mean(value_b(c) for c in left)) == 13.78

    # Round 3: A = 9. The naive value ignores what the trades said.
    naive = 9 + 2 * F(55 - 9, 9)
    assert round2(naive) == 19.22
    v = {c: 9 + c + F(55 - 9 - c, 8) for c in left}
    assert {c: float(x) for c, x in v.items()} == {1: 15.625, 2: 16.5, 3: 17.375}
    fv3 = mean(a + b + c for a, b, c in DEALS if a == 9 and b in left)
    assert fv3 == F(33, 2)
    assert all(F(31, 2) <= x <= F(35, 2) for x in v.values())  # the 15.5-17.5 quote cannot separate them
    # The follow-up: a one-wide quote at 16-17 separates all three, for 0.25 on average.
    assert v[1] < 16 and 16 <= v[2] <= 17 and v[3] > 17
    assert mean([v[1] - 16, F(0), 17 - v[3]]) == F(-1, 4)
    assert v[1] - 16 == F(-3, 8)

    # Round 4: C = 6. Public value 15 + B: 16, 17 or 18, fair 17. A pass at 16.5-17.5 leaves only 17.
    assert mean(a + b + c for a, b, c in DEALS if a == 9 and c == 6 and b in left) == 17
    assert [15 + c for c in left if F(33, 2) <= 15 + c <= F(35, 2)] == [17]
    assert 9 + 2 + 6 == 17
    assert 17 - F(31, 2) == F(3, 2)

    # The candidate who ignores the trades: quotes around the public value, to the nearest half.
    fv4 = F(15) + F(55 - 15, 8)
    assert fv4 == 20
    bids = [F(31, 2), F(31, 2), F(18), F(39, 2)]
    their = [value_b(2), value_b(2), v[2], F(17)]
    assert all(b > t for b, t in zip(bids, their, strict=True))
    assert sum(17 - b for b in bids) == F(-1, 2)

    # The printed tables are the generator's, and each cell obeys the rule.
    for number, (value, width, low, high) in gen_lookup.ROUNDS.items():
        text = (GEN / f"game-1-round-{number}.tex").read_text(encoding="utf-8")
        cells = re.findall(r"\\ivcell\{([\d.]+)\}\{([SBP])\}", text)
        assert len(cells) == 2 * (high - low) + 1
        for b, r in cells:
            b = F(b)
            want = "S" if b > value else "B" if b + width < value else "P"
            assert r == want
    assert gen_lookup.ROUNDS[1][0] == value_b(2) and gen_lookup.ROUNDS[3][0] == v[2]

    # Seeded simulation of the fair value once B is known to be 1 to 4.
    rng = np.random.default_rng(1)
    sums = []
    for _ in range(200_000):
        a, b, c = rng.permutation(10)[:3] + 1
        if b <= 4:
            sums.append(a + b + c)
    assert abs(np.mean(sums) - float(fv1)) < 0.02


def call(u):
    return max(u - 8, 0)


def put(u):
    return max(8 - u, 0)


DICE = list(product(range(1, 7), repeat=2))


def slope(payoff, base):
    """Least-squares hedge ratio of a payoff against one die, for a die d added to base."""
    xs = range(1, 7)
    ys = [payoff(base + d) for d in xs]
    my, mx = mean(ys), F(7, 2)
    return sum((F(y) - my) * (x - mx) for x, y in zip(xs, ys, strict=True)) / sum((x - mx) ** 2 for x in xs)


def test_q2():
    # Opening values and parity.
    c0, p0 = mean(call(a + b) for a, b in DICE), mean(put(a + b) for a, b in DICE)
    assert c0 == F(5, 9) and round2(c0) == 0.56
    assert p0 == F(14, 9) and round2(p0) == 1.56
    assert c0 - p0 == 7 - 8
    assert F(4 * 1 + 3 * 2 + 2 * 3 + 1 * 4, 36) == c0
    assert 10 * (F(7, 10) - c0) == F(13, 9) and round2(F(13, 9)) == 1.44

    assert 10 * call(12) == 40

    # The delta before any die: slope of the value after die 1 against die 1 is 1/3.
    after = {d: mean(call(d + e) for e in range(1, 7)) for d in range(1, 7)}
    assert after == {1: 0, 2: 0, 3: F(1, 6), 4: F(1, 2), 5: 1, 6: F(5, 3)}
    xs = range(1, 7)
    delta0 = sum((after[x] - c0) * (x - F(7, 2)) for x in xs) / sum((x - F(7, 2)) ** 2 for x in xs)
    assert delta0 == F(1, 3)
    assert mean(call(a + b) > 0 for a, b in DICE) == F(5, 18) and round2(F(5, 18)) == 0.28

    # After die 1 = 5: marks and hedge.
    assert after[5] == 1
    assert mean(put(5 + e) for e in xs) == F(1, 2)
    assert 10 * (F(7, 10) - 1) + 3 * (F(17, 2) - F(71, 10)) == F(12, 10)
    delta5 = slope(call, 5)
    assert delta5 == F(22, 35) and round2(delta5) == 0.63
    assert round(10 * delta5) == 6

    # The parity arbitrage: sell the call at 1.10, buy the put at 0.40, buy the future at 8.60.
    for u in range(2, 13):
        assert F(110, 100) - F(40, 100) - call(u) + put(u) + u - F(860, 100) == F(1, 10)
        # The opposite trade locks in a loss.
        assert -F(125, 100) + F(30, 100) + call(u) - put(u) - u + F(840, 100) == F(-55, 100)
    assert 1 - F(1, 2) == F(17, 2) - 8

    # The model path's P&L by die 2, without the arbitrage.
    def book(d2):
        u = 5 + d2
        return F(700, 100) - 10 * call(u) + 3 * (u - F(710, 100)) + 3 * (u - F(860, 100))

    by = {d: book(d) for d in xs}
    assert {d: round(float(v), 1) for d, v in by.items()} == {1: -4.1, 2: 1.9, 3: 7.9, 4: 3.9, 5: -0.1, 6: -4.1}
    # Line by line, at settlement U = 7.
    lines = [F(7), 5 * F(110, 100), 5 * (1 - F(40, 100)), 3 * (7 - F(710, 100)), 3 * (7 - F(860, 100)),
             5 * (7 - F(860, 100))]
    assert [round2(x) for x in lines] == [7.0, 5.5, 3.0, -0.3, -4.8, -8.0]
    assert sum(lines) == F(240, 100)
    assert lines[1] + lines[2] + lines[5] == F(1, 2)
    assert lines[0] + lines[3] + lines[4] == F(19, 10) == by[2]

    # The three hedging policies over all 36 outcomes, including what the spreads cost.
    def stats(values):
        m = mean(values)
        var = mean((v - m) ** 2 for v in values)
        return round2(m), round(float(var) ** 0.5, 2)

    none, static, dynamic = [], [], []
    for a, b in DICE:
        u = a + b
        short = F(7) - 10 * call(u)
        none.append(short)
        static.append(short + 3 * (u - F(710, 100)))
        fut = F(2 * a + 7, 2)  # the future's fair value after die 1
        trade = round(10 * slope(call, a)) - 3
        price = fut + F(1, 10) if trade > 0 else fut - F(1, 10)
        dynamic.append(short + 3 * (u - F(710, 100)) + trade * (u - price))
    assert stats(none) == (1.44, 10.39)
    assert stats(static) == (1.14, 6.62)
    assert stats(dynamic) == (0.84, 3.77)

    # Seeded simulation of the opening values.
    rng = np.random.default_rng(2)
    u = rng.integers(1, 7, 400_000) + rng.integers(1, 7, 400_000)
    assert abs(np.maximum(u - 8, 0).mean() - float(c0)) < 0.01
    assert abs(np.maximum(8 - u, 0).mean() - float(p0)) < 0.01


TEN = range(1, 11)


def first_price(a, bid, rival=lambda b: b + 1):
    """Expected profit of a sealed bid when the winner pays their own bid and a tie goes to the rival."""
    return mean((a + b - bid) if bid > rival(b) else F(0) for b in TEN)


def second_price(a, bid, rival=lambda b: 2 * b):
    """Expected profit when the winner pays the loser's bid and a tie goes to the rival."""
    return mean((a + b - rival(b)) if bid > rival(b) else F(0) for b in TEN)


def test_q3():
    bids = [F(i, 2) for i in range(41)]
    # Round 1: die 8. The naive value, and the best bid against a rival who bids B + 1.
    assert 8 + F(11, 2) == F(27, 2)
    best = max(bids, key=lambda b: first_price(8, b))
    assert best == F(17, 2) and first_price(8, best) == F(49, 20)
    assert sum(1 for b in bids if first_price(8, b) == first_price(8, best)) == 1
    row = {b: first_price(8, F(b)) for b in (6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 13.5)}
    assert [round2(x) for x in row.values()] == [2.25, 2.4, 2.45, 2.4, 2.25, 2.0, 0.0]
    wins = {b: mean(F(b) > x + 1 for x in TEN) for b in row}
    assert [float(x) for x in wins.values()] == [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0]
    assert mean(x for x in TEN if F(17, 2) > x + 1) == 4
    assert 8 + 4 == 12 and 8 + 3 == 11 and 3 + 1 == 4
    assert 11 - F(17, 2) == F(5, 2) and 11 - F(27, 2) == F(-5, 2)

    # Round 2: die 3, second price, rival bids 2B. Every bid in (4, 6] is best, and 6 is twice the die.
    top = max(second_price(3, b) for b in bids)
    assert top == F(3, 10) and second_price(3, F(6)) == top
    assert second_price(3, F(17, 2)) == F(1, 5)
    assert 3 + F(11, 2) == F(17, 2)
    assert 3 + 4 == 7 and 2 * 4 == 8 and 7 - 8 == -1
    assert 3 + 3 - 2 * 3 == 0

    # Round 3: die 8, rising price, the same payoff as round 2.
    top3 = max(second_price(8, b) for b in bids)
    assert top3 == F(14, 5) and second_price(8, F(16)) == top3
    assert second_price(8, F(27, 2)) == F(27, 10)
    assert 2 * 7 == 14 and 8 + 7 == 15 and 15 - 14 == 1
    assert F(27, 2) < 14 < 16

    # Round 4: die 5. No look: bid 5.5. A look: bid B + 1.5 and always clear 3.5.
    no_look = max(bids, key=lambda b: first_price(5, b))
    assert no_look == F(11, 2) and first_price(5, no_look) == F(4, 5)
    assert mean(x for x in TEN if F(11, 2) > x + 1) == F(5, 2)
    assert all(5 + b - (b + F(3, 2)) == F(7, 2) for b in TEN)
    assert F(7, 2) - F(4, 5) == F(27, 10)
    assert F(7, 2) - 2 == F(3, 2)
    assert 5 + 6 == 11 and 11 - F(15, 2) == F(7, 2)
    assert first_price(5, F(21, 2)) == F(-9, 20)
    assert 11 - F(21, 2) == F(1, 2)

    # Settlement: this deal and the averages.
    model = [F(5, 2), F(0), F(1), F(3, 2)]
    naive = [F(-5, 2), F(-1), F(0), F(1, 2)]
    assert sum(model) == 5 and sum(naive) == -3 and sum(model) - sum(naive) == 8
    average_model = [first_price(8, F(17, 2)), second_price(3, F(6)), second_price(8, F(16)), F(3, 2)]
    average_naive = [first_price(8, F(27, 2)), second_price(3, F(17, 2)), second_price(8, F(27, 2)), first_price(5, F(21, 2))]
    assert sum(average_model) == F(141, 20) and float(sum(average_model)) == 7.05
    assert sum(average_naive) == F(49, 20) and float(sum(average_naive)) == 2.45

    # The printed tables: every cell against the rule, the rival's bid from the dice dealt.
    assert gen_lookup.AUCTION == {1: F(3 + 1), 2: F(2 * 4), 3: F(2 * 7)}
    for number, rival in gen_lookup.AUCTION.items():
        text = (GEN / f"game-3-round-{number}.tex").read_text(encoding="utf-8")
        cells = re.findall(r"\\ivcell\{([\d.]+)\}\{([WL])\}", text)
        assert len(cells) == 41
        for b, r in cells:
            assert r == ("W" if F(b) > rival else "L")

    # The continuous follow-up: best responses on dice uniform on 0 to 1.
    a, x, b = sp.symbols("a x b", positive=True)
    first = sp.integrate(a + x - b, (x, 0, b))
    assert sp.solve(sp.diff(first, b), b) == [a]
    second = sp.integrate(a + x - 2 * x, (x, 0, b / 2))
    assert sp.solve(sp.diff(second, b), b) == [2 * a]

    # Seeded simulation of round 1 at the best bid.
    rng = np.random.default_rng(3)
    die = rng.integers(1, 11, 500_000)
    assert abs(np.where(8.5 > die + 1, 8 + die - 8.5, 0.0).mean() - 2.45) < 0.01
    assert abs(np.where(6 > 2 * die, 3 - die, 0.0).mean() - 0.3) < 0.01


def test_generated_tables_match_the_generator(tmp_path):
    gen_lookup.write(tmp_path)
    for path in tmp_path.iterdir():
        assert path.read_text(encoding="utf-8") == (GEN / path.name).read_text(encoding="utf-8")


def argbest(g, lo, hi, n=400001):
    grid = np.linspace(lo, hi, n)
    return float(grid[g(grid).argmax()])


def growth4(s):
    """Expected log growth per round of game 4, for stakes s."""
    return (
        0.6 * math.log1p(s[0]) + 0.4 * math.log1p(-s[0]),
        math.log1p(4 * s[1]) / 6 + 5 * math.log1p(-s[1]) / 6,
        0.45 * math.log1p(2 * s[2]) + 0.55 * math.log1p(-s[2]),
        0.36 * math.log1p(2 * s[3]) + 0.16 * math.log1p(-2 * s[3]),
        0.9 * math.log1p(s[4]) + 0.1 * math.log1p(-5 * s[4]),
    )


def test_q4():
    # Each model stake is the maximiser of expected log growth.
    assert abs(argbest(lambda f: 0.6 * np.log1p(f) + 0.4 * np.log1p(-f), 0, 0.9) - 0.2) < 1e-4
    assert argbest(lambda f: np.log1p(4 * f) / 6 + 5 * np.log1p(-f) / 6, 0, 0.9) == 0
    assert abs(argbest(lambda f: 0.45 * np.log1p(2 * f) + 0.55 * np.log1p(-f), 0, 0.9) - 0.175) < 1e-4
    # A stated payout is profit. Read as the total returned, round 3 is even money at 45% and no bet at all.
    assert argbest(lambda f: 0.45 * np.log1p(f) + 0.55 * np.log1p(-f), 0, 0.9) == 0
    f4 = argbest(lambda f: 0.36 * np.log1p(2 * f) + 0.16 * np.log1p(-2 * f), 0, 0.49)
    assert round(f4, 3) == 0.192 and abs(f4 - 5 / 26) < 1e-5
    # The same coin twice is one bet at 20 percent, split in two.
    assert abs(argbest(lambda f: 0.6 * np.log1p(2 * f) + 0.4 * np.log1p(-2 * f), 0, 0.49) - 0.1) < 1e-4
    assert abs(argbest(lambda f: 0.9 * np.log1p(f) + 0.1 * np.log1p(-5 * f), 0, 0.199) - 0.08) < 1e-4
    assert round(0.4 / (0.9 + 2.5 - 0.16), 3) == 0.123
    # Maximising expected money: every bet with positive value at the largest stake that owes nothing.
    values = {1: 0.6 - 0.4, 2: 4 / 6 - 5 / 6, 3: 0.45 * 2 - 0.55, 4: 0.6 - 0.4, 5: 0.9 - 0.1 * 5}
    assert [k for k, v in values.items() if v > 0] == [1, 3, 4, 5]
    assert 1 - 5 * 0.2 == 0 and 1 - 5 * 0.21 < 0  # round 5 cannot go past 20% without borrowing

    def run(s):
        w = 1000 * (1 - s[0])
        w *= 1 + 4 * s[1]
        w *= 1 + 2 * s[2]
        # Round 4: one coin wins and one loses on the same stake, so it nets to zero.
        return w * (1 + s[4])

    model, half = [0.2, 0, 0.175, 0.19, 0.08], [0.1, 0, 0.0875, 0.095, 0.04]
    reckless = [0.4, 0.2, 0.35, 0.38, 0.16]
    assert round(run(model), 2) == 1166.40 and round(run(half)) == 1100 and round(run(reckless)) == 2130
    assert [round(sum(growth4(s)), 3) for s in (model, half, reckless)] == [0.107, 0.079, -0.141]
    assert round(1 - math.exp(-0.141), 2) == 0.13
    # The path: 800, 800, 1080, 1080, then the stake and the finish.
    assert 1000 * 0.8 == 800 and round(800 * 0.175) == 140 and round(1080 * 0.19) == 205 and round(1080 * 0.08) == 86
    # Half-Kelly keeps about three quarters of the growth.
    assert 0.70 < sum(growth4(half)) / sum(growth4(model)) < 0.80
    # An overestimated edge at full Kelly: at half the edge, a small-bet approximation has zero growth.
    assert abs(15 * 0.075 - 0.5 * 15 * 15 * 0.01) < 1e-12


def score5(bid, ask, n):
    s = -math.log2(ask / bid)
    if n > ask:
        s -= 4 * math.log2(n / ask)
    if n < bid:
        s -= 4 * math.log2(bid / n)
    return s


def test_q5():
    nums = [
        int(sp.primepi(1000)),
        len(str(math.factorial(100))),
        math.comb(52, 5),
        sum(sp.prime(i) for i in range(1, 101)),
        sum(map(int, str(2**100))),
    ]
    assert nums == [168, 158, 2598960, 24133, 115]
    model = [(150, 180), (155, 160), (2.5e6, 2.7e6), (21000, 25000), (129, 150)]
    scores = [score5(*q, n) for q, n in zip(model, nums, strict=True)]
    assert [round(x, 2) for x in scores] == [-0.26, -0.05, -0.11, -0.25, -0.88]
    assert round(sum(scores), 2) == -1.55
    # Routes printed.
    assert round(1000 / math.log(1000)) == 145
    assert round(100 * math.log10(100 / math.e), 1) == 156.6 and round(0.5 * math.log10(2 * math.pi * 100), 1) == 1.4
    assert round(sp.prime(100)) == 541 and round(100 * math.log(100)) == 461
    assert round(100 * math.log10(2), 1) == 30.1 and len(str(2**100)) == 31
    digit = np.arange(10)
    assert digit.mean() == 4.5 and digit.var() == 8.25 and round(math.sqrt(31 * 8.25)) == 16
    assert round(31 * 4.5, 1) == 139.5 and round(float(sp.N(sp.erfinv(0.5) * sp.sqrt(2))), 2) == 0.67
    # Wide and tight players.
    wide = [(100, 200), (100, 200), (2e6, 4e6), (2e4, 4e4), (100, 200)]
    assert [round(score5(*q, n), 2) for q, n in zip(wide, nums, strict=True)] == [-1.0] * 5
    centres = [165, 157.5, 2.6e6, 23000, 139.5]
    tight = [score5(c * 0.99, c * 1.01, n) for c, n in zip(centres, nums, strict=True)]
    assert [round(x, 2) for x in tight] == [-0.08, -0.03, -0.03, -0.25, -1.09]
    assert round(sum(tight), 2) == -1.47
    # Expected score under a normal belief, in units of sigma. Exact, and by simulation.
    from scipy.stats import norm

    def exp_score(w):
        return -(2 * w + 8 * (norm.pdf(w) - w * norm.sf(w)))

    assert [round(exp_score(w), 2) for w in (float(norm.ppf(0.75)), 0.0, 2.0)] == [-2.54, -3.19, -4.07]
    grid = np.linspace(0, 3, 3001)
    assert abs(grid[np.argmax([exp_score(w) for w in grid])] - norm.ppf(0.75)) < 0.002
    z = np.random.default_rng(5).standard_normal(1_000_000)
    w = float(norm.ppf(0.75))
    sim = -(2 * w + 4 * np.maximum(np.abs(z) - w, 0)).mean()
    assert abs(sim - exp_score(w)) < 0.01
    # A penalty of 20 asks for the 5 percent tail on each side.
    cost20 = [2 * x + 2 * 20 * (norm.pdf(x) - x * norm.sf(x)) for x in grid]
    assert abs(grid[int(np.argmin(cost20))] - norm.ppf(0.95)) < 0.002


V6 = F(35, 12)


def var6(x, y, shared=True):
    if shared:
        return (x * x + y * y) * 2 * V6 + 2 * x * y * V6
    return (x * x + y * y) * V6


def test_q6():
    dice = list(product(range(1, 7), repeat=3))
    xs = [a + b for a, b, c in dice]
    ys = [a + c for a, b, c in dice]
    n = len(dice)
    assert F(sum(xs), n) == 7 and F(sum(v * v for v in xs), n) - 49 == 2 * V6
    assert F(sum(u * v for u, v in zip(xs, ys, strict=True)), n) - 49 == V6

    # Round 1: search every position up to 3 lots either way.
    def score1(x, y):
        ex = F(1, 2) * -x if x < 0 else -x * 1
        ey = F(1, 2) * y if y > 0 else y * 1
        return ex + ey - F(1, 10) * var6(x, y)

    best = max(product(range(-3, 4), repeat=2), key=lambda p: score1(*p))
    assert best == (-1, 1) and round2(score1(-1, 1)) == 0.42 and round2(score1(-2, 2)) == -0.33
    assert round2(score1(-1, 0)) == -0.08 and round2(score1(0, 1)) == -0.08

    # Round 2: position long 2 X, long 1 Y, only Y quoted.
    table = {y: (abs(y - 1) * F(1, 4), var6(2, y)) for y in (1, 0, -1, -2)}
    assert [round(float(v), 1) for _, v in table.values()] == [40.8, 23.3, 17.5, 23.3]
    assert [round2(c + v / 10) for c, v in table.values()] == [4.08, 2.58, 2.25, 3.08]
    assert min(range(-3, 2), key=lambda y: abs(y - 1) * F(1, 4) + var6(2, y) / 10) == -1

    # Round 3: A is known, so the two are independent.
    assert round(float(var6(2, -1, False)), 1) == 14.6 and round(float(var6(2, 0, False)), 1) == 11.7
    assert min(range(-3, 3), key=lambda y: abs(y + 1) * F(1, 10) + var6(2, y, False) / 10) == 0
    assert round(float(V6 / 10), 2) == 0.29

    # Settlement, from the dice 2, 5, 6.
    x_s, y_s = 2 + 5, 2 + 6
    cash = F(15, 2) - F(13, 2) - 18 + F(27, 2) - F(28, 5)
    assert float(cash) == -9.1 and float(cash + 2 * x_s) == 4.9
    no_hedge = 3 * (x_s - 6)
    assert no_hedge == 3
    lot = F(15, 2) - F(13, 2) - 18 + 3 * F(27, 4) + 2 * x_s - 2 * y_s
    assert float(lot) == 1.25
    # Edges and variances for the table.
    assert float(1 + 3 - 2 * F(1, 4) - F(1, 10)) == 3.4 and float(1 + 3 - 3 * F(1, 4)) == 3.25
    assert round(float(var6(2, -1)), 1) == 17.5 and round(float(var6(3, 0)), 1) == 52.5
    assert round(float(var6(2, -2)), 1) == 23.3
    assert round(float(F(49, 10) - F(17, 5)), 2) == 1.5
    # The hedge ratio by regression, and a spread doubles the Sharpe.
    assert float(V6 / (2 * V6)) == 0.5
    v = lambda x, y: float(var6(x, y))  # noqa: E731
    assert abs((1 / math.sqrt(v(-1, 1))) / (0.5 / math.sqrt(v(-1, 0))) - 2) < 1e-12


def odds7(k):
    o = F(7, 3) ** k
    return o / (1 + o) * 100


def ev7(k):
    p, up, dn = odds7(k), odds7(k + 1), odds7(k - 1)
    q = p / 100 * F(7, 10) + (1 - p / 100) * F(3, 10)
    return q, 3 - (q * max(up - p - 3, 0) + (1 - q) * max(p - dn - 3, 0)), q * (up - p) + (1 - q) * (p - dn)


def test_q7():
    assert [round(float(odds7(k)), 1) for k in range(5)] == [50.0, 70.0, 84.5, 92.7, 96.7]
    assert [round(float(ev7(k)[2]), 1) for k in range(5)] == [20.0, 16.8, 10.5, 5.4, 2.5]
    assert [round(float(ev7(k)[1]), 1) for k in range(5)] == [-14.0, -10.8, -4.5, 0.6, 2.7]
    assert float(ev7(1)[0]) == 0.58 and round(float((F(7, 3)) ** 2), 2) == 5.44
    # Enumeration of round 2 by the two flips, and the martingale check at every state.
    for k in range(5):
        q, _, _ = ev7(k)
        assert q * odds7(k + 1) + (1 - q) * odds7(k - 1) == odds7(k)
    # The result of a quote in this deal.
    path = [0, 1, 2, 3, 2, 3]  # value index before round 2, then after each flip

    def result(prev, new):
        p, v = float(odds7(prev)), float(odds7(new))
        return 3 - max(abs(v - p) - 3, 0)

    r5 = result(3, 2)
    assert round(float(odds7(3)) - 3, 1) == 89.7 and round(float(odds7(3) - 3 - odds7(2)), 2) == 5.22 and round(r5, 2) == -2.22
    model = 3 + r5
    assert round(model, 2) == 0.78
    always = 3 + sum(result(a, b) for a, b in zip(path, path[1:], strict=False))
    assert round(always, 2) == -26.14
    assert round(3 + float(ev7(3)[1]), 2) == 3.59
    exp_always = 3 + sum(float(ev7(k)[1]) for k in (0, 1, 2, 3, 2))
    assert round(exp_always, 2) == -30.19
    # Simulation of the fair value after three heads.
    rng = np.random.default_rng(7)
    good = rng.random(2_000_000) < 0.5
    h = rng.binomial(3, np.where(good, 0.7, 0.3))
    assert abs(good[h == 3].mean() * 100 - float(odds7(3))) < 0.5


LIM8, H8, PEN8, T8 = 2, 2, 4, 5
VALUES8 = list(range(94, 107))


def step8(pos, m, cont):
    total = F(0)
    for v in VALUES8:
        if v > m + H8 and pos > -LIM8:
            total += (m + H8 - 100) + cont(pos - 1)
        elif v < m - H8 and pos < LIM8:
            total += (100 - (m - H8)) + cont(pos + 1)
        else:
            total += cont(pos)
    return total / len(VALUES8)


def solve8():
    value = {(T8, p): F(-PEN8 * abs(p)) for p in range(-LIM8, LIM8 + 1)}
    policy = {}
    for t in range(T8 - 1, -1, -1):
        for p in range(-LIM8, LIM8 + 1):
            options = {m: step8(p, m, lambda q, t=t: value[(t + 1, q)]) for m in range(94, 107)}
            best = max(options.values())
            ties = [m for m, x in options.items() if x == best]
            value[(t, p)] = best
            policy[(t, p)] = min(ties, key=lambda m: (abs(m - 100), m))
    return value, policy


def test_q8():
    value, policy = solve8()
    assert round(float(value[(0, 0)]), 2) == 1.63
    want = {
        0: [100, 101, 100, 99, 100],
        1: [100, 101, 100, 99, 100],
        2: [100, 101, 100, 99, 100],
        3: [101, 101, 100, 99, 99],
        4: [101, 102, 100, 98, 99],
    }
    for t, row in want.items():
        assert [policy[(t, p)] for p in range(-2, 3)] == row

    # The no-lean player.
    flat = {(T8, p): F(-PEN8 * abs(p)) for p in range(-LIM8, LIM8 + 1)}
    for t in range(T8 - 1, -1, -1):
        for p in range(-LIM8, LIM8 + 1):
            flat[(t, p)] = step8(p, 100, lambda q, t=t: flat[(t + 1, q)])
    assert round(float(flat[(0, 0)]), 2) == 1.13

    # The deal: customers at 95, 96, 94, 102, 101.
    def play(centres):
        pos, cash = 0, 0
        for v, c in zip((95, 96, 94, 102, 101), centres, strict=True):
            m = c(pos) if callable(c) else c
            if v > m + H8 and pos > -LIM8:
                cash += m + H8 - 100
                pos -= 1
            elif v < m - H8 and pos < LIM8:
                cash += 100 - (m - H8)
                pos += 1
        return cash - PEN8 * abs(pos), pos

    assert play([policy[(t, 0)] if t == 0 else (lambda p, t=t: policy[(t, p)]) for t in range(5)]) == (6, 0)
    assert play([100] * 5) == (-4, 2)
    # A simulation of the expected value of the policy.
    rng = np.random.default_rng(8)
    total = 0.0
    n = 40_000
    for _ in range(n):
        pos, cash = 0, 0
        for t in range(T8):
            m = policy[(t, pos)]
            v = 94 + int(rng.integers(13))
            if v > m + H8 and pos > -LIM8:
                cash += m + H8 - 100
                pos -= 1
            elif v < m - H8 and pos < LIM8:
                cash += 100 - (m - H8)
                pos += 1
        total += cash - PEN8 * abs(pos)
    assert abs(total / n - float(value[(0, 0)])) < 0.05


def straddle9(x, jumps=(6, 10)):
    """Value of the straddle from distance x, with all small moves still to come, averaged over the jump."""
    return mean(F(abs(x + e)) for j in jumps for e in (j, -j))


def test_q9():
    us = [-2, 0, 0, 2]
    value = mean(abs(u + e) for u in us for j in (6, 10) for e in (j, -j))
    assert value == 8
    assert mean(abs(u + e) for u in us for e in (6, -6)) == 6 and mean(abs(u + e) for u in us for e in (10, -10)) == 10
    var = mean((u + e) ** 2 for u in us for j in (6, 10) for e in (j, -j))
    assert var == 70 and round(math.sqrt(70), 1) == 8.4 and round(0.8 * math.sqrt(70), 1) == 6.7
    # A normal with the same variance really has the 0.8 rule: the rule fails on this shape only.
    z = np.random.default_rng(9).standard_normal(1_000_000) * math.sqrt(70)
    assert abs(np.abs(z).mean() - 0.7979 * math.sqrt(70)) < 0.02
    # Round 2: at 101, with one small move left, the value and so the delta are unchanged.
    v101 = mean(abs(1 + u + e) for u in (-1, 1) for j in (6, 10) for e in (j, -j))
    v99 = mean(abs(-1 + u + e) for u in (-1, 1) for j in (6, 10) for e in (j, -j))
    assert v101 == 8 and v99 == 8
    assert straddle9(1) == 8
    # Round 3.
    assert mean(abs(7 + u) for u in (-1, 1)) == 7
    # From 101, the value after each of the four announcements, and their average: no expected fall across the news.
    after = [mean(abs(1 + e + u) for u in (-1, 1)) for e in (6, -6, 10, -10)]
    assert after == [7, 5, 11, 9] and mean(after) == 8
    # Settlement.
    paid = 2 * F(15, 2)
    model = 2 * abs(106 - 100) + 2 * (107 - 106) - paid
    assert model == -1 and 2 * abs(106 - 100) - paid == -3
    seller = 2 * 7 - 2 * abs(106 - 100)
    assert seller == 2
    assert 2 * (8 - F(15, 2)) == 1 and 2 * (7 - 8) == -2
    # The same deal with J = 10: stock 111 after the news, then 110; shares sold at 111.
    assert 2 * abs(110 - 100) + 2 * (111 - 110) - paid == 7
    assert 2 * 7 - 2 * abs(110 - 100) == -6


def post10(q1, q2=None):
    """The chance of each die of C, given C's first and optional second centre less 16.5."""
    weights = {}
    for d in range(1, 11):
        w = F(1, 10)
        for q in (q1, q2):
            if q is not None:
                w *= sum(F(1, 3) for n in (-3, 0, 3) if d + n == q)
        if w:
            weights[d] = w
    total = sum(weights.values())
    return {d: w / total for d, w in weights.items()}


def test_q10():
    assert 7 + 3 * F(11, 2) == F(47, 2)
    assert F(39, 2) - F(33, 2) == 3 and F(43, 2) - F(33, 2) == 5
    assert 7 + 3 + 5 + F(11, 2) == F(41, 2)
    assert post10(6) == {3: F(1, 3), 6: F(1, 3), 9: F(1, 3)}
    assert sum(d * w for d, w in post10(6).items()) == 6
    assert 7 + 3 + 5 + 6 == 21 and F(41, 2) + F(1, 2) == 21
    assert post10(6, 0) == {3: F(1)}
    assert 7 + 3 + 5 + 3 == 18
    # Trades.
    model = (21 - 20) + (22 - 17)
    assert model == 6
    own = sum(18 - p for p in (20, 22, 23, 17))
    assert own == -10
    assert F(1) + 1 + 1 == 3
    edge_own = (F(41, 2) - 20) + (F(41, 2) - 22) + (21 - 23) + (18 - 17)
    assert edge_own == -2
    # Simulation of C's quotes.
    rng = np.random.default_rng(10)
    die = rng.integers(1, 11, 3_000_000)
    n1, n2 = rng.choice([-3, 0, 3], (2, 3_000_000))
    keep = die + n1 == 6
    assert abs(die[keep].mean() - 6) < 0.02
    keep2 = keep & (die + n2 == 0)
    assert set(die[keep2].tolist()) == {3}


def w11(lots, rounds):
    q, r = divmod(lots, rounds)
    return F(1, 2) * ((rounds - r) * q * q + r * (q + 1) ** 2)


def choice11(lots, rounds, f, k):
    return F(1, 2) * k * k + (lots - k) * f + w11(lots - k, rounds - 1)


def test_q11():
    f = F(3, 2)
    assert [float(choice11(6, 4, f, k)) for k in (2, 3, 4)] == [11.0, 10.5, 12.0]
    assert min(range(7), key=lambda k: choice11(6, 4, f, k)) == 3
    assert [float(x) for x in (F(1, 2) * 4, 4 * f, w11(4, 3))] == [2.0, 6.0, 3.0]
    assert [float(x) for x in (F(9, 2), 3 * f, w11(3, 3))] == [4.5, 4.5, 1.5]
    assert [float(x) for x in (F(8), 2 * f, w11(2, 3))] == [8.0, 3.0, 1.0]
    assert min(range(4), key=lambda k: choice11(3, 3, F(0), k)) == 1
    assert min(range(3), key=lambda k: choice11(2, 2, F(-2), k)) == 0
    assert float(choice11(2, 2, F(-2), 1)) == -1 and float(choice11(2, 2, F(-2), 0)) == -2

    # Prices of the deal: 100, 102.5, 101.5, 100.5.
    prices = [F(100), F(205, 2), F(203, 2), F(201, 2)]
    assert prices[1] == 100 + F(3, 2) + 1 and prices[2] == prices[1] + 0 - 1 and prices[3] == prices[2] - 2 + 1

    def cost(lots, ps=prices):
        return sum(k * p + F(1, 2) * k * k for k, p in zip(lots, ps, strict=True))

    assert [float(cost(x)) for x in ((3, 1, 0, 2), (2, 2, 1, 1), (6, 0, 0, 0), (0, 0, 0, 6))] == [610.5, 612.0, 618.0, 621.0]
    # Expected, with the epsilons averaged out, so the prices are 100, 101.5, 101.5, 99.5.
    drift = [F(100), F(203, 2), F(203, 2), F(199, 2)]
    assert [float(cost(x, drift)) for x in ((3, 1, 0, 2), (2, 2, 1, 1), (6, 0, 0, 0), (0, 0, 0, 6))] == [607.5, 609.0, 618.0, 615.0]
    assert 0.5 * 36 == 18
    # Second route for round 1: search every split, knowing only the first forecast.
    known = [F(100), F(203, 2), F(203, 2), F(203, 2)]
    splits = [s for s in product(range(7), repeat=4) if sum(s) == 6]
    assert cost(min(splits, key=lambda s: (cost(s, known), -s[0])), known) == F(1221, 2)
    assert min(splits, key=lambda s: (cost(s, known), -s[0]))[0] == 3


PS12 = (F(1, 2), F(11, 20), F(2, 5), F(3, 5))


def win12(t, g, cache={}):  # noqa: B006
    if t == 4:
        return F(1) if g > 0 else F(0)
    if (t, g) not in cache:
        cache[(t, g)] = max(stake12(t, g, s) for s in range(5))
    return cache[(t, g)]


def stake12(t, g, s):
    return PS12[t] * win12(t + 1, g + s) + (1 - PS12[t]) * win12(t + 1, g - s)


def run12(policy):
    """Chance of finishing ahead, and the expected final gap, for a policy of (round, gap) -> stake."""
    states = {-3: F(1)}
    for t in range(4):
        new = {}
        for g, p in states.items():
            s = policy(t, g)
            for g2, w in ((g + s, PS12[t]), (g - s, 1 - PS12[t])):
                new[g2] = new.get(g2, F(0)) + p * w
        states = new
    return sum(p for g, p in states.items() if g > 0), sum(g * p for g, p in states.items())


def test_q12():
    assert [round(float(stake12(0, -3, s)), 3) for s in range(5)] == [0.658, 0.607, 0.629, 0.611, 0.665]
    assert max(range(5), key=lambda s: stake12(0, -3, s)) == 4
    assert round(float(stake12(1, -7, 4)), 2) == 0.33 and round(float(stake12(1, -7, 0)), 2) == 0.24
    assert [round(float(stake12(1, -7, s)), 3) for s in (1, 2, 3)] == [0.132, 0.132, 0.132]
    assert round(0.55 * 0.60, 2) == 0.33 and round(0.40 * 0.60, 2) == 0.24 and round(0.55 * 0.40 * 0.60, 3) == 0.132
    # Winning all three without a single full stake is possible: full stakes are not the only way.
    assert -7 + 3 + 3 + 2 == 1
    # After a stake below 4 that loses, even two full wins fall short.
    assert all(-7 - s + 8 <= 0 for s in (1, 2, 3))
    assert max(range(5), key=lambda s: stake12(1, -7, s)) == 4
    assert float(stake12(2, -3, 0)) == 0.6 and float(stake12(2, -3, 4)) == 0.4
    assert max(range(5), key=lambda s: stake12(2, -3, s)) == 0
    assert float(stake12(3, -3, 3)) == 0 and float(stake12(3, -3, 4)) == 0.6
    assert float(stake12(3, 1, 0)) == 1 and float(stake12(3, 1, 4)) == 0.6

    def model(t, g):
        return max(range(5), key=lambda s: (stake12(t, g, s), -s))

    win, gap = run12(model)
    assert round(float(win), 3) == 0.665 and round(float(gap), 2) == -2.58
    win, gap = run12(lambda t, g: 4 if PS12[t] > F(1, 2) else 0)
    assert round(float(win), 3) == 0.330 and round(float(gap), 2) == -1.80
    win, gap = run12(lambda t, g: 1)
    assert round(float(win), 3) == 0.066 and round(float(gap), 2) == -2.90
    # This deal: lose, win, no stake, win. Most points has no stake, win, no stake, win.
    assert -3 - 4 + 4 + 0 + 4 == 1 and -3 + 4 + 4 == 5 and -3 - 1 + 1 - 1 + 1 == -3
    # Being one ahead, staking nothing wins outright.
    assert win12(0, 1) == 1
