"""ETFs, Futures and Index Arbitrage: exact arithmetic with second routes, and limit cases."""
from fractions import Fraction as F
from functools import cache
from math import exp, sqrt

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

NONNUMERIC = {}


def test_q1():
    nav = F(50 * 20 + 30 * 50 + 10 * 100 + 500, 100)
    assert nav == 40
    assert round((40.10 / 40 - 1) * 1e4) == 25


def test_q2():
    assert F("40") + F("0.06") == F("40.06") and F("40") - F("0.04") == F("39.96")
    assert F("40.09") - F("40.06") == F("0.03")


def test_q3():
    fair = 100 * F("1.02") - 1 * F("1.01")
    assert fair == F("100.99")
    # The lock: borrow 100, buy, receive and invest the dividend, deliver at 102, repay.
    assert 102 + F("1.01") - 100 * F("1.02") == F("1.01") == 102 - fair


def test_q4():
    assert 4000 * 50 == 200_000
    assert 10_000_000 / 200_000 == 50 and round(1.2 * 50) == 60


def test_q5():
    prem = F(20, 4000) * 4
    assert prem == F(2, 100)
    assert prem + F(1, 100) == F(3, 100)
    assert 4000 * (1 + (F(3, 100) - F(1, 100)) / 4) == 4020
    assert F(3, 100) - F(25, 1000) == F(5, 1000)


def test_q6():
    assert 4000 * (1 + F(5, 100) / 4) == 4050
    assert 4050 - 4030 == 20
    assert F(20, 4000) * 4 == F(2, 100)


def test_q7():
    assert round(1.02 * 0.98, 4) == 0.9996
    assert round(1.06 * 0.94, 4) == 0.9964
    assert round(3 * (1.02 * 0.98 - 1) * 100, 2) == -0.12


def test_q8():
    a = 0.9 * (1 + 10 / 110)
    assert round(a, 4) == 0.9818
    assert round((a - 1) * 100, 2) == -1.82
    assert round((1 + a) / 2 - 1, 4) * 100 == -0.91
    assert round(1 + a, 4) == 1.9818


def test_q9():
    assert 110 - 100 == 10 and F(10, 200) == F(1, 20)
    # Cap weights do not need a trade: each weight is its own value over the total.
    assert F(110, 200) == F(100 * 11, 10 * 200)


def test_q10():
    notional = 10 * 50 * 4000
    assert notional == 2_000_000 and notional * F(5, 100) == 100_000
    loss = 10 * 50 * 100
    assert loss == 50_000
    assert 10 * 50 * 3900 * F(5, 100) == 97_500
    assert 97_500 - (100_000 - 50_000) == 47_500


def test_q11():
    k = 70 / 71.4
    assert round(k, 4) == 0.9804
    assert round(k**12, 3) == 0.788
    assert round((1 - k**12) * 100, 1) == 21.2
    # Limit: a flat curve costs nothing.
    assert (70 / 70) ** 12 == 1


def flow(L, a, r):
    return L * a * r * (L - 1)


def test_q12():
    a, r = F(1000), F(1, 100)
    assets = a * (1 + 3 * r)
    expo = 3 * a * (1 + r)
    assert assets == 1030 and expo == 3030
    assert 3 * assets - expo == 60 == flow(3, a, r)
    assert flow(-3, a, r) == 120
    assets, expo = a * (1 - 3 * r), -3 * a * (1 + r)
    assert -3 * assets - expo == 120
    assert flow(1, a, r) == 0  # a one-times fund has nothing to do


def test_q13():
    assert round((exp(-0.27) - 1) * 100, 1) == -23.7
    assert round((exp(-0.09) - 1) * 100, 1) == -8.6
    assert round(1.5**3 - 1, 3) == 2.375
    rng = np.random.default_rng(13)
    r = rng.normal(0, 0.3 / sqrt(252), (20_000, 252))
    r -= r.mean(axis=1, keepdims=True)  # flat index
    for lev, want in ((3, exp(-0.27)), (-1, exp(-0.09))):
        got = np.median(np.prod(1 + lev * r, axis=1) / np.prod(1 + r, axis=1) ** lev)
        assert abs(got - want) < 0.02


def test_q14():
    d = F(130, 60)
    assert round(float(d), 3) == 2.167
    assert F(143) / d == 66 and F(198, 3) == 66
    assert round(float(5 / d), 2) == 2.31 and round(10 / 3, 2) == 3.33


def test_q15():
    assert 4000 * F(2, 100) * F(1, 100) == F(8, 10)


def test_q16():
    assert 4000 * F(25, 1000) - 4000 * F(2, 100) == 20
    assert 4000 * F(25, 1000) == 100 and 4000 * F(2, 100) == 80


def test_q17():
    assert 15 + 4 == 19 and 9 - 2 + 1 == 8
    h = F(1, 12)
    assert 19 * h == 7 * h + 1


def test_q18():
    fair = 4020 * F(3, 100) / 4
    assert round(float(fair), 2) == 30.15
    # Second route: continuous carry over the quarter. Read as 2% for the quarter, the spread turns negative.
    assert abs(4020 * (exp(0.03 / 4) - 1) - 30.15) < 0.2
    assert 4020 * (F(5, 100) / 4 - F(2, 100)) < 0
    assert round(10 / 4020 * 100, 2) == 0.25
    assert 4060 - 4020 == 40


def test_q19():
    drag = F(1, 100) * (F(8, 100) - F(4, 100))
    assert drag == F(4, 10_000)
    assert -F(20, 100) + F(8, 100) - drag * 100 == F(-16, 100)


def test_q20():
    up = 4000 * (1 + (F(5, 100) - F(2, 100)) / 2)
    lo = 4000 * (1 + (F(45, 1000) - F(3, 1000) - F(2, 100)) / 2)
    cost = 4000 * F(1, 1000)
    assert up == 4060 and lo == 4044 and cost == 4
    assert up + cost == 4064 and lo - cost == 4040
    assert 2 * cost == 8 and up - lo == 16
    # Same rates, no fee, no costs: the band closes to one price.
    assert 4000 * (1 + (F(5, 100) - F(2, 100)) / 2) == up


def test_q21():
    assert F("95.50") - F("0.20") - 95 == F("0.30")
    assert round(0.5 * sqrt(3), 2) == 0.87
    assert round(0.87 / 0.30, 1) == 2.9


def test_q22():
    assert round(0.00005 * 40 * 100, 1) == 0.2
    assert round(1 - 0.2, 1) == 0.8
    assert round(0.008 * 100_000) == 800
    assert round(0.0001 * 40 * 100, 1) == 0.4 and round(0.004 * 100_000) == 400


def test_q23():
    assert 100 - 90 == 10
    assert round(10e6 * 2e-4) == 2000
    assert round(2000 / 190e6 * 1e4, 3) == 0.105


def test_q24():
    assert 30 + F(15, 100) * 200 == 60 and 40 + F(5, 100) * 200 == 50
    assert 60 - 50 == 10


def test_q25():
    assert 10 * F(8, 10) * F(2, 10) == F(16, 10)
    assert F(16, 10) / F(1, 10) == 16 and 16 / F(2, 10) == 80
    assert round(2 * sqrt(16), 1) == 8


def test_q26():
    # Drag from question 13's formula: it differs between the two funds.
    drag = lambda lev: exp(-0.5 * lev * (lev - 1) * 0.09)  # noqa: E731
    assert abs(drag(3) - exp(-0.27)) < 1e-12 and abs(drag(-3) - exp(-0.54)) < 1e-12
    total = lambda lx: drag(3) * exp(3 * lx) + drag(-3) * exp(-3 * lx)  # noqa: E731
    assert round(total(0), 2) == 1.35 and round(2 - total(0), 2) == 0.65
    grid = np.linspace(-1, 1, 200_001)
    best = 2 - drag(3) * np.exp(3 * grid) - drag(-3) * np.exp(-3 * grid)
    assert round(best.max(), 2) == 0.67 and abs(best.max() - (2 - 2 * exp(-0.405))) < 1e-6
    assert abs(grid[best.argmax()] + 0.045) < 1e-4
    hi, lo = brentq(lambda v: total(v) - 2, 0.01, 1), brentq(lambda v: total(v) - 2, -1, -0.01)
    assert round(hi * 100) == 28 and round(lo * 100) == -37
    rng = np.random.default_rng(26)
    n = 200_000
    logx_terms = rng.normal(0, 0.3 / sqrt(252), (n // 4, 252))
    up = np.prod(1 + 3 * logx_terms, axis=1)
    dn = np.prod(1 - 3 * logx_terms, axis=1)
    pnl = 2 - up - dn
    assert abs(pnl.mean()) < 0.03
    assert round(np.median(pnl), 2) == 0.41
    assert abs((pnl < 0).mean() - 0.285) < 0.01
    assert round(np.quantile(pnl, 0.05)) == -2
    # Second route: daily paths that end flat earn what the formula says, not 0.47.
    idx = np.log1p(logx_terms).sum(axis=1)
    assert abs(pnl[np.abs(idx) < 0.01].mean() - 0.65) < 0.02
    # Path by path, the formula with each path's own realised variance gives the daily product.
    rv = (logx_terms**2).sum(axis=1)
    formula = 2 - np.exp(-3 * rv + 3 * idx) - np.exp(-6 * rv - 3 * idx)
    assert np.median(np.abs(formula - pnl)) < 0.02
    # The exact means: the product of independent mean-one factors has mean one.
    assert F(1, 2) * (1 + 3 * F(1, 100)) + F(1, 2) * (1 - 3 * F(1, 100)) == 1


def test_q27():
    a, b, r = F(10), F(5), F(-4, 100)
    assert flow(3, a, r) == F(-24, 10) and flow(-3, b, r) == F(-24, 10)
    assert 3 * a * (1 + r) == F(288, 10) and a * (1 + 3 * r) == F(88, 10)
    assert 3 * F(88, 10) - F(288, 10) == F(-24, 10)
    assert -3 * b * (1 + r) == F(-144, 10) and b * (1 - 3 * r) == F(56, 10)
    assert -3 * F(56, 10) - F(-144, 10) == F(-24, 10)
    assert F(48, 10) / 20 == F(24, 100)


def test_q28():
    p = F(20, 36)
    assert p == F(5, 9)
    assert p * 120 + (1 - p) * 84 == 104
    zero = (p / F("1.06") + (1 - p) / F("1.02")) / F("1.04")
    assert round(float(zero), 5) == 0.92292
    fwd = 100 / zero
    fut = p * 120 * F("1.06") + (1 - p) * 84 * F("1.02")
    assert round(float(fwd), 2) == 108.35 and round(float(fut), 2) == 108.75
    # Second route: the forward is the bond-measure expectation; and a constant rate closes the gap.
    q_up = (p / F("1.06")) / (p / F("1.06") + (1 - p) / F("1.02"))
    assert q_up * 120 * F("1.06") + (1 - q_up) * 84 * F("1.02") == fwd
    r = F("1.04")
    p2 = (100 * r - 84) / 36
    z2 = 1 / (r * r)
    assert 100 / z2 == p2 * 120 * r + (1 - p2) * 84 * r


def test_q29():
    sig = np.array([[0.04, 0.03], [0.03, 0.09]])
    c = np.array([0.8 * 0.18 * 0.2, 0.7 * 0.18 * 0.3])
    assert round(c[0], 4) == 0.0288 and round(c[1], 4) == 0.0378
    w = np.linalg.solve(sig, c)
    assert np.allclose(w, [0.54, 0.24])
    assert round(w @ c, 6) == 0.024624
    assert round(w @ c / 0.18**2, 2) == 0.76
    assert round(18 * sqrt(1 - w @ c / 0.18**2), 1) == 8.8


def test_q30():
    moves = (4, -4)

    def solve(c):
        @cache
        def v(day, b, pos):
            # value from now on, in points, for a position in the gap; short earns when the gap falls
            out = -1e9
            for new in (-1, 0, 1):
                cost = c * (1 if new != pos else 0)
                if day == 2:
                    val = new * (0 - b) - cost  # new=-1 is short: gains b
                    out = max(out, val)
                else:
                    val = sum(new * m + v(day + 1, b + m, new) for m in moves) / 2 - cost
                    out = max(out, val)
            return out

        return v(0, 6, -1)

    # Long position +1 gains when the gap rises; -1 is short and gains when it falls.
    assert solve(0.0) == 7
    assert solve(0.5) == 6.875
    assert 7 - 6 == 1 and 6.875 - 6 == 0.875
    assert solve(100.0) == 6  # flipping is never worth it: you stay short and make 6
    assert (10 + 4) / 2 == 7 and (14 + 6) / 2 == 10 and (6 + 2) / 2 == 4


def test_q31():
    assert round(1.05 / 1.20 - 1, 4) == -0.125


def test_q32():
    assert 100 + 120 == 220


def test_q33():
    assert round(0.001 * 0.02 * 1e4, 1) == 0.2
    assert round(2 * sqrt(5), 2) == 4.47
    assert round(0.001 * 0.0447 * 1e4, 2) == 0.45
    # Built evenly over the five days instead of held whole: 0.2, 0.4, ... 1.0 of the position.
    built = sum((k / 5) ** 2 for k in range(1, 6))
    assert round(built, 1) == 2.2 and round(0.001 * 0.02 * sqrt(built) * 1e4, 2) == 0.30


def test_q34():
    assert round(exp(-0.12), 3) == 0.887
    assert round(1.1**3 * exp(-0.08 - 0.12), 3) == 1.090
    assert round(100 * (2 * norm.cdf(0.3) - 1), 1) == 23.6
    assert round(3 * 100 * (2 * norm.cdf(0.1) - 1), 1) == 23.9
    rng = np.random.default_rng(34)
    n, steps = 400, 25_000
    z = rng.standard_normal((n, steps))
    dt = 1 / steps
    r_i = 0.2 * sqrt(dt) * z - 0.5 * 0.04 * dt  # log index return
    idx = np.exp(r_i.sum(axis=1))
    ret = np.exp(r_i) - 1
    fund = np.exp(np.log1p(3 * ret - 2 * 0.04 * dt).sum(axis=1))
    formula = idx**3 * exp(-2 * 0.04 - 0.5 * 3 * 2 * 0.04)
    assert np.max(np.abs(fund / formula - 1)) < 0.01
    # Limit case L = 1: the fund is the index, whatever the rate or volatility.
    assert 1 * (1 - 1) == 0


def test_q35():
    assert round(2 * sqrt(16), 1) == 8
    assert 8 / 2 == 4
    assert round(2 * sqrt(1), 1) == 2 and 4 - 2 == 2
    assert round(100 * 0.02, 1) == 2
    assert round(2 * sqrt(5), 2) == 4.47
    assert round(2 / (2 * sqrt(5)), 2) == 0.45
    assert round(1.6 - 0.4, 1) == 1.2
    p = 2 * sqrt(1.2 / 0.1)
    assert round(p, 2) == 6.93 and round(p / 2, 2) == 3.46 and round(p / 2 - 2, 2) == 1.46
