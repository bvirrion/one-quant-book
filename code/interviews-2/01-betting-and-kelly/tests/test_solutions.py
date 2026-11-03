"""Betting and Kelly: every printed number, by exact arithmetic or direct optimisation, with seeded simulations and limit cases."""
import math
from fractions import Fraction as F
from itertools import product
from math import comb, log, sqrt

import numpy as np
from scipy.optimize import brentq, minimize_scalar
from scipy.stats import beta, binom, norm

NONNUMERIC = {}


def g(f, p=0.6, b=1.0, a=1.0):
    return p * log(1 + b * f) + (1 - p) * log(1 - a * f)


def argmax(fn, lo=0.0, hi=0.999):
    return minimize_scalar(lambda f: -fn(f), bounds=(lo, hi), method="bounded", options={"xatol": 1e-9}).x


def test_q1():
    assert F(1, 6) * 4 - F(5, 6) == F(-1, 6)
    assert F(5, 6) / F(1, 6) == 5
    assert F(1, 6) * 5 - F(5, 6) == 0  # the fair odds really make it zero
    assert round(2 / 1.90, 3) == 1.053
    assert round((200 - 100 * 1.90) / 200, 10) == 0.05
    assert round(1 - 1 / (2 / 1.9), 10) == 0.05
    rng = np.random.default_rng(1)
    w = rng.integers(1, 7, 200_000) == 6
    assert abs(np.where(w, 4, -1).mean() + 1 / 6) < 0.02


def test_q2():
    x, y = 1 / 2.5, 1 / 1.8
    assert round(x + y, 4) == 0.9556
    sx = 1000 * x / (x + y)
    sy = 1000 - sx
    assert round(sx, 1) == 418.6 and round(sy, 1) == 581.4
    assert round(sx * 2.5, 2) == round(sy * 1.8, 2) == 1046.51
    assert round(sx * 2.5 - 1000, 2) == 46.51
    assert 500 * 2.5 == 1250 and 500 * 1.8 == 900
    # Limit case: implied probabilities that add to 1 leave no lock.
    assert round(1 / (0.5 + 0.5) - 1, 10) == 0


def test_q3():
    f = argmax(lambda f: g(f, 0.55))
    assert abs(f - 0.10) < 1e-6
    assert round(g(0.1, 0.55), 4) == 0.0050
    assert round(0.5 * 0.1**2, 3) == 0.005
    assert abs(argmax(lambda f: g(f, 0.5))) < 1e-4  # no edge, no bet
    rng = np.random.default_rng(3)
    win = rng.random(2_000_000) < 0.55
    assert abs(np.where(win, log(1.1), log(0.9)).mean() - g(0.1, 0.55)) < 3e-4


def test_q4():
    assert abs(argmax(lambda f: g(f, 0.4, b=2)) - 0.10) < 1e-6
    assert round(0.4 - 0.6 / 2, 10) == 0.1 and round(0.3 - 0.7 / 2, 10) == -0.05
    assert argmax(lambda f: g(f, 0.3, b=2)) < 1e-4  # the best stake is nil
    assert round(0.4 * 2 - 0.6, 10) == 0.2 and round(0.3 * 2 - 0.7, 10) == -0.1


def test_q5():
    assert 0.5 * 1.5 + 0.5 * 0.6 == 1.05
    assert round(0.5 * log(0.9), 4) == -0.0527
    assert round(sqrt(0.9), 3) == 0.949
    assert round(1 - sqrt(0.9), 3) == 0.051
    rng = np.random.default_rng(5)
    paths = np.where(rng.random((4000, 200)) < 0.5, log(1.5), log(0.6)).sum(axis=1)
    assert abs(np.median(paths) / 200 - 0.5 * log(0.9)) < 0.01
    f = argmax(lambda f: 0.5 * log(1 + 0.5 * f) + 0.5 * log(1 - 0.4 * f))
    assert abs(f - 0.25) < 1e-6
    assert round(0.5 * log(1.0125), 4) == 0.0062


def test_q6():
    assert round(1.2**10, 2) == 6.19
    assert round(0.6**10 * 100, 1) == 0.6
    assert 2**10 == 1024
    assert round(0.6**10 * 1024, 2) == 6.19  # that one path is the whole mean
    assert round(1.04**10, 2) == 1.48 and round(0.8**10, 3) == 0.107
    rng = np.random.default_rng(6)
    alive = (rng.random((2_000_000, 10)) < 0.6).all(axis=1).mean()
    assert abs(alive - 0.6**10) < 3e-4


def test_q7():
    assert abs(argmax(g) - 0.2) < 1e-6
    assert round(g(0.2), 4) == 0.0201 and round(g(0.1), 4) == 0.0150
    assert round(g(0.1) / g(0.2), 2) == 0.75
    s = lambda f: sqrt(0.24) * log((1 + f) / (1 - f))  # noqa: E731
    assert round(s(0.2), 3) == 0.199 and round(s(0.1), 3) == 0.098
    assert round(sqrt(0.24), 2) == 0.49
    rng = np.random.default_rng(7)
    w = rng.random(2_000_000) < 0.6
    assert abs(np.where(w, log(1.2), log(0.8)).std() - s(0.2)) < 5e-4


def test_q8():
    assert abs(argmax(lambda f: g(f, 0.5, b=1, a=0.5)) - 0.5) < 1e-6
    assert round(0.5 * log(1.125), 3) == 0.059
    assert 0.5 / 0.5 - 0.5 / 1 == 0.5 and 0.5 - 0.5 / 1 == 0
    assert 0.5 * 0.5 == 0.25  # share of wealth at risk


def test_q9():
    w = brentq(lambda w: 0.5 * log(w + 150) + 0.5 * log(w - 100) - log(w), 101, 10_000)
    assert abs(w - 300) < 1e-6
    assert 0.5 * 150 - 0.5 * 100 == 25
    assert abs(argmax(lambda f: g(f, 0.5, b=1.5)) - 1 / 6) < 1e-6
    assert round(100 / (1 / 6)) == 600
    assert 0.5 * log(110 + 150) + 0.5 * log(110 - 100) < log(110)  # at $110 it is refused


def test_q10():
    mu, sig = 0.08, 0.16
    assert round(mu / sig**2, 3) == 3.125
    assert round(mu**2 / (2 * sig**2), 3) == 0.125
    s = mu / sig
    assert s == 0.5 and round(s / sig, 3) == 3.125 and round(s**2 / 2, 3) == 0.125
    assert round(3.125 * sig, 2) == 0.5
    # A second route: maximise f*mu - f^2 sig^2/2 numerically; and a simulated check of log growth at that leverage.
    f = minimize_scalar(lambda f: -(f * mu - 0.5 * f * f * sig * sig), bounds=(0, 10), method="bounded").x
    assert abs(f - 3.125) < 1e-4
    rng = np.random.default_rng(10)
    dt = 1 / 252
    r = rng.normal(mu * dt, sig * sqrt(dt), 2_000_000)
    assert abs(np.log1p(3.125 * r).mean() / dt - 0.125) < 0.02


def test_q11():
    assert round(g(0.4), 4) == -0.0024
    root = brentq(g, 0.2, 0.9)
    assert round(root, 3) == 0.389
    assert root < 0.4
    assert round(g(0.1), 4) == 0.0150 and round(g(0.3), 4) == 0.0147


def test_q12():
    fn = lambda f: 0.3 * log(1 + 2 * f) + 0.4 * log(1) + 0.3 * log(1 - f)  # noqa: E731
    assert abs(argmax(fn) - 0.25) < 1e-6
    assert round(0.3 * log(1.125), 4) == 0.0353
    assert abs(argmax(lambda f: g(f, 0.5, b=2)) - 0.25) < 1e-6  # the same bet with no pushes
    assert round(0.5 * log(1.125), 4) == 0.0589
    assert abs(0.6 * 0.5 * log(1.125) - 0.3 * log(1.125)) < 1e-12
    assert round(0.3 - 0.7 / 2, 2) == -0.05


def test_q13():
    fn = lambda f: 0.36 * log(1 + 2 * f) + 0.16 * log(1 - 2 * f)  # noqa: E731
    f = argmax(fn, 0, 0.49)
    assert abs(f - 0.4 / 2.08) < 1e-6 and round(f, 3) == 0.192 and round(2 * f, 3) == 0.385
    assert round(fn(f), 4) == 0.0395
    assert round(2 * g(0.2), 4) == 0.0403
    assert fn(f) < 2 * g(0.2)
    assert round(0.8**2, 2) == 0.64

    def many(n):
        def val(f):
            return sum(binom.pmf(k, n, 0.6) * log(1 + f * (2 * k - n)) for k in range(n + 1))

        return argmax(val, 0, 1 / n - 1e-12)

    assert round(many(5), 3) == 0.165 and round(5 * many(5), 2) == 0.83
    assert round(many(50), 3) == 0.02 and 50 * many(50) < 1
    assert abs(many(1) - 0.2) < 1e-6  # one bet gives back plain Kelly


def test_q14():
    mu = np.array([0.1, 0.1])
    for rho, each, total, gr in ((0.5, 1.667, 3.33, 0.1667), (0.0, 2.5, 5.0, 0.25)):
        cov = 0.04 * np.array([[1, rho], [rho, 1]])
        f = np.linalg.solve(cov, mu)
        assert round(f[0], 3) == each and round(f.sum(), 2) == total
        got = f @ mu - 0.5 * f @ cov @ f
        assert round(got, 4) == gr
        assert abs(sqrt(2 * got) - 0.5 * sqrt(2 / (1 + rho))) < 1e-12
    assert round(0.5 * sqrt(2 / 1.5), 3) == 0.577 and round(0.5 * sqrt(2), 3) == 0.707
    # Limit case: perfect correlation is one strategy with Kelly leverage 2.5, split in two.
    assert round(0.1 / (0.04 * 2), 3) == 1.25
    # The wrong answer: leverage 2.5 on each at correlation 0.5.
    cov = 0.04 * np.array([[1, 0.5], [0.5, 1]])
    f = np.array([2.5, 2.5])
    assert round(f @ mu - 0.5 * f @ cov @ f, 3) == 0.125


def test_q15():
    h = -(0.75 * log(0.75) + 0.25 * log(0.25))
    assert round(log(2) - h, 3) == 0.131
    assert abs(argmax(lambda f: g(f, 0.75)) - 0.5) < 1e-6
    assert abs(g(0.5, 0.75) - (log(2) - h)) < 1e-12
    assert round(log(2), 3) == 0.693
    assert round((log(2) - h) / log(2) * 100) == 19
    # Limit cases: a perfect tip and a useless tip.
    assert abs(argmax(lambda f: g(f, 0.5))) < 1e-4
    rng = np.random.default_rng(15)
    right = rng.random(1_000_000) < 0.75
    assert abs(np.where(right, log(1.5), log(0.5)).mean() - 0.1308) < 0.002


def test_q16():
    p = np.array([0.5, 0.3, 0.2])
    h = -(p * np.log(p)).sum()
    assert round(h, 4) == 1.0297 and round(log(3), 4) == 1.0986
    assert round(log(3) - h, 3) == 0.069

    def best(odds):
        grid = np.arange(0.01, 1, 0.01)
        top = (-np.inf, None)
        for a in grid:
            for b in grid:
                c = 1 - a - b
                if c < 0.005:
                    continue
                v = p @ np.log(np.array([a, b, c]) * odds)
                if v > top[0]:
                    top = (v, (round(a, 2), round(b, 2), round(c, 2)))
        return top

    v, split = best(np.array([3, 3, 3]))
    assert split == (0.5, 0.3, 0.2) and round(v, 3) == 0.069
    v, split = best(np.array([2, 4, 8]))
    assert split == (0.5, 0.3, 0.2) and round(v, 3) == 0.149


def test_q17():
    assert round(g(0.1, 0.51), 4) == -0.0030
    root = brentq(lambda f: g(f, 0.51), 0.01, 0.2)
    assert round(root, 4) == 0.0400 and round(10 / root) == 250
    assert abs(argmax(lambda f: g(f, 0.51)) - 0.02) < 1e-6
    assert round(10 / 0.02) == 500
    assert round(10 * 0.02, 2) == 0.2


def test_q18():
    assert round(50 * (0.6 - 0.4), 10) == 10
    assert round((2 / 3) ** 20 * 100, 2) == 0.03
    assert round((2 / 3) ** 4 * 100) == 20
    assert 50 / 0.2 == 250
    # Exact first-step: an absorbing walk with a far upper barrier gives the same ruin chance.
    r = 2 / 3
    far = 400
    assert abs((r**20 - r**far) / (1 - r**far) - r**20) < 1e-12
    rng = np.random.default_rng(18)
    steps = np.where(rng.random((200_000, 300)) < 0.6, 1, -1).cumsum(axis=1)
    assert abs((steps.min(axis=1) <= -4).mean() - r**4) < 0.005


def test_q19():
    def reach(p, start=100, top=200):
        r = (1 - p) / p
        return (1 - F(r).limit_denominator(1000) ** start) / (1 - F(r).limit_denominator(1000) ** top)

    assert f"{float(reach(0.4)):.1e}" == "2.5e-18"
    assert f"{float(1 - reach(0.6)):.1e}" == "2.5e-18"
    assert f"{(2 / 3) ** 100:.1e}" == "2.5e-18"
    assert f"{1.5 ** -100:.1e}" == "2.5e-18"
    # Limit case: a fair game gives start/top whatever the method.
    # Small target check by value iteration: all in is best at p = 0.4 on a coarse grid of stakes.
    n = 8
    v = np.zeros(2 * n + 1)
    v[2 * n] = 1
    for _ in range(400):
        for w in range(1, 2 * n):
            v[w] = max(0.4 * v[min(w + s, 2 * n)] + 0.6 * v[w - s] for s in range(1, w + 1))
    assert abs(v[n] - 0.4) < 1e-9


def test_q20():
    pi = lambda w: w * (1 - (1 - 5000 / w) ** 0.01)  # noqa: E731
    assert 0.01 * 5000 == 50
    assert round(pi(20_000), 2) == 57.45 and round(pi(10_000), 2) == 69.08
    assert pi(20_000) < 60 < pi(10_000)
    assert round(pi(20_000) - 50, 2) == 7.45 and round(pi(10_000) - 50, 2) == 19.08
    for w in (20_000, 10_000):  # indifference, by the other route
        assert abs(log(w - pi(w)) - 0.99 * log(w) - 0.01 * log(w - 5000)) < 1e-12
    assert 50 < pi(10_000_000) < 50.2  # huge wealth: close to the expected loss


def test_q21():
    assert 100 * (0.5 * 200 - 0.5 * 100) == 5000
    assert 150 * 10 == 1500
    assert sqrt(0.5 * (200 - 50) ** 2 + 0.5 * (-100 - 50) ** 2) == 150
    assert 200 * 33 - 100 * 67 < 0 < 200 * 34 - 100 * 66
    assert round(binom.cdf(33, 100, 0.5), 5) == 0.00044
    assert brentq(lambda w: log(w + 200) + log(w - 100) - 2 * log(w), 101, 10_000) - 200 < 1e-6
    assert 100 * 100 == 10_000

    # A log investor is never the colleague: wherever they refuse one flip, they refuse the 100 as well.
    def dlog(w, n):
        if w <= 100 * n:  # n tails wipe them out, and the logarithm of zero is minus infinity
            return -math.inf
        return sum(binom.pmf(h, n, 0.5) * (log(w + 300 * h - 100 * n) - log(w)) for h in range(n + 1))

    for w in (150, 199):
        assert dlog(w, 1) < 0 and dlog(w, 100) == -math.inf
    assert dlog(200, 1) > -1e-12
    for w in (1000, 10_000):
        assert dlog(w, 1) > 0 and dlog(w, 100) == -math.inf
    for w in (10_001, 20_000, 1_000_000):
        assert dlog(w, 1) > 0 and dlog(w, 100) > 0


def test_q22():
    gr = lambda c, s=1: (c - c * c / 2) * s * s  # noqa: E731
    assert gr(1) == 0.5 and gr(0.5) == 0.375
    assert round(log(2) / 0.5, 2) == 1.39 and round(log(2) / 0.375, 2) == 1.85
    assert round(log(2) / 0.375 - log(2) / 0.5, 2) == 0.46
    assert round((log(2) / 0.375) / (log(2) / 0.5), 2) == 1.33
    assert round(log(2) / 1, 2) == 0.69
    assert gr(2) == 0  # twice Kelly goes nowhere
    assert gr(0) == 0  # no leverage, no excess growth


def test_q23():
    gr = lambda f: 0.08 * f - 0.0128 * f * f  # noqa: E731
    assert round(gr(2), 4) == 0.1088
    assert round(gr(3.125), 4) == 0.125
    assert round(gr(2) / gr(3.125), 2) == 0.87
    c = 2 / 3.125
    assert c == 0.64 and round(c * (2 - c), 4) == round(gr(2) / gr(3.125), 4)
    assert round(0.08 / 0.0128, 2) == 6.25 and abs(gr(6.25)) < 1e-12


def test_q24():
    capped = sum(F(1, 2**k) * 2**k for k in range(1, 21)) + F(1, 2**20) * 2**20
    assert capped == 21
    assert sum(F(1, 2**k) * 2**k for k in range(1, 11)) == 10  # the partial sums grow without limit

    def price(w):
        val = lambda c: sum(2.0**-k * log(w - c + 2.0**k) for k in range(1, 200)) - log(w)  # noqa: E731
        return brentq(val, 0.01, w - 1e-6)

    assert round(price(1000), 2) == 10.95 and round(price(1_000_000), 2) == 20.87
    # Doubling the house's money adds one dollar.
    assert sum(F(1, 2**k) * 2**k for k in range(1, 22)) + F(1, 2**21) * 2**21 == 22


def test_q25():
    assert 1 / sqrt(4) == 0.5
    gr = lambda hat, s: hat * s - 0.5 * hat * hat  # noqa: E731
    assert gr(1.5, 1) == 0.375 and gr(1.5, 0.5) == -0.375
    assert round(gr(0.75, 1), 3) == 0.469 and round(gr(0.75, 0.5), 3) == 0.094
    assert round(gr(0.75, 1.5), 2) == 0.84 and gr(1.5, 1.5) == 1.125
    assert 0.5 * 1.5 * 1.5 == 1.125  # correct size on a correct estimate gives S^2/2


def ruin_lattice(f, p=0.6, x=0.5, n=1500, top=6.0):
    from collections import defaultdict

    state, dead = {(0, 0): 1.0}, 0.0
    up, down = log(1 + f), log(1 - f)
    for _ in range(n):
        nxt = defaultdict(float)
        for (a, b), q in state.items():
            for da, db, pr in ((1, 0, p), (0, 1, 1 - p)):
                v = (a + da) * up + (b + db) * down
                if v <= log(x):
                    dead += q * pr
                elif v <= top:
                    nxt[(a + da, b + db)] += q * pr
        state = nxt
    return dead


def test_q26():
    assert abs(0.6 / 1.2 + 0.4 / 0.8 - 1) < 1e-12
    full = ruin_lattice(0.2)
    half = ruin_lattice(0.1)
    assert round(full * 100, 1) == 45.5 and full <= 0.5
    assert round(half * 100, 1) == 10.5
    assert 0.5 ** (2 / 1 - 1) == 0.5 and 0.5 ** (2 / 0.5 - 1) == 0.125
    assert 0.1 ** (2 / 1 - 1) == 0.1
    # Second route: simulated continuous paths for Sharpe 1 at full Kelly, on a fine grid and a long horizon.
    rng = np.random.default_rng(26)
    dt = 1 / 250
    logw = (rng.normal(0.5 * dt, sqrt(dt), (2000, 12_500))).cumsum(axis=1)
    hit = (logw.min(axis=1) <= log(0.5)).mean()
    assert abs(hit - 0.5) < 0.05
    # Limit case: at twice Kelly the exponent is 0 and ruin is certain.
    assert 0.5 ** (2 / 2 - 1) == 1


def test_q27():
    c = 2 / (1 + log(0.05) / log(0.5))
    assert round(log(0.05) / log(0.5), 2) == 4.32
    assert round(c, 3) == 0.376
    assert round(c * (2 - c), 2) == 0.61
    assert abs(0.5 ** (2 / c - 1) - 0.05) < 1e-12
    # The hitting probability does not depend on S.
    for s in (0.5, 1, 2):
        m, v = (c - c * c / 2) * s * s, c * s
        assert abs(math.exp(-2 * m * log(2) / v**2) - 0.05) < 1e-12
    assert round(c * 1.5, 3) == 0.564
    assert round(0.5 ** (2 / (c * 1.5) - 1), 2) == 0.17


def test_q28():
    a, b = 61, 41
    m = a / (a + b)
    assert round(m, 3) == 0.598 and round(2 * m - 1, 3) == 0.196
    assert round(beta.std(a, b), 3) == 0.048
    lo, hi = beta.ppf(0.025, a, b), beta.ppf(0.975, a, b)
    assert round(lo, 2) == 0.50 and round(hi, 2) == 0.69
    # Exact expectation over the posterior, by simulation: the best stake sits at 2E[p] - 1.
    rng = np.random.default_rng(28)
    ps = rng.beta(a, b, 400_000)
    wins = rng.random(400_000) < ps
    f = argmax(lambda f: np.where(wins, log(1 + f), log(1 - f)).mean(), 0, 0.6)
    assert abs(f - (2 * m - 1)) < 0.01
    assert round(g(2 * m - 1, m), 3) == 0.019
    assert round(160 / 300, 3) == 0.533 and round(2 * 160 / 300 - 1, 3) == 0.067


def test_q29():
    grid = 16  # wealth in sixteenths of a dollar

    cache = {}

    def solve(p, left):
        key = (p, left)
        if key in cache:
            return cache[key]
        if left == 0:
            v = [1.0 if w >= 2 * grid else 0.0 for w in range(0, 17 * grid)]
        else:
            nxt = solve(p, left - 1)
            top = len(nxt) - 1
            v = [max(p * nxt[min(w + s, top)] + (1 - p) * nxt[w - s] for s in range(0, w + 1)) for w in range(top + 1)]
        cache[key] = v
        return v

    v3 = solve(0.6, 3)
    assert round(v3[grid], 3) == 0.648
    v2 = solve(0.6, 2)
    assert round(v2[int(1.5 * grid)], 2) == 0.84 and round(v2[grid], 2) == 0.6 and round(v2[grid // 2], 2) == 0.36
    assert round(0.6 * 0.84 + 0.4 * 0.36, 3) == 0.648
    best = max(range(0, grid + 1), key=lambda s: 0.6 * v2[grid + s] + 0.4 * v2[grid - s])
    assert best == grid // 2  # the first stake is 50 cents
    assert round(1.2**3, 3) == 1.728 < 2
    assert round(0.6**3, 3) == 0.216
    # Exhaustive policy check with a simulation of the stated plan.
    rng = np.random.default_rng(29)
    hits = 0
    wins = rng.random((300_000, 3)) < 0.6
    for row in wins:
        w = 1.0
        for k, won in enumerate(row):
            left = 3 - k
            if w >= 2:
                s = 0.0
            elif left == 3 or (left == 2 and w == 0.5):
                s = 0.5
            elif left == 2:
                s = 0.5  # from 1.5, go for 2; if lost, 1 with one bet left
            else:
                s = 1.0 if w >= 1 else 0.0
                s = min(s, 2 - w) if w >= 1 else 0.0
            w += s if won else -s
        hits += w >= 2
    assert abs(hits / 300_000 - 0.648) < 0.004


def test_q30():
    assert round(1000 * log(1.04), 1) == 39.2 and round(1000 * log(1.06), 1) == 58.3
    t = log(0.8 / 0.7) / (log(0.8 / 0.7) + log(1.3 / 1.2))
    assert round(t, 4) == 0.6252
    assert round(binom.cdf(625, 1000, 0.6), 2) == 0.95
    assert round(1000 * g(0.2), 1) == 20.1 and round(1000 * g(0.3), 1) == 14.7
    rng = np.random.default_rng(30)
    k = rng.binomial(1000, 0.6, 400_000)
    mine = k * log(1.2) + (1000 - k) * log(0.8)
    rival = k * log(1.3) + (1000 - k) * log(0.7)
    assert abs((mine > rival).mean() - binom.cdf(625, 1000, 0.6)) < 0.003


def test_q31():
    fn = lambda f: 0.9 * log(1 + 0.25 * f) + 0.1 * log(1 - f)  # noqa: E731
    assert abs(argmax(fn) - 0.5) < 1e-6
    assert round(fn(0.5), 4) == 0.0367
    mean = 0.9 * 0.25 - 0.1
    second = 0.9 * 0.0625 + 0.1
    assert round(mean, 3) == 0.125 and round(second, 5) == 0.15625
    var = second - mean**2
    assert round(var, 4) == 0.1406
    assert round(mean / var, 3) == 0.889 and round(mean / second, 2) == 0.8
    assert round(fn(mean / var), 3) == -0.039
    assert round(mean / sqrt(var), 2) == 0.33
    # Symmetric small bets: the rule works there, which is the limit that makes the point.
    assert abs(argmax(lambda f: g(f, 0.51)) - 0.02 / 1) < 1e-4


def test_q32():
    assert round(2**52 / comb(52, 26), 2) == 9.08

    def wealth(order):
        r, b, w = 26, 26, F(1)
        for c in order:
            w *= F(2 * (r if c == "r" else b), r + b)
            if c == "r":
                r -= 1
            else:
                b -= 1
        return w

    exact = F(2**52, comb(52, 26))
    rng = np.random.default_rng(32)
    for _ in range(20):
        deck = list("r" * 26 + "b" * 26)
        rng.shuffle(deck)
        assert wealth(deck) == exact
    # The bound on a small deck: any strategy's final wealth, summed over all colour sequences, is 2^6, so its
    # average over the balanced sequences is at most 2^6 / C(6, 3). Try random rules that depend on the history.
    n = 6
    seqs = list(product("rb", repeat=n))
    balanced = [s for s in seqs if s.count("r") == 3]
    assert len(balanced) == comb(6, 3)
    for seed in range(20):
        rules = np.random.default_rng(seed)
        table = {}

        def rule(hist, table=table, rules=rules):
            if hist not in table:
                table[hist] = (F(int(rules.integers(-10, 11)), 10))  # stake on red, negative meaning on black
            return table[hist]

        def final(seq):
            w = F(1)
            for i, c in enumerate(seq):
                w *= 1 + rule(seq[:i]) * (1 if c == "r" else -1)
            return w

        assert sum(final(s) for s in seqs) == 2**n
        assert sum(final(s) for s in balanced) / len(balanced) <= F(2**n, comb(6, 3))
    # Limit case: one red and one black card doubles exactly once.
    assert F(2**2, comb(2, 1)) == 2


def test_q33():
    def need(f, p=0.55):
        gr, s = p * log(1 + f) + (1 - p) * log(1 - f), sqrt(p * (1 - p)) * log((1 + f) / (1 - f))
        return (1.645 * s / gr) ** 2, gr, s

    n1, g1, s1 = need(0.10)
    n2, g2, s2 = need(0.05)
    assert round(n1) == 1075 and round(n2) == 476
    assert round(g1, 6) == 0.005008 and round(s1, 4) == 0.0998
    assert round(g2, 6) == 0.003753 and round(s2, 4) == 0.0498

    def chance(f, n, p=0.55):
        flat = n * log(1 / (1 - f)) / log((1 + f) / (1 - f))
        return 1 - binom.cdf(math.floor(flat + 1e-12), n, p)

    def exact(f):
        ok = [chance(f, n) >= 0.95 for n in range(1, 2500)]
        last_bad = max(i for i, v in enumerate(ok) if not v) + 1
        return last_bad + 1

    assert exact(0.10) == 1104 and exact(0.05) == 495
    small = (1.645 * 2 * sqrt(0.2475) / 0.1) ** 2
    assert round(small) == 268
    assert round((1.645 * sqrt(1 - 0.1**2) / 0.1) ** 2) == 268


def test_q34():
    def wealth(seq):
        a, b, w = 0, 0, F(1)
        for h in seq:
            m = F(a + 1, a + b + 2)
            w *= 2 * m if h else 2 * (1 - m)
            a, b = a + h, b + 1 - h
        return w

    closed = F(2**10, 11 * comb(10, 7))
    rng = np.random.default_rng(34)
    for _ in range(50):
        seq = [1] * 7 + [0] * 3
        rng.shuffle(seq)
        assert wealth([int(x) for x in seq]) == closed
    assert round(float(closed), 3) == 0.776
    assert round(2**10 * 0.7**7 * 0.3**3, 2) == 2.28
    assert round(2**10 * 0.7**7 * 0.3**3 / float(closed), 1) == 2.9
    assert round(float(wealth([1] * 10)), 2) == 93.09
    # The person who knew p = 0.7 stakes 40% on heads each time, and on this run does worse than the learner.
    assert round(1.4**10, 2) == 28.93 and 1.4**10 < float(wealth([1] * 10))
    assert abs(2**10 * 0.7**10 - 1.4**10) < 1e-9
    # The stake rule is a split: staking |2m-1| on the likelier side gives the same multiplier.
    for m in (F(1, 2), F(2, 3), F(3, 10)):
        side_up = 1 + abs(2 * m - 1) if m >= F(1, 2) else 1 - abs(2 * m - 1)
        assert side_up == 2 * m
    # The mixture route: the integral over p.
    from scipy.integrate import quad

    val = quad(lambda p: 2**10 * p**7 * (1 - p) ** 3, 0, 1)[0]
    assert abs(val - float(closed)) < 1e-9
    # The shortfall bound against the best fixed p for every count.
    for h in range(11):
        best = 2**10 * (h / 10) ** h * (1 - h / 10) ** (10 - h)
        assert best / float(F(2**10, 11 * comb(10, h))) <= 11 + 1e-9


def test_q35():
    assert round(norm.cdf(1) * 100, 1) == 84.1
    assert round((1 - norm.cdf(log(2) - 0.5)) * 100, 1) == 42.3
    assert round((1 - norm.cdf((log(2) - 0.375) / 0.5)) * 100, 1) == 26.2
    assert round(log(2) - 0.5, 3) == 0.193 and round((log(2) - 0.375) / 0.5, 3) == 0.636
    assert round((1 - norm.cdf(1)) * 100, 1) == 15.9
    # Simulate the replicating strategy in discrete time: wealth should end near 2 or 0, and start from 1.
    rng = np.random.default_rng(35)
    n, steps, s = 4000, 2000, 1.0
    dt = 1 / steps
    b = np.zeros(n)  # B under P
    t = 0.0
    w = np.full(n, 2 * norm.cdf(0.0))
    assert np.allclose(w, 1)
    for _ in range(steps - 1):
        y = b + s * t
        z = y / sqrt(1 - t)
        expo = 2 * norm.pdf(z) / sqrt(1 - t)
        db = rng.normal(0, sqrt(dt), n)
        w += expo * (db + s * dt)  # risky exposure earns Sharpe s per unit of volatility
        b += db
        t += dt
    assert abs((w > 1).mean() - norm.cdf(1)) < 0.02
    # Limit cases of the formula: S = 0 gives w/T, as for a fair game; target 1 gives certainty.
    assert abs(norm.cdf(norm.ppf(0.5) + 0) - 0.5) < 1e-12
    assert abs(norm.cdf(norm.ppf(0.999999) + 1) - 1) < 1e-5
