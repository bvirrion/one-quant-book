"""The Vol Surface and Vol Trading. Every printed surface number from a model, checked by simulation or a grid."""
from math import exp, log, pi, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.linalg import solve_banded
from scipy.optimize import brentq
from scipy.stats import norm

N, n = norm.cdf, norm.pdf
NONNUMERIC = {
    6: "why a surface has a skew: a judgement in words; the numbers in the stem carry no calculation",
}


def d1(s, k, v, t):
    return (log(s / k) + v * v * t / 2) / (v * sqrt(t))


def call(s, k, v, t):
    a = d1(s, k, v, t)
    return s * N(a) - k * N(a - v * sqrt(t))


def put(s, k, v, t):
    return call(s, k, v, t) - s + k


def vega(s, k, v, t):
    return s * n(d1(s, k, v, t)) * sqrt(t)


def iv(price, s, k, t):
    return brentq(lambda v: call(s, k, v, t) - price, 1e-4, 5)


def mix(k, t=1.0):
    return 0.5 * call(100, k, 0.1, t) + 0.5 * call(100, k, 0.3, t)


def test_q1():
    r = np.array([1, -1, 2, -2, 0]) / 100
    assert round(sqrt((r**2).mean()) * sqrt(252) * 100, 1) == 22.4
    assert round(sqrt(2), 3) == 1.414 and (r**2 * 1e4).sum() == 10
    # With returns of mean zero, the two estimators agree here.
    assert abs(r.std() - sqrt((r**2).mean())) < 1e-12


def test_q2():
    assert round(sqrt(252), 1) == 15.9 and round(24 / sqrt(252), 1) == 1.5
    assert round(sqrt(365)) == 19 and round(24 / sqrt(365), 2) == 1.26
    assert round(24 / sqrt(252) * sqrt(2 / pi), 1) == 1.2


def test_q3():
    m = 100 * 0.25 / sqrt(252)
    assert round(m, 2) == 1.57 and round(2 * (1 - N(1)), 2) == 0.32
    g = n(d1(100, 100, 0.25, 0.5)) / (100 * 0.25 * sqrt(0.5))
    th = 0.5 * g * 1e4 * 0.0625 / 252
    assert abs(0.5 * g * m * m - th) < 1e-12


def test_q4():
    f = (0.22**2 * 0.5 - 0.25**2 * 0.25) / 0.25
    assert round(f, 4) == 0.0343 and round(sqrt(f) * 100, 1) == 18.5 and 2 * 22 - 25 == 19
    assert round(0.22**2 * 0.5, 4) == 0.0242 and round(0.25**2 * 0.25, 4) == 0.0156
    # Independent periods: simulated variance adds across them.
    rng = np.random.default_rng(4)
    a = 0.25 * sqrt(0.25) * rng.standard_normal(1_000_000)
    b = sqrt(f * 0.25) * rng.standard_normal(1_000_000)
    assert abs((a + b).var() - 0.22**2 * 0.5) < 1e-3


def test_q5():
    assert 0.09 * 0.25 > 0.04 * 0.5
    assert round(call(100, 100, 0.3, 0.25), 2) == 5.98 and round(call(100, 100, 0.2, 0.5), 2) == 5.64
    assert round(call(100, 100, 0.3, 0.25) - call(100, 100, 0.2, 0.5), 2) == 0.34


def test_q7():
    assert 100_000 / 40 == 2500
    assert 2500 * (625 - 400) == 562_500 and 2500 * (225 - 400) == -437_500
    # Near the strike one volatility point is worth the vega notional.
    assert abs(2500 * (20.01**2 - 400) / 0.01 - 100_000) < 30


def test_q8():
    assert round(20 / sqrt(40), 2) == 3.16 and 20 / sqrt(2 * 200) == 1
    rng = np.random.default_rng(8)
    x = 0.2 / sqrt(252) * rng.standard_normal((100_000, 20))
    est = np.sqrt((x**2).mean(1) * 252)
    assert abs(est.std() - 0.0316) < 0.0015
    assert np.quantile(est, 0.025) > 0.135 and np.quantile(est, 0.975) < 0.265


def test_q9():
    assert round((18 / 30) ** 2, 2) == 0.36
    assert abs(30 * sqrt(1 / 5000 + (1 - 1 / 5000) * 0.36) - 18) < 0.01


def test_q10():
    vals = {k: round(iv(mix(k), 100, k, 1) * 100, 2) for k in (100, 80, 130)}
    assert vals == {100: 19.98, 80: 22.91, 130: 23.60}
    assert round(sqrt(0.05) * 100, 2) == 22.36
    # With no spread of states, the smile vanishes.
    assert abs(iv(call(100, 130, 0.2, 1), 100, 130, 1) - 0.2) < 1e-6
    # Symmetry in log strike around the forward of the log's natural centre is only rough: check the shape.
    assert iv(mix(80), 100, 80, 1) > iv(mix(100), 100, 100, 1) < iv(mix(130), 100, 130, 1)


def test_q11():
    c = [call(100, k, 0.2, 1) for k in (95, 100, 105)]
    assert [round(x, 2) for x in c] == [10.52, 7.97, 5.91]
    assert round((c[0] - 2 * c[1] + c[2]) / 25, 4) == 0.0198 and round((10.52 - 2 * 7.97 + 5.91) / 25, 4) == 0.0196
    assert round(n(-0.1) / 20, 5) == 0.01985
    # Rounding the quotes moves the answer by up to the stated amount.
    assert abs((10.52 - 2 * 7.97 + 5.91) / 25 - (c[0] - 2 * c[1] + c[2]) / 25) < 0.0008
    assert round(0.02 / 25, 4) == 0.0008 and round(0.0008 / 0.0198 * 100) == 4


def test_q12():
    assert 20 - 0.5 == 19.5 and 20 + 0.5 == 20.5
    assert round(vega(105, 100, 0.2, 1) / 100, 2) == 0.39
    assert round(call(105, 100, 0.205, 1) - call(105, 100, 0.2, 1), 1) == 0.2


def test_q13():
    assert round(N(0.1), 2) == 0.54 and round(vega(100, 100, 0.2, 1), 1) == 39.7
    assert round(39.7 * 0.002, 3) == 0.079
    assert round(0.54 + 0.079, 2) == 0.62 and round(0.54 - 0.079, 2) == 0.46

    def sm(s, k):  # smile depending on K/S, with the stated slope at the money
        return call(s, k, 0.2 - 0.2 * log(k / s), 1)

    h = 1e-3
    assert abs((sm(100 + h, 100) - sm(100 - h, 100)) / (2 * h) - 0.619) < 0.002


def test_q14():
    assert 2 * 0.5 == 1 and 1.5 - 1 == 0.5
    # The old strike is 2% above the new centre, on a smile lifted half a point.
    new_atm, slope = 1.5, -0.5
    assert new_atm + slope * 2 == 0.5


def test_q15():
    assert round(100_000 / 44 * 160, -2) == 363_600 and round(100_000 / 44) == 2273
    assert round(160 / 44, 1) == 3.6 and 22 - 18 == 4 and 160 / 44 < 4


def test_q16():
    assert round(1 / (4 * log(2)), 2) == 0.36 and round(4 * log(2), 2) == 2.77
    rng = np.random.default_rng(16)
    x = np.cumsum(rng.standard_normal((4000, 5000)) / sqrt(5000), axis=1)
    hi = x.max(1).clip(min=0)
    lo = x.min(1).clip(max=0)
    p = (hi - lo) ** 2 / (4 * log(2))
    assert abs(p.mean() - 1) < 0.05  # finely sampled, it is the variance
    ratio = p.var() / (x[:, -1] ** 2).var()
    assert 0.15 < ratio < 0.25
    # Coarser sampling of the same paths misses highs and lowers it.
    c = x[:, ::100]
    assert ((c.max(1).clip(min=0) - c.min(1).clip(max=0)) ** 2 / (4 * log(2))).mean() < p.mean()


def test_q17():
    assert round(25 * sqrt(365 / (3 * 252)), 1) == 17.4 and round(25 * sqrt(365 / 252)) == 30
    assert abs((0.174**2 * 3 / 365) / (0.25**2 / 252) - 1) < 0.01


def test_q18():
    w1, w2 = 0.36 * 5 / 252, 0.16 * 25 / 252
    assert round(w1, 5) == 0.00714 and round(w2, 5) == 0.01587
    base = (w2 - w1) * 252 / 20
    assert round(w2 - w1, 5) == 0.00873 and round(base, 3) == 0.110 and round(sqrt(base) * 100, 1) == 33.2
    e = w1 - base * 5 / 252
    assert round(e, 5) == 0.00496 and round(sqrt(e) * 100, 2) == 7.04
    assert round(sqrt(e) * sqrt(2 / pi) * 100, 1) == 5.6
    # Putting them together gives both quotes back.
    assert abs(sqrt((base * 25 / 252 + e) * 252 / 25) - 0.4) < 1e-9


def test_q19():
    t = 30 / 365
    v = sqrt(0.0625 + 0.0036 / t)
    assert round(v * 100, 1) == 32.6
    st = 2 * call(100, 100, v, t)
    assert round(st, 2) == 7.46

    def after(s):
        return call(s, 100, 0.25, 29 / 365) + put(s, 100, 0.25, 29 / 365)

    assert [round(after(s), 2) for s in (100, 103, 106, 110)] == [5.62, 6.20, 7.66, 10.60]
    be = brentq(lambda s: after(s) - st, 100, 115)
    assert round(be - 100, 1) == 5.7
    assert round(st - after(100), 2) == 1.83 and round(0.06 * sqrt(2 / pi) * 100, 1) == 4.8


def test_q20():
    assert round(sqrt(0.0425) * 100, 1) == 20.6 and 20**2 + 5**2 == 425
    # A distribution with those moments: the volatility swap's fair value is its mean, whatever its shape.
    rng = np.random.default_rng(20)
    s = 20 + 5 * rng.standard_normal(2_000_000)
    assert abs(sqrt((s**2).mean()) - 20.6) < 0.02 and abs(s.mean() - 20) < 0.02


def test_q21():
    def idx(sig, rho, m=50):
        return sqrt(sig**2 * (1 / m + (1 - 1 / m) * rho))

    assert round(idx(0.3, 0.3) * 100, 1) == 16.8 and round(idx(0.3, 0.2) * 100, 1) == 13.9
    assert round(idx(0.33, 0.2) * 100, 1) == 15.3
    assert round(idx(0.3, 0.3) ** 2, 5) == 0.02826 and round(idx(0.3, 0.2) ** 2, 5) == 0.01944
    assert round((idx(0.3, 0.3) ** 2 - idx(0.3, 0.2) ** 2) * 1e4) == 88
    rng = np.random.default_rng(21)
    m = 50
    z = rng.standard_normal((200_000, m))
    f = rng.standard_normal((200_000, 1))
    r = 0.3 * (sqrt(0.3) * f + sqrt(0.7) * z)
    assert abs(r.mean(1).std() - idx(0.3, 0.3)) < 0.001


def test_q22():
    assert round(put(100, 100, 0.2, 1) - put(100, 90, 0.25, 1), 2) == 2.69
    assert round(put(100, 100, 0.2, 1) - put(100, 90, 0.2, 1), 2) == 4.38
    assert round(put(100, 90, 0.25, 1), 2) == 5.27 and round(put(100, 90, 0.2, 1), 2) == 3.59
    assert round(put(100, 100, 0.2, 1), 2) == 7.97


def heston(v0, theta, kappa, xi, rho, t, steps, count, seed, with_noise=True):
    rng = np.random.default_rng(seed)
    x = np.zeros(count)
    v = np.full(count, v0)
    dt = t / steps
    bar = np.zeros(count)
    for _ in range(steps):
        z2 = rng.standard_normal(count)
        vp = np.maximum(v, 0)
        bar += vp * dt
        if with_noise:
            z1 = rng.standard_normal(count) * sqrt(1 - rho * rho) + rho * z2
            x += -0.5 * vp * dt + np.sqrt(vp * dt) * z1
        v = v + kappa * (theta - vp) * dt + xi * np.sqrt(vp * dt) * z2
    return 100 * np.exp(x), bar / t, v


def test_q23():
    assert round(2 * 2 * 0.04, 2) == 0.16 and 0.16 < 0.5**2
    _, _, v = heston(0.04, 0.04, 2.0, 0.5, 0.0, 1.0, 250, 20_000, 23)
    assert (v < 0).mean() > 0  # the plain step does cross below zero
    # With a small vol of vol the condition holds, and at the same step it does not cross.
    _, _, w = heston(0.04, 0.04, 2.0, 0.1, 0.0, 1.0, 250, 20_000, 23)
    assert (w < 0).mean() == 0


def test_q24():
    a, b = 0.04 / 12, 0.0484 * 0.25
    assert round(a, 5) == 0.00333 and round(b, 4) == 0.0121 and round((a + b) / 2, 5) == 0.00772
    assert round(sqrt((a + b) / 2 * 6) * 100, 1) == 21.5
    # Equal time weights hold: two months is halfway.
    assert abs((1 / 12 + 3 / 12) / 2 - 2 / 12) < 1e-12
    # A steep curve with no arbitrage at the ends: total variance rises from 0.0533 to 0.0625.
    v1, v2 = 0.8, 0.25
    t1, t2 = 1 / 12, 1.0
    w1, w2 = v1**2 * t1, v2**2 * t2
    assert w2 > w1
    # Linear in volatility overshoots, so total variance then falls: a calendar arbitrage it made up.
    lin = v1 + (v2 - v1) * (0.5 - t1) / (t2 - t1)
    assert lin**2 * 0.5 > w2
    # Linear in total variance stays between the two ends at every date.
    grid = [t1 + (t2 - t1) * i / 50 for i in range(51)]
    path = [w1 + (w2 - w1) * (t - t1) / (t2 - t1) for t in grid]
    assert all(b >= a for a, b in zip(path, path[1:], strict=False))


def test_q25():
    assert 0.5 * 625 + 0.5 * 484 == 554.5 and 2500 * (554.5 - 400) == 386_250
    assert round(2500 * 0.5 * 2 * 22, -3) == 55_000
    # Start of life: the same rule at strike 20 gives the vega notional.
    assert round(2500 * 2 * 20) == 100_000


def test_q26():
    ks = np.linspace(10, 1000, 19_801)
    dk = ks[1] - ks[0]

    def dollar_gamma(s, wfun):
        a = (np.log(s / ks) + 0.02) / 0.2
        g = n(a) / (s * 0.2)
        return s * s * (wfun(ks) * g).sum() * dk

    ones = [dollar_gamma(s, lambda k: 1 / k**2) for s in (80.0, 100.0, 120.0)]
    assert max(ones) / min(ones) - 1 < 0.002
    flat = [dollar_gamma(s, lambda k: np.ones_like(k)) for s in (80.0, 100.0, 120.0)]
    assert abs(flat[2] / flat[0] - 1.5**2) < 0.05 and abs(flat[1] / flat[0] - (100 / 80) ** 2) < 0.05
    # The log-contract value, and the strike the strip gives.
    a = quad(lambda k: put(100, k, 0.2, 1) / k**2, 1, 100, limit=200)[0]
    b = quad(lambda k: call(100, k, 0.2, 1) / k**2, 100, 2000, limit=200)[0]
    assert abs(2 * (a + b) - 0.04) < 1e-5


def test_q27():
    def c(k, slope):
        v = sqrt(slope * abs(log(k / 100)))
        return call(100, k, v, 1)

    far = (1e3, 1e4, 1e6, 1e8)
    bad = [c(k, 3.0) for k in far]
    good = [c(k, 1.5) for k in far]
    assert all(np.diff(bad) > 0) and round(c(300, 3.0)) == 42 and round(bad[-1]) == 82
    assert all(np.diff(good) < 0) and round(good[0]) == 23 and round(good[-1]) == 17
    assert round(log(4), 3) == 1.386 and round(2 * log(4), 2) == 2.77 and round(sqrt(2 * log(4)), 3) == 1.665


def test_q28():
    h, e = 0.5, 1e-3

    def dupire(fn, k, t):
        dt = (fn(k, t + e) - fn(k, t - e)) / (2 * e)
        dk = (fn(k + h, t) - 2 * fn(k, t) + fn(k - h, t)) / h**2
        return sqrt(2 * dt / (k * k * dk))

    assert abs(dupire(lambda k, t: call(100, k, 0.2, t), 100.0, 1.0) - 0.2) < 1e-4
    assert abs(dupire(lambda k, t: call(100, k, 0.2, t), 130.0, 0.5) - 0.2) < 1e-3
    got = dupire(mix, 100.0, 1.0)
    assert round(got * 100, 1) == 17.3
    assert abs(got - sqrt(lvar(0.0, 1.0))) < 1e-4
    a = n(0.05) / 0.1
    b = n(0.15) / 0.3
    assert round(a / (a + b), 2) == 0.75
    assert round(sqrt(0.75 * 0.01 + 0.25 * 0.09) * 100, 1) == 17.3


def local_paths(s0, count=120_000, steps=250, seed=29):
    rng = np.random.default_rng(seed)
    x = np.full(count, log(s0 / 100))
    dt = 1 / steps
    for _ in range(steps):
        lv = np.clip(0.2 - 0.2 * x, 0.02, 1.0)
        x += lv * sqrt(dt) * rng.standard_normal(count) - 0.5 * lv * lv * dt
    return 100 * np.exp(x)


def test_q29():
    s = local_paths(100)
    vals = [iv(np.maximum(s - k, 0).mean(), 100, k, 1) * 100 for k in (80, 100, 120)]
    assert abs(vals[0] - 22.05) < 0.2 and abs(vals[1] - 19.98) < 0.15 and abs(vals[2] - 18.13) < 0.2
    slope = (vals[2] - vals[0]) / 100 / log(120 / 80)
    assert abs(slope + 0.1) < 0.01


def test_q30():
    s = local_paths(105)
    at105 = iv(np.maximum(s - 105, 0).mean(), 105, 105, 1) * 100
    at100 = iv(np.maximum(s - 100, 0).mean(), 105, 100, 1) * 100
    assert abs(at105 - 19.01) < 0.15 and abs(at100 - 19.48) < 0.15
    assert round(19.98 - 19.01, 2) == 0.97 and round(19.98 - 19.48, 2) == 0.50
    assert round(0.1 * log(1.05) * 100, 2) == 0.49


def test_q31():
    def avg(t):
        return 0.09 + (0.04 - 0.09) * (1 - exp(-2 * t)) / (2 * t)

    assert [round(sqrt(avg(t)) * 100, 1) for t in (0.25, 1.0, 4.0)] == [22.5, 26.2, 28.9]
    assert round(avg(1.0), 4) == 0.0684 and round((1 - exp(-2)) / 2, 3) == 0.432
    _, bar, _ = heston(0.04, 0.09, 2.0, 0.5, 0.0, 1.0, 250, 100_000, 31, with_noise=False)
    assert abs(bar.mean() - avg(1.0)) < 0.0006
    for rho, want in ((-0.7, (23.1, 18.1, 14.6)), (0.0, (20.4, 18.8, 19.9))):
        s, _, _ = heston(0.04, 0.04, 2.0, 0.5, rho, 1.0, 250, 120_000, 1)
        got = [iv(np.maximum(s - k, 0).mean(), 100, k, 1) * 100 for k in (80, 100, 120)]
        assert max(abs(a - b) for a, b in zip(got, want, strict=True)) < 0.25
    # The mean of the volatility is below the root of the mean variance.
    assert np.sqrt(np.maximum(bar, 0)).mean() < sqrt(bar.mean())


def sabr(f, k, a, nu, rho, t):
    tail = 1 + (rho * nu * a / 4 + (2 - 3 * rho * rho) * nu * nu / 24) * t
    if abs(f - k) < 1e-9:
        return a * tail
    z = nu / a * log(f / k)
    x = log((sqrt(1 - 2 * rho * z + z * z) + z - rho) / (1 - rho))
    return a * z / x * tail


def test_q32():
    assert [round(sabr(100, k, 0.2, 0.4, -0.3, 1) * 100, 2) for k in (100, 80, 120)] == [20.11, 21.93, 19.44]
    rng = np.random.default_rng(3)
    c = 200_000
    x, a = np.zeros(c), np.full(c, 0.2)
    dt = 1 / 250
    for _ in range(250):
        z1 = rng.standard_normal(c)
        z2 = -0.3 * z1 + sqrt(1 - 0.09) * rng.standard_normal(c)
        x += -0.5 * a * a * dt + a * sqrt(dt) * z1
        a = a * np.exp(0.4 * sqrt(dt) * z2 - 0.08 * dt)
    s = 100 * np.exp(x)
    got = [iv(np.maximum(s - k, 0).mean(), 100, k, 1) * 100 for k in (100, 80, 120)]
    assert [round(g, 2) for g in got] == [20.14, 21.87, 19.44]
    assert round(0.3 * 0.4 * 0.2 / 4, 3) == 0.006
    assert round((2 - 3 * 0.09) * 0.16 / 24, 5) == 0.01153
    assert round(0.2 * (1 - 0.006 + (2 - 3 * 0.09) * 0.16 / 24), 4) == 0.2011
    # The printed sum is the formula's own value at the money, not merely close to it.
    assert abs(0.2 * (1 - 0.006 + (2 - 3 * 0.09) * 0.16 / 24) - sabr(100, 100, 0.2, 0.4, -0.3, 1)) < 1e-4


def merton(k, t, lam=0.1, jump=-0.2, sig=0.15):
    total = 0.0
    p = exp(-lam * t)
    for j in range(40):
        total += p * call(100 * exp(-lam * jump * t) * (1 + jump) ** j, k, sig, t)
        p *= lam * t / (j + 1)
    return total


def test_q33():
    want = {1 / 12: (20.8, 15.6, 15.2), 1.0: (16.7, 16.3, 16.0)}
    for t, w in want.items():
        got = [iv(merton(k, t), 100, k, t) * 100 for k in (90, 100, 110)]
        assert [round(g, 1) for g in got] == list(w)
    rng = np.random.default_rng(33)
    c = 2_000_000
    jumps = rng.poisson(0.1 / 12, c)
    s = 100 * exp(0.2 * 0.1 / 12) * 0.8**jumps * np.exp(0.15 * sqrt(1 / 12) * rng.standard_normal(c) - 0.5 * 0.0225 / 12)
    assert abs(s.mean() - 100) < 0.05
    assert abs(np.maximum(90 - s, 0).mean() - (merton(90, 1 / 12) - 10)) < 0.01


def test_q34():
    j = log(0.8)
    assert round(j * j, 4) == 0.0498 and round(2 * (-0.2 - j), 4) == 0.0463
    assert round(j * j - 2 * (-0.2 - j), 4) == 0.0035
    u = log(1.2)
    assert round(u * u, 4) == 0.0332 and round(2 * (0.2 - u), 4) == 0.0354
    assert round(2 * (0.2 - u) - u * u, 4) == 0.0021
    # Small moves agree, and the mismatch goes as the cube of the move.
    r = 0.01
    assert abs(log(1 + r) ** 2 - 2 * (r - log(1 + r))) < 1e-6


def smile_otm(k, slope=-0.1, floor=0.03):
    v = max(floor, 0.2 + slope * log(k / 100))
    return put(100, k, v, 1) if k < 100 else call(100, k, v, 1)


def strip_exact():
    return 2 * (quad(lambda k: smile_otm(k) / k**2, 1, 100, limit=300)[0] + quad(lambda k: smile_otm(k) / k**2, 100, 800, limit=300)[0])


def test_q35():
    x = strip_exact()
    assert round(x, 4) == 0.0422 and round(sqrt(x) * 100, 2) == 20.54
    assert round(0.04 * (1 + 3 * 0.01), 4) == 0.0412 and round(sqrt(0.0412) * 100, 2) == 20.30
    assert round(sqrt(x) * 100 - sqrt(0.0412) * 100, 2) == 0.24
    # The stated 3% floor sits far out: a 5% floor does not move the printed value.
    alt = 2 * (quad(lambda k: smile_otm(k, floor=0.05) / k**2, 1, 100, limit=300)[0] + quad(lambda k: smile_otm(k, floor=0.05) / k**2, 100, 800, limit=300)[0])
    assert abs(alt - x) < 1e-5
    assert abs(2 * (quad(lambda k: smile_otm(k, 0.0) / k**2, 1, 100, limit=300)[0] + quad(lambda k: smile_otm(k, 0.0) / k**2, 100, 800, limit=300)[0]) - 0.04) < 1e-6


def test_q36():
    lo, hi = 0.3 * sqrt(0.2), 0.3 * sqrt(0.8)
    assert round(lo * 100, 1) == 13.4 and round(hi * 100, 1) == 26.8

    def p(k, fa=100.0, fb=100.0):
        return 0.8 * call(fa, k, lo, 1) + 0.2 * call(fb, k, hi, 1)

    v = [iv(p(k), 100, k, 1) * 100 for k in (80, 100, 120)]
    assert [round(x, 1) for x in v] == [17.4, 16.1, 17.0]
    w = [iv(p(k, 103.75, 85.0), 100, k, 1) * 100 for k in (80, 100, 120)]
    assert round(0.8 * 103.75 + 0.2 * 85, 6) == 100
    assert w[0] - w[2] > 3 and v[0] - v[2] < 0.5


def test_q37():
    t = 1 / 12
    rng = np.random.default_rng(1)
    c, steps = 40_000, 21
    dt = t / steps
    s = np.full(c, 100.0)
    pnl = np.full(c, 2 * call(100, 100, 0.2, t))
    tau = t
    for _ in range(steps):
        d = 2 * N((np.log(s / 100) + 0.02 * tau) / (0.2 * sqrt(tau))) - 1
        ns = s * np.exp(0.16 * sqrt(dt) * rng.standard_normal(c) - 0.5 * 0.0256 * dt)
        pnl += d * (ns - s)
        s = ns
        tau -= dt
    pnl -= np.abs(s - 100)
    assert round(2 * call(100, 100, 0.2, t), 2) == 4.61
    assert round(pnl.mean(), 2) == 0.93 and round(pnl.std(), 2) == 0.75
    assert round((pnl < 0).mean(), 2) == 0.09 and round(float(np.quantile(pnl, 0.01)), 2) == -0.68
    assert round(pnl.mean() / pnl.std(), 1) == 1.2
    theory = 2 * call(100, 100, 0.2, t) - 2 * call(100, 100, 0.16, t)
    assert round(theory, 2) == 0.92 and abs(4 * 2 * vega(100, 100, 0.18, t) / 100 - theory) < 0.01
    assert round(4 * 2 * vega(100, 100, 0.18, t) / 100 / 4, 2) == 0.23
    # A 20 percent gap: the straddle's loss, before the hedge's small offset.
    assert round(abs(80 - 100) - 4.61, 1) == 15.4 and round(15.4 / 0.92) == 17


def test_q38():
    x = strip_exact()
    assert round(x, 5) == 0.04218

    def grid(step, lo, hi):
        ks = np.arange(lo, hi + step, step)
        return 2 * sum(smile_otm(float(k)) / k**2 for k in ks) * step

    vals = {(1, 50, 200): 0.04205, (5, 50, 200): 0.04250, (10, 50, 200): 0.04378, (5, 70, 140): 0.04096}
    for key, want in vals.items():
        assert round(grid(*key), 5) == want
    # Wide and fine gets the integral: both errors are the ones named.
    assert abs(grid(1, 1, 800) - x) < 2e-4


def test_q39():
    s, bar, _ = heston(0.04, 0.04, 2.0, 0.5, 0.0, 1.0, 250, 120_000, 39)
    vb = np.sqrt(np.maximum(bar, 1e-8))
    for k in (80, 100, 120):
        a = np.array([0.0])
        lk = np.log(100 / k)
        d = (lk + vb * vb / 2) / vb
        a = 100 * N(d) - k * N(d - vb)
        plain = np.maximum(s - k, 0)
        assert abs(a.mean() - plain.mean()) < 3 * plain.std() / sqrt(120_000)
        if k == 100:
            assert round(plain.std() / a.std()) == 5
    # Volatility fixed: mixing gives the formula itself.
    assert abs(100 * N(0.1) - 100 * N(-0.1) - call(100, 100, 0.2, 1)) < 1e-12


def lvar(x, t, s1=0.1, s2=0.3):
    a = -((x + 0.5 * s1 * s1 * t) ** 2) / (2 * s1 * s1 * t) - log(s1 * sqrt(t))
    b = -((x + 0.5 * s2 * s2 * t) ** 2) / (2 * s2 * s2 * t) - log(s2 * sqrt(t))
    m = np.maximum(a, b)
    wa, wb = np.exp(a - m), np.exp(b - m)
    return (wa * s1 * s1 + wb * s2 * s2) / (wa + wb)


def price_grid(k, dx=0.005, xmax=2.2, m=500):
    x = np.arange(-xmax, xmax + dx / 2, dx)
    val = np.maximum(100 * np.exp(x) - k, 0)
    ts = (np.arange(m + 1) / m) ** 2  # bunched near zero
    for i in range(m - 1, -1, -1):
        dt = ts[i + 1] - ts[i]
        v = lvar(x[1:-1], 0.5 * (ts[i] + ts[i + 1]))
        a = 0.5 * v / dx**2 + 0.25 * v / dx
        b = 0.5 * v / dx**2 - 0.25 * v / dx
        ab = np.zeros((3, len(x) - 2))
        ab[0, 1:] = -dt * b[:-1]
        ab[1] = 1 + dt * v / dx**2
        ab[2, :-1] = -dt * a[1:]
        rhs = val[1:-1].copy()
        rhs[0] += dt * a[0] * val[0]
        rhs[-1] += dt * b[-1] * val[-1]
        val[1:-1] = solve_banded((1, 1), ab, rhs)
    return float(np.interp(0.0, x, val))


def test_q40():
    assert abs(lvar(0.0, 1.0) - 0.75 * 0.01 - 0.25 * 0.09) < 3e-4
    want = {k: iv(mix(k), 100, k, 1) * 100 for k in (70, 100, 130)}
    assert round(want[70], 2) == 24.97
    worst = 0.0
    for k in want:
        worst = max(worst, abs(iv(price_grid(k), 100, k, 1) * 100 - want[k]))
    assert worst < 0.02
    # Plain daily Euler falls short at the far strike, and the fall is bias: it does not leave with more paths.
    rng = np.random.default_rng(7)
    c, steps = 100_000, 250
    x = np.zeros(c)
    dt = 1 / steps
    for i in range(steps):
        v = lvar(x, max((i + 0.5) * dt, dt / 2))
        x += -0.5 * v * dt + np.sqrt(v * dt) * rng.standard_normal(c)
    s = 100 * np.exp(x)
    got = iv(np.maximum(s - 70, 0).mean(), 100, 70, 1) * 100
    assert abs(got - 23.2) < 0.2 and want[70] - got > 1
    assert abs(s.mean() - 100) > 0.05
