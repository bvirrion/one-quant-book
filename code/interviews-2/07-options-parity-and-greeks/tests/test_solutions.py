"""Options: Parity and Greeks. Payoffs by enumeration, Greeks against finite differences, hedges by simulation."""
from fractions import Fraction as F
from math import exp, log, pi, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.stats import norm

N, n = norm.cdf, norm.pdf
NONNUMERIC = {}


def d12(s, k, v, t, r=0.0, q=0.0):
    a = (log(s / k) + (r - q + v * v / 2) * t) / (v * sqrt(t))
    return a, a - v * sqrt(t)


def call(s, k, v, t, r=0.0, q=0.0):
    a, b = d12(s, k, v, t, r, q)
    return s * exp(-q * t) * N(a) - k * exp(-r * t) * N(b)


def put(s, k, v, t, r=0.0, q=0.0):
    return call(s, k, v, t, r, q) - s * exp(-q * t) + k * exp(-r * t)


def vega(s, k, v, t):
    return s * n(d12(s, k, v, t)[0]) * sqrt(t)


def gamma(s, k, v, t):
    return n(d12(s, k, v, t)[0]) / (s * v * sqrt(t))


def test_q1():
    pay = lambda s: max(s - 100, 0) - max(s - 110, 0) - 3  # noqa: E731
    assert pay(90) == -3 and pay(103) == 0 and pay(120) == 7
    assert max(pay(x) for x in range(50, 200)) == 7 and min(pay(x) for x in range(50, 200)) == -3


def test_q2():
    pay = lambda s: abs(s - 100) - 8  # noqa: E731
    assert pay(92) == pay(108) == 0 and pay(105) == -3 and pay(120) == 12 and pay(100) == -8


def test_q3():
    pay = lambda s: max(s - 90, 0) - 2 * max(s - 100, 0) + max(s - 110, 0) - 2  # noqa: E731
    assert pay(100) == 8 and pay(92) == pay(108) == 0 and pay(70) == pay(150) == -2
    assert min(pay(x) + 2 for x in range(1, 300)) == 0


def test_q4():
    assert 100 + 2 == 102
    assert max(110 - 100, 0) - max(100 - 110, 0) - 2 == 8
    for s in range(50, 151, 10):
        assert max(s - 100, 0) - max(100 - s, 0) == s - 100


def test_q5():
    low = 100 - 90 * exp(-0.05)
    assert round(low, 2) == 14.39
    grown = 88 * exp(0.05)
    assert round(grown, 2) == 92.51
    assert round(grown - 90, 2) == 2.51 and round((grown - 90) * exp(-0.05), 2) == 2.39
    assert round(low - 12, 2) == 2.39
    # Early-exercise bound for question 14: the European bound beats immediate exercise when r is positive.
    assert 100 - 90 * exp(-0.05) > 100 - 90
    # The model respects the bound at every volatility.
    for v in (0.01, 0.2, 1.0):
        assert call(100, 90, v, 1, 0.05) >= low - 1e-9


def test_q6():
    assert round(100 * exp(-0.05), 2) == 95.12
    assert round(97 * exp(0.05), 2) == 101.97
    assert round(97 - 100 * exp(-0.05), 2) == 1.88
    for v in (0.1, 1.0, 5.0):
        assert put(100, 100, v, 1, 0.05) <= 95.13


def test_q7():
    pay = lambda s: max(110 - s, 0) - max(100 - s, 0)  # noqa: E731
    assert min(pay(x) for x in range(0, 200)) == 0 and pay(50) == 10 and pay(105) == 5
    assert 6 - 5 == 1


def test_q8():
    s, k, v, t = 100, 100, 0.2, 1
    bump = 1e-3
    for f, sign in ((call, 1), (put, -1)):
        delta = (f(s + bump, k, v, t) - f(s - bump, k, v, t)) / (2 * bump)
        gam = (f(s + bump, k, v, t) - 2 * f(s, k, v, t) + f(s - bump, k, v, t)) / bump**2
        veg = (f(s, k, v + bump, t) - f(s, k, v - bump, t)) / (2 * bump)
        th = f(s, k, v, t - bump) - f(s, k, v, t)
        assert delta * sign > 0 and gam > 0 and veg > 0 and th < 0
    # Same gamma, vega and theta for call and put, by parity at zero rates.
    assert abs(call(100, 100, 0.21, 1) - put(100, 100, 0.21, 1)) < 1e-9
    assert abs(call(103, 100, 0.2, 1) - put(103, 100, 0.2, 1) - 3) < 1e-9


def test_q9():
    assert round(10 * 100 * 0.6 + 5 * 100 * 0.3 - 200) == 550
    # Position times multiplier times delta, sign by sign: the short put is long delta.
    legs = [(10, 100, 0.6), (-5, 100, -0.3), (-200, 1, 1.0)]
    assert round(sum(q * m * d for q, m, d in legs)) == 550


def test_q10():
    assert round(5 * 100 * 0.5) == 250 and round(0.5 + 0.02, 2) == 0.52
    assert round(5 * 100 * 0.52) == 260 and 260 - 250 == 10
    # Contract gamma times the move gives the same 10 shares.
    assert round(5 * 100 * 0.02 * 1) == 10


def test_q11():
    assert 0.5 * 1000 * 4 - 1500 == 500 and 0.5 * 1000 * 1 - 1500 == -1000
    assert round(sqrt(1500 / 500), 2) == 1.73


def test_q12():
    assert 300 * 3 + 200 * 1 == 1100 and 500 * 3 == 1500


def test_q13():
    b = (call(100, 100, 0.2, 1, 0.01) - call(100, 100, 0.2, 1, 0.0))
    p = (put(100, 100, 0.2, 1, 0.01) - put(100, 100, 0.2, 1, 0.0))
    assert round(b, 2) == 0.47 and round(p, 2) == -0.53
    assert abs(b - p - (100 - 100 * exp(-0.01))) < 1e-9  # parity is the second route
    assert round(100 * N(-0.1) / 100, 2) == 0.46 and round(100 * N(0.1) / 100, 2) == 0.54
    assert round(0.46 + 0.54, 2) == 1


def test_q14():
    def tree(american, is_call, r=0.05, v=0.2, t=1.0, k=100.0, s0=100.0, m=400):
        dt = t / m
        u = exp(v * sqrt(dt))
        d = 1 / u
        q = (exp(r * dt) - d) / (u - d)
        disc = exp(-r * dt)
        sgn = 1 if is_call else -1
        s = s0 * u ** np.arange(m, -1, -1) * d ** np.arange(0, m + 1)
        val = np.maximum(sgn * (s - k), 0)
        for i in range(m - 1, -1, -1):
            s = s0 * u ** np.arange(i, -1, -1) * d ** np.arange(0, i + 1)
            val = disc * (q * val[:-1] + (1 - q) * val[1:])
            if american:
                val = np.maximum(val, sgn * (s - k))
        return float(val[0])

    # The right to exercise a call early is worth nothing, for a put it is worth something.
    assert abs(tree(True, True) - tree(False, True)) < 1e-9
    assert tree(True, False) > tree(False, False) + 0.3
    # The European tree agrees with the closed form, so the comparison is of the right objects.
    assert abs(tree(False, True) - call(100, 100, 0.2, 1, 0.05)) < 0.02
    # At a zero rate the put's right is worth nothing as well.
    assert abs(tree(True, False, r=0.0) - tree(False, False, r=0.0)) < 1e-9


def test_q15():
    assert round(100 - 100 * exp(-0.05), 2) == 4.88
    assert round(100 - 3 - 100 * exp(-0.05), 2) == 1.88
    for s in (50, 100, 150):  # at expiry all legs net to nothing
        c, p = max(s - 100, 0), max(100 - s, 0)
        assert c - p - s + 100 == 0


def test_q16():
    assert round(100 * 0.02, 2) == 2 and 2 > 1.88
    # Implied borrow: the rate b making S e^{-bT} - K e^{-rT} = 3.
    b = -log((3 + 100 * exp(-0.05)) / 100)
    assert round(b * 100, 1) == 1.9
    # Parity's gap, and with no borrow fee the call less put is parity's value.
    assert round(100 - 95.12, 2) == 4.88 and round(4.88 - 3, 2) == 1.88
    assert round(100 * exp(-0.0) - 100 * exp(-0.05), 2) == 4.88


def test_q17():
    assert round(100 - 100 * exp(-0.05), 2) == 4.88 and 100 - 100 == 0


def test_q18():
    for s in (10, 90, 100, 110, 300):
        assert (max(s - 90, 0) - max(90 - s, 0)) - (max(s - 110, 0) - max(110 - s, 0)) == 20
    assert round(log(20 / 18.7) * 100, 2) == 6.72
    assert round(20 * exp(-0.05), 2) == 19.02


def test_q19():
    assert 4 - 3.5 == 0.5
    # A model check: at zero dividends the longer European call is worth more.
    assert call(100, 100, 0.2, 0.25, 0.03) > call(100, 100, 0.2, 1 / 12, 0.03)
    # A dividend can reverse it, at this size, through a dividend yield over the longer life.
    assert call(100, 100, 0.2, 0.25, 0.0, 0.5) < call(100, 100, 0.2, 1 / 12, 0.0, 0.0)


def test_q20():
    assert round(gamma(100, 100, 0.2, 1), 4) == 0.0198
    g1 = gamma(100, 100, 0.2, 1 / 252)
    assert round(g1, 3) == 0.317
    assert round(g1 / gamma(100, 100, 0.2, 1)) == 16
    assert round(sqrt(2 * log(2)), 2) == 1.18
    assert round(sqrt(2 * log(2)) * 100 * 0.2 / sqrt(252), 2) == 1.48
    assert round(N(1.5 / (20 / sqrt(252))), 2) == 0.88 and round(N(-1.5 / (20 / sqrt(252))), 2) == 0.12
    # The half-gamma point, by direct search.
    grid = np.linspace(100, 104, 40_001)
    gs = np.array([gamma(x, 100, 0.2, 1 / 252) for x in grid[::40]])
    x = grid[::40][np.argmin(np.abs(gs - g1 / 2))]
    assert abs(x - 101.48) < 0.03


def test_q21():
    v = put(50, 100, 0.2, 1, 0.05)
    assert round(v, 2) == 45.13
    chg = put(50, 100, 0.2, 1 - 1 / 365, 0.05) - v
    assert round(chg * 100, 1) == 1.3
    assert round(chg * 365, 2) == 4.74
    assert round(100 * exp(-0.05) - 50, 2) == 45.12
    assert round(0.05 * 100 * exp(-0.05), 2) == 4.76


def test_q22():
    vs = [vega(100, k, 0.2, 1) / 100 for k in (80, 100, 120)]
    assert [round(x, 2) for x in vs] == [0.19, 0.40, 0.29]
    assert [round(d12(100, k, 0.2, 1)[0], 2) for k in (80, 100, 120)] == [1.22, 0.1, -0.81]
    assert round(log(1.2), 2) == 0.18 and round(log(0.8), 2) == -0.22


def test_q23():
    a, b = d12(100, 100, 0.4, 1)
    assert round(a, 1) == 0.2 and round(b, 1) == -0.2
    assert round(N(a), 3) == 0.579 and round(N(b), 3) == 0.421
    assert round(N(a) - N(b), 2) == 0.16
    rng = np.random.default_rng(23)
    z = rng.standard_normal(2_000_000)
    assert abs((100 * np.exp(0.4 * z - 0.08) > 100).mean() - N(b)) < 0.001
    # Small total volatility: the two come together.
    a, b = d12(100, 100, 0.001, 1)
    assert abs(N(a) - N(b)) < 0.001


def test_q24():
    assert round(0.55 - exp(-0.02), 4) == -0.4302
    assert round(exp(-0.02), 4) == 0.9802
    assert round(0.55 - 1, 2) == -0.45
    # Finite-difference check of the identity.
    b = 1e-3
    dc = (call(100 + b, 100, 0.2, 1, 0, 0.02) - call(100 - b, 100, 0.2, 1, 0, 0.02)) / (2 * b)
    dp = (put(100 + b, 100, 0.2, 1, 0, 0.02) - put(100 - b, 100, 0.2, 1, 0, 0.02)) / (2 * b)
    assert abs(dc - dp - exp(-0.02)) < 1e-6


def test_q25():
    assert round(0.04 * 3, 2) == 0.12
    assert round(0.12 * 3, 2) == 0.36
    assert round(2 * 0.5 * 0.04 * 9, 2) == 0.36


def test_q26():
    assert 200 * 2 == 400 and 0.5 * 50 * 4 == 100 and 300 * -1 == -300
    assert 400 + 100 - 300 - 150 == 50
    assert 120 - 50 == 70


def test_q27():
    pay = lambda s: max(s - 110, 0) - max(90 - s, 0) + 0.5  # noqa: E731
    assert pay(80) == -9.5 and pay(100) == 0.5 and pay(120) == 10.5
    assert round(0.35 + 0.27, 2) == 0.62 and round(0.37 - 0.31, 2) == 0.06
    assert round(0.37 + 0.31, 2) == 0.68


def test_q28():
    for s in range(50, 160, 5):
        hold = s + max(90 - s, 0) - max(s - 110, 0)
        assert hold == 90 + max(s - 90, 0) - max(s - 110, 0)
        assert 90 <= hold <= 110
    assert 100 + 3 - 3 - 90 == 10


def test_q29():
    pay = lambda s: s - 100 + 3 - max(s - 105, 0)  # noqa: E731
    assert pay(85) == -12 and pay(105) == 8 and pay(120) == 8
    assert 3 - 100 + 105 == 8
    for s in range(60, 150, 5):
        assert pay(s) == 8 - max(105 - s, 0)


def test_q30():
    assert round(5 * exp(-0.025), 2) == 4.88
    assert round(100 - 95 * exp(-0.025), 2) == 7.35
    # With the forward's fair relation to the stock the two forms are one.
    s = 100 * exp(-0.025)
    assert abs((s - 95 * exp(-0.025)) - 5 * exp(-0.025)) < 1e-12


def test_q31():
    a, b = d12(100, 100, 0.2, 1)
    assert round(b, 1) == -0.1 and round(N(b), 2) == 0.46 and round(N(a), 2) == 0.54
    eps = 0.5
    spread = (call(100, 100 - eps, 0.2, 1) - call(100, 100 + eps, 0.2, 1)) / (2 * eps)
    assert abs(spread - N(b)) < 1e-3
    rng = np.random.default_rng(31)
    z = rng.standard_normal(2_000_000)
    assert abs((100 * np.exp(0.2 * z - 0.02) > 100).mean() - N(b)) < 0.001


def test_q32():
    t = 1 / 12

    def g(s):
        return gamma(s, 100, 0.2, t) - gamma(s, 110, 0.2, t)

    assert g(100) > 0 and g(95) > 0 and g(110) < 0 and g(115) < 0
    star = sqrt(100 * 110) * exp(-0.04 * t / 2)
    assert round(star, 1) == 104.7
    assert abs(g(star)) < 1e-12 + abs(g(100)) * 0.02
    assert g(star - 0.5) > 0 > g(star + 0.5)


def test_q33():
    c, p = call(100, 100, 0.25, 1), put(100, 100, 0.27, 1)
    assert round(c, 2) == 9.95 and round(p, 2) == 10.74
    assert round(p - c, 2) == 0.79
    assert round(call(100, 100, 0.27, 1) - c, 2) == 0.79
    assert abs(vega(100, 100, 0.26, 1) / 100 * 2 - 0.79) < 0.01
    # Lower the forward by the gap, and one volatility fits both options.
    f = 100 - 0.79
    assert abs(call(f, 100, 0.26, 1) - put(f, 100, 0.26, 1) + 0.79) < 1e-9


def test_q34():
    assert round(100 * exp(-0.05), 2) == 95.12
    assert round(99 * exp(0.05), 2) == 104.08
    assert 100 - 1 == 99


def test_q35():
    v = 1e6 * n(d12(100, 100, 0.2, 1)[1]) / (100 * 0.2)
    assert round(v, -1) == 19_850
    w = 1e6 * n(d12(100, 100, 0.2, 1 / 252)[1]) / (100 * 0.2 / sqrt(252))
    assert round(w, -2) == 316_600
    # The spread covers the digital at every expiry price, and its delta stays under the cap for any time left.
    for s in range(50, 150):
        assert (max(s - 98, 0) - max(s - 100, 0)) * 1e6 / 2 >= (1e6 if s > 100 else 0)
    for t in (1e-5, 1 / 252, 1):
        for s in np.linspace(90, 110, 81):
            a = N(d12(s, 98, 0.2, t)[0]) - N(d12(s, 100, 0.2, t)[0])
            assert a * 1e6 / 2 <= 500_000
    assert 1e6 * n(d12(100, 100, 0.2, 1e-5)[1]) / (100 * 0.2 * sqrt(1e-5)) > 500_000


def test_q36():
    assert round((100.02 - 0.02 - 100) * 100_000) == 0
    assert round((100 - 98) * 100_000) == 200_000
    # The holder's choice runs against you: at 98 no exercise, at 102 exercise.
    for evening, exercised, result in ((98, False, -200_000), (102, True, 0)):
        assert (evening > 100) == exercised
        end = 100 if exercised else evening
        assert round((end - 100) * 100_000) == result


def test_q37():
    pv = 100 * exp(-0.05 * 0.25)
    assert round(pv, 2) == 98.76
    assert round(100 - pv, 2) == 1.24
    assert round(0.40 + 108 - pv, 2) == 9.64
    assert round(10 - (0.40 + 108 - pv), 2) == 0.36
    assert 2 > 100 - pv + 0.40


def test_q38():
    p = F(25, 100) / F(4, 10)
    assert p == F(5, 8)
    r = F(105, 100)
    up = (p * 0 + (1 - p) * 4) / r
    down = (p * 4 + (1 - p) * 36) / r
    assert round(float(up), 2) == 1.43 and round(float(down), 2) == 15.24
    eur = (p * up + (1 - p) * down) / r
    ame = (p * up + (1 - p) * max(down, 20)) / r
    assert round(float(eur), 2) == 6.29 and round(float(ame), 2) == 7.99
    assert round(float(ame - eur), 2) == 1.70


def test_q39():
    assert round(gamma(100, 100, 0.3, 1 / 12), 3) == 0.046
    assert round(gamma(120, 100, 0.3, 1 / 12), 4) == 0.0038
    a, b = 0.5 * 0.046 * 4, 0.5 * 0.0038 * 2.4**2
    assert round(a, 3) == 0.092 and round(b, 3) == 0.011
    assert round(a / b) == 8


def test_q40():
    vs = 2 * vega(100, 100, 0.2, 1)
    vst = vega(100, 90, 0.2, 1) + vega(100, 110, 0.2, 1)
    w = vs / vst
    assert round(vs, 1) == 79.4 and round(vst, 1) == 69.9 and round(w, 3) == 1.135

    def strad(v):
        return 2 * call(100, 100, v, 1)

    def strangle(v):
        return put(100, 90, v, 1) + call(100, 110, v, 1)

    assert round(strad(0.2), 2) == 15.93 and round(w * strangle(0.2), 2) == 8.95
    assert round(strad(0.2) - w * strangle(0.2), 2) == 6.99
    net = lambda v: w * strangle(v) - strad(v)  # noqa: E731
    assert round(net(0.25) - net(0.2), 2) == 0.10 and round(net(0.15) - net(0.2), 2) == 0.16
    # Zero vega at the start, by finite difference.
    assert abs(net(0.2001) - net(0.1999)) < 1e-4


def hedged(si, sr, t, steps, paths=20_000, cost=0.0, seed=1, delta_vol=None, s0=100.0, k=100.0):
    rng = np.random.default_rng(seed)
    dv = si if delta_vol is None else delta_vol
    dt = t / steps
    s = np.full(paths, s0)
    pnl = np.full(paths, call(s0, k, si, t))
    tau = t
    prev = np.zeros(paths)
    costs = np.zeros(paths)
    for i in range(steps):
        d = N((np.log(s / k) + dv * dv / 2 * tau) / (dv * sqrt(tau)))
        if i > 0:
            costs += cost / 2 * np.abs(d - prev) * s
        z = rng.standard_normal(paths)
        ns = s * np.exp(sr * sqrt(dt) * z - 0.5 * sr * sr * dt)
        pnl += d * (ns - s)
        s = ns
        prev = d
        tau -= dt
    pnl -= np.maximum(s - k, 0)
    return pnl, costs


def test_q41():
    approx = sqrt(pi / 4) * 0.2 * vega(100, 100, 0.2, 1) / sqrt(252)
    assert round(approx, 3) == 0.443
    assert round(sqrt(pi / 4), 3) == 0.886
    a, _ = hedged(0.2, 0.2, 1, 252)
    assert round(a.std(), 2) == 0.44
    assert abs(a.mean()) < 0.02  # right volatility: no edge either way
    b, _ = hedged(0.2, 0.2, 1, 1008, paths=5000)
    assert abs(b.std() / a.std() - 0.5) < 0.05
    assert round(call(100, 100, 0.2, 1), 2) == 7.97
    assert round(approx / 7.97 * 100, 1) == 5.6


def test_q42():
    k, s = 0.002, 0.2 * sqrt(1 / 252)
    assert round(s, 4) == 0.0126
    a = sqrt(2 / pi) * k / s
    assert round(a, 3) == 0.127
    hat = 0.2 * sqrt(1 + a)
    assert round(hat * 100, 1) == 21.2
    prem = vega(100, 100, 0.2, 1) * (hat - 0.2)
    assert round(prem, 2) == 0.49
    assert round(hat - 0.2, 4) == 0.0123
    _, c = hedged(0.2, 0.2, 1, 252, cost=k)
    assert round(c.mean(), 2) == 0.50


def test_q43():
    v1, vm = vega(100, 100, 0.2, 1), vega(100, 100, 0.2, 1 / 12)
    assert round(v1, 1) == 39.7 and round(vm, 1) == 11.5
    r = v1 / vm
    assert round(r, 2) == 3.45
    gy, gm = gamma(100, 100, 0.2, 1), gamma(100, 100, 0.2, 1 / 12)
    assert round(gm, 4) == 0.0691
    assert round(r * gm - gy, 3) == 0.218
    assert round(11.5 * 3.46, 1) == 39.8
    assert abs(vm * sqrt(12) / v1 - 1) < 0.01  # one lot of each cancels


def test_q44():
    def per_point(s):
        return (N(d12(s, 100, 0.205, 1)[1]) - N(d12(s, 100, 0.195, 1)[1]))

    assert round(per_point(90), 4) == 0.0070
    assert round(per_point(100), 4) == -0.0020
    assert round(per_point(110), 4) == -0.0107
    star = 100 * exp(-0.02)
    assert round(star, 2) == 98.02
    assert abs(per_point(star)) < 5e-6 and per_point(star - 1) > 0 > per_point(star + 1)


def test_q45():
    assert F(1, 5) == F(1_000_000, 5_000_000)


def test_q46():
    bs = call(100, 100, 0.2, 1)
    dk = (call(100, 101, 0.2, 1) - call(100, 99, 0.2, 1)) / 2
    assert round(call(100, 99, 0.2, 1), 2) == 8.44 and round(call(100, 101, 0.2, 1), 2) == 7.52
    assert round((7.52 - 8.44) / 2, 2) == -0.46
    assert round((bs - 100 * dk) / 100, 3) == 0.540
    # A smile that stays with the strike breaks the identity: the reading of delta rests on the assumption.
    sticky = lambda s, k: call(s, k, 0.2 + 0.1 * (100 - k) / 100, 1)  # noqa: E731
    assert abs(sticky(200, 200) - 2 * sticky(100, 100)) > 0.5
    assert round(N(0.1), 4) == 0.5398
    assert round((7.97 + 46) / 100, 4) == 0.5397
    # Homogeneity in the model itself, and the identity in full.
    assert abs(call(200, 200, 0.2, 1) - 2 * bs) < 1e-9
    assert abs(bs - (100 * N(0.1) - 100 * N(-0.1))) < 1e-9


def test_q47():
    c = {90: F(14), 100: F(8), 110: F("5.5"), 120: F(2)}
    assert all(c[a] >= c[b] for a, b in ((90, 100), (100, 110), (110, 120)))
    assert all(c[a] - c[b] <= 10 for a, b in ((90, 100), (100, 110), (110, 120)))
    assert c[100] - 2 * c[110] + c[120] == -1
    assert c[90] - 2 * c[100] + c[110] == F("3.5")
    pay = lambda s: max(s - 100, 0) - 2 * max(s - 110, 0) + max(s - 120, 0) + 1  # noqa: E731
    vals = [pay(s) for s in range(50, 200)]
    assert min(vals) == 1 and max(vals) == 11
    assert (c[90] - c[100]) / 10 == F(3, 5)
    assert (c[100] - c[110]) / 10 == F(1, 4)
    assert (c[110] - c[120]) / 10 == F(7, 20)


def test_q48():
    a = quad(lambda k: call(100, k, 0.2, 1), 100, 3000)[0]
    b = quad(lambda k: put(100, k, 0.2, 1), 1e-6, 100)[0]
    total = 10_000 + 2 * a + 2 * b
    assert round(2 * a + 2 * b, 2) == 408.11
    assert round(total, 2) == 10_408.11
    assert abs(total - 1e4 * exp(0.04)) < 1e-3
    # The identity at any terminal price, by direct integration of the two payoffs.
    for s in (40.0, 100.0, 170.0):
        low = np.linspace(0, 100, 100_001)
        high = np.linspace(100, 400, 300_001)
        part = np.trapezoid(np.maximum(low - s, 0), low) + np.trapezoid(np.maximum(s - high, 0), high)
        assert abs(1e4 + 200 * (s - 100) + 2 * part - s * s) < 1e-3


def test_q49():
    true = call(100, 100, 0.3, 0.25) - call(100, 100, 0.2, 0.25)
    assert round(true, 2) == 1.99
    a, _ = hedged(0.3, 0.2, 0.25, 63, delta_vol=0.3, seed=11)
    b, _ = hedged(0.3, 0.2, 0.25, 63, delta_vol=0.2, seed=12)
    assert abs(a.mean() - true) < 0.03 and abs(b.mean() - true) < 0.03
    assert abs(a.std() - 0.74) < 0.02
    assert abs(b.std() - 0.44) < 0.02
    # Hedged at the realised volatility, finer steps leave only discreteness: it falls with the root of the steps.
    c, _ = hedged(0.3, 0.2, 0.25, 252, paths=6000, delta_vol=0.2, seed=13)
    assert abs(c.std() / b.std() - 0.5) < 0.06


def test_q50():
    gam = 2 * 0.05 / 0.2**2
    assert round(gam, 9) == 2.5
    star = gam * 100 / (1 + gam)
    assert round(star, 2) == 71.43
    v = (100 - star) * (100 / star) ** -gam
    assert round(v, 2) == 12.32
    assert round(100 - star, 2) == 28.57
    # The ODE holds, and the level is the best one.
    val = lambda s, lev=star: (100 - lev) * (s / lev) ** -gam  # noqa: E731
    s, h = 100.0, 1e-3
    d1 = (val(s + h) - val(s - h)) / (2 * h)
    d2 = (val(s + h) - 2 * val(s) + val(s - h)) / h**2
    assert abs(0.5 * 0.04 * s * s * d2 + 0.05 * s * d1 - 0.05 * val(s)) < 1e-4
    levels = np.linspace(40, 99, 5901)
    best = levels[np.argmax([val(100.0, x) for x in levels])]
    assert abs(best - star) < 0.02
    # Smooth pasting at the boundary.
    dd = (val(star + h) - val(star - h)) / (2 * h)
    assert abs(dd + 1) < 1e-4
    # A rate near zero: the level goes to zero and the value towards the strike.
    g = 2 * 1e-4 / 0.04
    lev = g * 100 / (1 + g)
    assert lev < 1 and (100 - lev) * (100 / lev) ** -g > 95
