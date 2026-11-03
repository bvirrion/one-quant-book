"""Mock Interviews: every number printed in the written interviews, by exact arithmetic, then a seeded simulation."""
import math
from fractions import Fraction as F

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import norm

NONNUMERIC = {}


def call(s, k, vol, t):
    d1 = (math.log(s / k) + vol * vol * t / 2) / (vol * math.sqrt(t))
    return s * norm.cdf(d1) - k * norm.cdf(d1 - vol * math.sqrt(t))


def test_q1():
    # Round 2: arithmetic.
    assert 17 * 23 == 391 == 20**2 - 3**2
    assert F(7, 8) == F(875, 1000)
    assert 1400 * 3 // 100 == 42
    assert round(1.02**10, 3) == 1.219
    assert round(1 + 10 * 0.02 + 45 * 0.02**2, 3) == 1.218
    assert round(1.02**10, 2) == 1.22

    # Round 3: taking turns.
    p = F(1, 3) / (1 - F(2, 3) ** 2)
    assert p == F(3, 5)
    assert p == F(1, 3) + F(2, 3) * F(2, 3) * p
    assert 100 * p - 100 * (1 - p) == 20
    rng = np.random.default_rng(1)
    rolls = rng.geometric(1 / 3, 500_000)
    assert abs((rolls % 2 == 1).mean() - 0.6) < 0.003
    assert abs(rolls.mean() - 3) < 0.02
    # The smaller the chance per roll, the less going first is worth: at 1/6, about 54.5% against 45.5%.
    q = F(1, 6) / (1 - F(5, 6) ** 2)
    assert q == F(6, 11) and 2 * q - 1 < 2 * p - 1

    # Round 4: the market.
    assert F(7) - F(1, 2) == F(13, 2)
    assert 5 + F(7, 2) == F(17, 2) and F(15, 2) - F(17, 2) == -1
    seen = [d for d in range(1, 7) if d + F(7, 2) > F(15, 2)]
    assert seen == [5, 6]
    assert 5 + F(11, 2) == F(21, 2)
    assert F(15, 2) - F(21, 2) == -3
    assert F(15, 2) - 11 == F(-7, 2)

    # Round 5: the bet.
    def g(f):
        return 0.4 * math.log(1 + 2 * f) + 0.6 * math.log(1 - f)

    edge = F(4, 10) * 2 - F(6, 10)
    assert edge == F(1, 5) and edge / 2 == F(1, 10)
    grid = np.linspace(0, 0.45, 45_001)
    values = [g(x) for x in grid]
    assert abs(grid[int(np.argmax(values))] - 0.1) < 1e-4
    assert round(g(0.1) * 100, 2) == 0.97
    assert round(g(0.05) * 100, 2) == 0.73
    assert round(g(0.05) / g(0.1) * 100) == 76
    assert round(g(0.2) * 100, 2) == 0.07
    wins = rng.random(2_000_000) < 0.4
    assert abs(np.where(wins, math.log(1.2), math.log(0.9)).mean() - g(0.1)) < 0.0005

    # Round 6: the option.
    assert 0.4 * 100 * 0.2 == 8
    c = call(100, 100, 0.2, 1)
    assert round(c, 2) == 7.97
    assert round(norm.cdf(0.1), 2) == 0.54
    assert round(20 / math.sqrt(252), 2) == 1.26
    z = rng.standard_normal(2_000_000)
    end = 100 * np.exp(0.2 * z - 0.02)
    assert abs(np.maximum(end - 100, 0).mean() - c) < 0.03
    assert abs(np.maximum(100 - end, 0).mean() - c) < 0.03

    # Round 7: the ETF.
    assert F(5010, 100) - F(5001, 100) - F(2, 100) == F(7, 100)

    # Round 8: what volatility makes the call 10?
    implied = brentq(lambda v: call(100, 100, v, 1) - 10, 0.05, 0.6)
    assert round(implied * 100) == 25
    assert 0.4 * 100 * 0.25 == 10
    # The total: eight rounds, each out of 2.
    assert 8 * 2 == 16
    assert 3 + 3 + 7 + 10 + 7 + 7 + 5 + 3 == 45


def emax(n):
    return quad(lambda z: z * n * norm.cdf(z) ** (n - 1) * norm.pdf(z), -10, 12)[0]


def test_q2():
    rng = np.random.default_rng(2)
    # Round 2: orthant, exact and simulated, with limits.
    orth = lambda r: 0.25 + math.asin(r) / (2 * math.pi)  # noqa: E731
    assert abs(orth(0.5) - 1 / 3) < 1e-12 and orth(0) == 0.25 and abs(orth(1) - 0.5) < 1e-12
    x, z = rng.standard_normal((2, 2_000_000))
    y = 0.5 * x + math.sqrt(0.75) * z
    assert abs(((x > 0) & (y > 0)).mean() - 1 / 3) < 0.002
    assert round(0.5 * math.sqrt(2 / math.pi), 2) == 0.40 and abs(np.maximum(x, y).mean() - 0.399) < 0.002
    # Round 3: the short slope and the long slopes, by simulated regression.
    assert round(0.05 * math.sqrt(1000), 2) == 1.58
    assert 0.02 + 0.6 * 0.05 == 0.05 and round(0.02 * math.sqrt(1000 * 0.64), 1) == 0.5
    n = 2_000_000
    a, b = rng.standard_normal((2, n))
    s = 0.6 * a + 0.8 * b
    r = 0.02 * a + 0.05 * s + rng.standard_normal(n)
    long_b = np.linalg.lstsq(np.c_[a, s], r, rcond=None)[0]
    assert abs(long_b[0] - 0.02) < 0.003 and abs(long_b[1] - 0.05) < 0.003
    assert abs((a * r).mean() / (a * a).mean() - 0.05) < 0.003
    # Round 4.
    assert 0.02 * math.sqrt(2500) == 1 and round(0.02 * math.sqrt(500), 2) == 0.45 and round(1 / math.sqrt(500), 3) == 0.045
    # Round 5.
    em = emax(50)
    assert round(em, 2) == 2.25 and round(em / math.sqrt(3), 2) == 1.30
    assert round(2 - em / math.sqrt(3), 1) == 0.7 and round((2 - em / math.sqrt(3)) * math.sqrt(3), 1) == 1.2
    # Round 6: the size that makes the most money, by search.
    g = np.linspace(0, 3, 300001)
    assert abs(g[(g * (15 - 10 * np.sqrt(g))).argmax()] - 1) < 1e-3
    assert 15 - 10 * math.sqrt(1) == 5 and (15 / 10) ** 2 == 2.25
    # Round 7: an after-close announcement, whose reaction arrives overnight into day t + 1.
    events = 200_000
    surprise = rng.choice([-1.0, 1.0], events)

    def sharpe(ret):
        return (surprise * ret).mean() / (surprise * ret).std() * math.sqrt(252)

    day_t = rng.normal(0, 0.02, events)  # ended before the number was known
    overnight = 0.03 * surprise + rng.normal(0, 0.01, events)
    open_to_close = rng.normal(0, 0.02, events)
    day_t2 = rng.normal(0, 0.02, events)
    assert sharpe(overnight + open_to_close) > 10  # the join in the prompt: large and false
    assert abs(sharpe(open_to_close)) < 1 and abs(sharpe(day_t2)) < 1  # after the number is known, it collapses
    assert abs(sharpe(day_t)) < 1  # joining to day t's own return would show nothing: it holds no reaction
    no_news = rng.normal(0, 0.01, events) + open_to_close
    assert abs(sharpe(no_news)) < 1  # limit: with no reaction, the same join shows nothing either
    # Round 8: four times the breadth.
    assert (1 / 0.01) ** 2 == 10000
    assert 3 + 7 + 8 + 7 + 8 + 5 + 4 + 3 == 45


def bs(s, k, vol, t):
    d1 = (math.log(s / k) + vol * vol * t / 2) / (vol * math.sqrt(t))
    return d1, d1 - vol * math.sqrt(t)


def test_q3():
    # Round 2.
    assert 16 / math.sqrt(256) == 1 and round(0.8 * 100 * 0.16 * 0.5, 1) == 6.4
    assert abs(2 * call(100, 100, 0.16, 0.25) - 6.4) < 0.05
    assert abs((call(100, 100, 0.21, 1) - call(100, 100, 0.19, 1)) / 2 - 0.4) < 0.01
    # Round 3.
    sig = 0.2 * math.sqrt(1 / 12)
    gam = norm.pdf(0) / (100 * sig)
    assert abs(sig - 0.2 * 0.289) < 1e-3
    assert round(gam, 3) == 0.069 and round(0.5 * gam * 4, 3) == 0.138
    assert round(20 / math.sqrt(252), 2) == 1.26 and round(0.5 * gam * 1.26**2, 3) == 0.055
    assert round((0.5 * gam * 4 - 0.5 * gam * 1.26**2) * 100, 1) == 8.3
    # Second route: bump the price of the option for gamma.
    h = 0.5
    bump = (call(100 + h, 100, 0.2, 1 / 12) + call(100 - h, 100, 0.2, 1 / 12) - 2 * call(100, 100, 0.2, 1 / 12)) / h**2
    assert abs(bump - gam) < 0.002
    # Round 4.
    assert 0.09 / 12 == 0.0075 and round(0.04 * 2 / 12, 4) == 0.0067 and 0.04 * 2 / 12 < 0.09 / 12
    # A dated event inside the first month is in both expiries' variance, so it cannot explain the fall.
    for event in (0.0, 0.002, 0.005, 0.0067):
        assert abs(((0.04 * 2 / 12 - event) - (0.09 / 12 - event)) - (0.04 * 2 / 12 - 0.09 / 12)) < 1e-12
        assert (0.04 * 2 / 12 - event) - (0.09 / 12 - event) < 0
    # The same fall at every strike: the longer option is cheaper, which zero rates forbid.
    for k in (90, 100, 110):
        assert call(100, k, 0.2, 2 / 12) < call(100, k, 0.3, 1 / 12)
    # Round 5.
    d1, d2 = bs(100, 90, 0.25, 1)
    assert round(d1, 3) == 0.546 and round(d2, 3) == 0.296
    assert round(norm.cdf(-d2), 3) == 0.383 and round(norm.cdf(-d1), 3) == 0.292
    put = 90 * norm.cdf(-d2) - 100 * norm.cdf(-d1)
    assert round(put, 2) == 5.27 and abs(put - (call(100, 90, 0.25, 1) - 100 + 90)) < 1e-9
    vega = 100 * norm.pdf(d1)
    assert round(vega, 1) == 34.4 and round(vega * 1e6 / 100, -4) == 340000
    # Round 6.
    gam2 = norm.pdf(d1) / 25
    assert round(gam2, 4) == 0.0137 and round(0.5 * gam2 * 100, 2) == 0.69
    est = norm.cdf(-d1) * 10 + 0.5 * gam2 * 100 + vega / 100 * 10
    assert round(est, 2) == 7.05 and round(est - norm.cdf(-d1) * 10, 1) == 4.1
    full = call(90, 90, 0.35, 1 - 1 / 252)
    assert round(0.4 * 90 * 0.35, 1) == 12.6 and round(full, 1) == 12.5 and round(full - put, 1) == 7.2
    assert 2 + 4 + 9 + 6 + 9 + 7 + 5 + 3 == 45


def test_q4():
    ni = (200 - 50 - 20) * 0.75
    fcf = (200 - 50) * 0.75 + 50 - 60 - 10
    assert ni == 97.5 and fcf == 92.5
    # Second route: net income, add back after-tax interest, depreciation, less investment.
    assert ni + 20 * 0.75 + 50 - 60 - 10 == fcf
    ev = fcf * 1.03 / 0.06
    assert round(fcf * 1.03, 1) == 95.3 and round(ev) == 1588 and round((ev - 300) / 100, 2) == 12.88 and round(ev / 200, 1) == 7.9
    # The perpetuity as a long sum.
    assert abs(sum(fcf * 1.03**t / 1.09**t for t in range(1, 3000)) - ev) < 1e-6
    ev2 = fcf * 1.02 / 0.07
    assert round(fcf * 1.02, 2) == 94.35 and round(ev2) == 1348 and round((ev2 - 300) / 100, 2) == 10.48
    assert round(1 - (ev2 - 300) / (ev - 300), 2) == 0.19 and round(1 - ev2 / ev, 2) == 0.15
    # A deal.
    assert 500 / 20 == 25 and 150 / 125 == 1.2 and 2500 / 125 == 20
    # With a target on the same multiple, nothing is accretive.
    assert (100 + 50) / (100 + 1000 / 20) == 1
    assert round(200 / 1100 * 365) == 66 and round(300 / 1200 * 365) == 91
    assert 2 + 7 + 8 + 6 + 6 + 8 + 5 + 3 == 45


def test_q5():
    n = 2 * (1.96 + 0.84) ** 2 * 0.021 * 0.979 / 0.002**2
    assert abs(n - 80600) < 50
    assert round(2 * n / 100000, 1) == 1.6
    # Power by simulation at that size.
    rng = np.random.default_rng(5)
    m = 81000
    a, b = rng.binomial(m, 0.02, 200000) / m, rng.binomial(m, 0.022, 200000) / m
    pool = (a + b) / 2
    z = (b - a) / np.sqrt(2 * pool * (1 - pool) / m)
    assert abs((np.abs(z) > 1.96).mean() - 0.80) < 0.01
    tp, fp = 0.005 * 0.7, 0.995 * 0.02
    assert round(tp, 4) == 0.0035 and round(fp, 4) == 0.0199 and round(tp / (tp + fp), 2) == 0.15

    px = [100] * 9 + [1000]
    assert np.mean(px) == 190 and np.median(px) == 100
    px = [100] * 9 + [70]
    assert np.mean(px) == 97 and np.median(px) == 100
    # Noise regression with 200 features on 5,000 rows.
    i, o = [], []
    for _ in range(12):
        x, y = rng.standard_normal((5000, 200)), rng.standard_normal(5000)
        c = np.linalg.lstsq(x, y, rcond=None)[0]
        i.append(1 - ((y - x @ c) ** 2).sum() / (y**2).sum())
        xo, yo = rng.standard_normal((5000, 200)), rng.standard_normal(5000)
        o.append(1 - ((yo - xo @ c) ** 2).sum() / (yo**2).sum())
    assert abs(np.mean(i) - 0.04) < 0.003 and abs(np.mean(o) + 0.04) < 0.005
    # Variance ratio: formula and simulation of an MA(1) with autocorrelation -0.1.
    vr = lambda q: 1 + 2 * (1 - 1 / q) * -0.1  # noqa: E731
    assert round(vr(2), 2) == 0.90 and round(vr(60), 3) == 0.803
    th = float(np.roots([0.1, 1, 0.1]).real.max())
    e = rng.standard_normal(4_000_001)
    r = e[1:] + th * e[:-1]
    assert abs(np.corrcoef(r[1:], r[:-1])[0, 1] + 0.1) < 0.002
    q60 = np.convolve(r, np.ones(60), mode="valid")[::60]
    assert abs(q60.var() / (60 * r.var()) - vr(60)) < 0.02
    assert 3 + 7 + 7 + 6 + 6 + 7 + 6 + 3 == 45


def test_q6():
    assert round((1.96 * 20 / 0.01) ** 2, -5) == 15400000
    assert round(1 / (0.1 + 0.9 / 10), 2) == 5.26
    # Antithetic pairs: variance of the pair average against two independent paths.
    z = np.random.default_rng(6).standard_normal(2_000_000)
    s = lambda u: 100 * np.exp(0.2 * u - 0.02)  # noqa: E731
    call_, stra = lambda v: np.maximum(v - 100, 0), lambda v: np.abs(v - 100)
    gain = lambda f: f(s(z)).var() / 2 / (((f(s(z)) + f(s(-z))) / 2).var())  # noqa: E731
    assert gain(call_) > 1.4 and gain(stra) < 1.2
    # Richardson, on an error that is exactly second order.
    f = lambda h: 10 + 0.8 * h * h  # noqa: E731
    assert abs(f(0.5) - 10.2) < 1e-12 and abs(f(0.25) - 10.05) < 1e-12
    assert abs((4 * f(0.25) - f(0.5)) / 3 - 10) < 1e-12 and abs(f(0.125) - 10.0125) < 1e-12
    # Floating point.
    assert (1e16 + 1) - 1e16 == 0 and np.spacing(1e16) == 2
    t = 1e16
    for _ in range(10000):
        t += 1.0
    assert t == 1e16 and math.fsum([1e16] + [1.0] * 10000) == 1e16 + 10000
    assert sum([1.0] * 10000) + 1e16 == 1e16 + 10000
    # Scale.
    assert 10000 * 101 * 0.001 == 1010 and round(1010 / 64, 1) == 15.8 and round(1010 / 60) == 17
    assert 10000 * 4 * 0.001 == 40
    # The bump: too small and too large are both worse than the cube root rule.
    eps = 2.2e-16
    assert round(eps ** (1 / 3) * 1e6) == 6
    d1 = (0.2 * 0.2 / 2) / 0.2
    exact = norm.cdf(d1)
    err = lambda h: abs((call(100 + h, 100, 0.2, 1) - call(100 - h, 100, 0.2, 1)) / (2 * h) - exact)  # noqa: E731
    best = err(100 * eps ** (1 / 3))
    assert best < err(1e-9) and best < err(5.0)
    # A delta is between 0 and 1 at every spot.
    for x in (50, 100, 200):
        assert 0 < norm.cdf((math.log(x / 100) + 0.02) / 0.2) < 1
    assert 2 + 7 + 7 + 6 + 8 + 7 + 5 + 3 == 45


def race_outcomes(n):
    """Every final counter value for two threads, each doing load, add, store n times."""
    seen = set()

    def go(ia, ib, ra, rb, mem):
        key = (ia, ib, ra, rb, mem)
        if key in seen:
            return {}
        seen.add(key)
        if ia == 2 * n and ib == 2 * n:
            return {mem}
        out = set()
        if ia < 2 * n:
            out |= (go(ia + 1, ib, mem, rb, mem) if ia % 2 == 0 else go(ia + 1, ib, ra, rb, ra + 1)) or set()
        if ib < 2 * n:
            out |= (go(ia, ib + 1, ra, mem, mem) if ib % 2 == 0 else go(ia, ib + 1, ra, rb, rb + 1)) or set()
        return out

    return go(0, 0, 0, 0, 0)


def test_q7():
    assert round(math.log2(1000)) == 10 and 10 * 100 == 1000
    n, m = 100000, 2**32
    mean = n * (n - 1) / 2 / m
    assert n * (n - 1) // 2 == 4999950000 and round(mean, 2) == 1.16 and round(1 - math.exp(-mean), 2) == 0.69
    assert round(n * (n - 1) / 2 / 2**64 * 1e10) == 3
    rng = np.random.default_rng(7)
    pairs = []
    for _ in range(200):
        x = np.sort(rng.integers(0, m, n))
        pairs.append(int((np.diff(x) == 0).sum()))
    assert abs(np.mean(pairs) - mean) < 0.25
    # The queue: formula, Little's law, simulation by Lindley's recursion.
    for lam, t, q in ((0.8, 5, 4), (0.95, 20, 19)):
        assert round(1 / (1 - lam), 6) == t and round(lam * t, 6) == q
        a = rng.exponential(1 / lam, 400000)
        sv = rng.exponential(1.0, 400000)
        w, total = 0.0, 0.0
        for i in range(1, 400000):
            w = max(0.0, w + sv[i - 1] - a[i])
            total += w + sv[i]
        assert abs(total / 399999 - t) / t < 0.12
    assert round(64e6 * 23400 / 1e12, 1) == 1.5 and round(64e6 * 23400 / 5 * 250 / 1e12) == 75 and 64 * 10 == 640
    # Disks read the compressed bytes: 128 at 5 to 1, and with no compression the raw 640.
    assert 64 * 10 / 5 == 128 and 64 * 10 / 1 == 640
    # The race: two threads, n increments each, every interleaving.
    assert min(race_outcomes(2)) == 2 and max(race_outcomes(2)) == 4
    assert min(race_outcomes(3)) == 2 and max(race_outcomes(3)) == 6
    # The stall.
    assert round(0.05 / 60 * 100, 3) == 0.083 and 0.05 / 60 < 0.001
    lat = np.r_[np.full(int(60 * 1000 - 50), 20.0), np.full(50, 50000.0)]
    assert np.quantile(lat, 0.999) == 20
    assert 2 + 8 + 6 + 7 + 5 + 7 + 7 + 3 == 45


def test_q8():
    assert 3e9 * 1e-6 == 3000 and round(100e-9 * 3e9) == 300 and 3000 // 300 == 10
    assert round(84 * 8 / 1e10 * 1e9, 1) == 67.2
    assert 1200 / 200000 * 1000 == 6 and 1200 / 300000 * 1000 == 4
    assert round(1 - 0.99**5, 3) == 0.049 and round(1 - 0.99**20, 3) == 0.182
    u = np.random.default_rng(8).random((1_000_000, 5))
    assert abs((u < 0.01).any(axis=1).mean() - 0.049) < 0.001
    # A shared stall: one draw for all the steps.
    assert abs((u[:, :1] < 0.01).any(axis=1).mean() - 0.01) < 0.001
    assert round(0.2 * 15) == 3 and 3 / 3e9 * 1e9 == 1
    assert 1000 * 8 / 64 == 125 and 1000 * 100e-3 == 100 and 125 * 100e-3 == 12.5
    n = 2 * (1.96 + 0.84) ** 2 * 50**2 / 2**2
    assert round(n) == 9800 and round((1 + 0.9) / (1 - 0.9)) == 19 and round(n * 19, -3) == 186000
    # The variance of a mean under AR(1), by simulation.
    rng = np.random.default_rng(88)
    e = rng.standard_normal((4000, 4000)) * math.sqrt(1 - 0.81)
    x = np.zeros_like(e)
    x[:, 0] = rng.standard_normal(4000)
    for i in range(1, 4000):
        x[:, i] = 0.9 * x[:, i - 1] + e[:, i]
    assert abs(x.mean(axis=1).var() * 4000 / 19 - 1) < 0.1
    # Power by simulation at 9,800 samples each.
    a = rng.normal(500, 50 / math.sqrt(9800), 200000)
    b = rng.normal(498, 50 / math.sqrt(9800), 200000)
    z = (a - b) / (50 * math.sqrt(2 / 9800))
    assert abs((np.abs(z) > 1.96).mean() - 0.80) < 0.01
    assert 2 + 5 + 7 + 6 + 7 + 6 + 9 + 3 == 45


def test_q9():
    q99, q95 = norm.ppf(0.99), norm.ppf(0.95)
    assert round(q99 * 10, 1) == 23.3 and round(q95 * 10, 1) == 16.4 and round(q99 * 10 * math.sqrt(10), 1) == 73.6
    var = 100 + 400 + 2 * 0.3 * 10 * 20
    assert var == 620 and round(math.sqrt(var), 1) == 24.9
    assert round(160 / 620, 2) == 0.26 and round(460 / 620, 2) == 0.74
    assert round(30 * q99, 1) == 69.8 and round(math.sqrt(var) * q99, 1) == 57.9 and round(30 * q99 - math.sqrt(var) * q99) == 12
    # The exceptions.
    pmf = [math.comb(250, k) * 0.01**k * 0.99 ** (250 - k) for k in range(8)]
    tail = 1 - sum(pmf)
    assert 250 * 0.01 == 2.5 and round(tail * 100, 1) == 0.4
    z = -norm.ppf(8 / 250)
    assert round(z, 3) == 1.852 and round(q99 / z, 2) == 1.26
    # Shortfall.
    es = norm.pdf(1.96) / 0.025
    assert round(es, 2) == 2.34 and round(q99, 2) == 2.33
    from scipy.stats import t as student

    scale = math.sqrt(2)
    var_t = student.ppf(0.99, 4) / scale
    x = student.ppf(0.975, 4)
    es_t = (student.pdf(x, 4) / 0.025) * ((4 + x * x) / 3) / scale
    assert round(var_t, 2) == 2.65 and round(es_t, 2) == 2.82
    sim = np.random.default_rng(9).standard_t(4, 4_000_000) / scale
    cut = np.quantile(sim, 0.975)
    assert abs(sim[sim >= cut].mean() - es_t) < 0.02 and abs(sim.std() - 1) < 0.02
    # Liquidity.
    assert 100 / (0.2 * 20) == 25
    s = sum((k / 25) ** 2 for k in range(1, 26))
    assert round(s, 2) == 8.84 and round(math.sqrt(s), 2) == 2.97
    # Credit.
    assert round(0.02 * 0.6 * 100, 2) == 1.2 and round(0.02 * 0.6 * 1e4) == 120
    assert 2 + 7 + 6 + 8 + 5 + 6 + 4 + 7 == 45


def test_q10():
    assert round((15 - 0.4) / 125 * 100, 2) == 11.68 and round(0.05 * 125 + 0.4, 2) == 6.65
    # Touching a level, with the reflection principle.
    sig = 0.8 * math.sqrt(30 / 365)
    assert round(math.log(1.25), 3) == 0.223 and round(sig, 3) == 0.229
    p25 = 2 * norm.cdf(-math.log(1.25) / sig)
    p50 = 2 * norm.cdf(-math.log(1.5) / sig)
    assert round(math.log(1.25) / sig, 2) == 0.97 and round(p25, 2) == 0.33
    assert round(math.log(1.5), 3) == 0.405 and round(math.log(1.5) / sig, 2) == 1.77 and round(p50, 2) == 0.08
    assert round(15 / 150, 2) == 0.10
    rng = np.random.default_rng(10)
    st = rng.standard_normal((40000, 720)) * 0.8 * math.sqrt(1 / (365 * 24))
    top = st.cumsum(axis=1).max(axis=1)
    assert p25 - 0.04 < (top > math.log(1.25)).mean() < p25 + 0.005
    assert p50 - 0.02 < (top > math.log(1.5)).mean() < p50 + 0.005
    # Venues.
    assert 0.02 * 125 == 2.5 and round(3 * 0.02 * 125 / 3, 2) == 2.5 and round(125 / 3, 1) == 41.7
    assert round(1 - 0.98**3, 3) == 0.059 and 0.02 * 25 == 0.5
    # Two venues.
    assert 20 - 2 * 5 == 10 and 10 - 8 == 2

    def venues(fill, rebalance=8):  # the rebalance is paid only when both legs fill, as the prompt says
        return fill * (10 - rebalance) - (1 - fill) * 15

    assert round(venues(0.8), 6) == -1.4
    assert venues(1.0) == 2 and venues(0.0) == -15  # limits: every fill, and every miss
    assert round(venues(0.8, rebalance=0), 6) == 5 and abs(venues(15 / 25, rebalance=0)) < 1e-9
    assert abs(venues(15 / 17)) < 1e-9 and round(15 / 17 * 100) == 88
    filled = rng.random(1_000_000) < 0.8
    assert abs(np.where(filled, 10 - 8, -15).mean() + 1.4) < 0.02
    # Sizing, with a search for the best split at 20 percent volatility.
    th = np.linspace(0, math.pi / 2, 200001)
    ret = 2 * 20 * np.cos(th) + 1.5 * 20 * np.sin(th)
    i = ret.argmax()
    assert abs(20 * math.cos(th[i]) - 16) < 1e-3 and abs(20 * math.sin(th[i]) - 12) < 1e-3
    assert 16**2 + 12**2 == 20**2 and 2 * 16 + 1.5 * 12 == 50 and math.hypot(2, 1.5) == 2.5
    assert 2 * 16 + 0.75 * 12 == 41 and 41 / 20 == 2.05
    # A bad week.
    w, g = 20 / math.sqrt(52), 50 / 52
    z = (-6 - g) / w
    assert round(w, 2) == 2.77 and round(g, 2) == 0.96 and round(z, 2) == -2.51
    assert round(norm.cdf(z) * 100, 1) == 0.6 and round(1 / (norm.cdf(z) * 52)) == 3
    assert 5 + 10 + 8 + 7 + 8 + 8 + 9 + 5 == 60
