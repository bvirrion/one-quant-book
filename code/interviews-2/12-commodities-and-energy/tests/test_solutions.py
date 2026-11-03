"""Commodities and Energy. Curves by hand, physical assets as options, each checked by a second route."""
from itertools import combinations
from math import cos, exp, log, pi, sqrt

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

N, n = norm.cdf, norm.pdf
NONNUMERIC = {}


def blk(f, k, s, t, cp=1):
    d1 = (log(f / k) + s * s * t / 2) / (s * sqrt(t))
    d2 = d1 - s * sqrt(t)
    return float(cp * (f * N(cp * d1) - k * N(cp * d2)))


def marg(f1, f2, s1, s2, r, t):
    s = sqrt(s1 * s1 + s2 * s2 - 2 * r * s1 * s2)
    d1 = (log(f1 / f2) + s * s * t / 2) / (s * sqrt(t))
    d2 = d1 - s * sqrt(t)
    return float(f1 * N(d1) - f2 * N(d2)), float(N(d1)), float(N(d2)), s


def test_q1():
    assert 74 > 70 and 74 - 70 == 4
    # A flat spot in a stationary contango: the future earns minus the slope, whatever the level.
    assert (70 - 74) == -(74 - 70)


def test_q2():
    assert 80 * 1.05 + 4 == 88
    pnl = 92 - 80 * 1.05 - 4
    assert abs(pnl - 4) < 1e-9
    # The profit does not depend on the final spot: the delivery settles at the future's price.
    for s_t in (10, 80, 300):
        assert abs((s_t - 80 * 1.05 - 4) + (92 - s_t) - 4) < 1e-9


def test_q3():
    gas, ho = 2.4 * 42, 2.7 * 42
    assert round(gas, 2) == 100.8 and round(ho, 2) == 113.4
    assert round((2 * gas + ho - 3 * 80) / 3, 6) == 25


def test_q4():
    assert (5 - 5) * 1000 == 0 and (3 - 2) * 1000 == 1000
    # Any parallel shift is flat for a one-for-one spread.
    for d in (-30, 0, 11):
        assert ((72 + d) - 72) - ((70 + d) - 70) == 0


def test_q5():
    assert 60 - 7 * 5 == 25 and 25 * 100 * 16 == 40_000
    assert round(0.4 * 30, 9) == 12 and round(25 - 0.4 * 30, 9) == 13


def test_q6():
    y = 0.06 - log(66 / 70)
    assert round(y, 4) == 0.1188
    # Reprices the future; zero convenience gives full carry.
    assert abs(70 * exp(0.06 - y) - 66) < 1e-9
    assert 70 * exp(0.06) > 66


def test_q7():
    assert round(50 * exp(0.04 / 12) + 1, 2) == 51.17
    assert round(50 * exp(0.04 / 12) + 1 - 50, 2) == 1.17


def test_q8():
    r = 0.99**12
    assert round(1 - r, 3) == 0.114
    assert round(1 - 1.01**-12, 3) == 0.113
    # Simulate rolling on commodity A's stationary curve: buy at 1.01 S, sell at S.
    wealth = 1.0
    for _ in range(12):
        wealth *= 1 / 1.01
    assert abs(wealth - 1.01**-12) < 1e-12
    # Seasonal: each contract's price stays put, so zero P&L on each roll, and slopes sum to zero.
    f = [3 + 0.6 * cos(2 * pi * (m - 1) / 12) for m in range(1, 13)]
    pnl = sum(f[m] - f[m] for m in range(12))
    slopes = sum(f[(m + 1) % 12] - f[m] for m in range(12))
    assert pnl == 0 and abs(slopes) < 1e-12
    # The naive front-to-second sign does change with the season.
    assert f[1] < f[0] and f[7] > f[6]


def test_q9():
    h = 0.8 * 3 / 3.5
    assert round(h, 3) == 0.686 and round(h * 10e6 / 42000) == 163 and round(0.8**2, 2) == 0.64
    assert round(1 - sqrt(1 - 0.64), 2) == 0.40
    # Simulation: the variance is smallest at that ratio, and h = 1 is worse.
    rng = np.random.default_rng(1)
    f = rng.standard_normal(1_000_000) * 3.5
    s = 0.8 * 3 / 3.5 * f + rng.standard_normal(1_000_000) * 3 * 0.6
    v = {x: np.var(s - x * f) for x in (0.5, h, 1.0)}
    assert v[h] < v[0.5] and v[h] < v[1.0]
    assert abs(v[h] / np.var(s) - 0.36) < 2e-3


def test_q10():
    assert round(0.6 * exp(-2 / 12), 3) == 0.508 and round(0.6 * exp(-2), 3) == 0.081
    a1 = 0.6 * sqrt((1 - exp(-4)) / 4)
    a2 = 0.6 * sqrt((1 - exp(-4 / 12)) / (4 / 12))
    assert round(a1, 3) == 0.297 and round(a2, 3) == 0.553
    # Riemann sum and limit: at T -> 0 the average is the spot volatility.
    k = 20000
    t = (np.arange(k) + 0.5) / k
    assert abs(sqrt(np.mean((0.6 * np.exp(-2 * t)) ** 2)) - a1) < 1e-6
    assert abs(0.6 * sqrt((1 - exp(-4e-6)) / 4e-6) - 0.6) < 1e-5
    # Simulated option on the one-year future under this volatility.
    rng = np.random.default_rng(2)
    z = rng.standard_normal(1_000_000)
    x = a1 * z - a1**2 / 2
    assert abs(np.maximum(70 * np.exp(x) - 70, 0).mean() - blk(70, 70, a1, 1)) < 0.1


def test_q11():
    t = 1 / 12
    sa = 0.4 / sqrt(3)
    assert round(sa, 3) == 0.231
    a, e = blk(70, 70, sa, t), blk(70, 70, 0.4, t)
    assert round(a, 2) == 1.86 and round(e, 2) == 3.22
    assert round(a / e, 2) == 0.58
    assert round(0.4 * 70 * sa * sqrt(t), 2) == 1.87 and round(0.4 * 70 * 0.4 * sqrt(t), 2) == 3.23
    # Simulation of the arithmetic average over many fixings.
    rng = np.random.default_rng(3)
    k = 200
    dw = rng.standard_normal((100_000, k)) * 0.4 * sqrt(t / k)
    path = 70 * np.exp(np.cumsum(dw - 0.08 * t / k, axis=1))
    sim = np.maximum(path.mean(axis=1) - 70, 0).mean()
    assert abs(sim - a) < 0.03
    # The 22-fixing variance factor.
    assert round(23 * 45 / (6 * 22 * 22), 3) == 0.356 and round(0.4 * sqrt(23 * 45 / (6 * 484)), 3) == 0.239


def test_q12():
    gross = 77 - 73 - 3.5
    fin = 73 * 0.05 * 30 / 365
    assert gross == 0.5 and round(fin, 2) == 0.30 and round(gross - fin, 2) == 0.20
    # With no freight and no financing the gap is the whole spread; with freight of 4 it is shut.
    assert 77 - 73 - 4 == 0


def clear(demand, stack):
    q = 0
    for price, cap in stack:
        q += cap
        if q >= demand:
            return price
    return None


def test_q13():
    base = [(0, 30), (10, 40), (40, 40), (90, 20)]
    assert [clear(d, base) for d in (20, 60, 100, 115)] == [0, 10, 40, 90]
    assert clear(140, base) is None
    wind = [(0, 60), (10, 40), (40, 40), (90, 20)]
    assert [clear(d, wind) for d in (20, 60, 100, 115)] == [0, 0, 10, 40]
    # More wind can never raise a clearing price.
    for d in range(1, 131):
        assert clear(d, wind) <= clear(d, base)
    assert round((168 * 50 - 80 * 70) / 88, 2) == 31.82
    # Exact: the baseload is the hours-weighted average.
    assert abs((80 * 70 + 88 * ((168 * 50 - 80 * 70) / 88)) / 168 - 50) < 1e-12


def test_q14():
    v, a, b, s = marg(40, 35, 0.6, 0.4, 0.5, 0.25)
    assert round(s, 3) == 0.529 and round(v, 2) == 6.94 and round(a, 3) == 0.738 and round(b, 3) == 0.645
    assert round(b * 7, 2) == 4.52
    d1 = (log(40 / 35) + s * s * 0.125) / (s * 0.5)
    assert round(d1, 3) == 0.637 and round(d1 - s * 0.5, 3) == 0.372
    assert round(marg(40, 35, 0.6, 0.4, 0.9, 0.25)[0], 2) == 5.56 and round(marg(40, 35, 0.6, 0.4, 0.9, 0.25)[3], 3) == 0.297
    assert round(marg(30, 35, 0.6, 0.4, 0.5, 0.25)[0], 2) == 1.48
    # Simulation.
    rng = np.random.default_rng(4)
    z1, z2 = rng.standard_normal(2_000_000), rng.standard_normal(2_000_000)
    p = 40 * np.exp(0.6 * 0.5 * z1 - 0.045)
    g = 35 * np.exp(0.4 * 0.5 * (0.5 * z1 + sqrt(0.75) * z2) - 0.02)
    assert abs(np.maximum(p - g, 0).mean() - v) < 0.03
    # Limit: equal volatility and correlation near one leaves intrinsic alone.
    assert abs(marg(40, 35, 0.4, 0.4, 0.999999, 0.25)[0] - 5) < 1e-3
    # Linear homogeneity gives the two deltas as the value.
    assert abs(40 * a - 35 * b - v) < 1e-9


def test_q15():
    assert 20 - 58 == -38
    # Figures in the dated box: the second contract and the first imply a spread near 58.
    assert round(20.43 - (-37.63), 2) == 58.06
    # Bound holds with storage: a cost of 1 keeps the front at 19 or above.
    assert 20 - 1 == 19


def best_cycle(c, inj=0.02, wd=0.01):
    # Exact: all sets of buy-then-sell pairs for a one-unit tank at one unit a month.
    best = 0.0
    idx = range(len(c))
    for k in (1, 2, 3):
        for pts in combinations(idx, 2 * k):
            v = 0.0
            for a, b in zip(pts[::2], pts[1::2], strict=True):
                v += c[b] - c[a] - inj - wd
            best = max(best, v)
    return best


def test_q16():
    c = [3.00, 2.90, 2.85, 3.40, 3.60]
    assert round(best_cycle(c), 2) == 0.72
    assert round(3.60 - 2.85 - 0.03, 2) == 0.72
    up = 4.10 - 2.85 - 0.03
    dn = max(3.40, 3.10) - 2.85 - 0.03
    assert round(up, 2) == 1.22 and round(dn, 2) == 0.52 and round((up + dn) / 2, 2) == 0.87
    # Expected month 5 is unchanged.
    assert abs((4.10 + 3.10) / 2 - 3.60) < 1e-12

    # Exact dynamic program over fill and the revealed month 5 price, tank empty at the end.
    def v(m, fill, m5):
        if m == 5:
            return 0.0 if fill == 0 else -1e9
        price = m5 if m == 4 else c[m]
        best = v(m + 1, fill, m5)
        if fill == 0:
            best = max(best, -price - 0.02 + v(m + 1, 1, m5))
        else:
            best = max(best, price - 0.01 + v(m + 1, 0, m5))
        return best

    def root(m, fill):
        if m == 3:  # decision in month 4 sees the reveal, so it is an expectation over both cases
            return (v(3, fill, 4.10) + v(3, fill, 3.10)) / 2
        best = root(m + 1, fill)
        if fill == 0:
            best = max(best, -c[m] - 0.02 + root(m + 1, 1))
        else:
            best = max(best, c[m] - 0.01 + root(m + 1, 0))
        return best

    assert round(root(0, 0), 2) == 0.87
    # No uncertainty: the same program gives back the intrinsic value.
    assert round((v(0, 0, 3.60)), 2) == 0.72


def test_q17():
    total = sum(1e6 * 20 * exp(-0.05 * (k + 0.5)) for k in range(10))
    assert round(total / 1e6, 1) == 157.4
    assert 10e6 * 20 == 200e6
    assert round(200 - total / 1e6, 1) == 42.6 and round(total / 200e6, 3) == 0.787
    assert round(0.3 * total / 1e6) == 47
    assert 10e6 * 0.5 == 5e6 and 12 * 5e6 == 60e6
    # With a zero rate, one-for-one is right in a flat move.
    assert abs(sum(1e6 * 20 for _ in range(10)) - 200e6) < 1e-6


def test_q18():
    p = blk(70, 60, 0.3, 1, -1)
    assert round(p, 2) == 3.74
    k = brentq(lambda x: blk(70, x, 0.3, 1) - p, 70, 150)
    assert round(k, 2) == 84.30
    p2 = blk(70, 60, 0.36, 1, -1)
    k2 = brentq(lambda x: blk(70, x, 0.26, 1) - p2, 70, 150)
    assert round(p2, 2) == 5.11 and round(k2, 2) == 75.43
    assert round(k - k2) == 9
    # Limit: both at the forward, parity makes the premium zero.
    assert abs(blk(70, 70, 0.3, 1) - blk(70, 70, 0.3, 1, -1)) < 1e-9
    # Simulated collar costs nothing.
    z = np.random.default_rng(5).standard_normal(4_000_000)
    f = 70 * np.exp(0.3 * z - 0.045)
    assert abs((np.maximum(60 - f, 0) - np.maximum(f - k, 0)).mean()) < 0.02


def kirk(f1, f2, k, s1, s2, r, t):
    w = f2 / (f2 + k)
    s = sqrt(s1 * s1 + (s2 * w) ** 2 - 2 * r * s1 * s2 * w)
    d1 = (log(f1 / (f2 + k)) + s * s * t / 2) / (s * sqrt(t))
    d2 = d1 - s * sqrt(t)
    return float(f1 * N(d1) - (f2 + k) * N(d2)), s, w


def test_q19():
    v, s, w = kirk(100, 80, 15, 0.35, 0.3, 0.9, 0.5)
    assert round(w, 3) == 0.842 and round(s, 3) == 0.165 and round(v, 2) == 7.46
    sd = sqrt(35**2 + 24**2 - 2 * 0.9 * 35 * 24)
    assert round(sd) == 17 and round(sd * sqrt(0.5), 2) == 12.02
    x = 5 / (sd * sqrt(0.5))
    bach = sd * sqrt(0.5) * (n(x) + x * N(x))
    assert round(float(bach), 2) == 7.70
    rng = np.random.default_rng(6)
    z1, z2 = rng.standard_normal(4_000_000), rng.standard_normal(4_000_000)
    f1 = 100 * np.exp(0.35 * sqrt(0.5) * z1 - 0.35**2 / 4)
    f2 = 80 * np.exp(0.3 * sqrt(0.5) * (0.9 * z1 + sqrt(0.19) * z2) - 0.3**2 / 4)
    mc = np.maximum(f1 - f2 - 15, 0).mean()
    assert round(mc, 1) == 7.5 and abs(mc - v) < 0.03
    assert abs(mc - v) < abs(mc - bach)
    # With zero strike Kirk is Margrabe, exactly.
    assert abs(kirk(100, 80, 0, 0.35, 0.3, 0.9, 0.5)[0] - marg(100, 80, 0.35, 0.3, 0.9, 0.5)[0]) < 1e-12


def test_q20():
    q = 100 * 16 * 22
    assert q == 35_200 and 2 * q == 70_400
    m = marg(42, 40, 0.5, 0.35, 0.6, 1 / 12)
    d = marg(42, 40, 0.9, 0.5, 0.5, 1 / 8)
    assert round(m[3], 3) == 0.403 and round(d[3], 3) == 0.781
    assert round(m[0], 2) == 3.07 and round(d[0], 2) == 5.57
    assert round(m[0] * q, -3) == 108_000 and round(d[0] * q, -3) == 196_000
    assert round(m[1] * q) == 24_059 and round(m[2] * 8 * q) == 180_501
    assert round(d[1] * q) == 21_948 and round(d[2] * 8 * q) == 145_138
    assert round(m[1], 3) == 0.683 and round(m[2], 3) == 0.641
    # Intrinsic floor; both values above it.
    assert m[0] * q > 70_400 and d[0] * q > m[0] * q
    # The $32 case.
    mo, da = marg(32, 40, 0.5, 0.35, 0.6, 1 / 12)[0], marg(32, 40, 0.9, 0.5, 0.5, 1 / 8)[0]
    assert round(mo, 2) == 0.04 and round(mo * q, -2) == 1_500
    assert round(da, 2) == 1.16 and round(da * q, -3) == 41_000
    # Simulated monthly value.
    rng = np.random.default_rng(7)
    z1, z2 = rng.standard_normal(4_000_000), rng.standard_normal(4_000_000)
    t = 1 / 12
    p = 42 * np.exp(0.5 * sqrt(t) * z1 - 0.125 * t)
    g = 40 * np.exp(0.35 * sqrt(t) * (0.6 * z1 + 0.8 * z2) - 0.06125 * t)
    assert abs(np.maximum(p - g, 0).mean() - m[0]) < 0.01
