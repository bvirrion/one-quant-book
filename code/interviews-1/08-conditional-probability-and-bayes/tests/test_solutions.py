"""Every number printed in the answers of "Conditional Probability and Bayes": exact, then a seeded simulation."""
import itertools
import math
from fractions import Fraction as F

import numpy as np
from scipy import integrate, stats

C = math.comb
NONNUMERIC = {}


def test_q1():
    kids = list(itertools.product("BG", repeat=2))
    told = [k for k in kids if "G" in k]
    assert F(sum(k == ("G", "G") for k in told), len(told)) == F(1, 3)
    # Meet a random child: enumerate family and which child.
    pairs = [(k, i) for k in kids for i in range(2) if k[i] == "G"]
    assert F(sum(k == ("G", "G") for k, _ in pairs), len(pairs)) == F(1, 2)
    rng = np.random.default_rng(1)
    fam = rng.integers(0, 2, (500_000, 2))
    atleast = fam.sum(axis=1) >= 1
    assert abs((fam.sum(axis=1)[atleast] == 2).mean() - 1 / 3) < 0.003
    pick = rng.integers(0, 2, 500_000)
    girl = fam[np.arange(500_000), pick] == 1
    assert abs((fam.sum(axis=1)[girl] == 2).mean() - 1 / 2) < 0.003


def test_q2():
    p = F(1, 100) * F(99, 100) / (F(1, 100) * F(99, 100) + F(99, 100) * F(5, 100))
    assert p == F(1, 6)
    assert F(1, 99) * (F(99, 100) / F(5, 100)) == F(1, 5)  # odds 1:5
    # Prevalence 100%: the update has nothing to do. Perfect specificity: a positive is proof.
    assert F(1) * F(99, 100) / (F(1) * F(99, 100)) == 1
    assert F(1, 100) * F(99, 100) / (F(1, 100) * F(99, 100) + 0) == 1
    rng = np.random.default_rng(2)
    ill = rng.random(4_000_000) < 0.01
    pos = np.where(ill, rng.random(4_000_000) < 0.99, rng.random(4_000_000) < 0.05)
    assert abs(ill[pos].mean() - 1 / 6) < 0.003


def monty(rng, runs, doors=3):
    car = rng.integers(0, doors, runs)
    pick = rng.integers(0, doors, runs)
    return (car != pick).mean()


def test_q3():
    rng = np.random.default_rng(3)
    assert abs(monty(rng, 500_000) - 2 / 3) < 0.003
    assert abs(monty(rng, 500_000, 100) - 0.99) < 0.002
    # Exact: enumerate car and host's choice, with the host's random pick weighted.
    win = F(0)
    for car in range(3):
        doors = [d for d in range(3) if d not in (0, car)]
        for h in doors:
            other = next(d for d in range(3) if d not in (0, h))
            win += F(1, 3) * F(1, len(doors)) * (other == car)
    assert win == F(2, 3)


def test_q4():
    post = F(1, 100) / (F(1, 100) + F(99, 100) * F(1, 2**10))
    assert post == F(1024, 1123)
    assert round(float(post), 3) == 0.912
    assert F(1, 99) * 1024 == F(1024, 99)
    rng = np.random.default_rng(4)
    two = rng.random(8_000_000) < 0.01
    heads = np.where(two, True, rng.random(8_000_000) < 1 / 1024)
    assert abs(two[heads].mean() - float(post)) < 0.006
    # After no flips the belief is the prior; each head doubles the odds.
    assert F(1, 100) / (F(1, 100) + F(99, 100)) == F(1, 100)
    assert F(1, 99) * 2**7 > 1 > F(1, 99) * 2**6


def test_q5():
    faces = [("R", "R"), ("R", "R"), ("R", "B"), ("B", "R"), ("B", "B"), ("B", "B")]
    seen = [f for f in faces if f[0] == "R"]
    assert F(sum(f[1] == "R" for f in seen), len(seen)) == F(2, 3)
    rng = np.random.default_rng(5)
    side = rng.integers(0, 6, 500_000)
    arr = np.array([[f[0] == "R", f[1] == "R"] for f in faces])
    red = arr[side, 0]
    assert abs(arr[side, 1][red].mean() - 2 / 3) < 0.003


def test_q6():
    p = F(15, 100) * F(8, 10) / (F(15, 100) * F(8, 10) + F(85, 100) * F(2, 10))
    assert p == F(12, 29)
    assert round(float(p), 3) == 0.414
    assert F(15, 85) * 4 == F(12, 17)
    rng = np.random.default_rng(6)
    blue = rng.random(2_000_000) < 0.15
    says_blue = np.where(blue, rng.random(2_000_000) < 0.8, rng.random(2_000_000) < 0.2)
    assert abs(blue[says_blue].mean() - 12 / 29) < 0.003
    # A witness who is right half the time adds nothing.
    assert F(15, 100) * F(1, 2) / (F(15, 100) * F(1, 2) + F(85, 100) * F(1, 2)) == F(15, 100)
    # Mistaken reports about green taxis outnumber true reports about blue ones, 17 to 12.
    assert F(85, 100) * F(2, 10) == F(17, 100) and F(15, 100) * F(8, 10) == F(12, 100)


def test_q7():
    rolls = [r for r in itertools.product(range(1, 7), repeat=2) if 6 in r]
    assert len(rolls) == 11
    assert F(sum(r == (6, 6) for r in rolls), 11) == F(1, 11)
    assert F(sum(sum(r) == 7 for r in rolls), 11) == F(2, 11)
    # Told that the first die shows six: a different event.
    assert F(sum(r[0] == 6 and r[1] == 6 for r in rolls), sum(r[0] == 6 for r in rolls)) == F(1, 6)


def test_q8():
    assert (F(1, 2) * 1) / (F(1, 2) * 1 + F(1, 2) * F(1, 2)) == F(2, 3)
    rng = np.random.default_rng(8)
    first_red = rng.random(500_000) < 0.5
    drawn_red = first_red | (rng.random(500_000) < 0.5)
    assert abs(first_red[drawn_red].mean() - 2 / 3) < 0.003


def test_q9():
    # (who is pardoned, what the guard says); guard's choice when A is pardoned.
    a_b = F(1, 3) * F(1, 2)
    c_b = F(1, 3)
    assert a_b / (a_b + c_b) == F(1, 3) and c_b / (a_b + c_b) == F(2, 3)
    a_b = F(1, 3) * 1
    assert a_b / (a_b + c_b) == F(1, 2)
    # Guard who names C when he can: saying B means A cannot be the one pardoned.
    assert 0 / (F(0) + c_b) == 0
    rng = np.random.default_rng(9)
    who = rng.integers(0, 3, 600_000)
    coin = rng.random(600_000) < 0.5
    says_b = (who == 2) | ((who == 0) & coin)
    assert abs((who[says_b] == 0).mean() - 1 / 3) < 0.003


def test_q10():
    # First rule: the host opens at random and shows nothing.
    assert F(1, 3) * 1 / (F(1, 3) * 1 + F(2, 3) * F(1, 2)) == F(1, 2)
    # Second rule.
    car1, car2, car3 = F(1, 3), F(1, 3), F(1, 3)
    opens3 = car2  # only when the prize is behind door 2; he always prefers door 2
    assert opens3 / (opens3 + car1 * 0) == 1
    opens2 = car1 + car3
    assert car3 / opens2 == F(1, 2)
    # Averaged over what he does, switching still wins 2/3.
    assert opens3 * 1 + opens2 * F(1, 2) == F(2, 3)
    rng = np.random.default_rng(10)
    car = rng.integers(1, 4, 600_000)
    opened = rng.integers(2, 4, 600_000)
    ok = opened != car
    assert abs((car[ok] == 1).mean() - 1 / 2) < 0.003


def test_q11():
    kids = list(itertools.product(itertools.product("BG", range(7)), repeat=2))
    told = [k for k in kids if ("B", 2) in k]
    assert len(told) == 27
    assert F(sum(a[0] == "B" and b[0] == "B" for a, b in told), len(told)) == F(13, 27)
    assert 2 * 7 + 2 * 7 - 1 == 27 and 2 * 7 - 1 == 13
    # A more common fact, any day of the week: the answer falls back to one third.
    told = [k for k in kids if k[0][0] == "B" or k[1][0] == "B"]
    assert F(sum(a[0] == "B" and b[0] == "B" for a, b in told), len(told)) == F(1, 3)
    # Fixed to a rarer fact the answer climbs towards one half.
    days = 365
    assert abs(float(F(2 * days - 1, 4 * days - 1)) - 0.5) < 0.001
    rng = np.random.default_rng(11)
    b = rng.random((2_000_000, 2)) < 0.5
    d = rng.integers(0, 7, (2_000_000, 2))
    hit = (b & (d == 2)).any(axis=1)
    assert abs(b.all(axis=1)[hit].mean() - 13 / 27) < 0.006
    # A two-boy family contains a Tuesday boy 13/49 of the time, a one-boy family 7/49: nearly twice, not twice.
    days_two = list(itertools.product(range(7), repeat=2))
    assert F(sum(2 in d for d in days_two), 49) == F(13, 49)
    assert F(sum(a == 2 for a, _ in days_two), 49) == F(7, 49)
    # Exactly twice would have given one half.
    assert F(2 * 7, 2 * 7 + 2 * 7) == F(1, 2) != F(13, 13 + 14)


def test_q12():
    value, _ = integrate.quad(lambda p: p ** 8 * (1 - p) ** 3, 0, 1)
    norm, _ = integrate.quad(lambda p: p ** 7 * (1 - p) ** 3, 0, 1)
    assert abs(value / norm - 2 / 3) < 1e-9
    assert F(7 + 1, 10 + 2) == F(2, 3)
    assert F(0 + 1, 0 + 2) == F(1, 2)  # no data, the prior mean
    assert F(1, 3) == F(0 + 1, 1 + 2)  # after one tail
    rng = np.random.default_rng(12)
    p = rng.random(3_000_000)
    n = rng.binomial(10, p)
    keep = n == 7
    assert abs((rng.random(keep.sum()) < p[keep]).mean() - 2 / 3) < 0.004


def test_q13():
    biased = F(1, 2) * F(9, 16) / (F(1, 2) * F(9, 16) + F(1, 2) * F(1, 4))
    assert biased == F(9, 13)
    assert biased * F(3, 4) + (1 - biased) * F(1, 2) == F(35, 52)
    assert round(35 / 52, 3) == 0.673
    # A check that the update is not a straight average: with no flips the answer is 5/8.
    assert F(1, 2) * F(3, 4) + F(1, 2) * F(1, 2) == F(5, 8)
    rng = np.random.default_rng(13)
    p = np.where(rng.random(2_000_000) < 0.5, 0.75, 0.5)
    flips = rng.random((2_000_000, 3)) < p[:, None]
    keep = flips[:, 0] & flips[:, 1]
    assert abs(flips[keep, 2].mean() - 35 / 52) < 0.002


def test_q14():
    odds = F(1, 99) * 9 * 9
    assert odds == F(81, 99) == F(9, 11)
    assert odds / (1 + odds) == F(9, 20)
    third = odds * F(1, 9)
    assert third == F(1, 11)
    assert third / (1 + third) == F(1, 12)
    rng = np.random.default_rng(14)
    ill = rng.random(4_000_000) < 0.01
    t1, t2, t3 = rng.random((3, 4_000_000)) < 0.9
    p1, p2, p3 = np.where(ill, t1, ~t1), np.where(ill, t2, ~t2), np.where(ill, t3, ~t3)
    keep = p1 & p2
    assert abs(ill[keep].mean() - 0.45) < 0.01
    assert abs(ill[keep & ~p3].mean() - 1 / 12) < 0.01


def test_q15():
    a1, a2, b1, b2 = F(9, 10), F(30, 100), F(80, 100), F(2, 10)
    assert a1 > b1 and a2 > b2
    assert F(9 + 30, 110) == F(39, 110) and F(80 + 2, 110) == F(82, 110)
    assert F(39, 110) < F(82, 110)
    assert round(39 / 110, 2) == 0.35 and round(82 / 110, 2) == 0.75
    # If each strategy traded the same number each year, the reversal cannot happen.
    assert (a1 + a2) / 2 > (b1 + b2) / 2


def test_q16():
    real, fake = 50, 950
    tp, fp = real * F(8, 10), fake * F(5, 100)
    assert tp == 40 and fp == F(95, 2)
    assert tp / (tp + fp) == F(16, 35)
    assert round(16 / 35, 3) == 0.457
    # A stricter test: 1% with the same power.
    strict = tp / (tp + fake * F(1, 100))
    assert strict == F(40, 49 + F(1, 2)) and round(float(strict), 3) == 0.808
    # With no working signals, every flag is false.
    assert 0 / (0 + F(1000 * 5, 100)) == 0
    # A low base rate leaves most flags false at 5%, but a much stricter test changes that.
    assert tp / (tp + fp) < F(1, 2) < strict


def test_q17():
    odds = F(3, 2) ** 4
    assert float(odds) == 5.0625
    post = odds / (1 + odds)
    assert round(float(post), 3) == 0.835
    price = post * F(3, 5) + (1 - post) * F(2, 5)
    assert round(float(price), 3) == 0.567
    # Equal heads and tails: the price stays at one half.
    assert F(1, 2) * F(3, 5) + F(1, 2) * F(2, 5) == F(1, 2)
    rng = np.random.default_rng(17)
    p = np.where(rng.random(3_000_000) < 0.5, 0.6, 0.4)
    h = rng.binomial(10, p)
    keep = h == 7
    assert abs((rng.random(keep.sum()) < p[keep]).mean() - float(price)) < 0.003
    # Seven heads in ten fits both coins' world: likely under 0.6, likelier still under a 0.7 coin.
    pmf = lambda q: stats.binom.pmf(7, 10, q)  # noqa: E731
    assert round(float(pmf(0.6)), 3) == 0.215 and pmf(0.7) > pmf(0.6) > pmf(0.4)


def test_q18():
    w = {k: F(k * (k - 1), 4 * 3) for k in range(5)}
    assert [w[k] * 12 for k in range(5)] == [0, 0, 2, 6, 12]
    total = sum(w.values())
    nxt = sum(w[k] * F(k - 2, 2) for k in range(2, 5))
    assert nxt / total == F(3, 4) == F(2 + 1, 2 + 2)
    rng = np.random.default_rng(18)
    k = rng.integers(0, 5, 500_000)
    ball = rng.random((500_000, 4)).argsort(axis=1) < k[:, None]
    keep = ball[:, 0] & ball[:, 1]
    assert abs(ball[keep, 2].mean() - 0.75) < 0.003


def test_q19():
    others = (5_000_000 - 1) * 1e-6
    assert round(others) == 5
    assert abs(1 / (1 + others) - 1 / 6) < 1e-6
    # A scaled copy with the same ratio: 5,000 people, a match rate of one in a thousand.
    sim = np.random.default_rng(190)
    guilty = sim.random(6_000_000) < 1 / 5000
    match = guilty | (sim.random(6_000_000) < 1e-3)
    assert abs(guilty[match].mean() - 1 / 6) < 0.02
    # One suspect picked out by other evidence with an even prior: the match is near proof.
    assert 0.5 / (0.5 + 0.5 * 1e-6) > 0.99999
    rng = np.random.default_rng(19)
    others = rng.binomial(5_000_000 - 1, 1e-6, 500_000)
    assert abs((1 / (1 + others)).mean() - (1 - np.exp(-5)) / 5) < 0.002
    # The follow-up: test everyone, then pick one of the matchers at random.
    assert abs((1 - math.exp(-5)) / 5 - 0.1987) < 0.001


def test_q20():
    skilled = 0.1 * 0.7**5
    other = 0.9 * 0.5**5
    assert round(skilled, 4) == 0.0168 and round(other, 4) == 0.0281
    post = skilled / (skilled + other)
    assert round(post, 3) == 0.374
    assert round(post * 0.7 + (1 - post) * 0.5, 3) == 0.575
    rng = np.random.default_rng(20)
    good = rng.random(3_000_000) < 0.1
    wins = rng.binomial(5, np.where(good, 0.7, 0.5))
    assert abs(good[wins == 5].mean() - post) < 0.006
    # If skilled and unskilled had the same chance, the record would teach nothing.
    assert abs(0.1 * 0.5**5 / (0.1 * 0.5**5 + 0.9 * 0.5**5) - 0.1) < 1e-12


def test_q21():
    def profit(b, m):
        return b / 100 * (m * b / 2 - b)

    assert profit(40, 1.5) == 0.4 * (30 - 40) == -4.0
    assert max(profit(b, 1.5) for b in range(101)) == 0.0 == profit(0, 1.5)
    assert profit(100, 2.5) == 25.0 == max(profit(b, 2.5) for b in range(101))
    assert all(abs(profit(b, 2)) < 1e-12 for b in range(101))
    rng = np.random.default_rng(21)
    v = rng.random(4_000_000) * 100
    assert abs((np.where(v <= 40, 1.5 * v - 40, 0)).mean() + 4) < 0.05
    assert abs((np.where(v <= 100, 2.5 * v - 100, 0)).mean() - 25) < 0.1
    # The follow-up: positive bids earn something exactly when the multiple is above 2.
    assert all((profit(50, k) > 0) == (k > 2) for k in (1.5, 2, 2.01, 3))


def test_q22():
    p = F(1)
    for k in range(1, 11):
        p *= F(k, k + 1)
    assert p == F(1, 11)
    # Enumerate every colour sequence of length 10 exactly: exchangeable and uniform in the red count.
    def prob(seq):
        r, b, out = 1, 1, F(1)
        for c in seq:
            out *= F(r if c else b, r + b)
            r, b = r + c, b + 1 - c
        return out

    seqs = list(itertools.product((0, 1), repeat=10))
    assert sum(prob(s) for s in seqs) == 1
    red10 = sum(prob(s) for s in seqs if s[9])
    assert red10 == F(1, 2)
    assert sum(prob(s) for s in seqs if s[9] and s[0]) / red10 == F(2, 3)
    for k in range(11):
        assert sum(prob(s) for s in seqs if sum(s) == k) == F(1, 11)
    rng = np.random.default_rng(22)
    runs = 100_000
    first = tenth = both = 0
    for _ in range(runs):
        r, b = 1, 1
        seq = []
        for _ in range(10):
            c = rng.random() < r / (r + b)
            seq.append(c)
            r, b = r + c, b + (not c)
        first += seq[0]
        tenth += seq[9]
        both += seq[0] and seq[9]
    assert abs(both / tenth - 2 / 3) < 0.01


def test_q23():
    assert F(1, 3) != F(1, 4)
    value, _ = integrate.quad(lambda p: p * p, 0, 1)
    assert abs(value - 1 / 3) < 1e-12
    cov = F(1, 3) - F(1, 4)
    assert cov == F(1, 12)
    assert cov / F(1, 4) == F(1, 3)
    rng = np.random.default_rng(23)
    p = rng.random(2_000_000)
    a, b = rng.random((2, 2_000_000)) < p
    assert abs(np.corrcoef(a, b)[0, 1] - 1 / 3) < 0.002
    # A coin of known p has no correlation at all: nothing left to learn.
    a, b = rng.random((2, 2_000_000)) < 0.5
    assert abs(np.corrcoef(a, b)[0, 1]) < 0.003


def test_q24():
    rho = 0.5
    assert rho * 2 == 1.0 and 1 - rho**2 == 0.75
    assert abs(0.5 + math.asin(rho) / math.pi - 2 / 3) < 1e-12
    rng = np.random.default_rng(24)
    x, n = rng.normal(size=(2, 4_000_000))
    y = rho * x + math.sqrt(0.75) * n
    assert abs((y[x > 0] > 0).mean() - 2 / 3) < 0.002
    near = np.abs(x - 2) < 0.02
    assert abs(y[near].mean() - 1) < 0.03 and abs(y[near].var() - 0.75) < 0.03
    # Zero correlation brings it down to one half; perfect correlation up to one.
    assert 0.5 + math.asin(0) / math.pi == 0.5 and 0.5 + math.asin(1) / math.pi == 1
    assert round(math.sin(math.pi * 0.05), 2) == 0.16  # 55% sign agreement


def test_q25():
    weight = F(1, 9) / (F(1, 16) + F(1, 9))
    assert weight == F(16, 25)
    assert 100 + weight * 6 == F(2596, 25)
    assert float(100 + weight * 6) == 103.84
    assert 1 / (F(1, 16) + F(1, 9)) == F(144, 25)
    assert float(F(144, 25)) == 5.76
    assert abs(math.sqrt(5.76) - 2.4) < 1e-12
    rng = np.random.default_rng(25)
    v = rng.normal(100, 4, 4_000_000)
    s = v + rng.normal(0, 3, 4_000_000)
    near = np.abs(s - 106) < 0.05
    assert abs(v[near].mean() - 103.84) < 0.05 and abs(v[near].std() - 2.4) < 0.05
    # A perfect signal is believed fully; a useless one changes nothing.
    assert (1 / 1e-12) / (1 / 16 + 1 / 1e-12) > 0.999 and (1 / 1e12) / (1 / 16 + 1 / 1e12) < 1e-9


def test_q26():
    buy_high = F(1, 5) + F(4, 5) * F(1, 2)
    buy_low = F(4, 5) * F(1, 2)
    assert buy_high == F(3, 5) and buy_low == F(2, 5)
    post = F(1, 2) * buy_high / (F(1, 2) * buy_high + F(1, 2) * buy_low)
    assert post == F(3, 5)
    ask = 90 + 20 * post
    assert ask == 102
    assert 90 + 20 * (1 - post) == 98  # the bid, by symmetry
    post2 = post * buy_high / (post * buy_high + (1 - post) * buy_low)
    assert post2 == F(9, 13)
    assert round(float(90 + 20 * post2), 2) == 103.85
    # No informed traders: the ask is the mid. All informed: the ask is the top.
    assert 90 + 20 * (F(1, 2) * F(1, 2) / (F(1, 2) * F(1, 2) + F(1, 2) * F(1, 2))) == 100
    assert 90 + 20 * (F(1, 2) * 1 / (F(1, 2) * 1 + F(1, 2) * 0)) == 110
    rng = np.random.default_rng(26)
    high = rng.random(1_000_000) < 0.5
    informed = rng.random(1_000_000) < 0.2
    buy = np.where(informed, high, rng.random(1_000_000) < 0.5)
    assert abs((90 + 20 * high[buy]).mean() - 102) < 0.05
    # All informed: at 110 a buyer pays exactly what the stock is worth, and gains nothing.
    assert 110 - 110 == 0


def test_q27():
    assert F(49, 58) == F(49, 49 + 9)
    assert round(49 / 58, 3) == 0.845
    # Always agree: both right 70%, both wrong 30%.
    assert F(7, 10) / (F(7, 10) + F(3, 10)) == F(7, 10)
    assert F(55, 100) / (F(55, 100) + F(15, 100)) == F(11, 14)
    assert round(11 / 14, 3) == 0.786
    # Those are valid numbers: both right 55%, one right 15% each way, both wrong 15% keeps each at 70%.
    assert F(55, 100) + F(15, 100) == F(7, 10)
    assert F(55, 100) + F(15, 100) * 2 + F(15, 100) == 1
    # A joint simulation: the agreement structure gives the same answer.
    rng = np.random.default_rng(27)
    up = rng.random(2_000_000) < 0.5
    u = rng.random(2_000_000)
    a_right = u < 0.70
    b_right = (u < 0.55) | ((u >= 0.70) & (u < 0.85))
    a, b = np.where(a_right, up, ~up), np.where(b_right, up, ~up)
    both_up = a & b
    assert abs(up[both_up].mean() - 11 / 14) < 0.002
    # The other 30% splits evenly: each analyst is alone right on 15% of days, in the simulation too.
    assert (1 - F(55, 100) - F(15, 100)) / 2 == F(15, 100)
    assert abs((a_right & ~b_right).mean() - 0.15) < 0.001 and abs((b_right & ~a_right).mean() - 0.15) < 0.001


def test_q28():
    total = C(52, 13)
    none = C(48, 13)
    one = 4 * C(48, 12)
    any_ace = total - none
    p1 = F(any_ace - one, any_ace)
    assert round(float(p1), 4) == 0.3696
    spade = C(51, 12)
    spade_only = C(48, 12)
    p2 = F(spade - spade_only, spade)
    assert round(float(p2), 4) == 0.5612
    assert round(float(F(any_ace, total)), 3) == 0.696
    # Two-card hand, a small exact check of the same effect.
    assert F(6, C(52, 2) - C(48, 2)) == F(1, 33) and F(3, 51) == F(1, 17)
    rng = np.random.default_rng(28)
    hand = rng.random((300_000, 52)).argsort(axis=1)[:, :13]
    aces = (hand < 4).sum(axis=1)
    sp = (hand == 0).any(axis=1)
    assert abs((aces[aces >= 1] >= 2).mean() - float(p1)) < 0.004
    assert abs((aces[sp] >= 2).mean() - float(p2)) < 0.006


def door_walk(plan, car, step, pick, closed, weight):
    if step == 2:
        return weight * (pick == car)
    options = [d for d in closed if d not in (pick, car)]
    result = F(0)
    for h in options:
        now = [d for d in closed if d != h]
        w = weight * F(1, len(options))
        if plan[step]:
            others = [d for d in now if d != pick]
            for q in others:
                result += door_walk(plan, car, step + 1, q, now, w * F(1, len(others)))
        else:
            result += door_walk(plan, car, step + 1, pick, now, w)
    return result


def test_q29():
    def play(plan):
        return sum(door_walk(plan, car, 0, 0, [0, 1, 2, 3], F(1, 4)) for car in range(4))

    values = {plan: play(plan) for plan in itertools.product((0, 1), repeat=2)}
    assert values[(0, 0)] == F(1, 4)
    assert values[(0, 1)] == F(3, 4)
    assert values[(1, 0)] == F(3, 8)
    assert values[(1, 1)] == F(5, 8)
    assert max(values.values()) == F(3, 4)
    rng = np.random.default_rng(29)
    wins = 0
    for _ in range(50_000):
        car = rng.integers(4)
        closed = [0, 1, 2, 3]
        opts = [d for d in closed if d not in (0, car)]
        closed.remove(opts[rng.integers(len(opts))])
        opts = [d for d in closed if d not in (0, car)]
        closed.remove(opts[rng.integers(len(opts))])
        other = next(d for d in closed if d != 0)
        wins += other == car
    assert abs(wins / 50_000 - 0.75) < 0.006


def test_q30():
    assert sum(F(k, 2**k) for k in range(1, 60)) > F(1999, 1000)
    # E[L] = 2 and E[L^2] = 6 for a geometric on 1, 2, ...: Var = 2.
    assert abs(sum(k / 2**k for k in range(1, 200)) - 2) < 1e-12
    assert abs(sum(k * k / 2**k for k in range(1, 200)) - 6) < 1e-12
    rng = np.random.default_rng(30)
    size = rng.geometric(0.5, 3_000_000)
    assert abs(size.mean() - 2) < 0.003
    assert abs(len(size) / size.sum() - 0.5) < 0.001  # boys per child
    # Pick a child uniformly: a family is hit with weight equal to its size.
    assert abs((size**2).sum() / size.sum() - 3) < 0.01
    # A policy with every family exactly two has no spread, so both averages match.
    assert 2**2 / 2 == 2


def test_q31():
    ex = F(2, 3)
    assert ex == 2 * (F(1, 2) - F(1, 6))  # 2 * the integral over the triangle of x
    var = F(1, 2) - F(4, 9)
    assert var == F(1, 18)
    exy = F(5, 12)
    assert exy - ex * ex == -F(1, 36)
    assert (exy - ex * ex) / var == -F(1, 2)
    rng = np.random.default_rng(31)
    x, y = rng.random((2, 3_000_000))
    keep = x + y > 1
    assert abs(np.corrcoef(x[keep], y[keep])[0, 1] + 0.5) < 0.002
    assert abs(np.corrcoef(x, y)[0, 1]) < 0.002
    # The exact correlation for any hurdle c, by moments: it grows to -1/2 at c = 1 and stays there.
    def corr(c):
        if c >= 1:  # a triangle with its corner at (1, 1) and side s
            s = 2 - c
            mean, square, cross = 1 - s / 3, 1 - 2 * s / 3 + s * s / 6, 1 - 2 * s / 3 + s * s / 12
        else:  # the square less the corner x + y < c
            area = 1 - c * c / 2
            mean = (F(1, 2) - c**3 / 6) / area
            square = (F(1, 3) - c**4 / 12) / area
            cross = (F(1, 4) - c**4 / 24) / area
        return (cross - mean * mean) / (square - mean * mean)

    assert corr(F(1)) == corr(F(5, 4)) == corr(F(3, 2)) == corr(F(7, 4)) == -F(1, 2)
    low = [corr(F(k, 4)) for k in (1, 2, 3)]
    assert 0 > low[0] > low[1] > low[2] > -F(1, 2)
    for c in (0.5, 1.25, 1.75):
        keep = x + y > c
        assert abs(np.corrcoef(x[keep], y[keep])[0, 1] - float(corr(F(c)))) < 0.004


def test_q32():
    def post(r):
        crisis = stats.norm.pdf(r, 0, 3)
        calm = stats.norm.pdf(r, 0, 1)
        odds = 0.05 / 0.95 * crisis / calm
        return odds / (1 + odds), crisis / calm

    p, ratio = post(-4)
    assert round(ratio) == 409
    assert round(p, 3) == 0.956
    assert round(0.05 / 0.95 * ratio, 1) == 21.5
    p0, ratio0 = post(0)
    assert abs(ratio0 - 1 / 3) < 1e-12
    assert round(p0, 3) == 0.017
    rng = np.random.default_rng(32)
    crisis = rng.random(20_000_000) < 0.05
    r = rng.normal(0, np.where(crisis, 3.0, 1.0))
    near = np.abs(r + 4) < 0.1
    assert abs(crisis[near].mean() - p) < 0.01
    # The return where the two densities are equal: |r| = sqrt(2 ln 3 * 9/8).
    equal = math.sqrt(2 * math.log(3) * 9 / 8)
    assert round(equal, 2) == 1.57
    assert abs(post(equal)[1] - 1) < 1e-9


def test_q33():
    rng = np.random.default_rng(33)
    x, y = rng.exponential(1, (2, 3_000_000))
    s = x + y
    near = np.abs(s - 4) < 0.05
    u = x[near] / s[near]
    assert abs(u.mean() - 0.5) < 0.005 and abs(u.var() - 1 / 12) < 0.003
    assert abs((u < 0.25).mean() - 0.25) < 0.01
    x, y = rng.normal(size=(2, 3_000_000))
    s = x + y
    near = np.abs(s - 4) < 0.1
    assert abs(x[near].mean() - 2) < 0.02 and abs(x[near].var() - 0.5) < 0.02
    near = np.abs(s) < 0.05
    assert abs(x[near].mean()) < 0.03 and abs(x[near].var() - 0.5) < 0.02
    # Density ratio: e^{-x}e^{-(s-x)} does not depend on x.
    for z in (0.3, 1.1, 3.7):
        assert abs(math.exp(-z) * math.exp(-(4 - z)) - math.exp(-4)) < 1e-15


def test_q34():
    pairs = [(1, 2), (2, 4), (4, 8)]
    keep = F(0)
    switch = F(0)
    by_x = {}
    for a, b in pairs:
        for x, other in ((a, b), (b, a)):
            w = F(1, 6)
            keep += w * x
            switch += w * other
            by_x.setdefault(x, []).append((w, other))
    assert keep == switch == F(7, 2)
    gains = {x: sum(w * o for w, o in v) / sum(w for w, _ in v) for x, v in by_x.items()}
    assert gains == {1: 2, 2: F(5, 2), 4: 5, 8: 4}
    probs = {x: sum(w for w, _ in v) for x, v in by_x.items()}
    assert probs == {1: F(1, 6), 2: F(1, 3), 4: F(1, 3), 8: F(1, 6)}
    assert sum(probs[x] * (gains[x] - x) for x in gains) == 0
    assert gains[1] - 1 == 1 and gains[2] - 2 == F(1, 2) and gains[4] - 4 == 1 and gains[8] - 8 == -4
    rng = np.random.default_rng(34)
    k = rng.integers(0, 3, 1_000_000)
    small = 2.0**k
    you = rng.random(1_000_000) < 0.5
    x = np.where(you, small, 2 * small)
    other = np.where(you, 2 * small, small)
    assert abs(x.mean() - 3.5) < 0.02 and abs(other.mean() - 3.5) < 0.02
    assert abs(other[x == 2].mean() - 2.5) < 0.01


def test_q35():
    a = F(1, 2) * F(5, 15)
    b = F(1, 2) * F(20, 30)
    assert b / (a + b) == F(2, 3)
    assert F(2, 3) * 10 + F(1, 3) * F(5, 2) == F(15, 2)
    assert F(1, 2) * F(15, 2) + F(1, 2) * 15 == F(45, 4)  # the wait before any waiting
    rng = np.random.default_rng(35)
    gap = np.where(rng.random(4_000_000) < 0.5, 15.0, 30.0)
    wait = rng.random(4_000_000) * gap
    keep = wait > 10
    assert abs((gap[keep] == 30).mean() - 2 / 3) < 0.002
    assert abs((wait[keep] - 10).mean() - 7.5) < 0.02
    # With no wait at all, the belief stays even.
    assert F(1, 2) / (F(1, 2) + F(1, 2)) == F(1, 2)


def test_q36():
    p, q = F(2, 3), F(1, 3)
    assert p**2 / (p**2 + q**2) == F(4, 5)
    assert q**2 / (p**2 + q**2) == F(1, 5)
    assert 2 / (p**2 + q**2) == F(18, 5)
    # Simulate full Bayesian guessers: public log odds move only when a guess reveals a signal.
    rng = np.random.default_rng(36)
    runs = 100_000
    wrong = people = 0
    llr = math.log(2)
    for _ in range(runs):
        public = 0.0
        step = 0
        while True:
            step += 1
            signal = 1 if rng.random() < 2 / 3 else -1  # +1 points at the true type
            mine = public + signal * llr
            guess = signal if abs(mine) < 1e-9 else (1 if mine > 0 else -1)
            # Would each signal give the same guess? Then the guess reveals nothing: a cascade.
            hi = public + llr
            lo = public - llr
            guess_hi = 1 if hi > 1e-9 else (1 if abs(hi) < 1e-9 else -1)
            guess_lo = -1 if lo < -1e-9 else (-1 if abs(lo) < 1e-9 else 1)
            if guess_hi == guess_lo:
                wrong += guess_hi == -1
                people += step - 1
                break
            public += guess * llr
    assert abs(wrong / runs - 0.2) < 0.004
    assert abs(people / runs - 3.6) < 0.03
    # A perfect signal never goes wrong; a useless one is wrong half the time.
    assert F(1) ** 2 / (F(1) ** 2 + F(0) ** 2) == 1
    assert F(1, 2) ** 2 / (F(1, 2) ** 2 + F(1, 2) ** 2) == F(1, 2)


def test_q37():
    def value(rounds):
        total = F(0)
        for r in range(rounds):
            for seq in itertools.product((1, 0), repeat=r):
                h = sum(seq)
                t = r - h
                a = F(1, 2) * F(3, 5) ** h * F(2, 5) ** t
                b = F(1, 2) * F(2, 5) ** h * F(3, 5) ** t
                seen = a + b
                pa = a / seen
                up = pa * F(3, 5) + (1 - pa) * F(2, 5)
                total += seen * abs(2 * up - 1)
        return total

    assert value(1) == 0
    assert value(2) == F(1, 25)
    assert value(3) == F(2, 25)
    assert float(value(3)) == 0.08
    assert abs(F(7, 13) * 2 - 1 - F(1, 13)) == 0
    assert F(26, 100) * 2 == F(52, 100)
    assert F(52, 100) * F(1, 13) == F(1, 25)
    assert 3 * F(1, 5) == F(3, 5)  # knowing the coin: 0.2 a round
    rng = np.random.default_rng(37)
    p = np.where(rng.random(1_000_000) < 0.5, 0.6, 0.4)
    flips = rng.random((1_000_000, 3)) < p[:, None]
    score = np.zeros(1_000_000)
    net = np.zeros(1_000_000)
    for i in range(3):
        # Bet with the majority so far; when even, heads.
        bet_heads = net >= 0
        score += np.where(bet_heads == flips[:, i], 1, -1)
        net += np.where(flips[:, i], 1, -1)
    assert abs(score.mean() - 0.08) < 0.005


def test_q38():
    def bayes(heads, n):
        fair = math.exp(math.lgamma(n + 1) - math.lgamma(heads + 1) - math.lgamma(n - heads + 1) - n * math.log(2))
        flat = 1 / (n + 1)
        return fair, flat, fair / (fair + flat)

    fair, flat, post = bayes(60, 100)
    assert round(fair, 4) == 0.0108 and round(flat, 4) == 0.0099
    assert round(post, 3) == 0.523
    fair2, flat2, post2 = bayes(5100, 10_000)
    assert round(post2, 3) == 0.915
    assert round(fair2, 5) == 0.00108 and round(flat2, 5) == 0.0001
    assert round(stats.binomtest(60, 100, 0.5).pvalue, 3) == 0.057
    assert round(stats.binomtest(5100, 10_000, 0.5).pvalue, 3) == 0.047
    assert abs((60 - 50) / 5 - 2) < 1e-12 and abs((5100 - 5000) / 50 - 2) < 1e-12
    # Against one specific alternative, 60%: the data favour the alternative.
    lr = (0.6**60 * 0.4**40) / 0.5**100
    assert round(lr, 1) == 7.5
    assert round(1 / (1 + lr), 2) == 0.12
    rng = np.random.default_rng(38)
    runs = 2_000_000
    is_fair = rng.random(runs) < 0.5
    p = np.where(is_fair, 0.5, rng.random(runs))
    h = rng.binomial(100, p)
    assert abs(is_fair[h == 60].mean() - post) < 0.02


def test_q39():
    z100 = 2.508
    rng = np.random.default_rng(39)
    true = rng.normal(0, 0.5, (40_000, 100))
    measured = true + rng.normal(0, 0.5, (40_000, 100))
    best = measured.argmax(axis=1)
    rows = np.arange(40_000)
    assert abs(rng.normal(size=(40_000, 100)).max(axis=1).mean() - z100) < 0.01
    assert abs(measured[rows, best].mean() - z100 * math.sqrt(0.5)) < 0.01
    assert round(z100 * math.sqrt(0.5), 2) == 1.77
    assert round(0.5 * z100 * math.sqrt(0.5), 2) == 0.89
    assert abs(true[rows, best].mean() - 0.5 * z100 * math.sqrt(0.5)) < 0.01
    # No skill: the measured best is noise only, and the true Sharpe is zero.
    assert round(z100 * 0.5, 2) == 1.25
    # Shrink factor at the extremes: no noise keeps everything, no skill keeps nothing.
    assert 0.25 / (0.25 + 0) == 1 and 0 / (0 + 0.25) == 0
    assert abs(0.25 / (0.25 + 0.25) - 0.5) < 1e-12
    # Half of the measured edge is lost however many are tried: more tries raise both figures together.
    for count, runs in ((10, 40_000), (100, 20_000), (1000, 4_000)):
        t = rng.normal(0, 0.5, (runs, count))
        m = t + rng.normal(0, 0.5, (runs, count))
        i = m.argmax(axis=1)
        pick = np.arange(runs)
        assert abs(t[pick, i].mean() / m[pick, i].mean() - 0.5) < 0.01


def test_q40():
    between = stats.norm.cdf(20, 15, 10) - stats.norm.cdf(10, 15, 10)
    assert round(between, 3) == 0.383
    assert round(0.5 + 0.5 * between, 3) == 0.691
    rng = np.random.default_rng(40)
    n = 2_000_000
    pair = np.array([10.0, 20.0])
    side = rng.integers(0, 2, n)
    seen = pair[side]
    other = pair[1 - side]
    threshold = rng.normal(15, 10, n)
    say_larger = seen < threshold
    right = say_larger == (other > seen)
    assert abs(right.mean() - (0.5 + 0.5 * between)) < 0.001
    # If both numbers sit far from the threshold's mass, the edge shrinks but stays positive.
    far = stats.norm.cdf(1001, 15, 10) - stats.norm.cdf(1000, 15, 10)
    assert far >= 0
    assert 0.5 + 0.5 * (stats.norm.cdf(16, 15, 10) - stats.norm.cdf(15, 15, 10)) > 0.5
    # A fixed threshold below both numbers gives exactly one half: you always say "smaller".
    t = 5.0
    say_larger = seen < t
    right = say_larger == (other > seen)
    assert abs(right.mean() - 0.5) < 0.001
