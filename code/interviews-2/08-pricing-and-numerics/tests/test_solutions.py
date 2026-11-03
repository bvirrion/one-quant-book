"""Pricing and Numerics. Closed forms against second routes: simulation, trees, grids and integrals."""
from fractions import Fraction as F
from math import exp, log, pi, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.linalg import solve_banded
from scipy.optimize import brentq
from scipy.stats import norm, qmc

N, n = norm.cdf, norm.pdf
NONNUMERIC = {}


def d1(s, k, v, t, r=0.0):
    return (log(s / k) + (r + v * v / 2) * t) / (v * sqrt(t))


def call(s, k, v, t, r=0.0):
    a = d1(s, k, v, t, r)
    return s * N(a) - k * exp(-r * t) * N(a - v * sqrt(t))


def put(s, k, v, t, r=0.0):
    return call(s, k, v, t, r) - s + k * exp(-r * t)


def vega(s, k, v, t):
    return s * n(d1(s, k, v, t)) * sqrt(t)


def gamma(s, k, v, t):
    return n(d1(s, k, v, t)) / (s * v * sqrt(t))


def black(f, k, v, t):
    a = (log(f / k) + v * v * t / 2) / (v * sqrt(t))
    return f * N(a) - k * N(a - v * sqrt(t))


def crr(steps, s=100.0, k=100.0, v=0.2, t=1.0, r=0.0, am=False, is_put=False):
    dt = t / steps
    u = exp(v * sqrt(dt))
    d = 1 / u
    q = (exp(r * dt) - d) / (u - d)
    disc = exp(-r * dt)
    sg = -1 if is_put else 1
    x = s * u ** np.arange(steps, -1, -1) * d ** np.arange(0, steps + 1)
    val = np.maximum(sg * (x - k), 0)
    for i in range(steps - 1, -1, -1):
        x = s * u ** np.arange(i, -1, -1) * d ** np.arange(0, i + 1)
        val = disc * (q * val[:-1] + (1 - q) * val[1:])
        if am:
            val = np.maximum(val, sg * (x - k))
    return float(val[0])


def paths(rng, count, steps, v=0.2, t=1.0, s=100.0, r=0.0):
    dt = t / steps
    z = rng.standard_normal((count, steps))
    return s * np.exp(np.cumsum((r - v * v / 2) * dt + v * sqrt(dt) * z, axis=1))


def up_out(s, k, b, v, t):
    def u(x):
        return call(x, k, v, t) - call(x, b, v, t) - (b - k) * N(d1(x, b, v, t) - v * sqrt(t))

    return u(s) - (s / b) * u(b * b / s)


def test_q1():
    assert round(call(100, 100, 0.2, 1), 2) == 7.97 and round(call(100, 100, 0.3, 0.25), 2) == 5.98
    assert round(0.4 * 100 * 0.2) == 8 and round(0.4 * 100 * 0.3 * 0.5) == 6
    # The rule fails far from the money, as it should: it is an at-the-money rule.
    assert abs(call(120, 100, 0.2, 1) - 0.4 * 120 * 0.2) > 10


def test_q2():
    rng = np.random.default_rng(2)
    res = []
    for mu in (0.2, 0.02):
        s = np.full(40_000, 100.0)
        pnl = np.full(40_000, call(100, 100, 0.2, 1))
        dt = 1 / 100
        for i in range(100):
            tau = 1 - i * dt
            d = N((np.log(s / 100) + 0.02 * tau) / (0.2 * sqrt(tau)))
            ns = s * np.exp((mu - 0.02) * dt + 0.2 * sqrt(dt) * rng.standard_normal(40_000))
            pnl += d * (ns - s)
            s = ns
        pnl -= np.maximum(s - 100, 0)
        res.append(pnl)
    assert abs(res[0].mean()) < 0.05 and abs(res[1].mean()) < 0.05
    # The unhedged call is a better bet at the higher drift, so the hedge is what removed it.
    z = rng.standard_normal(400_000)
    assert np.maximum(100 * np.exp(0.18 + 0.2 * z) - 100, 0).mean() > call(100, 100, 0.2, 1) + 5


def test_q3():
    delta = F(20, 30)
    loan = 90 * delta
    assert delta == F(2, 3) and loan == 60
    assert 120 * delta - loan == 20 and 90 * delta - loan == 0
    q = F(100 - 90, 120 - 90)
    assert q == F(1, 3) and 100 * delta - loan == 20 * q == F(20, 3)
    assert 20 * F(8, 10) == 16


def test_q4():
    assert 15 / sqrt(10_000) == 0.15 and round((15 / 0.01) ** 2) == 2_250_000
    # A simulation of a payoff with that spread gives the error it should.
    rng = np.random.default_rng(4)
    means = (15 * rng.standard_normal((400, 10_000))).mean(1)
    assert abs(means.std() - 0.15) < 0.02


def test_q5():
    assert 8 - 6 == 2
    # Path by path in a simulation, and the limit of a far barrier in a closed form.
    s = paths(np.random.default_rng(5), 20_000, 50)
    pay = np.maximum(s[:, -1] - 100, 0)
    hit = s.min(1) <= 90
    assert abs((pay * hit).mean() + (pay * ~hit).mean() - pay.mean()) < 1e-9
    assert abs(up_out(100, 100, 5000, 0.2, 1) - call(100, 100, 0.2, 1)) < 1e-6


def test_q6():
    assert round(exp(-0.05), 3) == 0.951 and round(exp(-0.05) - 0.46, 3) == 0.491


def test_q7():
    assert round(0.3 / sqrt(3), 3) == 0.173 and round(0.4 * 100 * 0.3 / sqrt(3), 2) == 6.93
    assert round(0.4 * 100 * 0.3) == 12
    s = paths(np.random.default_rng(7), 40_000, 252, v=0.3)
    assert abs(np.maximum(s.mean(1) - 100, 0).mean() - 6.93) < 0.15
    assert np.maximum(s.mean(1) - 100, 0).mean() < np.maximum(s[:, -1] - 100, 0).mean()
    w = np.log(s).var(axis=0)
    assert abs(np.mean(np.cumsum(np.ones(252))) / 252 - 0.5) < 0.01 and w[-1] > w[0]


def test_q8():
    assert (20 + 1) * (20 + 2) // 2 == 231 and 2**21 - 1 == 2_097_151
    # Count directly, with small trees.
    for m in (1, 2, 3, 7):
        assert sum(i + 1 for i in range(m + 1)) == (m + 1) * (m + 2) // 2
        assert sum(2**i for i in range(m + 1)) == 2 ** (m + 1) - 1


def test_q9():
    rng = np.random.default_rng(9)
    z = rng.standard_normal(1_000_000)
    assert abs((z + -z).mean() / 2) < 1e-12
    assert np.allclose(z**2, (-z) ** 2)
    pay = np.maximum(100 * np.exp(0.2 * z - 0.02) - 100, 0)
    anti = (pay + np.maximum(100 * np.exp(-0.2 * z - 0.02) - 100, 0)) / 2
    assert round(1 - anti.var() / (pay.var() / 2), 2) == 0.37
    # A straddle is nearly even in z, so the same trick does not pay.
    st = np.abs(100 * np.exp(0.2 * z - 0.02) - 100)
    sa = (st + np.abs(100 * np.exp(-0.2 * z - 0.02) - 100)) / 2
    assert sa.var() / (st.var() / 2) > 1


def test_q10():
    assert abs(0.6 - 0.8 + 0.2) < 1e-12
    lo = np.linalg.cholesky(np.array([[1, 0.6], [0.6, 1]]))
    assert abs(lo[1, 0] - 0.6) < 1e-12 and abs(lo[1, 1] - 0.8) < 1e-12
    rng = np.random.default_rng(10)
    a, b = rng.standard_normal((2, 1_000_000))
    y = 0.6 * a + 0.8 * b
    assert abs(np.corrcoef(a, y)[0, 1] - 0.6) < 0.002 and abs(y.var() - 1) < 0.005
    assert round(0.36 + 0.16, 2) == 0.52


def test_q11():
    assert round(100 * exp(0.05), 2) == 105.13 and round(100 - 100 * exp(-0.05), 2) == 4.88
    assert abs(call(100, 100, 0.33, 1, 0.05) - put(100, 100, 0.33, 1, 0.05) - (100 - 100 * exp(-0.05))) < 1e-9


def test_q12():
    assert 2 * 4 == 8
    # The limit moves as the square of the step, in the scheme of question 27.
    assert abs(stable_step(200, 1.0, 0.2) / stable_step(200, 0.5, 0.2) - 4) < 1e-12


def test_q13():
    assert round(-log(1 - 0.5) / 2, 4) == 0.3466
    u = np.random.default_rng(13).random(1_000_000)
    x = -np.log(1 - u) / 2
    assert abs(x.mean() - 0.5) < 0.002 and abs(np.median(x) - 0.3466) < 0.002


def test_q14():
    d2 = d1(110, 100, 0.3, 0.5) - 0.3 * sqrt(0.5)
    assert round(d2, 3) == 0.343 and round(N(d2), 3) == 0.634
    assert round(d1(110, 100, 0.3, 0.5), 2) == 0.56 and round(N(d1(110, 100, 0.3, 0.5)), 2) == 0.71
    z = np.random.default_rng(14).standard_normal(2_000_000)
    assert abs((110 * np.exp(0.3 * sqrt(0.5) * z - 0.0225) > 100).mean() - N(d2)) < 0.001


def test_q15():
    a = d1(110, 100, 0.3, 0.5)
    assert round(110 * N(a), 2) == 78.17 and round(100 * N(a - 0.3 * sqrt(0.5)), 2) == 63.43
    assert round(call(110, 100, 0.3, 0.5), 2) == 14.75
    z = np.random.default_rng(15).standard_normal(2_000_000)
    s = 110 * np.exp(0.3 * sqrt(0.5) * z - 0.0225)
    assert abs((s * (s > 100)).mean() - 110 * N(a)) < 0.1
    assert s[s > 100].mean() > 110


def test_q16():
    g = gamma(100, 100, 0.2, 1)
    assert round(g, 4) == 0.0198
    th = -(call(100, 100, 0.2, 1 + 1e-4) - call(100, 100, 0.2, 1 - 1e-4)) / 2e-4
    assert round(th, 2) == -3.97 and abs(th + 0.5 * 0.04 * 1e4 * g) < 1e-5
    assert round(0.5 * 0.04 * 1e4 * 0.0198, 2) == 3.96
    assert round(3.97 / 252 * 100, 1) == 1.6
    # The equation with a rate too, at a point off the money.
    h = 1e-2
    r, s = 0.05, 90.0
    v = call(s, 100, 0.2, 1, r)
    vs = (call(s + h, 100, 0.2, 1, r) - call(s - h, 100, 0.2, 1, r)) / (2 * h)
    vss = (call(s + h, 100, 0.2, 1, r) - 2 * v + call(s - h, 100, 0.2, 1, r)) / h**2
    vt = -(call(s, 100, 0.2, 1 + 1e-4, r) - call(s, 100, 0.2, 1 - 1e-4, r)) / 2e-4
    assert abs(vt + 0.5 * 0.04 * s * s * vss + r * s * vs - r * v) < 1e-4


def test_q17():
    assert round(1e4 * exp(0.04)) == 10_408
    z = np.random.default_rng(17).standard_normal(4_000_000)
    assert abs(((100 * np.exp(0.2 * z - 0.02)) ** 2).mean() - 1e4 * exp(0.04)) < 5
    s = 100 * np.exp(0.2 * z - 0.02)
    assert abs(s.var() - 408) < 5


def test_q18():
    a = d1(100, 100, 0.2, 1)
    assert round(100 * N(a), 2) == 53.98 and round(N(a - 0.2), 4) == 0.4602
    assert round(100 * N(a) - 100 * N(a - 0.2), 2) == 7.97
    assert 100 * N(a) > 100 * N(a - 0.2)


def test_q19():
    def norm_call(k):
        d = (100 - k) / 20
        return (100 - k) * N(d) + 20 * n(d)

    assert round(norm_call(100), 2) == 7.98 and round(20 / sqrt(2 * pi), 2) == 7.98
    assert round(norm_call(80), 2) == 21.67
    assert round(20 * N(1) + 20 * n(1), 2) == 21.67
    i80 = brentq(lambda v: call(100, 80, v, 1) - norm_call(80), 0.01, 1)
    i120 = brentq(lambda v: call(100, 120, v, 1) - norm_call(120), 0.01, 1)
    assert round(i80 * 100, 1) == 22.4 and round(i120 * 100, 1) == 18.3
    z = np.random.default_rng(19).standard_normal(2_000_000)
    assert abs(np.maximum(20 * z, 0).mean() - norm_call(100)) < 0.05


def test_q20():
    assert round(2 * (1 - N(1)), 3) == 0.317 and round(1 - N(1), 2) == 0.16
    rng = np.random.default_rng(20)
    w = 20 * np.cumsum(rng.standard_normal((20_000, 252)), axis=1) / sqrt(252)
    assert abs((w.max(1) >= 20).mean() - 0.30) < 0.01
    shift = 0.5826 * 20 / sqrt(252)
    assert round(shift, 2) == 0.73 and round(2 * (1 - N(1 + shift / 20)), 3) == 0.300


def touch(s, b, v, t):
    a = log(b / s)
    return N((-a - v * v * t / 2) / (v * sqrt(t))) + (s / b) * N((-a + v * v * t / 2) / (v * sqrt(t)))


def test_q21():
    assert round(100 / 110, 3) == 0.909
    d = (-log(1.1) - 0.02) / 0.2
    assert round(d, 3) == -0.577 and round(N(d), 3) == 0.282 and round(2 * N(d), 3) == 0.564
    t = touch(100, 110, 0.2, 1)
    assert round(t, 3) == 0.603 and round(100 / 110 * N((-log(1.1) + 0.02) / 0.2), 3) == 0.321
    # A long horizon goes to the perpetual value, and a fine simulation agrees at one year.
    assert abs(touch(100, 110, 0.2, 400) - 100 / 110) < 1e-3
    s = paths(np.random.default_rng(21), 20_000, 2000)
    assert abs((s.max(1) >= 110).mean() - t) < 0.02


def test_q22():
    z = np.random.default_rng(22).standard_normal(2_000_000)
    assert abs((0.2 * z - 0.02).mean() + 0.02) < 0.001
    # Along a path: the log less the hedge's gain is minus half the realised variance.
    rng = np.random.default_rng(23)
    r = 0.2 * sqrt(1 / 2000) * rng.standard_normal((2000, 2000))
    s = np.exp(np.cumsum(r - 0.02 / 2000, axis=1))
    logpay = np.log(s[:, -1])
    gain = (np.diff(s, axis=1, prepend=1.0) / np.c_[np.ones(2000), s[:, :-1]]).sum(1)
    assert abs((gain - logpay).mean() - 0.02) < 0.002 and (gain - logpay).std() < 0.002


def test_q23():
    assert round(call(100, 100, 0.2, 0.5), 2) == 5.64
    rng = np.random.default_rng(23)
    s1 = 100 * np.exp(0.2 * sqrt(0.5) * rng.standard_normal(2_000_000) - 0.01)
    s2 = s1 * np.exp(0.2 * sqrt(0.5) * rng.standard_normal(2_000_000) - 0.01)
    assert abs(np.maximum(s2 - s1, 0).mean() - 5.64) < 0.03
    assert abs(call(1, 1, 0.2, 0.5) * 100 - call(100, 100, 0.2, 0.5)) < 1e-9


def test_q24():
    v = call(100, 100, 0.2, 1) + put(100, 100, 0.2, 0.5)
    assert round(v, 2) == 13.60 and round(put(100, 100, 0.2, 0.5), 2) == 5.64
    rng = np.random.default_rng(24)
    z = rng.standard_normal(400_000)
    st = 100 * np.exp(0.2 * sqrt(0.5) * z - 0.01)
    a = (np.log(st / 100) + 0.01) / (0.2 * sqrt(0.5))
    c = st * N(a) - 100 * N(a - 0.2 * sqrt(0.5))
    assert abs(np.maximum(c, c - st + 100).mean() - v) < 0.05
    assert round(2 * call(100, 100, 0.2, 1), 2) == 15.93


def test_q25():
    assert round(N(-2), 3) == 0.023 and round(1.25**4, 2) == 2.44 and round(exp(1), 2) == 2.72
    rng = np.random.default_rng(25)
    s = np.prod(1 + 0.5 * rng.standard_normal((2_000_000, 4)), axis=1)
    assert abs((s**2).mean() - 1.25**4) < 0.03
    # More steps do converge, and slowly.
    assert (1 + 1 / 400) ** 400 > 2.7


def test_q26():
    u = exp(0.2 * 0.5)
    q = (1 - 1 / u) / (u - 1 / u)
    assert round(u, 3) == 1.105 and round(1 / u, 3) == 0.905 and round(q, 3) == 0.475
    vals = {m: round(crr(m), 4) for m in (10, 11, 100, 101)}
    assert vals == {10: 7.7692, 11: 8.1472, 100: 7.9457, 101: 7.9852}
    assert round(call(100, 100, 0.2, 1), 4) == 7.9656
    assert round((vals[100] + vals[101]) / 2, 4) == 7.9655 and abs((crr(100) + crr(101)) / 2 - 7.9656) < 2e-4
    assert round((vals[10] + vals[11]) / 2, 3) == 7.958
    assert crr(10) < 7.9656 < crr(11) and crr(100) < 7.9656 < crr(101)


def stable_step(smax, ds, v):
    return ds * ds / (v * v * smax * smax)


def test_q27():
    assert abs(stable_step(200, 1.0, 0.2) - 1 / 1600) < 1e-15 and abs(stable_step(100, 1.0, 0.2) - 1 / 400) < 1e-15

    def run(steps):
        grid = np.arange(0.0, 201.0)
        val = np.maximum(grid - 100, 0)
        dt = 1.0 / steps
        a = 0.5 * 0.04 * grid[1:-1] ** 2 * dt
        for _ in range(steps):
            val[1:-1] += a * (val[2:] - 2 * val[1:-1] + val[:-2])
            val[-1] = 100.0
        return val

    good = run(1600)
    assert abs(good[100] - call(100, 100, 0.2, 1)) < 0.05
    bad = run(1200)
    assert np.abs(bad).max() > 1e6


def test_q28():
    m = np.array([[1, 0.9, 0.9], [0.9, 1, 0.0], [0.9, 0.0, 1]])
    assert round(float(np.linalg.det(m)), 2) == -0.62
    assert round(float(np.linalg.eigvalsh(m)[0]), 2) == -0.27
    fails = False
    try:
        np.linalg.cholesky(m)
    except np.linalg.LinAlgError:
        fails = True
    assert fails
    low = 0.81 - 0.19
    assert round(low, 2) == 0.62
    m[1, 2] = m[2, 1] = low + 1e-9
    assert np.linalg.eigvalsh(m)[0] > -1e-9
    m[1, 2] = m[2, 1] = low - 0.01
    assert np.linalg.eigvalsh(m)[0] < 0


def test_q29():
    v = 12 / 40
    assert v == 0.3 and round(call(100, 100, 0.3, 1), 4) == 11.9235
    assert round(vega(100, 100, 0.3, 1), 1) == 39.4
    v1 = v - (call(100, 100, v, 1) - 12) / vega(100, 100, v, 1)
    v2 = v1 - (call(100, 100, v1, 1) - 12) / vega(100, 100, v1, 1)
    assert round(v1 * 100, 3) == 30.194 and round(v2 * 100, 4) == 30.1938
    assert abs(v2 - brentq(lambda x: call(100, 100, x, 1) - 12, 0.01, 2)) < 1e-6
    # Far out of the money and from a poor guess, the raw step leaves the range.
    x = 0.05
    bad = x - (call(100, 200, x, 1) - 0.01) / max(vega(100, 200, x, 1), 1e-12)
    assert bad > 2 or bad < 0


def test_q30():
    assert round(13.15 / sqrt(100_000), 4) == 0.0416 and round(sqrt(2) * 0.0416 / 2, 3) == 0.029
    rng = np.random.default_rng(30)
    z, y = rng.standard_normal((2, 100_000))

    def f(s, x):
        return np.maximum(s * np.exp(0.2 * x - 0.02) - 100, 0)

    com = (f(101, z) - f(99, z)) / 2
    ind = (f(101, z) - f(99, y)) / 2
    assert round(com.std() / sqrt(1e5), 3) == 0.002 and abs(ind.std() / sqrt(1e5) - 0.0294) < 0.001
    assert round(com.std(), 2) == 0.59 and abs(ind.std() / com.std() - 16) < 1
    assert abs(com.mean() - N(0.1)) < 3 * com.std() / sqrt(1e5)


def test_q31():
    v = sqrt(0.25 * 0.09 * 2 + 2 * 0.25 * 0.5 * 0.09)
    assert round(0.25 * 0.09 * 2 + 2 * 0.25 * 0.5 * 0.09, 4) == 0.0675 and round(v, 4) == 0.2598
    assert round(call(100, 100, v, 1), 2) == 10.34
    rng = np.random.default_rng(31)
    a, b = rng.standard_normal((2, 2_000_000))
    c = 0.5 * a + sqrt(0.75) * b
    bas = 50 * np.exp(0.3 * a - 0.045) + 50 * np.exp(0.3 * c - 0.045)
    assert abs(np.maximum(bas - 100, 0).mean() - 10.37) < 0.03
    assert round(call(100, 100, sqrt(0.045), 1), 2) == 8.45 and round(call(100, 100, 0.3, 1), 2) == 11.92
    m2 = 0.5 * exp(0.09) + 0.5 * exp(0.045)
    assert round(sqrt(log(m2)) * 100, 2) == 26.03 and round(call(100, 100, sqrt(log(m2)), 1), 2) == 10.35
    assert abs(((bas / 100) ** 2).mean() - m2) < 0.002


def test_q32():
    z = np.random.default_rng(32).standard_normal(1_000_000)
    s = 100 * np.exp(0.2 * z - 0.02)
    pay = np.maximum(s - 100, 0)
    rho = np.corrcoef(pay, s)[0, 1]
    beta = np.cov(pay, s)[0, 1] / s.var()
    assert round(rho, 2) == 0.89 and round(beta, 2) == 0.58
    assert round(rho**2 * 100) == 79 and round(sqrt(1 - rho**2), 2) == 0.46 and round(1 / (1 - rho**2), 1) == 4.8
    adj = pay - beta * (s - 100)
    assert round(adj.std(), 1) == 6.0 and abs(pay.std() - 13.15) < 0.05
    assert abs(adj.mean() - call(100, 100, 0.2, 1)) < 0.03
    deep, far = np.maximum(s - 50, 0), np.maximum(s - 180, 0)
    assert np.corrcoef(deep, s)[0, 1] > 0.999 and np.corrcoef(far, s)[0, 1] < 0.6


def test_q33():
    v, f = 0.3 / sqrt(3), 100 * exp(-0.09 / 12)
    assert round(v * 100, 1) == 17.3 and round(f, 2) == 99.25 and round(black(f, 100, v, 1), 2) == 6.51
    m = 252
    vd = sqrt(0.09 * (m + 1) * (2 * m + 1) / (6 * m * m))
    fd = 100 * exp(-0.045 * (m + 1) / (2 * m) + vd * vd / 2)
    assert vd > v and round(black(fd, 100, vd, 1), 2) == 6.53
    s = paths(np.random.default_rng(33), 100_000, m, v=0.3)
    g = np.exp(np.log(s).mean(1))
    pay = np.maximum(g - 100, 0)
    assert abs(pay.mean() - black(fd, 100, vd, 1)) < 3 * pay.std() / sqrt(1e5)
    assert abs(call(100, 100, v, 1) - black(f, 100, v, 1)) > 0.25


def test_q34():
    m2 = 2 * 1e4 * (exp(0.09) - 1 - 0.09) / 0.09**2
    assert round(m2, 1) == 10_306.9
    v = sqrt(log(m2 / 1e4))
    assert round(v * 100, 2) == 17.39 and round(call(100, 100, v, 1), 2) == 6.93
    assert round(sqrt(1 - 0.9992**2), 2) == 0.04 and round(1 / sqrt(1 - 0.9992**2)) == 25
    m = 252
    vd = sqrt(0.09 * (m + 1) * (2 * m + 1) / (6 * m * m))
    fd = 100 * exp(-0.045 * (m + 1) / (2 * m) + vd * vd / 2)
    s = paths(np.random.default_rng(34), 50_000, m, v=0.3)
    pa = np.maximum(s.mean(1) - 100, 0)
    pg = np.maximum(np.exp(np.log(s).mean(1)) - 100, 0)
    beta = np.cov(pa, pg)[0, 1] / pg.var()
    adj = pa - beta * (pg - black(fd, 100, vd, 1))
    assert abs(adj.mean() - 6.92) < 0.01
    assert abs(pa.std() / adj.std() - 25) < 3
    assert round(pa.std() / sqrt(1e5), 3) == 0.036 and round(adj.std() / sqrt(1e5), 4) == 0.0014
    # The second-moment formula against the simulation's own.
    assert abs((s.mean(1) ** 2).mean() / 1e4 - m2 / 1e4) < 0.002


def test_q35():
    v = sqrt(0.09 + 0.04 - 0.06)
    assert round(v * 100, 1) == 26.5 and round(100 * (2 * N(v / 2) - 1), 2) == 10.52
    assert round(v / 2, 4) == 0.1323
    assert round(N(v / 2), 3) == 0.553 and round(N(-v / 2), 3) == 0.447
    # With no correlation the ratio's volatility is higher, and so is the price.
    assert round(sqrt(0.09 + 0.04) * 100) == 36 and round(100 * (2 * N(sqrt(0.13) / 2) - 1), 1) == 14.3
    rng = np.random.default_rng(35)
    a, b = rng.standard_normal((2, 2_000_000))
    c = 0.5 * a + sqrt(0.75) * b
    pay = np.maximum(100 * np.exp(0.3 * a - 0.045) - 100 * np.exp(0.2 * c - 0.02), 0)
    assert abs(pay.mean() - 10.52) < 0.05
    # With no volatility on B, it is a plain call on A.
    assert abs(100 * (2 * N(0.3 / 2) - 1) - call(100, 100, 0.3, 1)) < 1e-9
    # The lowest ratio volatility is the difference: perfect correlation.
    assert round(sqrt(0.09 + 0.04 - 2 * 0.3 * 0.2), 2) == 0.10


def test_q36():
    c = call(110, 100, 0.3, 1)
    assert round(c, 2) == 18.14 and round(c - 10, 2) == 8.14
    # The image formula gives S - K at any volatility when the barrier is the strike.
    for v in (0.1, 0.3, 0.6):
        assert abs(call(110, 100, v, 1) - (110 / 100) * call(100 * 100 / 110, 100, v, 1) - 10) < 1e-9
    s = paths(np.random.default_rng(36), 40_000, 500, s=110.0, v=0.3)
    x = np.log(np.c_[np.full(40_000, 110.0), s] / 100)
    stay = (x > 0).all(1) * np.prod(1 - np.exp(-2 * x[:, :-1] * x[:, 1:] / (0.09 / 500)), axis=1)
    pay = np.maximum(s[:, -1] - 100, 0) * stay - (s[:, -1] - 110)  # the stock as a control, with mean zero
    assert abs(pay.mean() - 10) < 3 * pay.std() / 200
    assert c > 10
    # The barrier below the strike: the value now rises with volatility.
    low = call(110, 100, 0.1, 1) - (110 / 95) * call(95 * 95 / 110, 100, 0.1, 1)
    high = call(110, 100, 0.3, 1) - (110 / 95) * call(95 * 95 / 110, 100, 0.3, 1)
    assert high > low + 0.1


def test_q37():
    vals = [round(up_out(100, 100, 130, v, 1), 2) for v in (0.2, 0.15, 0.25)]
    assert vals == [2.97, 3.87, 2.08]
    assert round(call(100, 100, 0.2, 1), 2) == 7.97
    s = paths(np.random.default_rng(37), 20_000, 2000)
    assert abs((np.maximum(s[:, -1] - 100, 0) * (s.max(1) < 130)).mean() - 2.97) < 0.1
    # Value vanishes at the barrier, and it is a plain call when the barrier is far.
    assert abs(up_out(129.9999, 100, 130, 0.2, 1)) < 1e-3


def test_q38():
    b = 130 * exp(0.5826 * 0.2 / sqrt(252))
    assert round(b, 2) == 130.96 and round(up_out(100, 100, b, 0.2, 1), 2) == 3.16
    s = paths(np.random.default_rng(38), 200_000, 252)
    pay = np.maximum(s[:, -1] - 100, 0) * (s.max(1) < 130)
    assert abs(pay.mean() - 3.14) < 0.03
    assert round((3.16 - 2.97) / 2.97 * 100) == 6
    assert round(0.5826 * 0.2 / sqrt(252), 5) == 0.00734
    # The constant itself: minus zeta(1/2) over the root of two pi.
    assert round(1.4603545 / sqrt(2 * pi), 4) == 0.5826


def test_q39():
    x = exp(-2 * log(130 / 120) * log(130 / 125) / (0.04 / 12))
    assert round(x, 3) == 0.152 and round(log(130 / 120), 3) == 0.080 and round(log(130 / 125), 4) == 0.0392
    assert abs(log(x) + 1.884) < 0.002
    # Bridge weights on monthly steps against the continuous price, and the plain monthly bias.
    rng = np.random.default_rng(39)
    m, dt = 12, 1 / 12
    z = rng.standard_normal((200_000, m))
    w = np.c_[np.zeros(200_000), np.cumsum(0.2 * sqrt(dt) * z - 0.02 * dt, axis=1)] + log(100)
    gap = log(130) - w
    live = (gap > 0).all(1)
    stay = np.prod(1 - np.exp(-2 * np.maximum(gap[:, :-1], 0) * np.maximum(gap[:, 1:], 0) / (0.04 * dt)), axis=1)
    pay = np.maximum(np.exp(w[:, -1]) - 100, 0)
    assert abs((pay * live * stay).mean() - 2.97) < 0.03
    assert round((pay * live).mean(), 1) == 3.7
    assert abs((pay * live).mean() - 3.73) < 0.04


def test_q40():
    z = np.random.default_rng(40).standard_normal(2_000_000)
    s = 100 * np.exp(0.2 * z - 0.02)
    pw = (s > 100) * s / 100
    lr = np.maximum(s - 100, 0) * z / 20
    assert round(pw.std(), 2) == 0.59 and round(lr.std(), 2) == 1.34
    assert abs(pw.mean() - N(0.1)) < 0.002 and abs(lr.mean() - N(0.1)) < 0.003
    assert round((lr.std() / pw.std()) ** 2) == 5
    # The digital: pathwise says nothing, the likelihood ratio gets the true delta.
    true = n(d1(100, 100, 0.2, 1) - 0.2) / 20
    assert abs(((s > 100) * z / 20).mean() - true) < 0.001


def test_q41():
    assert round(20 * sqrt(2 / pi), 2) == 15.96
    assert round(2 * 20 / sqrt(2 * pi), 2) == 15.96
    rng = np.random.default_rng(41)
    w = 20 * np.cumsum(rng.standard_normal((20_000, 252)), axis=1) / sqrt(252)
    # The exact mean of a discrete maximum, by Spitzer's identity, and the simulation.
    exact = sum(20 * sqrt(k / 252) / sqrt(2 * pi) / k for k in range(1, 253))
    assert round(exact, 2) == 15.24
    assert abs(w.max(1).clip(min=0).mean() - exact) < 3 * 12.1 / sqrt(20_000)
    assert round(0.5826 * 20 / sqrt(252), 2) == 0.73
    # The two payoffs have the same mean but are not the same trade.
    assert abs(np.abs(w[:, -1]).mean() - 15.96) < 0.25
    assert np.corrcoef(w.max(1).clip(min=0), np.abs(w[:, -1]))[0, 1] < 0.95


def test_q42():
    assert round(N(-0.1), 2) == 0.46 and round(vega(100, 100, 0.2, 1), 1) == 39.7
    assert round(39.7 * 0.002, 3) == 0.079 and round(N(-0.1) + 39.7 * 0.002, 2) == 0.54

    def smile(k):
        return call(100, k, 0.2 - 0.002 * (k - 100), 1)

    assert abs((smile(99.9) - smile(100.1)) / 0.2 - 0.5396) < 2e-3
    # With a flat smile, the spread is the plain digital.
    assert abs((call(100, 99.9, 0.2, 1) - call(100, 100.1, 0.2, 1)) / 0.2 - N(-0.1)) < 1e-4


def test_q43():
    p = 1 - N(4)
    assert round(p * 1e5, 2) == 3.17 and round(1 / sqrt(1e6 * p) * 100) == 18 and round(1e6 * p, 1) == 31.7
    x = np.random.default_rng(43).standard_normal(1_000_000) + 4
    w = np.exp(-4 * x + 8) * (x > 4)
    assert abs(w.mean() - p) < 3 * w.std() / 1e3
    assert round(w.std() / 1e3 / p * 100, 2) == 0.21
    assert round((sqrt(p * (1 - p)) / w.std()) ** 2, -3) == 7000
    assert 0.48 < (x > 4).mean() < 0.52
    # Shift too far, and the error rises.
    y = np.random.default_rng(44).standard_normal(1_000_000) + 7
    u = np.exp(-7 * y + 24.5) * (y > 4)
    assert u.std() > w.std()


def test_q44():
    true = call(100, 100, 0.2, 1)
    sob, mc = [], []
    for seed in range(20):
        u = qmc.Sobol(1, scramble=True, seed=seed).random_base2(14)[:, 0]
        sob.append(np.maximum(100 * np.exp(0.2 * norm.ppf(u) - 0.02) - 100, 0).mean() - true)
        z = np.random.default_rng(seed).standard_normal(2**14)
        mc.append(np.maximum(100 * np.exp(0.2 * z - 0.02) - 100, 0).mean() - true)
    assert round(float(np.std(mc)), 3) == 0.097
    assert round(float(np.std(sob)), 4) == 0.0006
    assert 130 < np.std(mc) / np.std(sob) < 180


def test_q45():
    big = crr(20_000, r=0.05, am=True, is_put=True)
    euro = put(100, 100, 0.2, 1, 0.05)
    a100, a101, a200 = (crr(m, r=0.05, am=True, is_put=True) for m in (100, 101, 200))
    e100 = crr(100, r=0.05, is_put=True)
    assert round(big, 4) == 6.0903 and round(euro, 4) == 5.5735
    assert round(a100, 4) == 6.0824 and round(a101, 4) == 6.1046 and round(a200, 4) == 6.0864
    assert round(e100, 4) == 5.5536
    assert round(a100 - big, 4) == -0.0080 and abs((a100 + a101) / 2 - big - 0.0031) < 1e-4
    assert round(a100 - e100 + euro - big, 4) == 0.0120 and round(2 * a200 - a100 - big, 4) == 0.0001
    assert abs(euro - e100) > 2 * abs(big - a100)
    # Parity of the steps matters for the extrapolation: from odd to even it fails.
    assert abs(2 * crr(50, r=0.05, am=True, is_put=True) - crr(25, r=0.05, am=True, is_put=True) - big) > 0.05
    # The level below which you exercise today lies between 81 and 82.
    for s, low in ((81.0, True), (82.0, False)):
        extra = crr(800, s=s, r=0.05, am=True, is_put=True) - (100 - s)
        assert (abs(extra) < 1e-6) == low


def fd_call(nt, implicit_first, ds=0.25, t=0.02, smax=200.0, k=100.0, v=0.2):
    grid = np.arange(0.0, smax + ds / 2, ds)
    m = len(grid) - 1
    val = np.maximum(grid - k, 0)
    i = np.arange(1, m)
    dt = t / nt
    a = 0.5 * v * v * grid[i] ** 2 / ds**2
    for step in range(nt):
        th = 1.0 if step < implicit_first else 0.5
        rhs = val[i] + (1 - th) * dt * a * (val[i + 1] - 2 * val[i] + val[i - 1])
        rhs[-1] += th * dt * a[-1] * (smax - k)
        ab = np.zeros((3, m - 1))
        ab[0, 1:] = -th * dt * a[:-1]
        ab[1] = 1 + 2 * th * dt * a
        ab[2, :-1] = -th * dt * a[1:]
        val[i] = solve_banded((1, 1), ab, rhs)
        val[-1] = smax - k
    return grid, val


def test_q46():
    grid, val = fd_call(5, 0)
    j = int(100 / 0.25)
    g = (val[j + 1] - 2 * val[j] + val[j - 1]) / 0.25**2
    gu = (val[j + 2] - 2 * val[j + 1] + val[j]) / 0.25**2
    assert round(g, 2) == -1.36 and round(gu, 2) == 0.87
    assert round(gamma(100, 100, 0.2, 0.02), 3) == 0.141
    assert abs(val[j] - call(100, 100, 0.2, 0.02)) < 0.05
    grid, val = fd_call(5, 2)
    g2 = (val[j + 1] - 2 * val[j] + val[j - 1]) / 0.25**2
    assert round(g2, 3) == 0.141
    # Fine time steps cure it too: the scheme is consistent.
    grid, val = fd_call(200, 0)
    assert abs((val[j + 1] - 2 * val[j] + val[j - 1]) / 0.25**2 - 0.141) < 0.002
    # Amplification factors in the large limit.
    x = 1e6
    assert abs((1 - x) / (1 + x) + 1) < 1e-5 and 1 / (1 + 2 * x) < 1e-6


def test_q47():
    def sd(k):
        a = d1(100, k, 0.2, 1)
        m2 = 1e4 * exp(0.04) * N(a + 0.2) - 200 * k * N(a) + k * k * N(a - 0.2)
        return sqrt(m2 - call(100, k, 0.2, 1) ** 2)

    assert round(sd(100), 2) == 13.15 and round(sd(130), 2) == 4.82
    assert round((sd(100) / 0.01) ** 2, -4) == 1_730_000 and round((sd(130) / 0.01) ** 2, -3) == 233_000
    assert round(sd(100) / call(100, 100, 0.2, 1), 2) == 1.65 and round(sd(130) / call(100, 130, 0.2, 1), 2) == 4.78
    z = np.random.default_rng(47).standard_normal(4_000_000)
    s = 100 * np.exp(0.2 * z - 0.02)
    assert abs(np.maximum(s - 130, 0).std() - sd(130)) < 0.02


def lsm_fit(rng, count, r=0.05, v=0.2, k=100.0, dates=12):
    dt = 1 / dates
    z = rng.standard_normal((count // 2, dates))
    z = np.r_[z, -z]
    s = 100 * np.exp(np.cumsum((r - v * v / 2) * dt + v * sqrt(dt) * z, axis=1))
    cash = np.maximum(k - s[:, -1], 0)
    betas = {}
    for t in range(dates - 2, -1, -1):
        cash = cash * exp(-r * dt)
        itm = k - s[:, t] > 0
        x = np.vander(s[itm, t] / k, 4)
        betas[t] = np.linalg.lstsq(x, cash[itm], rcond=None)[0]
        ex = k - s[itm, t] > x @ betas[t]
        pick = np.where(itm)[0][ex]
        cash[pick] = k - s[pick, t]
    return cash * exp(-r * dt), betas


def lsm_fresh(rng, betas, count, r=0.05, v=0.2, k=100.0, dates=12):
    dt = 1 / dates
    z = rng.standard_normal((count // 2, dates))
    z = np.r_[z, -z]
    s = 100 * np.exp(np.cumsum((r - v * v / 2) * dt + v * sqrt(dt) * z, axis=1))
    val = np.zeros(count // 2 * 2)
    done = np.zeros(count // 2 * 2, bool)
    for t in range(dates - 1):
        itm = (k - s[:, t] > 0) & ~done
        ex = k - s[itm, t] > np.vander(s[itm, t] / k, 4) @ betas[t]
        pick = np.where(itm)[0][ex]
        val[pick] = (k - s[pick, t]) * exp(-r * dt * (t + 1))
        done[pick] = True
    val[~done] = np.maximum(k - s[~done, -1], 0) * exp(-r)
    return val


def bermudan(dates, steps, r=0.05, v=0.2):
    dt = 1 / steps
    u = exp(v * sqrt(dt))
    d = 1 / u
    q = (exp(r * dt) - d) / (u - d)
    x = 100 * u ** np.arange(steps, -1, -1) * d ** np.arange(0, steps + 1)
    val = np.maximum(100 - x, 0)
    every = steps // dates
    for i in range(steps - 1, -1, -1):
        x = 100 * u ** np.arange(i, -1, -1) * d ** np.arange(0, i + 1)
        val = exp(-r * dt) * (q * val[:-1] + (1 - q) * val[1:])
        if i % every == 0 and i > 0:
            val = np.maximum(val, 100 - x)
    return float(val[0])


def test_q48():
    tree = bermudan(12, 2004)
    assert round(tree, 2) == 6.04
    rng = np.random.default_rng(3)
    ins, betas = lsm_fit(rng, 100_000)
    out = lsm_fresh(rng, betas, 100_000)
    se = out.std() / sqrt(1e5)
    assert round(se, 3) == 0.023
    assert abs(ins.mean() - tree) < 3 * se and abs(out.mean() - tree) < 3 * se
    assert round(ins.mean(), 2) == 6.04 and round(out.mean(), 2) == 6.03
    assert out.mean() > put(100, 100, 0.2, 1, 0.05)  # worth more than the European
    # Few paths: the fit overstates against fresh paths, on average across seeds, and the tree sits between them.
    ins400, out400, se400 = [], [], []
    for seed in range(40):
        r2 = np.random.default_rng(100 + seed)
        a, b = lsm_fit(r2, 400)
        ins400.append(a.mean())
        out400.append(lsm_fresh(r2, b, 20_000).mean())
        se400.append(a.std() / 20)
    assert round(np.mean(ins400), 1) == 6.2 and round(np.mean(out400), 1) == 5.9
    assert np.mean(out400) < tree < np.mean(ins400)
    assert abs(np.mean(se400) - 0.37) < 0.02 and round(np.std(ins400), 1) == 0.2


def american_grid(ds=1.0, nt=100, smax=300.0, implicit_first=4, r=0.05, v=0.2, k=100.0, t=1.0):
    grid = np.arange(0.0, smax + ds / 2, ds)
    m = len(grid) - 1
    pay = np.maximum(k - grid, 0)
    val = pay.copy()
    i = np.arange(1, m)
    dt = t / nt
    a = 0.5 * v * v * grid[i] ** 2 / ds**2 - 0.5 * r * grid[i] / ds
    b = -(v * v * grid[i] ** 2 / ds**2 + r)
    c = 0.5 * v * v * grid[i] ** 2 / ds**2 + 0.5 * r * grid[i] / ds
    for step in range(nt):
        th = 1.0 if step < implicit_first else 0.5
        rhs = val[i] + (1 - th) * dt * (a * val[i - 1] + b * val[i] + c * val[i + 1])
        rhs[0] += th * dt * a[0] * k
        x = val[i].copy()
        lo, up, dg = -th * dt * a, -th * dt * c, 1 - th * dt * b
        for _ in range(300):
            old = x.copy()
            for j in range(m - 1):
                left = x[j - 1] if j else 0.0
                right = x[j + 1] if j < m - 2 else 0.0
                y = (rhs[j] - lo[j] * left - up[j] * right) / dg[j]
                x[j] = max(pay[j + 1], x[j] + 1.3 * (y - x[j]))
            if np.abs(x - old).max() < 1e-6:
                break
        val[i] = x
        val[0] = k
    return grid, val


def american_cut(ds=1.0, nt=100, smax=200.0, r=0.05, v=0.2, k=100.0, t=1.0, implicit_first=4):
    grid = np.arange(0.0, smax + ds / 2, ds)
    m = len(grid) - 1
    pay = np.maximum(k - grid, 0)
    val = pay.copy()
    i = np.arange(1, m)
    dt = t / nt
    a = 0.5 * v * v * grid[i] ** 2 / ds**2 - 0.5 * r * grid[i] / ds
    b = -(v * v * grid[i] ** 2 / ds**2 + r)
    c = 0.5 * v * v * grid[i] ** 2 / ds**2 + 0.5 * r * grid[i] / ds
    for step in range(nt):
        th = 1.0 if step < implicit_first else 0.5
        rhs = val[i] + (1 - th) * dt * (a * val[i - 1] + b * val[i] + c * val[i + 1])
        rhs[0] += th * dt * a[0] * k
        ab = np.zeros((3, m - 1))
        ab[0, 1:] = -th * dt * c[:-1]
        ab[1] = 1 - th * dt * b
        ab[2, :-1] = -th * dt * a[1:]
        val[i] = np.maximum(solve_banded((1, 1), ab, rhs), pay[i])
        val[0] = k
    return float(val[100])


def test_q49():
    grid, val = american_grid(smax=200.0, nt=60)
    j = 100
    assert abs(val[j] - 6.0903) < 0.01
    # The value never falls below the payoff, and the boundary is where it first exceeds it.
    pay = np.maximum(100 - grid, 0)
    assert (val >= pay - 1e-9).all()
    inside = grid[(val > pay + 1e-4) & (grid < 100)]
    assert 80 < inside.min() < 84
    assert round(crr(2000, r=0.05, am=True, is_put=True), 2) == 6.09
    # The printed figure: a dollar step and a hundred time steps.
    grid, val = american_grid(smax=200.0, nt=100)
    assert abs(val[100] - 6.085) < 0.005
    # Solving the linear system and then cutting off at the payoff does worse on the same grid, with Crank-Nicolson.
    cut = american_cut(nt=100)

    assert abs(cut - 6.0903) > abs(val[100] - 6.0903)


def test_q50():
    def cf(u, s=100.0, v=0.2, t=1.0):
        return np.exp(1j * u * (log(s) - v * v * t / 2) - v * v * u * u * t / 2)

    def price(k, up=200.0):
        p2 = 0.5 + quad(lambda u: (np.exp(-1j * u * log(k)) * cf(u) / (1j * u)).real, 1e-8, up, limit=400)[0] / pi
        p1 = 0.5 + quad(lambda u: (np.exp(-1j * u * log(k)) * cf(u - 1j) / (1j * u * 100)).real, 1e-8, up, limit=400)[0] / pi
        return 100 * p1 - k * p2, p1, p2

    c, p1, p2 = price(100.0)
    assert round(c, 6) == 7.965567 and round(p1, 6) == 0.539828 and round(p2, 6) == 0.460172
    assert abs(c - call(100, 100, 0.2, 1)) < 1e-7
    assert round(price(120.0)[0], 6) == 2.147299 and abs(price(120.0)[0] - call(100, 120, 0.2, 1)) < 1e-7
    # A too-short upper limit does lose accuracy.
    assert abs(price(100.0, up=2.0)[0] - c) > 0.01
    assert abs(price(100.0, up=200.0)[0] - c) < 1e-9
