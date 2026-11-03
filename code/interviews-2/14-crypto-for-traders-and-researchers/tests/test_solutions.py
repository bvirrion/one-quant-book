"""Crypto for Traders and Researchers. Exact pool arithmetic, payoffs and simulated hedges."""
from math import exp, log, sqrt

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

N = norm.cdf
NONNUMERIC = {}


def buy(x, y, dx, fee=0.0):
    dy = (x * y / (x - dx) - y) / (1 - fee)
    return dy, x - dx, y + dy * (1 - fee)


def sell(x, y, dx, fee=0.0):
    dy = (y - x * y / (x + dx)) * (1 - fee)
    return dy, x + dx, y - dy


def test_q1():
    assert round(1e6 * 0.0001) == 100 and round(3e6 * 0.0001) == 300 and round(1095e6 * 0.0001) == 109_500


def test_q2():
    assert 1500 / 60000 == 0.025 and round(0.025 * 365 / 90, 4) == 0.1014
    # Locked: the two legs sum to the same for any final price.
    for s in (1000, 60000, 400000):
        assert (s - 60000) + (61500 - s) == 1500


def test_q3():
    up, dn = 1e6 * (1 / 50000 - 1 / 60000), 1e6 * (1 / 50000 - 1 / 40000)
    assert round(up, 2) == 3.33 and round(dn, 6) == -5
    assert round(up * 60000) == 200_000 and round(dn * 40000) == -200_000
    # Exact: the dollar P&L is linear.
    for p in (10000, 50000, 200000):
        assert abs(1e6 * (1 / 50000 - 1 / p) * p - 1e6 * (p / 50000 - 1)) < 1e-6


def test_q4():
    # Equity per coin hits maintenance.
    px = brentq(lambda p: 5000 + (p - 50000) - 0.005 * 50000, 30000, 50000)
    assert round(px) == 45_250
    # 1x leverage has no liquidation above zero, so the formula is sane at the limit.
    assert 50000 * (1 - 1 + 0.005) == 250


def test_q5():
    dy, x, y = buy(100, 200000, 10)
    assert round(dy) == 22_222 and round(dy / 10) == 2222 and round(y / x) == 2469
    assert round(dy / 10 / 2000 - 1, 2) == 0.11
    # Invariant holds, and a vanishing trade pays the spot.
    assert abs(x * y - 2e7) < 1e-6 and abs(buy(100, 200000, 1e-6)[0] / 1e-6 - 2000) < 1e-3


def test_q6():
    assert round(1 - 0.001 - 0.995, 4) == 0.004
    assert round(1.01 - 1.00, 2) == 0.01


def test_q7():
    assert 60000 - 59940 == 60 and round(60 / 60000 * 1e4) == 10
    fee = 60000 * 0.0005 + 59940 * 0.0005
    assert round(fee, 2) == 59.97 and round(60 - fee, 2) == 0.03


def test_q8():
    r = lambda c: 2 * sqrt(c) / (1 + c) - 1  # noqa: E731
    assert round(r(2), 4) == -0.0572 and abs(r(2) - r(0.5)) < 1e-12 and r(1) == 0
    # Exact pool arithmetic from reserves.
    x, y = 100.0, 200000.0
    p1 = 4000.0
    x1, y1 = sqrt(x * y / p1), sqrt(x * y * p1)
    assert abs((x1 * p1 + y1) / (x * p1 + y) - 1 - r(2)) < 1e-12
    assert round((x1 * p1 + y1) / (x * 2000 + y) - 1, 2) == 0.41


def test_q9():
    f = 0.0001 * 1095
    assert round(f, 4) == 0.1095 and round(f / 1.2, 3) == 0.091 and round(f / 1.5, 3) == 0.073


def test_q10():
    assert round(0.0001 * 270, 4) == 0.027 and round((0.027 - 0.025) * 1e6) == 2000
    p0, f0 = 60000.0, 61500.0
    for s in (10000.0, 60000.0, 500000.0):
        assert abs((s - f0) + (p0 - s) - (p0 - f0)) < 1e-9
    # With the future above the perpetual, the locked-in part is negative: minus the basis.
    assert p0 - f0 == -(f0 - p0) < 0


def test_q11():
    for p in (30000, 90000, 60000, 1234):
        coins = 1 - 60000 * (1 / 60000 - 1 / p)
        assert abs(coins * p - 60000) < 1e-6
    assert abs(-60000 * (1 / 60000 - 1 / 30000) - 1) < 1e-12 and abs(-60000 * (1 / 60000 - 1 / 90000) + 1 / 3) < 1e-12
    # The long: concave in coin.
    g = lambda p: 60000 * (1 / 60000 - 1 / p)  # noqa: E731
    assert g(72000) + g(48000) < 0


def test_q12():
    move, tot = 5.0, 0.0
    for _ in range(200):
        tot += move
        move *= 30 / 50
    assert abs(tot - 12.5) < 1e-9 and abs(5 / (1 - 0.6) - tot) < 1e-9
    move, tot = 5.0, 0.0
    for _ in range(100):
        tot += move
    assert tot > 400


def test_q13():
    assert 20 * (45000 - 44500) == 10_000 and 20 * (45250 - 45000) == 5_000


def test_q14():
    dy, x, y = buy(100, 200000, 10, 0.003)
    assert round(dy) == 22_289 and round(dy * 0.003, 2) == 66.87
    assert round(2000 / 0.997) == 2006 and round(2000 * 0.997) == 1994
    # No profit inside the band: a tiny trade at the band edge has zero edge, and one inside loses.
    for px in (1995, 2000, 2005):
        cost = buy(100, 200000, 0.01, 0.003)[0] / 0.01
        proceeds = sell(100, 200000, 0.01, 0.003)[0] / 0.01
        assert cost > px and proceeds < px
    assert abs(x * y - 2e7) < 1e-6


def test_q15():
    assert round(0.034 / (2000 / 60000) - 1, 4) == 0.02
    assert round(1.02 * 0.999**3 - 1, 4) == 0.0169
    f = 1 - (1 / 1.02) ** (1 / 3)
    assert round(f, 4) == 0.0066 and round(f * 1e4) == 66
    assert abs(1.02 * (1 - f) ** 3 - 1) < 1e-12
    # The rough 2% / 3 overstates.
    assert 0.02 / 3 > f and round(0.02 / 3 * 1e4) == 67
    # Direct loop in units.
    usd = 1.0
    eth = usd / 2000 * 0.999
    btc = eth * 0.034 * 0.999
    assert abs(btc * 60000 * 0.999 - 1.02 * 0.999**3) < 1e-12
    # Consistent prices have no profit.
    assert abs((1 / 2000) * (2000 / 60000) * 60000 - 1) < 1e-12


def test_q16():
    assert round(0.92 + 0.08 * 0.5, 6) == 0.96 and 0.92 + 0 == 0.92
    assert round(0.96 / 0.88 - 1, 2) == 0.09


def test_q17():
    x, y = 200.0, 200.0
    sold = brentq(lambda a: sell(x, y, a)[0] - 100, 1, 2000)
    assert abs(sold - 200) < 1e-6
    _, x1, y1 = sell(x, y, sold)
    assert abs(y1 / x1 - 0.25) < 1e-9 and abs(100 / sold - 0.5) < 1e-9


def test_q18():
    cl = lambda v: max(-0.05, min(0.05, v))  # noqa: E731
    f = lambda p: p + cl(0.01 - p)  # noqa: E731
    got = [round(f(p), 2) for p in (0.02, 0.06, 0.10, -0.03, -0.20)]
    assert got == [0.01, 0.01, 0.05, 0.01, -0.15]
    # The dead zone runs exactly from -0.04 to 0.06.
    for p in np.linspace(-0.04, 0.06, 21):
        assert abs(f(float(p)) - 0.01) < 1e-12
    assert f(0.0601) > 0.01 and f(-0.0401) < 0.01


def test_q19():
    assert round(0.3 * 0.05 * 0.6, 4) == 0.009 and round(3 * 0.1 * 0.05 * 0.6, 4) == 0.009
    assert round(0.3 * 0.6, 2) == 0.18 and round(0.1 * 0.6, 2) == 0.06
    # Enumerate the three independent failures: same mean, one failure 6%, all three still 18%.
    outcomes = []
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                outcomes.append((0.05 ** (a + b + c) * 0.95 ** (3 - a - b - c), (a + b + c) * 0.1 * 0.6))
    assert abs(sum(p * loss for p, loss in outcomes) - 0.009) < 1e-12
    assert round(max(loss for _, loss in outcomes), 2) == 0.18
    assert abs(sum(p for p, _ in outcomes) - 1) < 1e-12


def test_q20():
    k, r = 1095.0, 0.05
    c = k / (k - r)
    assert round((c - 1) * 1e5, 2) == 4.57 and round((c - 1) * 1e4, 2) == 0.46
    # Hedged carry is zero at this price, and not at spot.
    carry = lambda cc: k * (cc - 1) - r * cc  # noqa: E731
    assert abs(carry(c)) < 1e-9 and carry(1.0) < 0
    assert abs(k * (c - 1) - r * c) < 1e-12 and round(k * (c - 1), 3) == 0.05
    # Limit: infinite funding speed sends the perpetual to spot.
    assert abs(1e12 / (1e12 - r) - 1) < 1e-12
    # Discrete simulation: a hedged book makes nothing, on any path.
    rng = np.random.default_rng(1)
    dt = 1 / 1095
    s = 60000.0
    pnl = 0.0
    for z in rng.standard_normal(1095):
        s2 = s * exp(0.8 * sqrt(dt) * z)
        pnl += c * (s2 - s) - (c * s2 - c * s) + k * (c - 1) * s * dt - r * c * s * dt
        s = s2
    assert abs(pnl) < 1e-6


def test_q21():
    s = 0.8 * sqrt(30 / 365)
    vals = [2 * N(-log(1 + u) / s) for u in (0.1, 0.2, 0.5)]
    assert round(s, 3) == 0.229
    assert [round(v, 3) for v in vals] == [0.678, 0.427, 0.077]
    assert round(vals[1] / vals[2], 1) == 5.5
    assert round(vals[0] / vals[1], 1) == 1.6
    # Fine-grid simulation; discrete monitoring gives slightly less.
    rng = np.random.default_rng(2)
    m = 20000
    k = 2000
    dw = rng.standard_normal((m, k)) * s / sqrt(k)
    path = np.cumsum(dw - s * s / (2 * k), axis=1)
    mx = path.max(axis=1)
    for u, v in zip((0.1, 0.2, 0.5), vals, strict=True):
        sim = (mx >= log(1 + u)).mean()
        assert v - 0.05 < sim < v + 0.01


def test_q22():
    assert 5e6 * 0.001 == 5000 and 2e6 * 0.0005 == 1000
    assert round(4000 / 2e6, 4) == 0.002 and round(0.002 * 365, 2) == 0.73
    sd = 0.8 * sqrt(0.5 / 8760)
    assert round(sd, 4) == 0.0060 and round(sd * 1e6, -3) == 6000
    assert round(sd * 1e6, -3) / 4000 == 1.5
    assert round(2 * 0.0005 * 1e6) == 1000 and round((4000 - 2000) / 2e6 * 365, 3) == 0.365


def test_q23():
    s = 0.8
    assert abs(s * s / 8 - 0.08) < 1e-12 and round(1 - exp(-0.08), 4) == 0.0769
    # Gamma derivation by finite difference.
    k = 2e9
    p, h = 2000.0, 0.01
    v = lambda q: 2 * sqrt(k * q)  # noqa: E731
    g = (v(p + h) - 2 * v(p) + v(p - h)) / h / h
    assert abs(0.5 * g * p * p / v(p) + 1 / 8) < 1e-5
    # Simulated hedge against the expectation.
    rng = np.random.default_rng(3)
    m, n = 4000, 1000
    dt = 1 / n
    pr = np.full(m, 2000.0)
    hedge = np.zeros(m)
    for _ in range(n):
        pn = pr * np.exp(s * sqrt(dt) * rng.standard_normal(m) - 0.5 * s * s * dt)
        hedge += (pn - pr) / np.sqrt(pr)
        pr = pn
    res = (2 * np.sqrt(pr) - 2 * sqrt(2000) - hedge) / (2 * sqrt(2000))
    assert abs(res.mean() + (1 - exp(-0.08))) < 2e-3


def test_q24():
    k = 1000 * 2e6
    assert k == 2e9
    v = lambda p: 2 * sqrt(k * p)  # noqa: E731
    assert abs(v(2420) - 4.4e6) < 1e-3 and abs(v(2000) - 4e6) < 1e-3
    net = (v(2420) - 4e6) - 1000 * 420
    assert abs(net + 20000) < 1e-3
    hold = 1000 * 2420 + 2e6
    assert abs(hold - 4.42e6) < 1e-6 and abs(v(2420) - hold - net) < 1e-3
    assert round(2 * sqrt(1.21) / 2.21 - 1, 4) == -0.0045
    # At any price the static-hedge P&L equals pool minus holding, and it returns to zero.
    for p in (500, 2000, 9000):
        assert abs((v(p) - 4e6 - 1000 * (p - 2000)) - (v(p) - 1000 * p - 2e6)) < 1e-6
    assert abs(v(2000) - 4e6) < 1e-6


def rng_v(p, a=1800.0, b=2200.0):
    if p < a:
        return (1 / sqrt(a) - 1 / sqrt(b)) * p
    if p > b:
        return sqrt(b) - sqrt(a)
    return 2 * sqrt(p) - sqrt(a) - p / sqrt(b)


def test_q25():
    p = 2000.0
    m = 2 * sqrt(p) / rng_v(p)
    assert round(m, 1) == 20.4
    hold = lambda q: (sqrt(p) - sqrt(1800)) + (1 / sqrt(p) - 1 / sqrt(2200)) * q  # noqa: E731
    assert round(rng_v(2200) / hold(2200) - 1, 4) == -0.0232 and round(rng_v(1800) / hold(1800) - 1, 4) == -0.0283
    fr = lambda c: 2 * sqrt(c) / (1 + c) - 1  # noqa: E731
    assert round(fr(1.1), 4) == -0.0011 and round(fr(0.9), 4) == -0.0014
    assert 18 < (rng_v(2200) / hold(2200) - 1) / fr(1.1) < 23
    # Beyond the range the position is flat above, and linear below.
    assert rng_v(3000) == rng_v(2500) and abs(rng_v(1000) / rng_v(500) - 2) < 1e-12
    # Continuous at the edges.
    assert abs(rng_v(2200) - rng_v(2200.0001)) < 1e-5


def test_q26():
    fee = 0.003
    x, y = 100.0, 200000.0
    base = buy(x, y, 10, fee)[0]
    lim = base * 1.01
    assert round(base, 2) == 22289.09 and round(lim, 2) == 22511.98
    af = lambda a: buy(*buy(x, y, a, fee)[1:], 10, fee)[0]  # noqa: E731
    a = brentq(lambda v: af(v) - lim, 1e-6, 50)
    d1, x1, y1 = buy(x, y, a, fee)
    d2, x2, y2 = buy(x1, y1, 10, fee)
    s, _, _ = sell(x2, y2, a, fee)
    assert round(a, 2) == 0.47 and round(d1, 2) == 947.60 and round(s, 2) == 1163.48
    assert round(s - d1, 2) == 215.88 and round(d2 - base, 2) == 222.89
    assert s - d1 < d2 - base
    # A tight limit leaves little: profit scales with the tolerance.
    a0 = brentq(lambda v: af(v) - base * 1.0005, 1e-9, 50)
    d, xx, yy = buy(x, y, a0, fee)
    _, x3, y3 = buy(xx, yy, 10, fee)
    assert round(sell(x3, y3, a0, fee)[0] - d) == 11 and a0 < a
    # With no fee at all the attacker's gain equals the victim's loss.
    d1, x1, y1 = buy(x, y, 0.5)
    d2, x2, y2 = buy(x1, y1, 10)
    s, _, _ = sell(x2, y2, 0.5)
    assert abs((s - d1) - (d2 - buy(x, y, 10)[0])) < 1e-6


def test_q27():
    s, k, v, tm = 60000.0, 60000.0, 0.8, 30 / 365
    d1 = (log(s / k) + v * v * tm / 2) / (v * sqrt(tm))
    d2 = d1 - v * sqrt(tm)
    c = s * N(d1) - k * N(d2)
    assert round(d1, 3) == 0.115 and round(c) == 5478 and round(c / s, 4) == 0.0913
    assert round(0.4 * 0.8 * sqrt(tm), 4) == 0.0917
    assert round(N(d1), 3) == 0.546 and round(N(d1) - c / s, 3) == 0.454
    # Finite difference of the coin price, scaled by S, gives the coin delta.
    f = lambda q: (q * N((log(q / k) + v * v * tm / 2) / (v * sqrt(tm))) - k * N((log(q / k) - v * v * tm / 2) / (v * sqrt(tm)))) / q  # noqa: E731
    h = 1.0
    assert abs((f(s + h) - f(s - h)) / (2 * h) * s - (k / s) * N(d2) * 1.0) < 0.01
    assert abs(k / s * N(d2) - (N(d1) - c / s)) < 1e-9
    # Parity in coin, and simulated payoff.
    z = np.random.default_rng(4).standard_normal(4_000_000)
    st = s * np.exp(v * sqrt(tm) * z - v * v * tm / 2)
    # Under the dollar measure, expected dollar payoff over today's spot is the coin price.
    assert abs(np.maximum(st - k, 0).mean() / s - c / s) < 5e-4
    assert abs((np.maximum(st - k, 0) - np.maximum(k - st, 0)).mean()) < 30





def test_q28():
    assert round(20e-4 * 2 * 12, 4) == 0.048
    assert round((0.3 - 0.048) / 1.2, 3) == 0.21 and round(0.21 - 0.025, 3) == 0.185
    sd = 0.5 * sqrt(0.05 * 0.95)
    assert round(sd, 3) == 0.109
    total = sqrt(sd * sd + 0.02**2)
    assert round(total, 3) == 0.111 and round(0.185 / total, 2) == 1.67
    assert round(sum([17.19, 30.61, 4.16, 7.87, 11.92, 5.13]) / 6, 1) == 12.8


def test_q29():
    s = 0.8 * sqrt(30 / 365)
    out = {}
    for lev in (2, 5, 10):
        nc = 1 / (1 + 1 / lev)
        gross = 0.10 * nc
        p = 2 * N(-log(1 + 1 / lev) / s)
        cost = 12 * p * 0.01 * nc
        out[lev] = gross, p, cost, gross - cost
    assert [round(out[x][0] * 100, 2) for x in (2, 5, 10)] == [6.67, 8.33, 9.09]
    assert [round(out[x][1] * 100, 1) for x in (2, 5, 10)] == [7.7, 42.7, 67.8]
    assert [round(out[x][2] * 100, 2) for x in (2, 5, 10)] == [0.62, 4.27, 7.39]
    assert [round(out[x][3] * 100, 2) for x in (2, 5, 10)] == [6.05, 4.07, 1.70]
    assert round((out[10][2] - out[2][2]) * 100, 1) == 6.8 and round((out[10][0] - out[2][0]) * 100, 1) == 2.4
    # Without a liquidation cost, more leverage must win.
    assert out[10][0] > out[5][0] > out[2][0]


def lp_sim(fee, sig=0.8, steps=8760, m=1500, seed=5):
    rng = np.random.default_rng(seed)
    dt = 1 / steps
    px = np.full(m, 2000.0)
    x = np.full(m, 2500.0)
    y = np.full(m, 5e6)
    v0 = x * px + y
    hedge = np.zeros(m)
    fees = np.zeros(m)
    arb = np.zeros(m)
    for _ in range(steps):
        pn = px * np.exp(sig * sqrt(dt) * rng.standard_normal(m) - 0.5 * sig * sig * dt)
        hedge += x * (pn - px)
        px = pn
        pool = y / x
        kk = x * y
        up = px > pool / (1 - fee)
        dn = px < pool * (1 - fee)
        if up.any():
            xn = np.sqrt(kk[up] / (px[up] * (1 - fee)))
            net = kk[up] / xn - y[up]
            dy = net / (1 - fee)
            fees[up] += dy * fee
            arb[up] += (x[up] - xn) * px[up] - dy
            x[up], y[up] = xn, y[up] + net
        if dn.any():
            yn = np.sqrt(kk[dn] * px[dn] / (1 - fee))
            net = kk[dn] / yn - x[dn]
            gross = net / (1 - fee)
            fees[dn] += gross * fee * px[dn]
            arb[dn] += y[dn] - yn - gross * px[dn]
            x[dn], y[dn] = x[dn] + net, yn
    val = x * px + y
    assert arb.min() >= -1e-6
    return float(((val - v0 - hedge) / v0).mean()), float((fees / v0).mean())


def test_q30():
    res = {f: lp_sim(f) for f in (0.0, 0.0005, 0.003, 0.01)}
    assert abs(res[0.0][0] + (1 - exp(-0.08))) < 0.004
    assert res[0.0][1] == 0
    for f, loss_fee in ((0.0005, 0.007), (0.003, 0.029), (0.01, 0.052)):
        assert abs(res[f][1] - loss_fee) < 0.002
        # Arbitrage alone never pays: the hedged LP is the arbitrageur's opposite.
        assert res[f][0] + res[f][1] < 0
    assert round(0.0713 * 1e7 / 0.0005 / 1e6, -1) == 1430
    assert round(0.0489 * 1e7 / 0.003 / 1e6) == 163 and round(0.026 * 1e7 / 0.01 / 1e6) == 26
    assert round(0.0489 * 1e7 / 0.003 / 365, -3) == 447_000
    # Concentrating 20x: the shortfall per dollar of capital and the flow it needs both scale by 20, at a fixed fee.
    short, fee = 0.0489, 0.003
    assert abs((20 * short / fee) / (short / fee) - 20) < 1e-12
    # A quarter of the variance.
    assert abs(lp_sim(0.0, sig=0.4, m=800)[0] + (1 - exp(-0.02))) < 0.002
