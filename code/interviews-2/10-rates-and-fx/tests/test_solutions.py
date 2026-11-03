"""Rates and FX. Curves by hand, models against simulation and against closed forms."""
from math import exp, log, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import norm

N, n = norm.cdf, norm.pdf
NONNUMERIC = {}


def bond(c, y, m):
    return sum(c / (1 + y) ** i for i in range(1, m + 1)) + 100 / (1 + y) ** m


def mdur(c, y, m):
    h = 1e-5
    p = bond(c, y, m)
    return -(bond(c, y + h, m) - bond(c, y - h, m)) / (2 * h) / p


def conv(c, y, m):
    h = 1e-4
    p = bond(c, y, m)
    return (bond(c, y + h, m) - 2 * p + bond(c, y - h, m)) / h**2 / p


def black(f, k, v, t):
    a = (log(f / k) + v * v * t / 2) / (v * sqrt(t))
    return f * N(a) - k * N(a - v * sqrt(t))


def test_q1():
    assert round(100 / 1.04**5, 2) == 82.19 and round(100 * exp(-0.2), 2) == 81.87


def test_q2():
    assert round(bond(5, 0.04, 1), 2) == 100.96 and abs(bond(5, 0.05, 1) - 100) < 1e-9
    assert abs(bond(7, 0.07, 9) - 100) < 1e-9  # a par bond at any maturity


def test_q3():
    assert round(5 / 1.04, 2) == 4.81 and round(mdur(0, 0.04, 5), 2) == 4.81
    e = 100 / 1.041**5 - 100 / 1.04**5
    assert abs(e + 0.40) < 0.015


def test_q4():
    assert round(1e7 * 8 * 1e-4) == 8000 and round(25 * 8000) == 200_000


def test_q5():
    f = 1.04**2 / 1.03 - 1
    assert round(f * 100, 2) == 5.01
    # The zero-cost pair: buy a one-year, financed by selling two-year zeros.
    sell = (1 / 1.03) / (1 / 1.04**2)
    assert abs(sell / 1 - (1 + f)) < 1e-12


def test_q6():
    assert round(4500 / (8 * 1e-4)) == 5_625_000
    assert round((10e6 * 8 - 10e6 * 4.5) * 1e-4) == 3500


def test_q7():
    assert 10 * 4500 == 45_000
    # The fixed bond's DV01 less the floater's, on a real five-year swap, near the quote.
    d = (bond(4, 0.04, 5) - bond(4, 0.0401, 5)) / 100 * 1e7
    assert abs(d - 4500) < 100


def test_q8():
    assert 100 * (1 - 0.04 * 90 / 360) == 99.0
    assert round((1 / 99) * (360 / 90) * 100, 2) == 4.04


def test_q9():
    assert round(1.10 * 1.05 / 1.03, 4) == 1.1214
    assert round((1.10 * 1.05 / 1.03 - 1.10) * 1e4) == 214


def test_q10():
    assert round(1.10 * 150) == 165 and round(166 - 1.10 * 150) == 1


def test_q11():
    assert round(1e6 * 1.10) == 1_100_000 and round(1 / 1.10, 3) == 0.909


def test_q12():
    assert round(1.10 * 1.05 / 1.03, 4) == 1.1214
    assert round((1.05 / 1.03 - 1) * 100, 1) == 1.9
    # At the break-even the loan and the deposit match in each currency.
    x = 1.10 * 1.05 / 1.03
    assert abs(1.10 * 1.05 - 1.03 * x) < 1e-12


def test_q13():
    assert round(-8 + 0.5 * 80 * 0.0001 * 100, 1) == -7.6 and round(8 + 0.5 * 80 * 0.0001 * 100, 1) == 8.4


def test_q14():
    d1 = 1 / 1.03
    d2 = (1 - 0.04 * d1) / 1.04
    assert round(d1, 5) == 0.97087 and round(d2, 5) == 0.92420
    assert round((d2**-0.5 - 1) * 100, 2) == 4.02 and round((d1 / d2 - 1) * 100, 2) == 5.05
    assert abs(4 * d1 + 104 * d2 - 100) < 1e-9


def test_q15():
    d = [1 / (1 + r) ** (i + 1) for i, r in enumerate((0.03, 0.04, 0.05))]
    assert [round(x, 5) for x in d] == [0.97087, 0.92456, 0.86384]
    par = (1 - d[2]) / sum(d)
    fwd = (d[0] - d[2]) / (d[1] + d[2])
    assert round(par * 100, 2) == 4.93 and round(fwd * 100, 2) == 5.99
    # The par bond prices at 100, and a one-period forward leg is D_start - D_end.
    assert abs(par * sum(d) + d[2] - 1) < 1e-12
    assert abs(fwd * (d[1] + d[2]) - (d[0] - d[2])) < 1e-12


def test_q16():
    d2, d5, d10 = mdur(4, 0.04, 2), mdur(4, 0.04, 5), mdur(4, 0.04, 10)
    assert [round(x, 3) for x in (d2, d5, d10)] == [1.886, 4.452, 8.111]
    w = (d5 - d2) / (d10 - d2)
    assert round(w, 3) == 0.412
    assert round(w * conv(4, 0.04, 10) + (1 - w) * conv(4, 0.04, 2), 1) == 36.5 and round(conv(4, 0.04, 5), 1) == 25.0

    def bar(y):
        return w * bond(4, y, 10) + (1 - w) * bond(4, y, 2) - 100

    assert round(bar(0.03), 2) == 4.64 and round(bond(4, 0.03, 5) - 100, 2) == 4.58
    assert round(bar(0.05), 2) == -4.28 and round(bond(4, 0.05, 5) - 100, 2) == -4.33
    assert bar(0.03) > bond(4, 0.03, 5) - 100 and bar(0.05) > bond(4, 0.05, 5) - 100


def test_q17():
    a = np.linalg.solve([[1, 1], [1.886, 8.111]], [100, 445.2])
    assert round(a[0], 1) == 58.8 and round(a[1], 1) == 41.2
    assert round(4.452 * 10 * 1.0, 1) == 44.5


def test_q18():
    assert round(8000 / 190, 1) == 42.1 and 8000 * 5 + 8000 * 5 == 80_000
    assert 8000 * 10 - 8000 * 10 == 0


def test_q19():
    beta = 0.7 * 75 / 80
    assert round(beta, 3) == 0.656 and round(8000 * beta, -1) == 5250
    assert round(75 * sqrt(1 - 0.49), 1) == 53.6
    assert round(sqrt(80**2 + 75**2 - 2 * 0.7 * 80 * 75), 1) == 60.2
    assert round(5250 / 190, 1) == 27.6
    # A simulation of the two series gives the same residuals.
    rng = np.random.default_rng(19)
    a, b = rng.standard_normal((2, 1_000_000))
    y2, y10 = 80 * a, 75 * (0.7 * a + sqrt(0.51) * b)
    assert abs((y10 - beta * y2).std() - 53.6) < 0.2 and abs((y10 - y2).std() - 60.2) < 0.2


def test_q20():
    assert round(bond(4, 0.03, 2) - 100, 2) == 1.91
    assert round(1 / 1.03 + 1 / 1.03**2, 4) * 1 == 1.9135
    assert abs(bond(4, 0.03, 2) - 100 - (1 / 1.03 + 1 / 1.03**2)) < 1e-9


def test_q21():
    assert round(0.5 * 0.0001 * 5 * 5.25 * 1e4, 1) == 13.1
    # Ho-Lee, exact: the future's rate less the forward's, from the Gaussian model.
    t, s = 5.0, 0.01
    tau = 0.25
    # Future's rate is the risk-neutral mean; the forward's is that less the covariance with the bond.
    gap = 0.5 * s * s * t * (t + tau)
    assert abs(gap * 1e4 - 13.1) < 0.1


def test_q22():
    b = [93.0 - 100 * 0.92, 110.8 - 100 * 1.10, 125.6 - 100 * 1.25]
    assert [round(x, 1) for x in b] == [1.0, 0.8, 0.6] and int(np.argmin(b)) == 2
    # Both factors at a 6 percent yield: above it the long bond is cheapest, below it the short.
    assert bond(6, 0.07, 20) < bond(6, 0.07, 5) and bond(6, 0.05, 5) < bond(6, 0.05, 20)


def test_q23():
    assert round(0.2 * 3.6, 2) == 0.72 and round(1 + 0.72, 2) == 1.72
    assert round(1.72 / 3.6 * 100) == 48 and round(3.8 + 0.48, 2) == 4.28
    # The roll from real prices: a 4% four-year at 3.8%.
    assert abs(bond(4, 0.038, 4) - 100 - 0.72) < 0.03


def test_q24():
    m = 0.05 + (0.03 - 0.05) * exp(-1)
    v = 1e-4 / (2 * 0.5) * (1 - exp(-2))
    assert round(m * 100, 2) == 4.26 and round(sqrt(v) * 100, 2) == 0.93
    assert round(N(-m / sqrt(v)) * 100, 4) == 0.0002
    # With the exact transition in a simulation, the same two moments.
    rng = np.random.default_rng(24)
    r = np.full(400_000, 0.03)
    for _ in range(4):
        r = 0.05 + (r - 0.05) * exp(-0.25) + sqrt(1e-4 * (1 - exp(-0.5))) * rng.standard_normal(400_000)
    assert abs(r.mean() - m) < 1e-4 and abs(r.std() - sqrt(v)) < 1e-4


def test_q25():
    assert round(0.0001 * 100 / 6 * 1e4, 1) == 16.7
    # Simulate the integral of the driftless rate; the average discount has that yield.
    rng = np.random.default_rng(25)
    z = rng.standard_normal((200_000, 200))
    dt = 10 / 200
    i = (0.01 * sqrt(dt) * np.cumsum(z, axis=1) * dt).sum(1)
    y = -log(np.exp(-i).mean()) / 10
    assert abs(y * 1e4 + 16.7) < 0.8
    # Second route: this model's forward curve is f - s^2 T^2 / 2, and the yield is its average. It is not flat.
    avg = quad(lambda u: -0.0001 * u * u / 2, 0, 10)[0] / 10
    assert abs(avg * 1e4 + 16.7) < 0.05 and abs(-0.0001 * 100 / 2) > 0
    # A truly flat forward curve gives a zero yield of exactly its level.
    assert abs(quad(lambda u: 0.04, 0, 10)[0] / 10 - 0.04) < 1e-12


def test_q26():
    a = 0.95 * 0.25 * black(0.04, 0.04, 0.2, 1)
    assert round(a * 1e4, 2) == 7.57 and abs(0.95 * 0.25 * 0.04 * (2 * N(0.1) - 1) - a) < 1e-12
    assert round(0.95 * 0.25 * 0.008 * 0.3989 * 1e4, 2) == 7.58
    assert round(0.2 * 0.04 * 1e4) == 80 and round(0.2 * 0.02 * 1e4) == 40


def test_q27():
    assert round(4.5 * 0.008 * 0.3989 * 100, 2) == 1.44
    assert round(4.5 * 0.0001 * 0.3989 * 100, 3) == 0.018
    z = np.random.default_rng(27).standard_normal(2_000_000)
    assert abs(4.5 * np.maximum(0.008 * z, 0).mean() * 100 - 1.44) < 0.005


def test_q28():
    assert round(4.5 * (4 - 5), 1) == -4.5
    rng = np.random.default_rng(28)
    for sig in (0.005, 0.02):
        s = 0.04 + sig * rng.standard_normal(2_000_000)
        gap = (np.maximum(s - 0.05, 0) - np.maximum(0.05 - s, 0)).mean() * 4.5
        assert abs(gap + 0.045) < 0.0005


def test_q29():
    x = 1.1245 / 1.10 * 1.03 - 1
    assert round(x * 100, 3) == 5.294 and round((x - 0.05) * 1e4) == 29


def gk(s, k, rd, rf, v, t):
    f = s * exp((rd - rf) * t)
    return exp(-rd * t) * black(f, k, v, t)


def test_q30():
    f = 1.10 * exp(0.02)
    a = (log(f / 1.10) + 0.005) / 0.1
    c = gk(1.10, 1.10, 0.05, 0.03, 0.1, 1)
    p = c - 1.10 * exp(-0.03) + 1.10 * exp(-0.05)
    assert round(f, 4) == 1.1222 and round(c, 4) == 0.0536 and round(p, 4) == 0.0324
    assert round(exp(-0.03) * N(a), 3) == 0.581 and round(N(a), 3) == 0.599
    assert round(exp(-0.05) * (f - 1.10), 4) == 0.0211 and abs(c - p - exp(-0.05) * (f - 1.10)) < 1e-12
    h = 1e-5
    d = (gk(1.10 + h, 1.10, 0.05, 0.03, 0.1, 1) - gk(1.10 - h, 1.10, 0.05, 0.03, 0.1, 1)) / (2 * h)
    assert abs(d - exp(-0.03) * N(a)) < 1e-6


def test_q31():
    c = gk(1.10, 1.10, 0.05, 0.03, 0.1, 1)
    assert round(c / 1.10, 4) == 0.0487
    # From the dollar side: a put on euros per dollar, rates swapped, per dollar and then on 1.10 dollars.
    s, k = 1 / 1.10, 1 / 1.10
    f = s * exp(0.03 - 0.05)
    put = exp(-0.03) * (black(f, k, 0.1, 1) - f + k)
    assert abs(put * 1.10 * 1.10 - c) < 1e-12
    assert round(put * 1.10, 4) == 0.0487
    assert round(put, 4) == 0.0443 and round(put * 1.10 * 1.10, 4) == 0.0536
    # The inverse rate has the same log variance, whichever way it is quoted.
    z = np.random.default_rng(31).standard_normal(1_000_000)
    assert abs(np.log(1 / (1.10 * np.exp(0.1 * z))).std() - 0.1) < 1e-3


def test_q32():
    assert 10 + 0.5 - 1 == 9.5 and 10 + 0.5 + 1 == 11.5
    f = 1.1222
    kc = brentq(lambda k: exp(-0.03) * N((log(f / k) + 0.095**2 / 2) / 0.095) - 0.25, 0.8, 1.6)
    kp = brentq(lambda k: exp(-0.03) * (N((log(f / k) + 0.115**2 / 2) / 0.115) - 1) + 0.25, 0.8, 1.6)
    assert round(kc, 3) == 1.199 and round(kp, 3) == 1.048
    assert round(0.25 * exp(0.03), 4) == 0.2576 and round(norm.ppf(0.2576), 3) == -0.651
    assert abs(f * exp(0.651 * 0.095 + 0.095**2 / 2) - kc) < 1e-3


def test_q33():
    assert round(0.01 + 0.0081 + 0.009, 4) == 0.0271
    assert round(sqrt(0.0271) * 100, 2) == 16.46 and round(sqrt(0.01 + 0.0081 - 0.009) * 100, 1) == 9.5
    rng = np.random.default_rng(33)
    a, b = rng.standard_normal((2, 1_000_000))
    u, w = 0.1 * a, 0.09 * (0.5 * a + sqrt(0.75) * b)
    assert abs((u + w).std() - sqrt(0.0271)) < 2e-4
    # In reverse, the correlation from three volatilities.
    assert abs((0.0271 - 0.01 - 0.0081) / (2 * 0.1 * 0.09) - 0.5) < 1e-9


def test_q34():
    f = 1.0
    for r, d in ((0.04, 1), (0.04, 1), (0.05, 1), (0.04, 1), (0.04, 3)):
        f *= 1 + r * d / 360
    assert round(f, 7) == 1.0008058
    assert round((f - 1) * 360 / 7 * 100, 3) == 4.144
    assert round((0.04 * 1 + 0.04 + 0.05 + 0.04 + 0.04 * 3) / 7 * 100, 3) == 4.143
    # The one-third rule for the accrual, from a Brownian average.
    rng = np.random.default_rng(34)
    w = np.cumsum(rng.standard_normal((200_000, 200)), axis=1) / sqrt(200)
    assert abs(w.mean(1).var() - 1 / 3) < 0.01


def vas(t, k=0.5, th=0.05, s=0.01, r0=0.03):
    b = (1 - exp(-k * t)) / k
    return exp((th - s * s / (2 * k * k)) * (b - t) - s * s * b * b / (4 * k) - b * r0)


def test_q35():
    assert round(vas(5), 4) == 0.8083 and round(-log(vas(5)) / 5 * 100, 2) == 4.26
    assert round((0.05 - 1e-4 / (2 * 0.25)) * 100, 2) == 4.98
    assert abs(-log(vas(2000)) / 2000 - 0.0498) < 1e-4
    rng = np.random.default_rng(35)
    c, m = 40_000, 500
    dt = 5 / m
    r = np.full(c, 0.03)
    i = np.zeros(c)
    for _ in range(m):
        i += 0.5 * r * dt
        r = r + 0.5 * (0.05 - r) * dt + 0.01 * sqrt(dt) * rng.standard_normal(c)
        i += 0.5 * r * dt
    assert abs(np.exp(-i).mean() - vas(5)) < 3e-4


def test_q36():
    k, s, f0 = 0.1, 0.01, 0.04
    rng = np.random.default_rng(36)
    c, m = 40_000, 1000
    dt = 10 / m
    r = np.full(c, f0)
    i = np.zeros(c)
    for j in range(m):
        t = j * dt
        theta = k * f0 + s * s * (1 - exp(-2 * k * t)) / (2 * k)
        i += 0.5 * r * dt
        r = r + (theta - k * r) * dt + s * sqrt(dt) * rng.standard_normal(c)
        i += 0.5 * r * dt
    assert abs(np.exp(-i).mean() - exp(-0.4)) < 3 * np.exp(-i).std() / 200 + 2e-4

    # The printed forward against a second route: minus the T-derivative of the Hull-White log bond price.
    def b(u, v):
        return (1 - exp(-k * (v - u))) / k

    def printed(t, big, x):
        return f0 + 0.5 * s * s * (b(0, big) ** 2 - b(t, big) ** 2) + exp(-k * (big - t)) * x

    def logp(t, big, x):
        rate = f0 + 0.5 * s * s * b(0, t) ** 2 + x
        return -f0 * (big - t) + b(t, big) * f0 - s * s / (4 * k) * (1 - exp(-2 * k * t)) * b(t, big) ** 2 - b(t, big) * rate

    h = 1e-5
    for t, big, x in ((1.0, 5.0, 0.01), (3.0, 10.0, -0.02), (7.5, 8.0, 0.0)):
        assert abs(-(logp(t, big + h, x) - logp(t, big - h, x)) / (2 * h) - printed(t, big, x)) < 1e-7
    # At T = t it is the short rate, whose simulated mean at ten years is the fitted one.
    assert abs(printed(10.0, 10.0, 0.0) - (f0 + 0.5 * s * s * b(0, 10.0) ** 2)) < 1e-12
    assert abs(r.mean() - printed(10.0, 10.0, 0.0)) < 3 * r.std() / 200 + 1e-4
    # Without the convexity term in the drift, the model misses.
    r = np.full(c, f0)
    i = np.zeros(c)
    for _ in range(m):
        i += 0.5 * r * dt
        r = r + (k * f0 - k * r) * dt + s * sqrt(dt) * rng.standard_normal(c)
        i += 0.5 * r * dt
    assert np.exp(-i).mean() - exp(-0.4) > 1e-3


def test_q37():
    a = 0.96 + 0.92
    cap = a * black(0.04, 0.04, 0.2, 1)
    assert round(cap * 1e4, 1) == 59.9
    assert abs(cap - a * 0.04 * (2 * N(0.1) - 1)) < 1e-12
    rng = np.random.default_rng(37)
    vals = {}
    for rho in (1.0, 0.5, 0.0):
        z1 = rng.standard_normal(2_000_000)
        z2 = rho * z1 + sqrt(1 - rho * rho) * rng.standard_normal(2_000_000)
        s = 0.5 * (0.04 * np.exp(0.2 * z1 - 0.02) + 0.04 * np.exp(0.2 * z2 - 0.02))
        vals[rho] = a * np.maximum(s - 0.04, 0).mean() * 1e4
    assert abs(vals[1.0] - 60) < 0.4 and abs(vals[0.5] - 52) < 0.4 and abs(vals[0.0] - 43) < 0.5
    assert vals[0.5] <= cap * 1e4 and vals[0.0] < vals[0.5] < vals[1.0]


def callable_parts(y, s=0.01):
    x, w = np.polynomial.hermite_e.hermegauss(80)
    w = w / w.sum()
    p = np.array([bond(5, y + s * z, 4) for z in x])
    call = (w * np.maximum(p - 100, 0)).sum() / (1 + y)
    return bond(5, y, 5), call


def test_q38():
    want = {0.04: (104.45, 3.86, 100.60), 0.05: (100.00, 1.39, 98.61), 0.06: (95.79, 0.29, 95.50)}
    for y, w in want.items():
        b, c = callable_parts(y)
        assert (round(b, 2), round(c, 2), round(b - c, 2)) == w
    h = 1e-4
    for y, d in ((0.04, 1.44), (0.05, 2.60), (0.06, 3.76)):
        lo, hi = callable_parts(y - h), callable_parts(y + h)
        v = callable_parts(y)
        assert round(-((hi[0] - hi[1]) - (lo[0] - lo[1])) / (2 * h) / (v[0] - v[1]), 2) == d
        assert abs(mdur(5, y, 5) - 4.3) < 0.1
    # Negative convexity in the middle: the second difference of the callable is below zero.
    a = [callable_parts(y)[0] - callable_parts(y)[1] for y in (0.048, 0.05, 0.052)]
    assert a[0] - 2 * a[1] + a[2] < 0


def test_q39():
    assert abs(bond(6, 0.06, 5) - 100) < 1e-9 and abs(bond(6, 0.06, 20) - 100) < 1e-9
    y = 0.06 + 0.01 * np.random.default_rng(39).standard_normal(400_000)

    def p(m):
        return (6 / y) * (1 - (1 + y) ** -m) + 100 * (1 + y) ** -m

    a, b = p(5), p(20)
    assert round(np.minimum(a, b).mean(), 1) == 97.6
    assert round(min(a.mean(), b.mean()) - np.minimum(a, b).mean(), 1) == 2.5
    assert bond(6, 0.08, 20) < bond(6, 0.08, 5) and bond(6, 0.04, 5) < bond(6, 0.04, 20)
    # The cheaper of the two is concave in the yield at the crossing: the long is the one short the option.
    low = lambda u: min(bond(6, u, 5), bond(6, u, 20))  # noqa: E731
    assert low(0.05) + low(0.07) - 2 * low(0.06) < 0


def test_q40():
    r = np.array([[1, 0.85, 0.7, 0.6], [0.85, 1, 0.9, 0.8], [0.7, 0.9, 1, 0.9], [0.6, 0.8, 0.9, 1]])
    v = np.array([80, 85, 75, 65.0])
    c = r * np.outer(v, v)
    w, u = np.linalg.eigh(c)
    w, u = w[::-1], u[:, ::-1]
    s = w / w.sum()
    assert [round(x * 100, 1) for x in s[:3]] == [85.3, 10.7, 2.6]
    assert np.allclose(np.abs(u[:, 0]).round(2), [0.50, 0.59, 0.50, 0.40], atol=0.011)
    pc2 = u[:, 1] * np.sign(u[3, 1])
    assert np.allclose(pc2.round(2), [-0.74, -0.09, 0.40, 0.53], atol=0.011)
    pc3 = u[:, 2] * np.sign(u[1, 2])
    assert np.allclose(pc3.round(2), [-0.42, 0.62, 0.19, -0.63], atol=0.011)
    # A butterfly built from PC3 has no exposure to the first two.
    assert abs(pc3 @ u[:, 0]) < 1e-9 and abs(pc3 @ u[:, 1]) < 1e-9


def test_q41():
    f, sg, tau, t = 0.04, 0.2, 1.0, 5.0
    exact = tau * f * f * (exp(sg * sg * t) - 1) / (1 + tau * f) * 1e4
    rule = tau * f * f * sg * sg * t / (1 + tau * f) * 1e4
    assert round(exact, 2) == 3.41 and round(rule, 2) == 3.08
    z = np.random.default_rng(41).standard_normal(4_000_000)
    ft = f * np.exp(sg * sqrt(t) * z - 0.5 * sg * sg * t)
    assert abs((ft * (1 + tau * ft)).mean() / (1 + tau * f) * 1e4 - f * 1e4 - exact) < 0.3
    assert (ft.mean() - f) * 1e4 < 0.3


def test_q42():
    def a(y):
        return (1 - (1 + y) ** -10) / y

    h = 1e-5
    da = (a(0.04 + h) - a(0.04 - h)) / (2 * h)
    assert round(a(0.04), 2) == 8.11 and round(da, 1) == -40.4 and round(-da / a(0.04), 2) == 4.98
    assert round((exp(0.2) - 1), 4) == 0.2214
    rule = 0.0016 * (exp(0.2) - 1) * (-da / a(0.04)) * 1e4
    assert round(rule, 1) == 17.6

    def under_annuity(fn, vol=0.2):
        return quad(lambda x: n(x) * fn(0.04 * exp(vol * sqrt(5) * x - 0.5 * vol * vol * 5)), -8, 8)[0]

    # The change of measure must give E^T[1] = 1, which the division by E^A[1/A] enforces.
    exact = (under_annuity(lambda u: u / a(u)) / under_annuity(lambda u: 1 / a(u)) - 0.04) * 1e4
    assert round(exact, 1) == 18.2
    # Without that normalisation, the flat-yield map gives E^T[1] of about 1.002, and the number is too high.
    assert round(under_annuity(lambda u: 1 / a(u)) * a(0.04), 3) == 1.002
    assert (under_annuity(lambda u: u / a(u)) * a(0.04) - 0.04) * 1e4 > exact + 0.5
    # Limits: no volatility, or an annuity that does not move, gives no adjustment.
    assert abs(under_annuity(lambda u: u / a(u), 1e-9) / under_annuity(lambda u: 1 / a(u), 1e-9) - 0.04) < 1e-9
    assert abs(under_annuity(lambda u: u / 8.0) / under_annuity(lambda u: 1 / 8.0) - 0.04) < 1e-9
    z = np.random.default_rng(42).standard_normal(4_000_000)
    s = 0.04 * np.exp(0.2 * sqrt(5) * z - 0.1)
    assert abs(s.mean() - 0.04) < 1e-4
    sim = ((s / a(s)).mean() / (1 / a(s)).mean() - 0.04) * 1e4
    assert abs(sim - 18.2) < 0.3


def test_q43():
    assert round(100 * exp(0.3 * 0.2 * 0.1), 2) == 100.60
    # Yen measure: S and Y (the yen price of a dollar) are martingales, correlated +0.3; the dollar measure weights by Y.
    rng = np.random.default_rng(43)
    a = rng.standard_normal(4_000_000)
    b = 0.3 * a + sqrt(0.91) * rng.standard_normal(4_000_000)
    s = 100 * np.exp(0.2 * a - 0.02)
    y = np.exp(0.1 * b - 0.005)
    assert abs((s * y).mean() / y.mean() - 100.60) < 0.04
    # With the correlation reversed, the forward falls below spot; with none, it stays.
    b2 = -0.3 * a + sqrt(0.91) * rng.standard_normal(4_000_000)
    y2 = np.exp(0.1 * b2 - 0.005)
    assert abs((s * y2).mean() / y2.mean() - 99.40) < 0.04


def test_q44():
    f = 1.1222
    assert round(f * exp(0.005), 4) == 1.1278 and round(f * exp(-0.005), 4) == 1.1166
    k = f * exp(0.005)
    a = (log(f / k) + 0.005) / 0.1
    assert abs(a) < 1e-12
    kp = f * exp(-0.005)
    b = (log(f / kp) - 0.005) / 0.1
    assert abs(b) < 1e-12
    # Premium-included delta for the call and the put cancel at that strike.
    c = (kp / f) * N(b)
    p = -(kp / f) * N(-b)
    assert abs(c + p) < 1e-12


def test_q45():
    ts = np.array([1, 2, 3, 5.0])
    zs = np.array([0.03, 0.04, 0.038, 0.042])

    def fw(t, h=1e-4):
        z = lambda u: np.interp(u, ts, zs) * u  # noqa: E731
        return (z(t + h) - z(t - h)) / (2 * h)

    assert [round(float(fw(t)) * 100, 1) for t in (1.999, 2.001, 2.999, 3.001)] == [6.0, 3.6, 3.2, 4.4]
    ln = -zs * ts
    flats = [(ln[i] - ln[i + 1]) / (ts[i + 1] - ts[i]) for i in range(3)]
    assert [round(x * 100, 1) for x in flats] == [5.0, 3.4, 4.8]
    assert abs(0.04 + 2 * 0.01 - 0.06) < 1e-12 and abs(0.04 - 2 * 0.002 - 0.036) < 1e-12


def test_q46():
    assert round(4.45 * 0.8, 2) == 3.56 and round(0.3989 * 3.56, 2) == 1.42
    assert round(4.5 * 0.8 * 0.3989, 2) == 1.44
    z = np.random.default_rng(46).standard_normal(1_000_000)
    y = 0.04 + 0.008 * z
    p = (4 / y) * (1 - (1 + y) ** -5) + 100 * (1 + y) ** -5
    assert abs(np.maximum(p - p.mean(), 0).mean() - 1.42) < 0.03


def test_q47():
    assert round((99.5 + 2 - 100) / 100 / 0.5, 4) == 0.03 and round((0.03 - 0.025) * 0.5 * 100, 2) == 0.25


K_S, S_S, F0 = 0.1, 0.01, 0.04


def p0(t):
    return exp(-F0 * t)


def bb(t, big):
    return (1 - exp(-K_S * (big - t))) / K_S


def alpha(t):
    return S_S**2 / (2 * K_S**2) * (1 - exp(-K_S * t)) ** 2


def vx(t):
    return S_S**2 / (2 * K_S) * (1 - exp(-2 * K_S * t))


def pt(t, big, y):
    b = bb(t, big)
    return p0(big) / p0(t) * np.exp(-b * (y + alpha(t)) - 0.5 * b * b * vx(t))


def jam(dates, strike, expiry=1):
    ys = brentq(lambda y: sum(strike * pt(expiry, t, y) for t in dates) + pt(expiry, dates[-1], y) - 1, -0.2, 0.2)
    tot = 0.0
    for t in dates:
        c = strike + (1 if t == dates[-1] else 0)
        x = float(pt(expiry, t, ys))
        sp = S_S * bb(expiry, t) * sqrt((1 - exp(-2 * K_S * expiry)) / (2 * K_S))
        h = log(p0(t) / (p0(expiry) * x)) / sp + 0.5 * sp
        tot += c * (x * p0(expiry) * N(-h + sp) - p0(t) * N(-h))
    return tot


def test_q48():
    dates = [2, 3, 4, 5, 6]
    strike = (p0(1) - p0(6)) / sum(p0(t) for t in dates)
    assert round(strike * 100, 2) == 4.08
    v = jam(dates, strike)
    assert round(v * 100, 3) == 1.338
    rng = np.random.default_rng(48)
    y = -alpha(1) + sqrt(vx(1)) * rng.standard_normal(1_000_000)
    ann = sum(pt(1, t, y) for t in dates)
    pay = p0(1) * np.maximum(1 - pt(1, 6, y) - strike * ann, 0)
    assert abs(pay.mean() - v) < 3 * pay.std() / 1000
    assert round(pay.std() / 1000 * 100, 3) == 0.002
    assert abs((p0(1) * pt(1, 3, y)).mean() - p0(3)) < 5e-5


def vv(k, atm=0.10):
    f, df = 1.1222, exp(-0.05)
    k1, k2, k3 = 1.0482, f * exp(0.005), 1.1992
    v1, v2, v3 = 0.115, 0.10, 0.095

    def px(x, sig):
        return df * black(f, x, sig, 1)

    def veg(x):
        return df * f * n((log(f / x) + atm * atm / 2) / atm)

    w1 = veg(k) / veg(k1) * log(k2 / k) * log(k3 / k) / (log(k2 / k1) * log(k3 / k1))
    w2 = veg(k) / veg(k2) * log(k / k1) * log(k3 / k) / (log(k2 / k1) * log(k3 / k2))
    w3 = veg(k) / veg(k3) * log(k / k1) * log(k / k2) / (log(k3 / k1) * log(k3 / k2))
    p = px(k, atm) + w1 * (px(k1, v1) - px(k1, atm)) + w2 * (px(k2, v2) - px(k2, atm)) + w3 * (px(k3, v3) - px(k3, atm))
    iv = brentq(lambda s: px(k, s) - p, 0.01, 0.5)
    return iv, (w1, w2, w3)


def test_q49():
    assert round(vv(1.10)[0] * 100, 2) == 10.41 and round(vv(1.25)[0] * 100, 2) == 9.57 and round(vv(1.30)[0] * 100, 2) == 9.97
    assert [round(x, 2) for x in vv(1.25)[1]] == [0.33, -0.96, 1.56]
    for k, want in ((1.0482, 11.5), (1.1992, 9.5), (1.1222 * exp(0.005), 10.0)):
        assert abs(vv(k)[0] * 100 - want) < 1e-6
    # With a flat smile the rule leaves the flat price alone, and the weights reproduce the vega.
    w = vv(1.15)[1]
    assert abs(sum(w) - 1) < 0.5


def bermudan_grid(speed=0.1, ex=(1, 2, 3, 4), vol=0.01):
    global K_S
    old = K_S
    K_S = speed
    try:
        gy = np.linspace(-0.2, 0.2, 801)
        strike = (p0(1) - p0(5)) / sum(p0(t) for t in range(2, 6))
        var1 = vx(1)
        m1 = -S_S * S_S * quad(lambda u: exp(-K_S * (1 - u)) * bb(u, 1), 0, 1)[0]
        nod = np.linspace(-6, 6, 241)
        wt = n(nod)
        wt = wt / wt.sum()

        def step(v, t):
            yp = gy[:, None] * exp(-K_S) + m1 + sqrt(var1) * nod
            return (np.interp(yp.ravel(), gy, v).reshape(yp.shape) * wt).sum(1) * pt(t, t + 1, gy)

        v = np.zeros_like(gy)
        for t in range(4, -1, -1):
            if t in ex:
                val = 1 - pt(t, 5, gy) - strike * sum(pt(t, u, gy) for u in range(t + 1, 6))
                v = np.maximum(v, val)
            if t > 0:
                v = step(v, t - 1)
        check = float(np.interp(0.0, gy, step(pt(1, 3, gy), 0)))
        return float(np.interp(0.0, gy, v)), check, strike
    finally:
        K_S = old


def test_q50():
    euro = {d: bermudan_grid(ex=(d,))[0] for d in (1, 2, 3, 4)}
    berm, check, strike = bermudan_grid()
    fast = bermudan_grid(speed=0.3)[0]
    fast_best = max(bermudan_grid(speed=0.3, ex=(d,))[0] for d in (1, 2, 3, 4))
    assert [round(euro[d] * 100, 2) for d in (1, 2, 3, 4)] == [1.14, 1.18, 0.95, 0.54]
    assert round(berm * 100, 3) == 1.585 and round((berm - euro[2]) * 100, 2) == 0.40
    assert round((berm - euro[2]) / euro[2] * 100) == 34
    assert round(fast * 100, 3) == 1.105 and round(fast_best * 100, 2) == 0.76
    assert round((fast - fast_best) / fast_best * 100) == 45
    assert abs(check - p0(3)) < 1e-6
    assert abs(euro[1] - jam([2, 3, 4, 5], strike)) < 2e-5
    assert berm >= max(euro.values())
