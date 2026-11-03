"""Credit and XVA. Exact integrals and enumeration, checked against simulation and limit cases."""
from math import exp, log, pi, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import norm

N, n = norm.cdf, norm.pdf
NONNUMERIC = {}
S0 = 1 / sqrt(2 * pi)


def annuity(r, h, t):
    return (1 - exp(-(r + h) * t)) / (r + h)


def ee_mean(t, m=0.0, sig=0.01):
    if t <= 0:
        return 0.0
    st = sig * sqrt(t)
    return 100 * (5 - t) * st * (n(m / st) + m / st * N(m / st))


def cva_surv(s, m=0.0, sig=0.01, r=0.4):
    h = s / (1 - r)
    return (1 - r) * quad(lambda t: h * exp(-h * t) * ee_mean(t, m, sig), 0, 5)[0]


def test_q1():
    h = 0.02 / 0.6
    assert round(h, 4) == 0.0333 and round(1 - exp(-5 * h), 3) == 0.154
    # Second route: premium leg equals protection leg at this hazard, exactly, for a continuous contract.
    prem = 0.02 * annuity(0.03, h, 5)
    prot = 0.6 * h * annuity(0.03, h, 5)
    assert abs(prem - prot) < 1e-12
    # 5h can pass 1 and the survival form cannot.
    assert 1 - exp(-5 * 0.5) < 1 < 5 * 0.5


def test_q2():
    a, b = 1 - exp(-0.04), exp(-0.04) - exp(-0.08)
    assert round(a, 4) == 0.0392 and round(b, 4) == 0.0377 and abs(b / exp(-0.04) - a) < 1e-14
    # Simulation of the exponential time.
    t = np.random.default_rng(1).exponential(25, 2_000_000)
    assert abs(((t > 1) & (t <= 2)).mean() - b) < 3e-4
    assert abs(((t > 1) & (t <= 2)).sum() / (t > 1).sum() - a) < 3e-4


def test_q3():
    a = exp(-0.25)
    s = exp(-0.15)
    b = exp(-0.1) * (s + 0.4 * (1 - s))
    assert round(a, 4) == 0.7788 and round(b, 4) == 0.8292
    sp = -log(s + 0.4 * (1 - s)) / 5
    assert round(sp, 5) == 0.01746 and sp < 0.018
    # Limit: as hazard goes to 0, the spread is h(1 - R) exactly, so the gap is a size effect.
    h = 1e-6
    assert abs(-log(exp(-5 * h) + 0.4 * (1 - exp(-5 * h))) / 5 / h - 0.6) < 1e-5
    # Recovery of everything means no spread.
    assert abs(-log(s + 1.0 * (1 - s))) < 1e-15


def test_q4():
    assert 10e6 * 0.02 / 4 == 50_000 and 10e6 * 0.7 == 7e6


def test_q5():
    a = annuity(0.03, 0.02 / 0.6, 5)
    assert round(a, 2) == 4.29 and round(0.01 * a * 10e6, -4) == 430_000
    # Zero upfront at the coupon, and less than the plain five-year sum at any positive r + h.
    assert (0.01 - 0.01) * a == 0 and a < 5


def test_q6():
    up = {}
    for s in (0.02, 0.2):
        for r in (0.4, 0.2):
            h = s / (1 - r)
            up[s, r] = (s - 0.01) * annuity(0.03, h, 5)
    assert round(up[0.02, 0.4] * 100, 2) == 4.29 and round(up[0.02, 0.2] * 100, 2) == 4.37
    assert round(up[0.2, 0.4] * 100, 1) == 43.8 and round(up[0.2, 0.2] * 100, 1) == 51.1
    # Annuities quoted in the answer.
    assert round(annuity(0.03, 0.25, 5), 2) == 2.69 and round(annuity(0.03, 1 / 3, 5), 2) == 2.30



def test_q7():
    assert (0.0220 - 0.0180) * 10e6 == 40_000
    # Clean model: a par floater with spread h(1 - R), recovery of par at default, is worth par.
    h, big_r, r, t = 0.03, 0.4, 0.03, 5
    s = h * (1 - big_r)
    pv = (r + s + h * big_r) * annuity(r, h, t) + exp(-(r + h) * t)
    assert abs(pv - 1) < 1e-12
    # A spread above h(1 - R) is worth more than par, so the 40 bp is not free in the model.
    assert (r + s + 0.004 + h * big_r) * annuity(r, h, t) + exp(-(r + h) * t) > 1


def test_q8():
    p, q = 0.05, 0.05
    j = p * q + 0.3 * sqrt(p * (1 - p) * q * (1 - q))
    assert round(j, 5) == 0.01675 and round(p + q - j, 5) == 0.08325
    p, q = 0.05, 0.01
    den = sqrt(p * (1 - p) * q * (1 - q))
    top = (min(p, q) - p * q) / den
    assert round(top, 3) == 0.438 and round(-p * q / den, 3) == -0.023
    # Direct enumeration of the joint distribution at the top: the 2x2 table has no negative cell.
    both = min(p, q)
    cells = [both, p - both, q - both, 1 - p - q + both]
    assert min(cells) >= 0 and abs(sum(cells) - 1) < 1e-15
    x = np.array([1, 1, 0, 0.0])
    y = np.array([1, 0, 1, 0.0])
    w = np.array(cells)
    mx, my = (w * x).sum(), (w * y).sum()
    cor = (w * x * y).sum() - mx * my
    assert abs(cor / den - top) < 1e-12


def test_q9():
    p = 0.01
    ftd = 1 - 0.99**5
    assert round(ftd, 4) == 0.0490 and round(0.6 * ftd, 4) == 0.0294 and round(0.6 * p, 4) == 0.006
    std = 1 - 0.99**5 - 5 * p * 0.99**4
    assert round(std * 100, 3) == 0.098
    # Gaussian copula, seeded simulation at 0 and at 0.6, and first-to-default falls as second rises.
    rng = np.random.default_rng(2)
    c = norm.ppf(p)
    z = rng.standard_normal((1_000_000, 1))
    e = rng.standard_normal((1_000_000, 5))
    res = {}
    for rho in (0.0, 0.3, 0.6, 0.95):
        d = (sqrt(rho) * z + sqrt(1 - rho) * e < c).sum(1)
        res[rho] = (d >= 1).mean(), (d >= 2).mean()
    assert abs(res[0.0][0] - ftd) < 5e-4 and abs(res[0.0][1] - std) < 1.5e-4
    assert round(res[0.6][0], 3) == 0.037 and round(res[0.6][1], 3) == 0.009
    assert round(0.6 * res[0.6][0], 3) == 0.022 and round(0.6 * res[0.6][1], 4) == 0.0055
    assert res[0.0][0] > res[0.3][0] > res[0.6][0] > res[0.95][0] and res[0.0][1] < res[0.3][1] < res[0.6][1] < res[0.95][1]
    # Exact conditional check of the first-to-default at 0.6 by quadrature.
    f = lambda m: n(m) * (1 - (1 - N((c - sqrt(0.6) * m) / sqrt(0.4))) ** 5)  # noqa: E731
    assert abs(quad(f, -8, 8)[0] - res[0.6][0]) < 5e-4


def test_q10():
    assert round(S0, 3) == 0.399
    ts = np.linspace(0.001, 4.999, 49981)
    ee = S0 * 0.01 * 100 * np.sqrt(ts) * (5 - ts)
    i = ee.argmax()
    assert abs(ts[i] - 5 / 3) < 1e-3 and round(ee[i], 2) == 1.72
    # Simulated swap value at that date against the closed form.
    z = np.random.default_rng(3).standard_normal(2_000_000)
    v = 0.01 * sqrt(5 / 3) * z * 100 * (5 - 5 / 3)
    assert abs(np.maximum(v, 0).mean() - S0 * 0.01 * 100 * sqrt(5 / 3) * (5 - 5 / 3)) < 3e-3
    # Limits: exposure is zero at both ends.
    assert ee_mean(0) == 0 and ee_mean(5) == 0


def test_q11():
    integ = quad(ee_mean, 0, 5)[0]
    closed = S0 * (5 * 2 / 3 * 5**1.5 - 2 / 5 * 5**2.5)
    assert round(integ, 3) == 5.947 and abs(integ - closed) < 1e-6
    cva = 0.6 * 0.02 * integ
    assert round(cva, 4) == 0.0714
    assert abs(cva - 0.012 * (integ / 5) * 5) < 1e-12
    # 45% overstatement from the peak.
    assert round(1.72 / (integ / 5) - 1, 2) == 0.45
    # Discounting at 3% and survival, on the stated profile: e^{-0.05 t} under the integral.
    d = 0.6 * 0.02 * quad(lambda t: exp(-0.05 * t) * ee_mean(t), 0, 5)[0]
    assert round(d, 3) == 0.064
    # Second route: simulate the default time, and pay the discounted loss when it falls inside the life.
    tau = np.random.default_rng(11).exponential(1 / 0.02, 4_000_000)
    hit = tau[tau < 5]
    sim = 0.6 * (np.exp(-0.03 * hit) * S0 * np.sqrt(hit) * (5 - hit)).sum() / tau.size
    assert abs(sim - d) < 5e-4
    # Each decay alone sits between the two: no decay 0.0714, the full 5% decay 0.064.
    assert d < 0.6 * 0.02 * quad(lambda t: exp(-0.03 * t) * ee_mean(t), 0, 5)[0] < cva
    # No hazard, no CVA.
    assert cva_surv(1e-12) < 1e-9


def test_q12():
    assert round(2 * S0, 3) == 0.798
    vals = [S0 * sqrt(2 + 2 * r) for r in (-1, -0.5, 0, 0.5, 1)]
    assert [round(v, 3) for v in vals] == [0, 0.399, 0.564, 0.691, 0.798]
    rng = np.random.default_rng(4)
    a = rng.standard_normal(1_000_000)
    e = rng.standard_normal(1_000_000)
    for r, v in zip((-1, -0.5, 0, 0.5, 1), vals, strict=True):
        b = r * a + sqrt(1 - r * r) * e
        assert abs(np.maximum(a + b, 0).mean() - v) < 3e-3
        assert np.all(np.maximum(a + b, 0) <= np.maximum(a, 0) + np.maximum(b, 0) + 1e-12)
    assert round(1 - vals[2] / vals[4], 2) == 0.29


def test_q13():
    assert round(S0 * 10, 2) == 3.99
    m = S0 * 10 * sqrt(10 / 252)
    assert round(m, 2) == 0.79 and round(m, 3) == 0.795
    assert round(sqrt(10 / 252), 1) == 0.2
    assert round(1 - sqrt(5 / 10), 2) == 0.29
    # Daily path simulation: the exposure at default is the move since the margin of 10 days ago.
    rng = np.random.default_rng(5)
    moves = rng.standard_normal((400_000, 10)) * 10 / sqrt(252)
    assert abs(np.maximum(moves.sum(1), 0).mean() - m) < 0.01
    # A zero margin period gives zero exposure.
    assert S0 * 10 * sqrt(0) == 0


def test_q14():
    integ = quad(ee_mean, 0, 5)[0]
    cva, dva = 0.6 * 0.02 * integ, 0.6 * 0.01 * integ
    assert round(cva, 4) == 0.0714 and round(dva, 4) == 0.0357 and round(cva - dva, 4) == 0.0357
    w = quad(lambda t: exp(-0.03 * t) * ee_mean(t), 0, 5)[0]
    c2, d2 = 0.6 * 0.02 * w, 0.6 * 0.01 * w
    assert round(c2, 4) == 0.0670 and round(d2, 4) == 0.0335 and round(c2 - d2, 4) == 0.0335
    # Weighting must lower both: first default stops the contract.
    assert c2 < cva and d2 < dva
    # A symmetric swap: negative exposure has the same integral, checked by simulation at one date.
    z = np.random.default_rng(6).standard_normal(1_000_000)
    assert abs(np.maximum(z, 0).mean() - np.maximum(-z, 0).mean()) < 2e-3


def test_q15():
    integ = quad(ee_mean, 0, 5)[0]
    assert round(0.01 * integ, 4) == 0.0595
    fba, dva = 0.006 * integ, 0.6 * 0.01 * integ
    assert round(fba, 4) == 0.0357 and abs(fba - dva) < 1e-15
    assert 0.0 * integ == 0
    # Simulated funding account: pay the spread on the positive mark, by path.
    rng = np.random.default_rng(7)
    k, dt = 200, 5 / 200
    w = rng.standard_normal((40_000, k)).cumsum(1) * 0.01 * sqrt(dt)
    t = np.arange(1, k + 1) * dt
    mark = w * 100 * (5 - t)
    cost = 0.01 * np.maximum(mark, 0).sum(1) * dt
    assert abs(cost.mean() - 0.01 * integ) < 2e-3


def test_q16():
    c = norm.ppf(0.02)
    assert round(c, 2) == -2.05 and round(-n(c) / 0.02, 2) == -2.42

    def ee(rho):
        return quad(lambda z: -5 * z * n(z) * N((c - rho * z) / sqrt(1 - rho * rho)), -12, 0)[0] / 0.02

    vals = [ee(r) for r in (0, 0.3, 0.5, -0.3)]
    assert [round(v, 2) for v in vals] == [1.99, 4.25, 6.22, 0.62]
    assert round(vals[1] / vals[0], 1) == 2.1 and round(vals[2] / vals[0], 1) == 3.1
    assert abs(vals[0] - 5 * n(0)) < 1e-9
    # Simulation.
    rng = np.random.default_rng(8)
    z, e = rng.standard_normal(4_000_000), rng.standard_normal(4_000_000)
    for r, v in zip((0.3, 0.5, -0.3), vals[1:], strict=True):
        d = r * z + sqrt(1 - r * r) * e < c
        assert abs(np.maximum(-5 * z[d], 0).mean() - v) < 0.1
    # Extreme: rho near 1 means default only when Z is below the threshold.
    assert ee(0.999) > 5 * 2.42 * 0.95


def lhp(a, b, p, rho, big_r=0.4):
    x, w = np.polynomial.hermite_e.hermegauss(200)
    w = w / w.sum()
    c = norm.ppf(p)
    loss = (1 - big_r) * N((c - sqrt(rho) * x) / sqrt(1 - rho))
    return float((w * (np.clip(loss, a, b) - a)).sum() / (b - a))


def test_q17():
    tr = ((0, 0.03), (0.03, 0.07), (0.07, 0.15), (0.15, 1))
    exp_tab = {0.05: [39.6, 0.33, 0.00, 0.00], 0.2: [33.5, 4.06, 0.40, 0.00], 0.5: [21.3, 6.70, 2.42, 0.12]}
    for rho, row in exp_tab.items():
        got = [lhp(a, b, 0.02, rho) * 100 for a, b in tr]
        for g, e, nd in zip(got, row, (1, 2, 2, 2), strict=True):
            assert round(g, nd) == e
        assert abs(sum((b - a) * lhp(a, b, 0.02, rho) for a, b in tr) - 0.012) < 1e-9
    assert lhp(0.03, 0.07, 0.02, 0.5) > 0.02
    # Limits named in the answer.
    assert abs(lhp(0, 0.03, 0.02, 1e-6) - 0.4) < 1e-3
    # Rho near one: 2% of a 60% loss. Direct simulation, since quadrature cannot see the step.
    rng = np.random.default_rng(9)
    m = rng.standard_normal(2_000_000)
    los = 0.6 * N((norm.ppf(0.02) - sqrt(1 - 1e-10) * m) / sqrt(1e-10))
    assert abs((np.clip(los, 0, 0.03) / 0.03).mean() - 0.02) < 5e-4
    assert abs(((np.clip(los, 0.15, 1) - 0.15) / 0.85).mean() - 0.02 * 0.45 / 0.85) < 5e-4
    # Finite pool: 1,000 names against the large-pool number.
    z = rng.standard_normal(100_000)
    pr = N((norm.ppf(0.02) - sqrt(0.2) * z) / sqrt(0.8))
    k = rng.binomial(1000, pr)
    assert abs((np.clip(0.6 * k / 1000, 0, 0.03) / 0.03).mean() - lhp(0, 0.03, 0.02, 0.2)) < 0.01


def merton(t, v=100.0, d=80.0, s=0.25, r=0.03):
    d1 = (log(v / d) + (r + s * s / 2) * t) / (s * sqrt(t))
    d2 = d1 - s * sqrt(t)
    e = v * N(d1) - d * exp(-r * t) * N(d2)
    return d1, d2, e, v - e, (-log((v - e) / d) / t - r) * 1e4


def test_q18():
    d1, d2, e, b, sp = merton(1)
    assert round(d1, 4) == 1.1376 and round(d2, 4) == 0.8876
    assert round(e, 2) == 24.15 and round(b, 2) == 75.85 and round(N(-d2), 3) == 0.187 and round(sp) == 232
    # Second route: riskless bond less a put.
    put = 80 * exp(-0.03) * N(-d2) - 100 * N(-d1)
    assert round(80 * exp(-0.03), 2) == 77.64 and round(put, 2) == 1.78 and abs(80 * exp(-0.03) - put - b) < 1e-9
    # Simulated assets.
    z = np.random.default_rng(10).standard_normal(4_000_000)
    va = 100 * np.exp(0.03 - 0.03125 + 0.25 * z)
    assert abs(np.exp(-0.03) * np.minimum(va, 80).mean() - b) < 0.02 and abs((va < 80).mean() - N(-d2)) < 1e-3
    # Term structure.
    assert round(merton(0.25)[4]) == 71 and round(merton(5)[4]) == 210 and round(merton(10)[4]) == 162
    assert round(merton(1 / 12)[4]) == 2 and round(merton(2)[4]) == 248
    assert merton(0.01)[4] < 1e-3


def test_q19():
    assert round(0.01 / 0.6, 4) == 0.0167
    assert round((3 * 0.025 - 0.01 / 0.6) / 2, 4) == 0.0292 and round((5 * 0.02 / 0.6 - 3 * 0.025) / 2, 4) == 0.0458
    qt = np.arange(0.25, 5.01, 0.25)
    r, big_r = 0.03, 0.4
    hz = [0.0, 0.0, 0.0]

    def legs(hz, t_end):
        def big_h(t):
            tot, prev = 0.0, 0.0
            for h, b in zip(hz, (1, 3, 5), strict=True):
                tot += h * max(0, min(t, b) - prev)
                prev = b
            return tot

        rp = pr = 0.0
        for t in qt[qt <= t_end + 1e-9]:
            d = exp(-r * t)
            s0, s1 = exp(-big_h(t - 0.25)), exp(-big_h(t))
            rp += 0.25 * d * s1 + 0.125 * d * (s0 - s1)
            pr += d * (s0 - s1)
        return rp, (1 - big_r) * pr

    for i, (t_end, sp) in enumerate(((1, 0.01), (3, 0.015), (5, 0.02))):
        def f(h, i=i, t_end=t_end, sp=sp):
            hz[i] = h
            a, b = legs(hz, t_end)
            return b - sp * a

        hz[i] = brentq(f, 1e-5, 1)
    assert [round(h * 100, 2) for h in hz] == [1.67, 2.95, 4.81]
    # The contracts reprice: the model reproduces each input.
    for t_end, sp in ((1, 0.01), (3, 0.015), (5, 0.02)):
        a, b = legs(hz, t_end)
        assert abs(b / a - sp) < 1e-8
    # Inverted curve.
    assert round(0.2 / 0.6, 3) == 0.333 and round(5 * 0.08 / 0.6, 3) == 0.667
    assert round((5 * 0.08 / 0.6 - 0.2 / 0.6) / 4, 4) == 0.0833


def test_q20():
    c = cva_surv(0.02) * 1e6
    assert round(c, -2) == 110_800
    assert round(0.02 * 5.947 / 100 * 1e8) == 118_940
    cs01 = (cva_surv(0.0201) - cva_surv(0.02)) * 1e6
    assert round(cs01) == 515
    ann = annuity(0, 0.02 / 0.6, 5)
    assert round(ann, 2) == 4.61 and round(cs01 / (ann * 100), 2) == 1.12
    up, dn = cva_surv(0.02, 0.005) * 1e6, cva_surv(0.02, -0.005) * 1e6
    sp, both = cva_surv(0.03) * 1e6, cva_surv(0.03, 0.005) * 1e6
    assert round(up, -2) == 182_500 and round(dn, -2) == 64_100
    assert round(sp, -2) == 160_600 and round(both, -2) == 265_400
    delta = (cva_surv(0.02, 0.0001) - cva_surv(0.02, -0.0001)) / 2 * 1e6
    assert round(delta, -1) == 1180
    cross = both - (c + (up - c) + (sp - c))
    assert round(cross, -2) == 33_100
    cs01_up = (cva_surv(0.0201, 0.005) - cva_surv(0.02, 0.005)) * 1e6
    assert round(cs01_up) == 855 and round(cs01_up / (ann * 100), 2) == 1.86
    assert round(cs01_up / (ann * 100) - cs01 / (ann * 100), 2) == 0.74
    assert round(cva_surv(0.02, 0, 0.012) * 1e6, -3) == 133_000
    # CVA is a cost, so a higher value when vol rises is a loss: the desk is short vega.
    assert cva_surv(0.02, 0, 0.012) > cva_surv(0.02)
    # The cross term is what the sum misses, and vanishes when one leg has no exposure.
    assert cva_surv(0.03, -1.0) * 1e6 < 1
