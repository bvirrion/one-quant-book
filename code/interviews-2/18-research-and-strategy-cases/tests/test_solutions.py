"""Research and Strategy Cases. Rules of thumb tested against simulations of the mistake they warn about."""
from math import erf, exp, log, pi, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import norm

Phi, phi, Q = norm.cdf, norm.pdf, norm.ppf
NONNUMERIC = {
    20: "A data-checking order for a take-home; the answer leads with the order and how to build your own checklist.",
    26: "An ordered list of questions about a backtest; the answer leads with the order and what each answer changes.",
}


def emax(n):
    """Exact expected maximum of n standard normals."""
    return quad(lambda z: z * n * Phi(z) ** (n - 1) * phi(z), -10, 12)[0]


def ar(rng, n, m, rho):
    x = np.zeros((n, m))
    e = rng.standard_normal((n, m))
    x[:, 0] = e[:, 0]
    for i in range(1, m):
        x[:, i] = rho * x[:, i - 1] + sqrt(1 - rho * rho) * e[:, i]
    return x


def test_q1():
    assert round(0.0008 / 0.012 * sqrt(252), 2) == 1.06


def test_q2():
    assert 1 * sqrt(4) == 2 and (2 / 0.5) ** 2 == 16
    # Simulated t of a mean with SR 1 at 4 years.
    r = np.random.default_rng(1).standard_normal((20000, 1008)) * (0.1 / sqrt(252)) + 0.1 / 252
    t = r.mean(axis=1) / (r.std(axis=1) / sqrt(1008))
    assert abs(t.mean() - 2) < 0.02


def test_q3():
    assert round(10 / 60 * sqrt(252), 2) == 2.65 and round((10 - 0.4 * 5) / 60 * sqrt(252), 2) == 2.12


def test_q4():
    assert 50 * 0.05 * 5 == 12.5 and 12.5 * 200 == 2500


def test_q5():
    assert round(0.55 - 0.45, 6) == 0.1 and round(sqrt(1 - 0.01), 3) == 0.995
    assert round(0.1 / 0.995 * 10, 3) == 1.005


def test_q6():
    m, s = sqrt(2 / pi), sqrt(1 - 2 / pi)
    assert round(m, 3) == 0.798 and round(s, 3) == 0.603 and round(m / s, 2) == 1.32
    assert round(m / s * sqrt(252)) == 21
    rng = np.random.default_rng(2)
    r = rng.standard_normal(4_000_000)
    bad = np.sign(r) * r
    good = np.sign(r[:-1]) * r[1:]
    assert abs(bad.mean() / bad.std() * sqrt(252) - m / s * sqrt(252)) < 0.05
    assert abs(good.mean() / good.std() * sqrt(252)) < 0.05


def test_q7():
    assert round(1 - 0.95**20, 3) == 0.642 and 20 * 0.05 == 1
    # The level that holds the best of 20 at 5 percent.
    level = 1 - 0.95 ** (1 / 20)
    assert abs(1 - (1 - level) ** 20 - 0.05) < 1e-12 and abs(level - 0.0025) < 1e-4


def test_q8():
    assert round(Phi(-1), 2) == 0.16 and round(Phi(-2), 3) == 0.023


def test_q9():
    assert round(0.97 * 0.10 + 0.03 * -1, 4) == 0.067


def test_q10():
    assert 10 / 25 == 0.4
    r = np.random.default_rng(3).standard_normal(100000) * 0.25 + 0.1
    assert abs((0.4 * r).mean() / (0.4 * r).std() - r.mean() / r.std()) < 1e-12


def test_q11():
    rng = np.random.default_rng(4)
    em = emax(100)
    assert abs(rng.standard_normal((200000, 100)).max(axis=1).mean() - em) < 0.01
    assert round(em, 2) == 2.51 and round(em / sqrt(5), 2) == 1.12
    assert round(sqrt(2 * log(100)), 2) == 3.03 and round(sqrt(2 * log(100)) / sqrt(5), 2) == 1.36
    # Full simulation: sample Sharpes of the best of 100.
    r = rng.standard_normal((2000, 100, 60)) * 0.03
    sr = r.mean(axis=2) / r.std(axis=2) * sqrt(12)
    # Sample Sharpes on 60 points carry a t-distribution's slightly fatter tails.
    assert abs(sr.max(axis=1).mean() - em / sqrt(5)) < 0.06


def test_q12():
    z = Q(0.9)
    top = phi(z) / 0.1
    assert round(z, 4) == 1.2816 and round(top, 3) == 1.755
    assert round(2 * top * 0.03 * 0.02, 4) == 0.0021
    rng = np.random.default_rng(5)
    s = rng.standard_normal((500, 3000))
    r = 0.03 * s + sqrt(1 - 0.0009) * rng.standard_normal((500, 3000))
    hi, lo = s >= np.quantile(s, 0.9, axis=1, keepdims=True), s <= np.quantile(s, 0.1, axis=1, keepdims=True)
    sp = ((r * hi).sum(axis=1) / hi.sum(axis=1) - (r * lo).sum(axis=1) / lo.sum(axis=1)).mean() * 0.02
    assert abs(sp - 0.0021) < 1e-4
    # No skill means no spread, by simulation with the correlation removed.
    r0 = rng.standard_normal((500, 3000))
    sp0 = ((r0 * hi).sum(axis=1) / hi.sum(axis=1) - (r0 * lo).sum(axis=1) / lo.sum(axis=1)).mean() * 0.02
    assert abs(sp0) < 1e-4


def test_q13():
    assert round(log(0.5) / log(0.9), 2) == 6.58
    assert round(4 / 0.1) == 40
    assert round(1 - 0.9**6.58, 2) == 0.50 and round(1 - 0.9**20, 2) == 0.88
    assert abs(sum(4 * 0.9**k for k in range(5000)) - 40) < 1e-9


def tstat(x, y):
    t_ = x.shape[1]
    xx = x - x.mean(axis=1, keepdims=True)
    yy = y - y.mean(axis=1, keepdims=True)
    b = (xx * yy).sum(axis=1) / (xx * xx).sum(axis=1)
    res = yy - b[:, None] * xx
    return b / np.sqrt((res * res).sum(axis=1) / (t_ - 2) / (xx * xx).sum(axis=1))


def test_q14():
    rng = np.random.default_rng(6)
    n, t_, h = 1200, 1000, 20
    e = rng.standard_normal((n, t_ + h))
    c = np.cumsum(e, axis=1)
    y = c[:, h:] - c[:, :-h]
    slow = ar(rng, n, t_, 0.99)
    fast = rng.standard_normal((n, t_))
    ts, tf = tstat(slow, y), tstat(fast, y)
    assert abs(ts.std() - 4.4) < 0.3 and abs((np.abs(ts) > 1.96).mean() - 0.65) < 0.05
    assert abs(tf.std() - 1.0) < 0.08 and abs((np.abs(tf) > 1.96).mean() - 0.05) < 0.02


def test_q15():
    assert round(200 * sqrt(0.05), 1) == 44.7 and round(200 * sqrt(0.025), 1) == 31.6
    assert round(0.5**1.5, 2) == 0.35 and round(2 * 0.5**1.5, 2) == 0.71
    assert round(1 - 0.5**1.5, 2) == 0.65 and round(1 - 2 * 0.5**1.5, 2) == 0.29


def test_q16():
    g = np.linspace(0.01, 12, 119900)
    p = g * (30 - 10 * np.sqrt(g))
    i = p.argmax()
    assert abs(g[i] - 4) < 1e-3 and abs(p[i] - 40) < 1e-3
    assert abs(10 * sqrt(4) - 20) == 0 and 30 - 20 == 10
    assert abs(9 * (30 - 10 * sqrt(9))) == 0
    assert abs(20 / 30 - 2 / 3) < 1e-12


def test_q17():
    assert [(2 / s) ** 2 for s in (2, 1, 0.5)] == [1, 4, 16]


def test_q18():
    assert 20 - 11 - 3 - 2 - 2 - 1 == 1


def test_q19():
    f = 0.15 / 0.01
    assert f == 15 and round(f * 0.15 - 0.5 * f * f * 0.01, 3) == 1.125
    assert abs(f * 0.075 - 0.5 * f * f * 0.01) < 1e-12
    assert round(7.5 * 0.075 - 0.5 * 56.25 * 0.01, 3) == 0.281
    # Simulation of log growth with small steps.
    rng = np.random.default_rng(7)
    k = 365
    r = rng.standard_normal((2000, k)) * 0.10 / sqrt(k) + 0.075 / k
    g = np.log1p(15 * r).sum(axis=1).mean()
    assert abs(g - 0) < 0.03


def test_q21():
    ic = np.array([0.03, 0.02])
    c = np.array([[1, 0.5], [0.5, 1]])
    w = np.linalg.solve(c, ic)
    assert [round(float(i), 4) for i in w] == [0.0267, 0.0067]
    assert round(float(w[0] / w.sum()), 2) == 0.8
    assert round(float(sqrt(ic @ w)), 4) == 0.0306
    assert abs(np.linalg.solve([[1, 2 / 3], [2 / 3, 1]], ic)[1]) < 1e-12
    assert round(sqrt(0.03**2 + 0.02**2), 3) == 0.036


def test_q22():
    assert 200 * 0.1 == 20 and (20 - 10) / 200 == 0.05 and 10 / 20 == 0.5
    assert round((10 + 200 * 0.08) / 20, 1) == 1.3


def test_q23():
    rev = 1e9 * 0.02 * 1e-4 * 365
    assert round(rev) == 730_000 and round(2e6 / (1e9 * 1e-4 * 365), 4) == 0.0548


def test_q24():
    m = 0.35 * 3 - 0.65
    v = 0.35 * 9 + 0.65 - m * m
    assert round(m, 6) == 0.4 and round(v, 2) == 3.64 and round(sqrt(v), 2) == 1.91
    assert round(m / sqrt(v), 2) == 0.21 and round(m / sqrt(v) * 10, 1) == 2.1
    assert round(0.65**10, 4) == 0.0135


def test_q25():
    assert 15 - 0.5 * 8 == 11
    assert round(sqrt(0.01 - 0.25 * 0.0256), 3) == 0.06 and round(0.11 / 0.06, 2) == 1.83
    # Reassembling: beta part and residual give back the total variance.
    assert abs((0.5 * 0.16) ** 2 + 0.06**2 - 0.01) < 1e-12


def test_q27():
    rng = np.random.default_rng(8)
    m = 3000
    a, b = rng.standard_normal((m, 100)), rng.standard_normal((m, 100))
    best = a.argmax(axis=1)
    assert round(emax(100) / sqrt(2.5), 2) == 1.59
    assert abs(a.max(axis=1).mean() - emax(100)) < 0.03
    oos = b[np.arange(m), best]
    assert abs(oos.mean()) < 0.05
    rank = (b > oos[:, None]).sum(axis=1) + 1
    assert abs(rank.mean() - 50.5) < 1.5 and abs((rank > 50).mean() - 0.5) < 0.03
    # With true skill in one strategy, in-sample rank carries information.
    a[:, 0] += 4
    b[:, 0] += 4
    best = a.argmax(axis=1)
    assert b[np.arange(m), best].mean() > 2


def test_q28():
    rng = np.random.default_rng(9)
    t_, k = 500, 20
    i, o = [], []
    for _ in range(800):
        x, y = rng.standard_normal((t_, k)), rng.standard_normal(t_)
        b = np.linalg.lstsq(x, y, rcond=None)[0]
        i.append(1 - ((y - x @ b) ** 2).sum() / (y**2).sum())
        xo, yo = rng.standard_normal((t_, k)), rng.standard_normal(t_)
        o.append(1 - ((yo - xo @ b) ** 2).sum() / (yo**2).sum())
    assert abs(np.mean(i) - 0.04) < 0.002 and abs(np.mean(o) + 0.04) < 0.004
    # Adjusted R-squared removes it.
    assert abs(1 - (1 - np.mean(i)) * (t_ - 1) / (t_ - k - 1)) < 0.003


def test_q29():
    m = 0.8 * 0.2 + 0.2 * -0.2
    within = 0.8 * 0.01 + 0.2 * 0.04
    between = 0.8 * (0.2 - m) ** 2 + 0.2 * (-0.2 - m) ** 2
    assert round(m, 4) == 0.12 and round(within, 3) == 0.016 and round(between, 4) == 0.0256
    assert round(within + between, 4) == 0.0416 and round(sqrt(within + between), 3) == 0.204
    assert round(m / sqrt(within + between), 2) == 0.59 and round(0.8 * 2 + 0.2 * -1, 6) == 1.4
    rng = np.random.default_rng(10)
    calm = rng.random(2_000_000) < 0.8
    r = np.where(calm, 0.2 + 0.1 * rng.standard_normal(2_000_000), -0.2 + 0.2 * rng.standard_normal(2_000_000))
    assert abs(r.mean() / r.std() - m / sqrt(within + between)) < 2e-3


def test_q30():
    kap = log(2) / 10
    assert round(kap, 4) == 0.0693
    survive = lambda t: erf(2 * exp(-kap * t) / sqrt(2 * (1 - exp(-2 * kap * t))))  # noqa: E731
    mean_t = quad(survive, 0, 2000, limit=400, points=[1, 20, 100])[0]
    assert round(mean_t, 1) == 20.6
    assert round(brentq(lambda t: survive(t) - 0.5, 1, 100), 1) == 16.5
    # Second route: the backward equation, in units of the stationary sd.
    t2 = quad(lambda y: exp(y * y / 2) * quad(lambda z: exp(-z * z / 2), y, 12)[0], 0, 2)[0] / kap
    assert abs(t2 - mean_t) < 0.01
    # Third route: simulation, on a fine grid because a coarse one overstates the time.
    rng = np.random.default_rng(11)
    m = 3000
    sd = 0.02 * sqrt(2 * kap)
    dt = 0.01
    x = np.full(m, 0.04)
    tm = np.zeros(m)
    alive = np.ones(m, bool)
    for _ in range(100000):
        if not alive.any():
            break
        x[alive] += -kap * x[alive] * dt + sd * sqrt(dt) * rng.standard_normal(alive.sum())
        tm[alive] += dt
        alive &= x > 0
    assert abs(tm.mean() - mean_t) < 1.0 and abs(np.median(tm) - 16.5) < 1.0
    assert round(252 / mean_t, 1) == 12.3 and round((0.04 - 0.002) * 12.3, 2) == 0.47


def test_q31():
    mean = 0.98 * 0.12 + 0.02 * -0.40
    var = 0.98 * (0.01 + 0.0144) + 0.02 * 0.16 - mean**2
    assert round(mean, 4) == 0.1096 and round(var, 4) == 0.0151
    assert round(sqrt(var), 3) == 0.123 and round(mean / sqrt(var), 2) == 0.89
    assert round(log(0.1) / log(0.98)) == 114
    assert 1 - 0.98**114 >= 0.9 > 1 - 0.98**113


def test_q32():
    edge = lambda ms: 2 * 2 ** (-ms / 200) - 1  # noqa: E731
    assert [round(edge(x), 2) for x in (50, 200, 400)] == [0.68, 0.0, -0.5]
    assert abs(edge(200)) < 1e-12 and edge(0) == 1


def test_q33():
    rng = np.random.default_rng(12)
    st = rng.standard_normal((300000, 20)) * 0.01
    c = st.cumsum(axis=1)
    hit = c <= -0.05
    any_ = hit.any(axis=1)
    first = np.where(any_, hit.argmax(axis=1), 19)
    r = c[np.arange(300000), first]
    assert abs(r.mean()) < 3e-4 and abs(c[:, -1].mean()) < 3e-4
    assert abs(c[:, -1].std() - 0.01 * sqrt(20)) < 3e-4 and abs(r.std() - 0.0428) < 5e-4
    assert abs(any_.mean() - 0.21) < 0.01
    # With momentum, the stop adds value; with reversal, it loses.
    rho = 0.2
    for sign in (1, -1):
        e = rng.standard_normal((100000, 20)) * 0.01
        x = np.zeros_like(e)
        x[:, 0] = e[:, 0]
        for i in range(1, 20):
            x[:, i] = sign * rho * x[:, i - 1] + e[:, i]
        cc = x.cumsum(axis=1)
        h = cc <= -0.05
        a = h.any(axis=1)
        fi = np.where(a, h.argmax(axis=1), 19)
        stop_gain = (cc[np.arange(100000), fi] - cc[:, -1]).mean()
        assert stop_gain * sign > 3e-4


def test_q34():
    rng = np.random.default_rng(13)
    t_, k, h = 1000, 10, 20
    res = {"r": [], "b": [], "p": []}

    def score(x, y, folds, train):
        sse = sst = 0.0
        for f, tr in zip(folds, train, strict=True):
            b = np.linalg.lstsq(np.c_[np.ones(len(tr)), x[tr]], y[tr], rcond=None)[0]
            p = np.c_[np.ones(len(f)), x[f]] @ b
            sse += ((y[f] - p) ** 2).sum()
            sst += ((y[f] - y[tr].mean()) ** 2).sum()
        return 1 - sse / sst

    idx = np.arange(t_)
    for _ in range(400):
        x = ar(rng, k, t_ + h, 0.99).T[:t_]
        c = np.cumsum(rng.standard_normal(t_ + h))
        y = c[h:] - c[:-h]
        perm = rng.permutation(t_)
        rf = np.array_split(perm, 5)
        res["r"].append(score(x, y, rf, [np.setdiff1d(idx, f) for f in rf]))
        bl = np.array_split(idx, 5)
        res["b"].append(score(x, y, bl, [np.setdiff1d(idx, f) for f in bl]))
        pu = [np.r_[np.arange(0, max(f[0] - h, 0)), np.arange(min(f[-1] + h + 1, t_), t_)] for f in bl]
        res["p"].append(score(x, y, bl, pu))
    assert abs(np.mean(res["r"]) - 0.15) < 0.02
    assert abs(np.mean(res["b"]) + 0.46) < 0.06 and abs(np.mean(res["p"]) + 0.55) < 0.06


def test_q35():
    assert round((1.96 / 0.04) ** 2) == 2401 and round((2.8 / 0.04) ** 2) == 4900
    assert round((1.96 / 0.02) ** 2) == 9604 and round((2.8 / 0.02) ** 2) == 19600
    # Power by simulation of binomial win counts.
    rng = np.random.default_rng(14)
    w = rng.binomial(4900, 0.52, 200000)
    t = (2 * w / 4900 - 1) * sqrt(4900)
    assert abs((t > 1.96).mean() - 0.80) < 0.01
    w = rng.binomial(2401, 0.52, 200000)
    t = (2 * w / 2401 - 1) * sqrt(2401)
    assert abs((t > 1.96).mean() - 0.5) < 0.01


def test_q36():
    b = 8 / (sqrt(300) - 10)
    a = 20 + 10 * b
    assert round(b, 2) == 1.09 and round(a, 2) == 30.93
    assert round(a - b * sqrt(500), 1) == 6.5
    q = ((a - 5) / (1.5 * b)) ** 2
    assert round(q, -1) == 250 and round((a - 5) / (1.5 * b), 1) == 15.8
    # Marginal at 300, from the fit and by a bump.
    mg = a - 1.5 * b * sqrt(300)
    assert round(mg, 1) == 2.5
    f = lambda x: x * (a - b * sqrt(x))  # noqa: E731
    assert abs((f(300.01) - f(299.99)) / 0.02 - mg) < 1e-4


def test_q37():
    assert round((sqrt(1.25) - 1) * 30, 2) == 3.54 and round((sqrt(1.0625) - 1) * 30, 2) == 0.92
    # Correlated with the book, the same dataset adds less, and at rho = SR2/SR1 it adds nothing.
    sr = lambda s, r: sqrt((1 + s * s - 2 * r * s) / (1 - r * r))  # noqa: E731
    assert sr(0.5, 0.5) == 1.0 and sr(0.5, 0.0) > sr(0.5, 0.3) > 1


def test_q38():
    em = emax(200)
    assert abs(np.random.default_rng(15).standard_normal((100000, 200)).max(axis=1).mean() - em) < 0.01
    assert round(em, 3) == 2.746 and round(em / sqrt(3), 3) == 1.585
    h = 2.4 - em / sqrt(3)
    assert round(h, 3) == 0.815
    prec = 1 / 0.25 + 3
    assert prec == 7 and round(sqrt(1 / prec), 3) == 0.378
    m1 = (3 * h) / prec
    assert round(m1, 2) == 0.35
    prec2 = prec + 0.5
    m2 = (prec * m1 + 0.5 * 0.5) / prec2
    assert round(m1, 3) == 0.349 and round(m2, 3) == 0.359 and round(sqrt(1 / prec2), 3) == 0.365
    assert round(Phi(-m2 * sqrt(prec2)), 2) == 0.16
    # The yardstick is the live Sharpe's own noise: six months has variance 2, the same as in the update above.
    se_live = sqrt(1 / 0.5)
    assert round(se_live, 1) == 1.4
    assert round((0.5 - m2) / se_live, 1) == 0.1 and round((2.4 - 0.5) / se_live, 1) == 1.3
    sharpes = np.random.default_rng(38).normal(0.0, 1.0, (200_000, 126)).mean(axis=1) * sqrt(252)
    assert abs(sharpes.std() - se_live) < 0.01
    assert round(2.4 / m2) == 7 and round(m2 / 2.4, 2) == 0.15
    # Fewer trials leave more to explain: with one trial there is no haircut.
    assert abs(emax(1)) < 1e-6 and emax(20) < emax(200)


def test_q39():
    base = 20e9 * 0.5e-4 * 365
    assert round(base / 1e6) == 365
    assert [round(base * s / 1e6, 2) for s in (0.01, 0.02, 0.05)] == [3.65, 7.3, 18.25]
    assert round(0.009 * 20e6) == 180_000 and 0.15 * 20e6 == 3e6
    assert round(6.18e6 / base, 4) == 0.0169 and round(9.18e6 / base, 4) == 0.0252
    assert round(6.18e6 / (base / 2), 4) == 0.0339 and round(9.18e6 / (base / 2), 4) == 0.0503
    # At break-even, profit is zero by a direct sum; half the capture exactly doubles each share.
    assert abs(base * (9.18e6 / base) - 6e6 - 0.18e6 - 3e6) < 1e-6
    assert abs(9.18e6 / (base / 2) - 2 * 9.18e6 / base) < 1e-12


def test_q40():
    rho = 2 ** (-1 / 5)
    sq = sqrt(pi / 2)
    vol = sq * 200 / sqrt(500)
    assert round(vol, 1) == 11.2

    def row(h):
        a = 2 * sq * (1 - rho**h) / (h * (1 - rho))
        c = 5 * sqrt(2 * (1 - rho**h)) / h
        return a, c, a - c, (a - c) / vol * sqrt(252)

    want = {1: (2.51, 2.54, -0.04, -0.05), 3: (2.20, 1.37, 0.82, 1.16), 5: (1.94, 1.00, 0.94, 1.33), 6: (1.82, 0.89, 0.94, 1.33), 10: (1.45, 0.61, 0.84, 1.19), 20: (0.91, 0.34, 0.57, 0.80)}
    for h, w in want.items():
        assert [round(x, 2) for x in row(h)] == list(w)
    best = max(range(1, 40), key=lambda h: row(h)[2])
    assert best in (5, 6)
    assert round(row(5)[0] / vol * sqrt(252), 1) == 2.7 and round(row(1)[0] / vol * sqrt(252), 1) == 3.5
    # Full simulation of the book at h = 5.
    rng = np.random.default_rng(16)
    n, days = 500, 6000
    s = ar(rng, n, days, rho)
    pos = np.zeros_like(s)
    for t in range(days):
        pos[:, t] = s[:, t - t % 5]
    pos /= np.abs(pos).sum(axis=0, keepdims=True)
    # Expected return is 2 bp per unit of the current signal, and the noise is 200 bp.
    ret = 2 * s + 200 * rng.standard_normal((n, days))
    gross = (pos * ret).sum(axis=0)
    trade = np.abs(np.diff(pos, axis=1)).sum(axis=0)
    net = gross[1:] - 5 * trade
    assert abs(gross.mean() - row(5)[0]) < 0.25
    assert abs(trade.mean() - sqrt(2 * (1 - rho**5)) / 5) < 0.01
    assert abs(net.mean() - row(5)[2]) < 0.3 and abs(gross.std() - vol) < 0.25
