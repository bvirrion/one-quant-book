"""Markets and Microstructure: exact arithmetic, closed forms against simulation, and limit cases."""
from fractions import Fraction as F
from math import comb, cosh, exp, log, sinh, sqrt

import numpy as np
from scipy.optimize import minimize
from scipy.stats import gamma, norm, poisson

NONNUMERIC = {
    11: "states a routing rule; checked against the ledger, no computed number",
    14: "states Regulation SHO requirements; checked against the ledger",
    40: "judgement and law on spoofing, through the ledger",
    41: "a judgement on a tick-size change, with no number to check",
}


def test_q1():
    cost = 100 * F("100.02") + 200 * F("100.03")
    assert cost == F("30008")
    avg = cost / 300
    assert round(float(avg), 4) == 100.0267
    assert round(float(avg - 100) * 100, 2) == 2.67
    assert (F("99.98") + F("100.03")) / 2 == F("100.005")
    assert 400 - 200 == 200


def test_q2():
    assert (F("100") + F("100.02")) / 2 == F("100.01")
    micro = (F("100") * 100 + F("100.02") * 900) / 1000
    assert micro == F("100.018")
    wrong = (F("100") * 900 + F("100.02") * 100) / 1000
    assert wrong == F("100.002")
    # Equal sizes: the microprice is the mid.
    assert (F("100") * 500 + F("100.02") * 500) / 1000 == F("100.01")


def test_q3():
    left, fills = 250, []
    for size in (100, 200, 50):
        take = min(size, left)
        fills.append(take)
        left -= take
    assert fills == [100, 150, 0]
    pr = [250 * s / 350 for s in (100, 200, 50)]
    assert [round(x, 1) for x in pr] == [71.4, 142.9, 35.7]
    assert round(sum(pr), 9) == 250


def test_q4():
    eff = 2 * (F("100.03") - F("100.00"))
    real = 2 * (F("100.03") - F("100.02"))
    imp = 2 * (F("100.02") - F("100.00"))
    assert eff == F("0.06") and real == F("0.02") and imp == F("0.04")
    assert real + imp == eff


def test_q5():
    assert F("1") + F("0.3") + F("0.2") == F("1.5")
    assert 1 + 2 * F("0.2") == F("1.4")
    assert F("0.3") - F("0.2") == F("0.1")


def test_q6():
    assert F("0.01") / 5 * 10_000 == 20
    assert F("0.01") / 500 * 10_000 == F("0.2")


def test_q7():
    assert round(2 * sqrt(0.0004), 10) == 0.04
    rng = np.random.default_rng(7)
    n = 2_000_000
    q = rng.choice([-1, 1], n)
    m = rng.normal(0, 0.01, n).cumsum()
    p = m + 0.02 * q
    d = np.diff(p)
    cov = np.mean(d[1:] * d[:-1]) - d.mean() ** 2
    assert abs(cov + 0.0004) < 2e-5
    # Limit: no spread, no autocovariance.
    d0 = np.diff(m)
    assert abs(np.mean(d0[1:] * d0[:-1])) < 1e-5


def test_q8():
    vwap = (100 * F(10) + 200 * F("10.2") + 700 * F("10.1")) / 1000
    assert vwap == F("10.11")
    assert vwap - F("10.08") == F("0.03")
    assert round(0.03 / 10.11 * 1e4) == 30
    assert (F(10) + F("10.2") + F("10.1")) / 3 == F("10.1")


def test_q9():
    assert 30 / 2 == 15
    assert round(30 / (0.2 * 2)) == 75


def test_q10():
    fair = 2 * 10 * F("1.25")
    assert fair == 25
    assert (F("25.2") - 25) / 25 == F("0.008")
    assert 80 - 30 == 50
    assert round(25 * 0.005, 3) == 0.125


def test_q12():
    buys = {101: 100, 100: 200, 99: 300}
    sells = {99: 150, 100: 150, 101: 200}
    table = {}
    for price in (99, 100, 101):
        d = sum(v for k, v in buys.items() if k >= price)
        s = sum(v for k, v in sells.items() if k <= price)
        table[price] = (d, s, min(d, s))
    assert table == {99: (600, 150, 150), 100: (300, 300, 300), 101: (100, 500, 100)}
    assert max(table, key=lambda p: table[p][2]) == 100


def test_q13():
    x = 200_000 / 0.9
    assert round(x) == 222_222
    assert round(x / 2_000_000 * 100, 1) == 11.1
    assert abs(x / (x + 2_000_000) - 0.1) < 1e-12
    assert round(200_000 * 9) == 1_800_000


def test_q15():
    assert round(0.02 * sqrt(0.01) * 1e4) == 20 and round(0.02 * sqrt(0.04) * 1e4) == 40
    assert 4**1.5 == 8


def test_q16():
    exe, com, opp = 8000 * F("0.10"), 8000 * F("0.01"), 2000 * F("0.30")
    assert (exe, com, opp) == (800, 80, 600)
    assert exe + com + opp == 1480
    assert round(1480 / 500_000 * 1e4, 1) == 29.6
    # The paper-portfolio route.
    assert 10_000 * F("0.30") - (8000 * F("0.20") - 80) == 1480


def test_q17():
    n, rate = 21, 1.5
    assert n / rate == 14
    assert round(sqrt(n) / rate, 2) == 3.06
    p = 1 - poisson.cdf(20, 30)
    assert round(p, 2) == 0.96
    assert abs(gamma.cdf(20, n, scale=1 / rate) - p) < 1e-9
    rng = np.random.default_rng(17)
    t = rng.exponential(1 / rate, (400_000, n)).sum(axis=1)
    assert abs(t.mean() - 14) < 0.03 and abs((t <= 20).mean() - p) < 0.002


def test_q18():
    front, back = F("0.5") - F("0.2"), F("0.5") - F("0.7")
    assert front == F("0.3") and back == F("-0.2") and front - back == F("0.5")


def test_q19():
    prior = F(3, 10)
    up, down = F(1, 4) + F(3, 8), F(3, 8)

    def post(p, like_hi, like_lo):
        return p * like_hi / (p * like_hi + (1 - p) * like_lo)

    pa = post(prior, up, down)
    pb = post(prior, down, up)
    assert round(float(pa), 4) == 0.4167 and round(float(pb), 4) == 0.2045
    ask, bid = 100 + 20 * pa, 100 + 20 * pb
    assert round(float(ask), 2) == 108.33 and round(float(bid), 2) == 104.09
    assert round(float(ask - 106), 2) == 2.33 and round(float(106 - bid), 2) == 1.91
    assert post(pa, down, up) == prior
    # Break-even check by simulation: the ask earns zero on a buy.
    rng = np.random.default_rng(19)
    n = 2_000_000
    hi = rng.random(n) < 0.3
    v = np.where(hi, 120, 100)
    informed = rng.random(n) < 0.25
    buy = np.where(informed, hi, rng.random(n) < 0.5)
    assert abs((float(ask) - v[buy]).mean()) < 0.05
    assert abs((v[~buy] - float(bid)).mean()) < 0.05
    # All informed: the quotes reach the two values.
    assert post(prior, F(1), F(0)) == 1 and post(prior, F(0), F(1)) == 0


def test_q20():
    assert F("0.5") + F("0.2") == F("0.7") and F("-0.5") + F("0.2") == F("-0.3")
    assert 1_000_000 * F("0.007") == 7000 and 1_000_000 * F("-0.003") == -3000
    assert 1 + F("0.2") == F("1.2")


def test_q21():
    proceeds = 100 * 50
    earn, fee = F(4, 100) * proceeds / 4, F(6, 100) * proceeds / 4
    assert (earn, fee) == (50, 75)
    assert fee - earn == 25
    assert 100 * F("0.5") == 50
    assert fee - earn + 50 == 75
    assert F(75, 100) == F("0.75") and 50 - F("0.75") == F("49.25")
    # Fee equal to interest and no dividend: no cost.
    assert F(4, 100) * proceeds / 4 - earn == 0


def test_q22():
    assert 50 * F(9, 10) == 45
    assert F("44.90") <= 45
    assert F("44.89") > F("44.88")


def test_q23():
    w = [F("0.40"), F("0.15"), F("0.15"), F("0.30")]
    p = [F("100.0"), F("100.5"), F("101.0"), F("100.2")]
    vwap = sum(a * b for a, b in zip(w, p, strict=True))
    twap = sum(p) / 4
    assert vwap == F("100.285") and twap == F("100.425")
    assert twap - vwap == F("0.14")
    assert round(0.14 / 100.285 * 1e4) == 14
    assert sum(a * 100 for a in w) == sum([F(100)] * 4) / 4  # equal prices: no gap


def test_q24():
    v = F("0.7") * 100 + F("0.3") * F("100.30")
    assert v == F("100.09")
    assert F("100.30") - v == F("0.21") == F("0.30") * F("0.7")
    share = 1
    assert (1 - share) * F("100") + share * F("100.30") == F("100.30")


def test_q25():
    lam = 0.003 / 0.015**2
    assert round(lam, 1) == 13.3
    assert round(0.005 + lam * 0.015**2, 10) == 0.008
    assert round(0.003 / 0.015, 2) == 0.2


def test_q26():
    p = F(9, 32)
    assert float(p) == 0.28125
    rng = np.random.default_rng(26)
    you = rng.uniform(200, 400, 3_000_000)
    mm = rng.uniform(150, 350, 3_000_000)
    assert abs((you < mm).mean() - float(p)) < 0.001
    assert round(float(p) * 1.7, 3) == 0.478


def test_q27():
    assert F(1, 3) * 1 - F(2, 3) * F(1, 2) == 0
    assert F(2, 5) - F(3, 5) * F(1, 2) == F(1, 10)
    # Limits: a sure fill saves the whole cent; no fill costs only the leak.
    gain = lambda p: p * 1 - (1 - p) * F(1, 2)  # noqa: E731
    assert gain(F(1)) == 1 and gain(F(0)) == -F(1, 2)
    # A seller who knows the price will fall: buying at mid, then a fall of 2 cents, loses against crossing.
    mid, offer, after = F(100), F(100) + F(1, 100), F(100) - F(2, 100)
    assert after - mid < 0 and (after - mid) - (after - offer) == F(1, 100)


def test_q28():
    assert F(1) - F("0.2") - F("0.1") - F("0.2") == F("0.5")


def test_q29():
    noise = 0.0004**2 / 2
    true = 0.02**2
    m = true + 390 * noise
    s = true + 23_400 * noise
    assert round(390 * noise, 7) == 0.0000312 and round(m, 6) == 0.000431
    assert round(sqrt(m) * 100, 2) == 2.08 and round((sqrt(m) / 0.02 - 1) * 100) == 4
    assert round(23_400 * noise, 5) == 0.00187 and round(s, 5) == 0.00227
    assert round(sqrt(s) * 100, 2) == 4.77
    rng = np.random.default_rng(29)
    n, days = 23_400, 200
    rv = []
    for _ in range(days):
        r = rng.normal(0, 0.02 / sqrt(n), n)
        p = r.cumsum() + 0.0002 * rng.choice([-1, 1], n)
        rv.append((np.diff(p, prepend=0) ** 2).sum())
    assert abs(sqrt(np.mean(rv)) - sqrt(s)) < 0.0005


def test_q30():
    beta = 0.75 * 30 / 15
    assert beta == 1.5 and 10 * beta == 15
    res = 30 * sqrt(1 - 0.75**2)
    assert round(res, 2) == 19.84 and round(res / 10, 2) == 1.98
    assert round(res / 100 * 10e6 / 16, -3) == 124_000
    assert round(0.75**2 * 100) == 56
    assert round((1 - sqrt(1 - 0.75**2)) * 100) == 34
    assert 15 * 0.15**2 * 0 == 0
    # The dollar-for-dollar hedge leaves beta 0.5.
    assert 1.5 - 1 == 0.5


def test_q31():
    k = 0.5
    grid = np.linspace(0.01, 10, 100_000)
    best = grid[np.argmax(grid * np.exp(-k * grid))]
    assert abs(best - 2) < 1e-3
    assert round(exp(-1), 2) == 0.37 and round(2 * exp(-1), 2) == 0.74
    assert abs(1 * exp(-1) - 2 * exp(-1) / 2) < 1e-12


def test_q32():
    d = F("0.8")
    assert d / (2 + d) == F(2, 7)
    assert round(float(d / (2 + d)) * 100, 1) == 28.6
    cost = lambda p: -p + (1 - p) * (1 + d)  # noqa: E731
    assert cost(F(2, 7)) == 1
    assert cost(F(0)) == F("1.8")
    # Limit: no adverse drift, and posting never costs more than crossing.
    assert F(0) / (2 + F(0)) == 0


def test_q33():
    imb = [abs(a - b) for a, b in ((60, 40), (70, 30), (50, 50), (90, 10))]
    assert imb == [20, 40, 0, 80]
    assert F(sum(imb), 4 * 100) == F(35, 100)


def test_q34():
    assert sum(100 * k for k in range(1, 11)) / 100 == 55
    slices = sum(100 * (1 + F(1, 5) * (k - 1)) for k in range(1, 11))
    assert slices == 1900 and slices / 100 == 19
    assert sum(k * k for k in range(1, 10)) == 285
    risk = 100 * sqrt(285) * 5 / 100
    assert round(sqrt(285), 1) == 16.9 and round(risk) == 84
    assert 55 - 19 == 36 and round(risk / 36, 1) == 2.3


def test_q35():
    X, a, b, c = 1000, 0.0002, 0.0001, 0.0001

    def cost(y, a=a, b=b, c=c):
        return a * (X - y) ** 2 + a * y**2 + b * (X - y) * y + c * y**2

    y = X * (2 * a - b) / (4 * a - 2 * b + 2 * c)
    assert round(y) == 375
    grid = min(range(0, 1001), key=cost)
    assert grid == 375
    assert round(cost(375), 2) == 143.75
    assert round(cost(500), 2) == 150 and round(cost(0), 2) == 200
    assert round(a * (625**2 + 375**2), 2) == 106.25
    assert round(b * 625 * 375, 2) == 23.44 and round(c * 375**2, 2) == 14.06
    assert min(range(0, 1001), key=lambda v: cost(v, c=0.0)) == 500
    vals = {round(cost(v, b=2 * a, c=0.0), 6) for v in (0, 100, 375, 1000)}
    assert vals == {200.0}


def test_q36():
    p = F(sum(comb(9, k) for k in range(3, 10)), 512)
    assert p == F(466, 512)
    assert round(float(p), 3) == 0.910
    assert round((2 * float(p) - 1) / 2, 2) == 0.41
    assert F(7, 10) - F(1, 2) == F(1, 5)
    # Direct first-step recursion gives the same, and equal queues give one half.

    def race(a, b):
        if a == 0:
            return F(1)
        if b == 0:
            return F(0)
        return (race(a - 1, b) + race(a, b - 1)) / 2

    assert race(3, 7) == p and race(5, 5) == F(1, 2)


def test_q37():
    rho = F(4, 5)
    assert 1 - rho == F(1, 5) and -1 - rho == F(-9, 5)
    pup = (1 + rho) / 2
    assert pup == F(9, 10)
    assert pup * F(1, 5) + (1 - pup) * F(-9, 5) == 0
    assert 1 + 4 * F(1, 5) == F(9, 5)
    rng = np.random.default_rng(37)
    n = 2_000_000
    s = np.empty(n)
    s[0] = 1
    u = rng.random(n)
    for i in range(1, n):
        s[i] = s[i - 1] if u[i] < 0.9 else -s[i - 1]
    d = s[1:] - 0.8 * s[:-1]
    assert abs(np.corrcoef(d[1:], d[:-1])[0, 1]) < 0.003
    assert abs(np.corrcoef(s[1:], s[:-1])[0, 1] - 0.8) < 0.003


def test_q38():
    t = 1 / (0.2 * 2)
    assert t == 2.5
    imp = 2 / 3 * 2 * sqrt(0.5)
    assert round(imp, 3) == 0.943
    sd = 2 * sqrt(t / 3)
    assert round(sd, 2) == 1.83
    assert round(imp + sd / 2, 2) == 1.86
    h = 1.2 * sqrt(t / 3)
    assert round(h, 2) == 1.10 and round(imp + h / 2, 2) == 1.49
    # The variance of a linearly falling position, by numerical integration.
    ts = np.linspace(0, t, 100_001)
    assert abs(np.trapezoid((1 - ts / t) ** 2, ts) - t / 3) < 1e-6


def test_q39():
    u = 0.1 * 4 * 0.5
    assert round(u, 2) == 0.2
    assert round(100 - 5 * u, 2) == 99
    spread = u + (2 / 0.1) * log(1 + 0.1 / 1.5)
    assert round(spread, 2) == 1.49 and round(spread / 2, 3) == 0.745
    assert round(99 - spread / 2, 2) == 98.25 and round(99 + spread / 2, 2) == 99.75

    # The indifference prices, from the certainty equivalent directly.
    def ce(q, s=100.0):
        return q * s - 0.5 * 0.1 * q * q * 4 * 0.5

    assert abs((ce(6) - ce(5)) - (100 - u * 5.5)) < 1e-9
    assert abs((ce(5) - ce(4)) - (100 - u * 4.5)) < 1e-9
    assert abs(((ce(6) - ce(5)) + (ce(5) - ce(4))) / 2 - 99) < 1e-9
    assert abs(((ce(1) - ce(0)) + (ce(0) - ce(-1))) / 2 - 100) < 1e-9  # no position, centre at the mid


def test_q42():
    def h(n):
        snipe = 0.5 * (n - 1) / n
        return snipe * 2 / (1 + snipe)

    assert round(h(3), 6) == 0.5
    assert h(1) == 0
    assert round(h(10**9), 2) == 0.67
    assert abs(1 * h(3) - 0.5 * 2 / 3 * (2 - h(3))) < 1e-12


def test_q43():
    per = F(9, 10) * 200 * F(1, 2) + F(1, 10) * 800 * (F(1, 2) - 1)
    assert per == 50
    ev = lambda q: per * F(q, 1000 + q)  # noqa: E731
    assert round(float(ev(100)), 1) == 4.5 and ev(1000) == 25 and ev(3000) == F(75, 2)
    q = F(1000, 3)
    assert 800 * q / (1000 + q) == 200


def test_q44():
    se = 30 * sqrt(2 / 400)
    assert round(se, 2) == 2.12 and round(1.2 / se, 2) == 0.57
    z = norm.ppf(0.975) + norm.ppf(0.8)
    assert round(z, 1) == 2.8
    assert round(2 * 2.8**2 * (30 / 1.2) ** 2) == 9800
    assert abs(2 * z**2 * 625 - 9800) < 100
    rng = np.random.default_rng(44)
    n = 9800
    diffs = rng.normal(1.2, 30 * sqrt(2 / n), 200_000)
    assert abs((np.abs(diffs) > 1.96 * 30 * sqrt(2 / n)).mean() - 0.8) < 0.01


def test_q45():
    b, x = F(1, 10**6), 50_000
    assert b * x * x == 2500
    assert 3 * b * x * x == 7500
    profit = lambda y: y * b * (x - y)  # noqa: E731
    assert max(range(0, 50_001, 100), key=profit) == 25_000
    assert profit(25_000) == 625
    assert 2 * b * x * 25_000 == 2500
    assert F(2500, 7500) == F(1, 3)
    # Direct price accounting for both players.
    p0 = F(100)
    y = 25_000
    me_with = x * (p0 - b * (x + y)) + x * (p0 - b * (2 * x + y))
    me_without = x * (p0 - b * x) + x * (p0 - b * 2 * x)
    assert me_without - me_with == 2500
    him = y * (p0 - b * (x + y)) - y * (p0 - b * 2 * x)
    assert him == 625


def test_q46():
    a = 2 / 3 * 0.02 * sqrt(0.25)
    bb = 0.02 / sqrt(3)
    t = a / bb
    assert round(a * 100, 3) == 0.667 and round(bb * 100, 3) == 1.155
    assert round(t, 3) == 0.577
    assert round(a * t**-0.5 * 100, 2) == round(bb * t**0.5 * 100, 2) == 0.88
    assert round(2 * sqrt(a * bb) * 100, 2) == 1.75
    grid = np.linspace(0.05, 5, 100_000)
    assert abs(grid[np.argmin(a / np.sqrt(grid) + bb * np.sqrt(grid))] - t) < 1e-3


def test_q47():
    assert 100 * F(95, 100) == 95 and 100 * F(105, 100) == 105
    assert 2 * 5 == 10  # the doubled band
    assert (16 * 60 - (15 * 60 + 35)) == 25  # 3:35 to 4:00 is 25 minutes
    assert (9 * 60 + 45) - (9 * 60 + 30) == 15


def test_q48():
    su, sv = 1000, 2
    beta, lam = su / sv, sv / (2 * su)
    assert beta == 500 and lam == 0.001
    assert beta * beta * sv * sv == su * su  # order variance equals noise variance
    assert abs(lam - beta * sv**2 / (beta**2 * sv**2 + su**2)) < 1e-15
    assert sv * su / 2 == 1000
    assert sv**2 * 0.5 == 2
    rng = np.random.default_rng(48)
    n = 2_000_000
    v, u = rng.normal(0, sv, n), rng.normal(0, su, n)
    x = beta * v
    y = x + u
    assert abs(np.polyfit(y, v, 1)[0] - lam) < 2e-5
    profit = (x * (v - lam * y)).mean()
    assert abs(profit - 1000) < 15
    assert abs(((v - lam * y) ** 2).mean() - 2) < 0.01
    assert abs(((-u) * (lam * y)).mean() + 1000) < 15  # noise traders lose it
    assert abs(sv * (2 * su) / 2 - 2000) < 1e-9  # doubling noise doubles the profit


def test_q49():
    def path(kappa, t):
        return sinh(kappa * (1 - t)) / sinh(kappa)

    assert round((1 - path(1, 0.5)) * 100, 1) == 55.7
    assert round((1 - path(3, 0.5)) * 100, 1) == 78.7
    assert round(sinh(0.5), 4) == 0.5211 and round(sinh(1), 4) == 1.1752
    assert round(sinh(1.5), 4) == 2.1293 and round(sinh(3), 3) == 10.018

    def closed(k):
        q = sinh(2 * k) / (4 * k)
        return k * k * (0.5 + q) / sinh(k) ** 2, (q - 0.5) / sinh(k) ** 2

    # Numeric integration of the path.
    def numeric(k):
        ts = np.linspace(0, 1, 200_001)
        x = np.sinh(k * (1 - ts)) / sinh(k)
        v = k * np.cosh(k * (1 - ts)) / sinh(k)
        return np.trapezoid(v * v, ts), np.trapezoid(x * x, ts)

    for k in (1, 3):
        a, b = closed(k)
        c, d = numeric(k)
        assert abs(a - c) < 1e-6 and abs(b - d) < 1e-6
    a1, b1 = closed(1)
    a3, b3 = closed(3)
    assert round(a1, 3) == 1.019 and round(b1, 4) == 0.2945
    assert round(a3, 3) == 1.552 and round(b3, 4) == 0.1625
    assert round((a1 - 1) * 100, 1) == 1.9 and round((1 - b1 * 3) * 100, 1) == 11.7
    assert round((a3 - 1) * 100) == 55 and round((1 - b3 * 3) * 100) == 51
    # Limit: kappa to zero gives the straight line.
    assert abs(path(1e-6, 0.3) - 0.7) < 1e-6
    assert cosh(0) == 1
    # A discretised minimiser agrees with the sinh path.
    n = 20
    dt = 1 / n
    k = 3

    def objective(z):
        x = np.concatenate([[1.0], z, [0.0]])
        return (np.diff(x) ** 2 / dt).sum() + k * k * (x[:-1] ** 2).sum() * dt

    res = minimize(objective, np.linspace(1, 0, n + 1)[1:-1], method="L-BFGS-B")
    assert abs(res.x[n // 2 - 1] - path(k, 0.5)) < 0.02


def test_q50():
    def cost(x, a):
        x0, x1, x2 = x
        return F(1, 2) * (x0**2 + x1**2 + x2**2) + a * (x0 * x1 + x1 * x2) + a * a * x0 * x2

    a = F(1, 2)
    best = (F(2, 5), F(1, 5), F(2, 5))
    assert cost(best, a) == F(3, 10)
    eq = (F(1, 3),) * 3
    assert round(float(cost(eq, a)), 4) == 0.3056
    assert cost((F(1), F(0), F(0)), a) == F(1, 2)
    assert round((1 - float(cost(best, a)) / float(cost(eq, a))) * 100, 1) == 1.8
    assert round((1 - float(cost(best, a)) / 0.5) * 100) == 40
    # Numerical minimum agrees, on the simplex.
    grid = np.linspace(0, 1, 401)
    top = (1e9, None)
    for x0 in grid:
        for x1 in grid:
            x2 = 1 - x0 - x1
            if x2 < 0:
                continue
            v = float(cost((x0, x1, x2), 0.5))
            if v < top[0]:
                top = (v, (x0, x1, x2))
    assert abs(top[1][0] - 0.4) < 0.01 and abs(top[1][1] - 0.2) < 0.01
    # The two limits, and the closed-form cost.
    for aa, want in ((F(0), (F(1, 3), F(1, 3), F(1, 3))), (F(1), (F(1, 2), F(0), F(1, 2)))):
        s = 3 - aa
        w = (1 / s, (1 - aa) / s, 1 / s)
        assert w == want
    assert F(1, 2) * (1 + a) / (3 - a) == F(3, 10)
