"""Options and Bond Arithmetic at Speed: each estimate against the exact value it stands in for."""
from math import exp, log, pi, sqrt

import numpy as np
from scipy.stats import norm

NONNUMERIC = {}


def call(s, k, sig, t, r=0.0):
    d1 = (log(s / k) + (r + sig * sig / 2) * t) / (sig * sqrt(t))
    return s * norm.cdf(d1) - k * exp(-r * t) * norm.cdf(d1 - sig * sqrt(t))


def delta(s, k, sig, t):
    return norm.cdf(log(s / k) / (sig * sqrt(t)) + sig * sqrt(t) / 2)


def bond(c, y, n, face=100):
    return sum(c / (1 + y) ** i for i in range(1, n + 1)) + face / (1 + y) ** n


def test_q1():
    assert round(0.4 * 100 * 0.2, 2) == 8
    assert round(0.4 * 50 * 0.3 * sqrt(0.5), 2) == 4.24
    assert round(call(100, 100, 0.2, 1), 2) == 7.97
    assert round(call(50, 50, 0.3, 0.5), 2) == 4.22
    assert round(1 / sqrt(2 * pi), 1) == 0.4
    # The closed form used in the text, and a simulation of the first.
    assert abs(100 * (2 * norm.cdf(0.1) - 1) - call(100, 100, 0.2, 1)) < 1e-9
    rng = np.random.default_rng(1)
    z = rng.standard_normal(1_000_000)
    pay = np.maximum(100 * np.exp(0.2 * z - 0.02) - 100, 0).mean()
    assert abs(pay - 7.97) < 0.05


def test_q2():
    assert round(0.8 * 200 * 0.4 * 0.5, 1) == 32
    assert round(2 * call(200, 200, 0.4, 0.25), 2) == 31.86
    assert round(32 / 200 * 100) == 16
    assert round(40 / 16, 1) == 2.5 and round(sqrt(252), 1) == 15.9
    assert round(sqrt(2 / pi), 1) == 0.8
    # Chance of finishing beyond 0.8 of a standard deviation either way: a bit more than 40%.
    assert 0.40 < 2 * (1 - norm.cdf(0.8)) < 0.45


def test_q3():
    assert round(delta(100, 100, 0.2, 1), 4) == 0.5398
    assert round(delta(100, 100, 0.2, 1) - 1, 4) == -0.4602
    assert round(0.5 + 0.4 * 0.1, 2) == 0.54
    assert round(norm.cdf(-0.1), 2) == 0.46
    # Bump the price: the numerical delta agrees with the formula.
    bump = (call(100.01, 100, 0.2, 1) - call(99.99, 100, 0.2, 1)) / 0.02
    assert abs(bump - delta(100, 100, 0.2, 1)) < 1e-5


def test_q4():
    v = lambda s, t: (call(s, s, 0.205, t) - call(s, s, 0.195, t))  # noqa: E731
    assert round(v(100, 1), 2) == 0.40
    assert round(v(100, 0.25), 2) == 0.20
    assert round(v(500, 1), 1) == 2.0
    assert round(0.004 * 100 * 1, 2) == 0.40 and round(0.004 * 100 * 0.5, 2) == 0.20 and round(0.004 * 500, 2) == 2
    assert round(v(100, 1), 3) == 0.397


def test_q5():
    gap = 100 - 100 * exp(-0.05)
    assert round(gap, 2) == 4.88
    assert round(12 - gap, 2) == 7.12
    assert round(5 - gap, 2) == 0.12
    assert round(100 * exp(0.05), 2) == 105.13
    # Parity check by the model at any volatility: call less put at the same strike.
    for sig in (0.1, 0.3, 0.8):
        c = call(100, 100, sig, 1, 0.05)
        p = c - gap
        pay = 100 * exp(-0.05) * norm.cdf(-(log(1) + (0.05 - sig * sig / 2)) / sig) - 100 * norm.cdf(
            -(log(1) + 0.05 + sig * sig / 2) / sig
        )
        assert abs(p - pay) < 1e-9


def test_q6():
    assert round(25e6 * 6.5 * 0.003) == 487_500
    assert round(0.5 * 60 * 0.003**2 * 100, 3) == 0.027
    assert round(25e6 * 0.5 * 60 * 0.003**2) == 6750
    assert round(487_500 - 6750) == 480_750
    assert 6.5 * 0.30 == 1.95
    # Convexity adds whichever way yields go.
    assert 0.5 * 60 * (-0.003) ** 2 > 0


def test_q7():
    assert round(10e6 * 8.2 * 0.0001) == 8200
    assert round(8200 / 65, 1) == 126.2


def test_q8():
    p = 100 / 1.04**10
    assert round(p, 2) == 67.56 and round(exp(-0.4), 2) == 0.67
    assert round(10 / 1.04, 2) == 9.62
    change = p - 100 / 1.041**10
    assert round(change, 2) == 0.65
    assert round(100 / 1.041**10, 1) == 66.9
    assert round(9.62 * 0.001 * p, 2) == 0.65


def test_q9():
    assert round((1.04**2 / 1.03 - 1) * 100, 2) == 5.01
    assert round(2 * 4 - 3, 1) == 5
    assert round(1.04**2, 4) == 1.0816
    # If the rates are flat, the forward equals the rate.
    assert abs(1.04**2 / 1.04 - 1.04) < 1e-12


def test_q10():
    fair = 1.10 * 1.05 / 1.03
    assert round(fair, 4) == 1.1214 and round(1.10 * 1.02, 3) == 1.122
    usd = 1.10 / 1.03
    assert round(usd, 3) == 1.068
    assert round(usd * 1.05, 4) == 1.1214
    assert round((1.13 - fair) * 100, 2) == 0.86
    # Equal rates mean a forward at spot.
    assert abs(1.10 * 1.03 / 1.03 - 1.10) < 1e-12


def test_q11():
    assert round(50.02 - 49.90 - 0.03, 2) == 0.09
    assert round(0.09 * 50_000) == 4500
    assert 49.90 - 50.04 < 0


def test_q12():
    sig = 12 / (0.8 * 100 * 0.5)
    assert round(sig, 2) == 0.30
    assert round(100 * 0.3 * 0.5) == 15 and round(12 / 0.8) == 15
    assert 1 / 0.8 == 1.25
    # Exact implied volatility from the model is close.
    from scipy.optimize import brentq

    iv = brentq(lambda v: 2 * call(100, 100, v, 0.25) - 12, 0.05, 1)
    assert abs(iv - 0.30) < 0.005


def test_q13():
    g = norm.pdf(0.1) / (100 * 0.2)
    assert round(g, 2) == 0.02 and round(g, 4) == 0.0198
    assert round(0.5 * 0.02 * 10000 * 0.04, 2) == 4
    assert round(4 / 252, 3) == 0.016
    assert round(8 / 2 / 252, 3) == 0.016
    # Exact one-day theta by repricing.
    th = call(100, 100, 0.2, 1) - call(100, 100, 0.2, 1 - 1 / 252)
    assert round(th, 3) == 0.016
    m = 100 * 0.2 / sqrt(252)
    assert round(m, 2) == 1.26
    assert abs(0.5 * g * m**2 - 0.5 * g * 100**2 * 0.04 / 252) < 1e-12


def test_q14():
    assert round(2 * exp(-0.04 * 0.25), 2) == 1.98
    assert round(95 * exp(-0.04 * 0.5), 2) == 93.12
    assert round(100 - 2 * exp(-0.01) - 95 * exp(-0.02), 2) == 4.90
    assert round(100 - 95 * exp(-0.02), 2) == 6.88


def test_q15():
    assert round(100 + 0.5, 2) == 100.5
    assert round(0.5 * 1.015, 4) == 0.5075
    assert round(100 + 0.5075, 2) == 100.51
    assert round(100 * (1 + 0.03 * 0.5), 2) == 101.5
    assert round((101.5 - 100.5) / 100 / 0.5 * 100, 1) == 2.0


def test_q16():
    assert abs(bond(5, 0.05, 10) - 100) < 1e-9
    a = (1 - 1.05**-10) / 0.05
    assert round(a, 2) == 7.72
    # Modified duration by bumping the price: at par it is the annuity factor.
    d = -(bond(5, 0.0501, 10) - bond(5, 0.0499, 10)) / 0.0002 / 100
    assert abs(d - a) < 0.001
    assert round(a * 0.1, 2) == 0.77
    assert round(100 - a * 0.1, 2) == 99.23 and round(bond(5, 0.051, 10), 2) == 99.23


def test_q17():
    carry = (4.5 - 3.5) * 0.25
    assert carry == 0.25
    assert 10 * 0.25 == 2.5
    roll = 4.5 * 0.025
    assert round(roll, 2) == 0.11
    assert round(carry + roll, 2) == 0.36
    assert round((carry + roll) / 4.5 * 100) == 8
    # Limit cases: no financing gap and a flat curve give nothing.
    assert (4.5 - 4.5) * 0.25 + 4.5 * 0 == 0


def test_q18():
    assert round(40.5 / 40 - 1, 4) == 0.0125
    assert round(40 * 1.01, 2) == 40.40
    assert round((40.5 / 40.4 - 1) * 1e4) == 25
    assert 25 - 20 == 5


def test_q19():
    assert round(4000 * (1 + 0.03 * 0.25), 2) == 4030
    assert (4036 - 4030) / 4000 == 0.0015
    assert 15 - 10 == 5
    assert round(0.0005 * 4000, 2) == 2


def test_q20():
    spread = call(100, 100, 0.2, 1) - call(100, 110, 0.2, 1)
    assert round(spread, 2) == 3.67
    assert round(spread / 10, 3) == 0.367
    d2 = log(100 / 105) / 0.2 - 0.1
    assert round(d2, 3) == -0.344
    assert round(norm.cdf(d2) * 100, 1) == 36.5
    # Simulation of the digital.
    rng = np.random.default_rng(20)
    z = rng.standard_normal(2_000_000)
    assert abs((100 * np.exp(0.2 * z - 0.02) > 105).mean() - norm.cdf(d2)) < 0.002


def test_q21():
    d = 0.5
    bach = 20 * (norm.pdf(d) - d * (1 - norm.cdf(d)))
    assert round(bach, 2) == 3.96
    assert round(20 * (0.35 - 0.5 * 0.31), 1) == 3.9
    bs = call(100, 110, 0.2, 1)
    assert round(bs, 2) == 4.29
    assert round((bs - bach) / bs * 100) == 8
    assert bach < bs
    # At the money the two agree to first order, in the normal limit.
    assert abs(20 * norm.pdf(0) - call(100, 100, 0.2, 1)) < 0.03
    # The classic wrong answer: the straight line from at the money, with its delta, is too low, by convexity.
    line = round(0.4 * 20) - 0.5 * 10
    assert line == 3 and line < bach < bs
    for kl, km, kh in ((100, 110, 120), (105, 110, 115)):
        assert call(100, kl, 0.2, 1) + call(100, kh, 0.2, 1) > 2 * call(100, km, 0.2, 1)
    # The option's value falls more slowly further out: the drop from 110 to 120 is less than from 100 to 110.
    assert call(100, 110, 0.2, 1) - call(100, 120, 0.2, 1) < call(100, 100, 0.2, 1) - call(100, 110, 0.2, 1)


def test_q22():
    assert round(norm.cdf(-1), 2) == 0.16
    assert round(log(100 / 120) / 0.2 + 0.1, 2) == -0.81
    assert round(delta(100, 120, 0.2, 1), 2) == 0.21
    assert round(log(100 / 105) / 0.05 + 0.025, 2) == -0.95
    assert round(delta(100, 105, 0.05, 1), 2) == 0.17
    assert round(log(1.2), 3) == 0.182
    # The limit: as total volatility falls, delta at one standard deviation goes to 0.16.
    assert abs(delta(100, 100.1, 0.001, 1) - norm.cdf(-1)) < 0.005


def test_q23():
    two, ten = 2300 / 190, 2300 / 830
    assert round(two, 1) == 12.1 and round(ten, 2) == 2.77
    assert 10 * 460 == 4600
    assert abs(4600 - two * 190 - ten * 830) < 1e-9  # parallel move
    assert abs(two * 190 - ten * 830) < 1e-9  # steepening: wings move opposite ways
    assert round(2 * 4.4 - 4.0 - 4.6, 1) == 0.2
    assert 4600 * 5 == 23_000
    assert 4600 - 5 * 190 - 5 * 830 == -500
    assert round(10 + two + ten - 10, 1) == 14.9


def test_q24():
    t = 1 / 12
    collect = 2 * call(100, 100, 0.3, t)
    assert round(0.8 * 100 * 0.3 * sqrt(t), 2) == 6.93
    assert round(collect, 2) == 6.91
    assert round(1 * sqrt(252) / 100, 2) == 0.16
    low = 2 * call(100, 100, 0.16, t)
    assert round(low, 2) == 3.68
    assert round(collect - low, 2) == 3.22
    assert round(0.8 * 100 * sqrt(t), 1) == 23.1
    assert round(0.8 * 100 * sqrt(t) * 0.14, 2) == 3.23
    gam = 2 * norm.pdf(0.3 * sqrt(t) / 2) / (100 * 0.3 * sqrt(t))
    assert round(gam, 3) == 0.092
    assert round(0.5 * gam * 1e4 * (0.09 - 0.0256) * t, 2) == 2.47
    # The simulation: delta-hedged at 30% with the stock at 16% realised, many paths.
    rng = np.random.default_rng(24)
    n, steps = 20_000, 84  # hedged four times a day
    dt = t / steps
    s = np.full(n, 100.0)
    tau = t
    pnl = np.full(n, collect)
    for _ in range(steps):
        d1 = np.log(s / 100) / (0.3 * sqrt(tau)) + 0.15 * sqrt(tau)
        dlt = 2 * norm.cdf(d1) - 1
        z = rng.standard_normal(n)
        ns = s * np.exp(0.16 * sqrt(dt) * z - 0.5 * 0.0256 * dt)
        pnl += dlt * (ns - s)  # short the straddle, long its delta
        s = ns
        tau -= dt
    pnl -= np.abs(s - 100)
    assert abs(pnl.mean() - (collect - low)) < 0.05
    assert pnl.std() > 0.2  # a mean, not a certainty


def test_q25():
    total = 8 / 0.8
    assert total == 10
    base = 0.09 / 252
    assert round(base, 6) == 0.000357 and round(5 * base, 5) == 0.00179
    event = 0.01 - 5 * base
    assert round(event, 5) == 0.00821
    assert round(sqrt(event) * 100, 2) == 9.06
    assert round(sqrt(5 * base) * 100, 1) == 4.2
    assert round(10 - 4.2, 1) == 5.8
    mine = 0.0036 + 5 * base
    assert round(mine, 5) == 0.00539
    assert round(sqrt(mine) * 100, 2) == 7.34
    assert round(0.8 * sqrt(mine) * 100, 2) == 5.87
    assert round(event / 0.01 * 100) == 82
