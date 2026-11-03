"""Every number printed in the answers of "Statistics": exact formulas, then seeded simulations."""
import math
from itertools import combinations

import numpy as np
from scipy import stats

NONNUMERIC = {}
N = stats.norm


def test_q1():
    assert (60 - 50) / 5 == 2
    assert round(2 * N.sf(2), 4) == 0.0455
    exact = 2 * stats.binom.sf(59, 100, 0.5)
    assert round(exact, 3) == 0.057
    assert round(2 * N.sf(1.9), 3) == 0.057
    # The two routes differ only through the half-count correction.
    assert abs(exact - 2 * N.sf(1.9)) < 0.001


def test_q2():
    se = 1 / math.sqrt(400)
    assert se == 0.05
    assert round(1.96 * se, 3) == 0.098
    assert 400 * 4 == 1600
    rng = np.random.default_rng(2)
    m = rng.normal(0.1, 1, (20_000, 400)).mean(axis=1)
    assert abs((np.abs(m - 0.1) < 0.098).mean() - 0.95) < 0.005
    # The wrong answer fails: twice the data narrows by sqrt(2) only, four times by 2.
    m2 = rng.normal(0.1, 1, (5_000, 800)).mean(axis=1)
    m4 = rng.normal(0.1, 1, (5_000, 1600)).mean(axis=1)
    assert abs(m.std() / m2.std() - math.sqrt(2)) < 0.05
    assert abs(m.std() / m4.std() - 2) < 0.06


def test_q3():
    p = 0.9 * 0.05 / (0.9 * 0.05 + 0.1 * 0.8)
    assert round(p, 2) == 0.36
    assert abs(0.9 * 0.05 - 0.045) < 1e-12
    assert abs(0.1 * 0.8 - 0.08) < 1e-12
    # Limits: all ideas bad gives a dud with certainty; all good gives none.
    assert 1 * 0.05 / (1 * 0.05 + 0) == 1
    rng = np.random.default_rng(3)
    good = rng.random(2_000_000) < 0.1
    passed = np.where(good, rng.random(2_000_000) < 0.8, rng.random(2_000_000) < 0.05)
    assert abs((~good & passed).sum() / passed.sum() - p) < 0.003


def test_q4():
    rng = np.random.default_rng(4)
    x = rng.normal(size=(1_000_000, 5))
    assert abs(x.var(axis=1, ddof=1).mean() - 1) < 0.003
    assert abs(x.var(axis=1).mean() - 0.8) < 0.003
    # Non-normal data: the bias formula does not depend on the shape.
    y = rng.exponential(size=(1_000_000, 5))
    assert abs(y.var(axis=1, ddof=1).mean() - 1) < 0.01


def test_q5():
    assert round(1 - 0.95**20, 2) == 0.64
    assert round(0.05 / 20, 4) == 0.0025
    sidak = 1 - 0.95 ** (1 / 20)
    assert round(sidak, 5) == 0.00256
    assert abs(1 - (1 - sidak) ** 20 - 0.05) < 1e-12
    assert round(1 - (1 - 0.0025) ** 20, 3) == 0.049


def test_q6():
    assert 1000 / 2**5 == 31.25
    rng = np.random.default_rng(6)
    wins = (rng.random((200_000, 5)) < 0.5).all(axis=1).mean() * 1000
    assert abs(wins - 31.25) < 1
    # Lucky after 5 years: next year still 50%.
    assert round(1 - 0.5**5, 3) == 0.969


def test_q7():
    p = 2 * stats.binom.sf(14, 20, 0.5)
    assert round(p, 4) == 0.0414
    assert sum(math.comb(20, k) for k in range(15, 21)) == 21700
    assert 2 * 21700 / 2**20 == p
    # With a different shape, the sign count has the same law.
    rng = np.random.default_rng(7)
    x = rng.standard_cauchy((200_000, 20))
    assert abs(((x > 0).sum(axis=1) >= 15).mean() - p / 2) < 0.002


def test_q8():
    vals = [5, 7, 9, 1, 2, 3]
    obs = 21
    sums = [sum(c) for c in combinations(vals, 3)]
    assert len(sums) == 20
    assert sum(s >= obs for s in sums) == 1
    assert 1 / 20 == 0.05


def test_q9():
    assert round(1.96 / math.sqrt(5), 3) == 0.877
    assert round(stats.t.ppf(0.975, 4), 3) == 2.776
    assert round(2.776 / math.sqrt(5), 3) == 1.241
    assert round(stats.t.ppf(0.975, 29), 2) == 2.05
    rng = np.random.default_rng(9)
    x = rng.normal(size=(500_000, 5))
    t = x.mean(axis=1) / (x.std(axis=1, ddof=1) / math.sqrt(5))
    assert abs((np.abs(t) < 1.96).mean() - 0.878) < 0.003
    assert abs((np.abs(t) < 2.776).mean() - 0.95) < 0.002


def test_q10():
    assert round(1 / math.sqrt(103), 3) == 0.099
    assert round((1 - 0.25) / math.sqrt(103), 3) == 0.074
    z = np.arctanh(0.5)
    assert round(z, 3) == 0.549
    assert 1 / math.sqrt(100) == 0.1
    lo, hi = np.tanh(z - 0.196), np.tanh(z + 0.196)
    assert round(lo, 2) == 0.34 and round(hi, 2) == 0.63
    rng = np.random.default_rng(10)
    n = 103
    a = rng.standard_normal((50_000, n))
    b = 0.5 * a + math.sqrt(0.75) * rng.standard_normal((50_000, n))
    ax = a - a.mean(axis=1, keepdims=True)
    bx = b - b.mean(axis=1, keepdims=True)
    r = (ax * bx).sum(axis=1) / np.sqrt((ax**2).sum(axis=1) * (bx**2).sum(axis=1))
    zr = np.arctanh(r)
    assert abs(zr.std() - 0.1) < 0.002
    assert abs((np.abs(zr - z) < 0.196).mean() - 0.95) < 0.005


def test_q11():
    exact = 1 - 0.05 ** (1 / 100)
    assert round(exact, 4) == 0.0295
    assert 3 / 100 == 0.03
    assert abs(-math.log(0.05) - 2.996) < 0.001
    # Failing 0 of 100 at the bound has chance 5%.
    assert abs((1 - exact) ** 100 - 0.05) < 1e-12


def test_q12():
    for sr, years in ((0.5, 16), (1, 4), (2, 1)):
        assert sr * math.sqrt(years) == 2
    rng = np.random.default_rng(12)
    t = 16 * 252
    mu = 0.5 / math.sqrt(252)
    x = rng.normal(mu, 1, (2000, t))
    m = x.mean(axis=1) / x.std(axis=1, ddof=1) * math.sqrt(252)
    assert abs(m.std() - 1 / math.sqrt(16)) < 0.01
    assert abs(m.mean() / m.std() - 2) < 0.1


def test_q13():
    z = 1.96 + 0.84
    assert abs(z**2 - 7.84) < 1e-9
    n = z**2 * (1 / 0.05) ** 2
    assert round(n) == 3136
    assert round(n / 252, 1) == 12.4
    assert round(z**2 * (1 / 0.1) ** 2) == 784
    assert round(784 / 252, 1) == 3.1
    rng = np.random.default_rng(13)
    m = rng.normal(0.05, 1 / math.sqrt(3136), 500_000)
    assert abs((np.abs(m * math.sqrt(3136)) > 1.96).mean() - 0.8) < 0.003


def test_q14():
    p = [0.001, 0.008, 0.012, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    assert sum(x <= 0.05 / 10 for x in p) == 1
    bh = max(k for k in range(1, 11) if p[k - 1] <= k * 0.05 / 10)
    assert bh == 3
    # Holm also stops after the first.
    assert p[0] <= 0.05 / 10 and p[1] > 0.05 / 9


def test_q15():
    assert 8 / 4 == 2 and 4 / 2 == 2
    rng = np.random.default_rng(15)
    x = rng.gamma(2, 2, (20_000, 50))
    th = x.var(axis=1, ddof=1) / x.mean(axis=1)
    kk = x.mean(axis=1) / th
    # Against the MLE, which is sharper for the shape in a modest sample.
    fit = np.array([stats.gamma.fit(s, floc=0)[0] for s in x[:300]])
    assert fit.var() < kk[:300].var()
    assert abs(th.mean() - 2) < 0.1


def test_q16():
    n, xb = 5, 2
    assert 1 / xb == 0.5
    assert (n - 1) / (n * xb) == 0.4
    rng = np.random.default_rng(16)
    x = rng.exponential(1 / 3, (1_000_000, 5))
    est = 1 / x.mean(axis=1)
    assert abs(est.mean() - 3 * 5 / 4) < 0.01
    assert abs((4 / 5 * est).mean() - 3) < 0.01


def test_q17():
    lam = 2
    a = lam * math.exp(-2 * lam)
    b = math.exp(-lam) * (1 - math.exp(-lam))
    assert round(a, 4) == 0.0366
    assert round(b, 4) == 0.1170
    assert round(b / a, 2) == 3.19
    n = 200
    rng = np.random.default_rng(17)
    x = rng.poisson(lam, (200_000, n))
    assert abs(np.exp(-x.mean(axis=1)).var() * n / a - 1) < 0.04
    assert abs((x == 0).mean(axis=1).var() * n / b - 1) < 0.02
    assert abs(x.mean(axis=1).var() * n / lam - 1) < 0.02
    # Misspecified: overdispersed counts, e^-mean is off and the fraction is right.
    y = rng.negative_binomial(1, 1 / 3, (50_000, n))
    assert abs(y.mean() - 2) < 0.01
    assert abs((y == 0).mean() - 1 / 3) < 0.002
    assert abs(np.exp(-y.mean(axis=1)).mean() - math.exp(-2)) < 0.01
    assert 1 / 3 > 2 * math.exp(-2)


def test_q18():
    assert round(1 - 1 / math.e, 3) == 0.632
    n = 1000
    assert abs(1 - (1 - 1 / n) ** n - 0.632) < 0.001
    rng = np.random.default_rng(18)
    distinct = [len(set(rng.integers(0, n, n).tolist())) / n for _ in range(300)]
    assert abs(np.mean(distinct) - 0.632) < 0.003
    # Bootstrap standard error of a mean matches the formula on a fixed sample.
    x = rng.normal(size=500)
    boots = rng.choice(x, (20_000, 500)).mean(axis=1)
    assert abs(boots.std() - x.std() / math.sqrt(500)) < 0.002


def test_q19():
    rho = 0.5
    assert (1 + rho) / (1 - rho) == 3
    rng = np.random.default_rng(19)
    n = 2000
    reps = 4000
    e = rng.standard_normal((reps, n + 100))
    x = np.zeros_like(e)
    for t in range(1, n + 100):
        x[:, t] = rho * x[:, t - 1] + e[:, t]
    x = x[:, 100:]
    true = x.mean(axis=1).var()
    naive = (x.var(axis=1) / n).mean()
    assert abs(true / naive - 3) < 0.2
    # Bootstraps on one path: plain gets the naive answer, blocks get close to the true one.
    path = x[0]
    plain = rng.choice(path, (4000, n)).mean(axis=1).var()
    assert abs(plain / (path.var() / n) - 1) < 0.1
    b = 50
    starts = rng.integers(0, n - b, (4000, n // b))
    idx = (starts[..., None] + np.arange(b)).reshape(4000, -1)
    block = path[idx].mean(axis=1).var()
    assert block / plain > 2


def test_q20():
    n = 1000
    assert round(math.sqrt(6 / n), 4) == 0.0775
    assert round(math.sqrt(24 / n), 3) == 0.155
    jb = n / 6 * (0.25 + 9 / 4)
    assert round(jb, 1) == 416.7
    assert round(stats.chi2.ppf(0.95, 2), 2) == 5.99
    rng = np.random.default_rng(20)
    x = rng.normal(size=(20_000, 1000))
    s, k = stats.skew(x, axis=1), stats.kurtosis(x, axis=1)
    assert abs(s.std() - 0.0775) < 0.003
    assert abs(k.std() - 0.155) < 0.01
    # Stochastic volatility with normal shocks fails the test too.
    vol = np.exp(rng.normal(size=(2000, 1000)) * 0.5)
    y = vol * rng.normal(size=(2000, 1000))
    jby = 1000 / 6 * (stats.skew(y, axis=1) ** 2 + stats.kurtosis(y, axis=1) ** 2 / 4)
    assert (jby > 5.99).mean() > 0.99


def test_q21():
    p = N.cdf(-5)
    assert round(p * 1e7, 2) == 2.87
    years = 1 / p / 252
    assert 13_500 < years < 14_000
    q = stats.t.cdf(-5 * math.sqrt(3), 3)
    assert round(q, 4) == 0.0016
    assert round(1 / q / 252, 1) == 2.5
    rng = np.random.default_rng(21)
    x = rng.standard_t(3, 4_000_000) / math.sqrt(3)
    assert abs((x < -5).mean() - q) < 0.0001


def test_q22():
    o = np.array([30, 18, 20, 22, 16, 14])
    assert o.sum() == 120
    chi = ((o - 20) ** 2 / 20).sum()
    assert chi == 8
    assert round(stats.chi2.sf(8, 5), 3) == 0.156
    z = (30 - 20) / math.sqrt(120 * (1 / 6) * (5 / 6))
    assert round(z, 2) == 2.45
    assert round(2 * N.sf(z), 3) == 0.014
    # After choosing the largest of 6 faces, multiply by 6.
    assert round(6 * 2 * N.sf(z), 2) == 0.09


def test_q23():
    n = 100
    assert 1 + (n - 1) / 2 == 50.5
    sd = math.sqrt(n - 1) / 2
    assert round(sd, 2) == 4.97
    assert round((30 - 50.5) / sd, 1) == -4.1
    assert round((65 - 50.5) / sd, 1) == 2.9
    rng = np.random.default_rng(23)
    x = rng.integers(0, 2, (300_000, n))
    runs = 1 + (x[:, 1:] != x[:, :-1]).sum(axis=1)
    assert abs(runs.mean() - 50.5) < 0.05
    assert abs(runs.std() - sd) < 0.03


def test_q24():
    n = 100
    se_u = math.sqrt(2 * 100 / n)
    se_p = math.sqrt(2 * 100 * (1 - 0.9) / n)
    assert round(se_u, 2) == 1.41
    assert round(se_p, 2) == 0.45
    assert round(1 / se_u, 2) == 0.71
    assert round(1 / se_p, 2) == 2.24
    assert round(se_u / se_p, 2) == 3.16
    rng = np.random.default_rng(24)
    z = rng.standard_normal((200_000, n))
    a = math.sqrt(0.9) * z + math.sqrt(0.1) * rng.standard_normal((200_000, n))
    b = math.sqrt(0.9) * z + math.sqrt(0.1) * rng.standard_normal((200_000, n))
    assert abs(((a - b) * 10).mean(axis=1).std() - se_p) < 0.005


def test_q25():
    z = 3 / math.sqrt(2)
    assert round(z, 2) == 2.12
    assert round(2 * N.sf(z), 3) == 0.034
    assert 0 + 1.96 > 3 - 1.96
    # Overlap occurs when the gap is below 3.92 se; significance needs 2.77 se.
    assert round(1.96 * 2, 2) == 3.92
    assert round(1.96 * math.sqrt(2), 2) == 2.77
    # At the boundary of non-overlap, the true level.
    assert round(2 * N.sf(3.92 / math.sqrt(2)), 4) == 0.0056
    # The general rule: the gap between the two thresholds, by a factor of at most sqrt(2).
    grid = np.linspace(0.01, 100, 20_000)
    factor = (1 + grid) / np.sqrt(1 + grid**2)
    assert (factor > 1).all() and (factor <= math.sqrt(2) + 1e-12).all()
    assert abs(factor[np.abs(grid - 1).argmin()] - math.sqrt(2)) < 1e-6
    # Unequal errors, by simulating the estimates: gap 5 with errors 1 and 2 overlaps and is significant.
    assert 5 < 1.96 * (1 + 2) and 5 > 1.96 * math.sqrt(1 + 4)
    rng = np.random.default_rng(25)
    a = rng.normal(0, 1, 2_000_000)
    b = rng.normal(0, 2, 2_000_000)
    assert abs((np.abs(a - b) > 1.96 * math.sqrt(5)).mean() - 0.05) < 0.001
    assert abs((np.abs(a - b) > 1.96 * 3).mean() - 2 * N.sf(1.96 * 3 / math.sqrt(5))) < 0.001


def test_q26():
    x = np.arange(1, 11, dtype=float)
    y = x.copy()
    y[-1] = 100
    r = np.corrcoef(x, y)[0, 1]
    assert round(r, 2) == 0.59
    assert round(stats.spearmanr(x, y)[0], 6) == 1
    # Dropping the point gives a Pearson value of 1 too.
    assert abs(np.corrcoef(x[:-1], y[:-1])[0, 1] - 1) < 1e-12


def test_q27():
    n = 10

    def mse(c):
        m = n - 1
        return (2 * m + m**2) / c**2 - 2 * m / c + 1

    assert round(mse(9), 4) == 0.2222
    assert round(mse(10), 2) == 0.19
    assert round(mse(11), 4) == 0.1818
    g = np.linspace(5, 20, 15001)
    assert abs(g[mse(g).argmin()] - (n + 1)) < 0.002
    rng = np.random.default_rng(27)
    x = rng.normal(size=(1_000_000, n))
    ss = ((x - x.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    assert abs(((ss / 11 - 1) ** 2).mean() - 2 / 11) < 0.001
    assert abs((ss / 11).mean() - 9 / 11) < 0.001
    # S/11 is closer than S/9 only above the point midway in 1/c, and only about a third of the time.
    assert round(2 / (1 / 11 + 1 / 9), 6) == 9.9
    assert round(stats.chi2.sf(9.9, 9), 2) == 0.36
    closer = np.abs(ss / 11 - 1) < np.abs(ss / 9 - 1)
    assert abs(closer.mean() - stats.chi2.sf(9.9, 9)) < 0.002
    assert ss[closer].min() > 9.9 and ss[~closer].max() <= 9.9
    # It still wins on squared error, through the large samples.
    assert ((ss / 11 - 1) ** 2).mean() < ((ss / 9 - 1) ** 2).mean()
    # Heavy tails shift the best divisor upward: at Laplace it is larger.
    y = rng.laplace(scale=math.sqrt(0.5), size=(1_000_000, n))
    sy = ((y - y.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    best = (sy**2).mean() / sy.mean()
    assert best > 12


def test_q28():
    need = (2 * N.isf(0.05)) ** 2
    assert round(need, 2) == 10.82
    assert N.sf(math.sqrt(11) / 2) < 0.05 < N.sf(math.sqrt(10) / 2)
    rng = np.random.default_rng(28)
    m0 = rng.normal(0, 1, (500_000, 11)).mean(axis=1)
    m1 = rng.normal(1, 1, (500_000, 11)).mean(axis=1)
    assert abs((m0 > 0.5).mean() - N.sf(math.sqrt(11) / 2)) < 0.001
    assert abs((m1 < 0.5).mean() - N.sf(math.sqrt(11) / 2)) < 0.001
    assert round(N.sf(math.sqrt(11) / 2), 3) == 0.049


def test_q29():
    rng = np.random.default_rng(29)
    z = rng.standard_normal((400_000, 10))
    s = z.cumsum(axis=1) / np.sqrt(np.arange(1, 11))
    any196 = (np.abs(s) > 1.96).any(axis=1).mean()
    assert round(any196, 2) == 0.19
    p256 = (np.abs(s) > 2.56).any(axis=1).mean()
    assert abs(p256 - 0.05) < 0.003
    assert round(2 * N.sf(2.56), 3) == 0.010
    # Five looks.
    five = (np.abs(s[:, 1::2]) > 1.96).any(axis=1).mean()
    assert round(five, 2) == 0.14
    # No limit: it creeps towards 1. By 2000 looks it is well above a third.
    w = rng.standard_normal((3000, 2000)).cumsum(axis=1) / np.sqrt(np.arange(1, 2001))
    assert (np.abs(w) > 1.96).any(axis=1).mean() > 0.4


def test_q30():
    n = 1000
    assert abs(1 - (1 - 1 / n) ** n - 0.632) < 0.001
    rng = np.random.default_rng(30)
    x = rng.random(n)
    m = x.max()
    boot = rng.choice(x, (20_000, n)).max(axis=1)
    assert abs((boot == m).mean() - 0.632) < 0.01
    # True law: n (theta - max) is exponential with mean theta; no atom.
    t = n * (1 - rng.random((100_000, n)).max(axis=1))
    assert abs(t.mean() - 1) < 0.02
    assert abs((t < 0.5).mean() - (1 - math.exp(-0.5))) < 0.005
    # Exact interval: P(max / theta <= u) = u^n.
    assert round(0.05 ** (1 / 1000), 4) == 0.9970


def test_q31():
    s, n = 0.3, 120
    normal = math.sqrt((1 + s * s / 2) / n)
    assert round(normal, 4) == 0.0933
    fat = math.sqrt((1 + 1 * s + 5 / 4 * s * s) / n)
    assert round(fat, 4) == 0.1085
    assert round(fat / normal, 2) == 1.16
    rng = np.random.default_rng(31)
    x = rng.normal(s, 1, (400_000, n))
    sr = x.mean(axis=1) / x.std(axis=1, ddof=1)
    assert abs(sr.std() / normal - 1) < 0.03
    # A two-point mixture with skew and fat tails: formula vs simulation.
    big = rng.random((200_000, n)) < 0.02
    y = np.where(big, -6 + rng.normal(size=(200_000, n)) * 2, rng.normal(0.3, 1, (200_000, n)))
    g3, g4 = stats.skew(y.ravel()), stats.kurtosis(y.ravel(), fisher=False)
    mu, sd = y.mean(), y.std()
    s2 = mu / sd
    sim = (y.mean(axis=1) / y.std(axis=1, ddof=1)).std()
    form = math.sqrt((1 - g3 * s2 + (g4 - 1) / 4 * s2 * s2) / n)
    assert abs(sim / form - 1) < 0.05


def test_q32():
    rho, s = 0.2, 0.3
    assert round(s * math.sqrt(12), 2) == 1.04
    v = 12 + 2 * sum((12 - k) * rho**k for k in range(1, 12))
    a = s * 12 / math.sqrt(v)
    assert round(v, 1) == 17.4
    assert round(a, 2) == 0.86
    vn = 12 + 2 * sum((12 - k) * (-rho) ** k for k in range(1, 12))
    an = s * 12 / math.sqrt(vn)
    assert round(an, 2) == 1.25
    rng = np.random.default_rng(32)
    n, yrs = 12 * 100_000, 12
    e = rng.standard_normal(n)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = rho * x[t - 1] + e[t]
    x = x / x.std() + s
    y = x[: n // yrs * yrs].reshape(-1, yrs).sum(axis=1)
    assert abs(y.mean() / y.std() - a) < 0.015


def test_q33():
    t = 5
    assert round(math.sqrt(2 * (1 - 0.8) / t), 3) == 0.283
    assert round(math.sqrt(2 / t), 3) == 0.632
    assert round(0.632 / 0.283, 2) == 2.23
    rng = np.random.default_rng(33)
    d = 252 * t
    z = rng.standard_normal((30_000, d))
    a = math.sqrt(0.8) * z + math.sqrt(0.2) * rng.standard_normal((30_000, d))
    b = math.sqrt(0.8) * z + math.sqrt(0.2) * rng.standard_normal((30_000, d))
    mu = 1 / math.sqrt(252)
    sa = (a + mu).mean(axis=1) / (a + mu).std(axis=1) * math.sqrt(252)
    sb = (b + mu).mean(axis=1) / (b + mu).std(axis=1) * math.sqrt(252)
    assert abs((sa - sb).std() - 0.283) < 0.006
    assert (sa - sb > 0.283).mean() > 0.1
    # Both wrong formulas overstate the error; the one-sample formula is right only at correlation 1/2.
    assert round(1 / math.sqrt(t), 3) == 0.447
    assert (sa - sb).std() < 1 / math.sqrt(t) < math.sqrt(2 / t)
    assert abs(math.sqrt(2 * (1 - 0.5) / t) - 1 / math.sqrt(t)) < 1e-12


def test_q34():
    p, n = 0.01, 1000
    q = N.ppf(p)
    assert round(q, 3) == -2.326
    f = N.pdf(q)
    assert round(f, 4) == 0.0267
    se = math.sqrt(p * (1 - p) / n) / f
    assert round(se, 3) == 0.118
    se2 = 2.326 / math.sqrt(2 * n)
    assert round(se2, 3) == 0.052
    assert round(se / se2, 2) == 2.27
    rng = np.random.default_rng(34)
    x = rng.standard_normal((40_000, n))
    assert abs(np.quantile(x, 0.01, axis=1).std() / se - 1) < 0.03
    assert abs((2.326 * x.std(axis=1)).std() / se2 - 1) < 0.03
    # On fat tails the normal rule is biased and the sample quantile is not.
    y = rng.standard_t(3, (5000, n)) / math.sqrt(3)
    true = stats.t.ppf(0.01, 3) / math.sqrt(3)
    assert abs(np.quantile(y, 0.01, axis=1).mean() - true) < 0.05
    assert abs(-2.326 * y.std(axis=1).mean() - true) > 0.3


def test_q35():
    s, n = 2.0, 101
    a = s / math.sqrt(2 * n)
    b = s / 2 * math.sqrt(5 / n)
    assert round(a, 3) == 0.141
    assert round(b, 3) == 0.222
    assert round(b / a, 2) == 1.58
    assert abs(b / a - math.sqrt(5 / 2)) < 1e-12
    rng = np.random.default_rng(35)
    x = rng.laplace(scale=2 / math.sqrt(2), size=(200_000, n))
    assert abs(x.std(axis=1, ddof=1).std() / b - 1) < 0.07
    z = rng.normal(0, 2, (200_000, n))
    assert abs(z.std(axis=1, ddof=1).std() / a - 1) < 0.02
    # The chi-square 95% interval misses far too often on Laplace data.
    lo, hi = stats.chi2.ppf([0.025, 0.975], n - 1)
    v = x.var(axis=1, ddof=1)
    cover = ((n - 1) * v / hi < 4) & (4 < (n - 1) * v / lo)
    assert cover.mean() < 0.85


def test_q36():
    rho = 0.02 / math.sqrt(0.5 * 0.25)
    assert round(rho, 3) == 0.057
    rng = np.random.default_rng(36)
    n = 40_000_000
    s = rng.standard_normal(n)
    f = rho * s + math.sqrt(1 - rho * rho) * rng.standard_normal(n)
    a = math.sqrt(0.5) * s + math.sqrt(0.5) * rng.standard_normal(n)
    b = math.sqrt(0.25) * f + math.sqrt(0.75) * rng.standard_normal(n)
    assert abs(np.corrcoef(a, b)[0, 1] - 0.02) < 0.0005
    # Limit: no noise leaves the measurement unchanged.
    assert 0.02 / math.sqrt(1) == 0.02


def test_q37():
    t, sig = 10, 20.0
    assert round(sig / math.sqrt(t), 1) == 6.3
    daily = sig / math.sqrt(2 * 252 * t)
    assert round(daily, 2) == 0.28
    monthly = sig / math.sqrt(2 * 12 * t)
    assert round(monthly, 2) == 1.29
    assert round(6.3 / daily, 0) == 22
    rng = np.random.default_rng(37)
    for steps in (120, 2520):
        r = rng.normal(0.05 * t / steps, 0.2 * math.sqrt(t / steps), (20_000, steps))
        ann_mean = r.sum(axis=1) / t
        ann_vol = np.sqrt((r**2).sum(axis=1) / t)
        assert abs(ann_mean.std() - 0.2 / math.sqrt(t)) < 0.002
        assert abs(ann_vol.std() - 0.2 / math.sqrt(2 * steps)) < 0.001


def test_q38():
    d = 10
    rng = np.random.default_rng(38)
    for scale in (0.0, 1.0, 2.0, 5.0):
        theta = np.zeros(d)
        theta[0] = scale * math.sqrt(d)
        x = theta + rng.standard_normal((400_000, d))
        js = x * (1 - (d - 2) / (x**2).sum(axis=1, keepdims=True))
        risk_js = ((js - theta) ** 2).sum(axis=1).mean()
        risk_x = ((x - theta) ** 2).sum(axis=1).mean()
        assert risk_js < risk_x
        # Stein's formula for the risk.
        form = d - (d - 2) ** 2 * (1 / (x**2).sum(axis=1)).mean()
        assert abs(form - risk_js) < 0.02
        if scale == 0:
            assert abs(risk_js - 2) < 0.02
    # d = 2: the factor vanishes and there is no gain.
    assert 2 - 2 == 0
    # Three dimensions at zero: risk is 2 of 3.
    y = rng.standard_normal((400_000, 3))
    j3 = y * (1 - 1 / (y**2).sum(axis=1, keepdims=True))
    assert abs((j3**2).sum(axis=1).mean() - 2) < 0.03


def test_q39():
    from scipy.integrate import quad

    info = quad(lambda z: 4 * z**2 / (1 + z**2) ** 2 / (math.pi * (1 + z**2)), -np.inf, np.inf)[0]
    assert abs(info - 0.5) < 1e-9
    assert round(math.pi**2 / 4, 3) == 2.467
    assert round(8 / math.pi**2, 2) == 0.81
    rng = np.random.default_rng(39)
    n = 301
    x = rng.standard_cauchy((3000, n))
    med = np.median(x, axis=1)
    assert abs(med.var() * n / (math.pi**2 / 4) - 1) < 0.1
    # One Newton sequence from the median finds the MLE; variance 2 / n.
    th = med.copy()
    for _ in range(30):
        z = x - th[:, None]
        grad = (2 * z / (1 + z * z)).sum(axis=1)
        th = th + grad / (n / 2)
    assert abs(th.var() * n / 2 - 1) < 0.1
    assert th.var() < med.var()
    # The mean is no better than one draw.
    m = x.mean(axis=1)
    assert abs(np.median(np.abs(m)) - 1) < 0.1


def test_q40():
    rng = np.random.default_rng(40)
    m, m0, alpha = 20, 15, 0.1
    fdr = []
    for _ in range(40_000):
        p = np.empty(m)
        p[:m0] = rng.random(m0)
        p[m0:] = N.sf(rng.normal(3, 1, m - m0))
        order = np.sort(p)
        hits = np.nonzero(order <= (np.arange(1, m + 1)) * alpha / m)[0]
        if hits.size:
            k = hits[-1] + 1
            cut = order[k - 1]
            fdr.append((p[:m0] <= cut).sum() / k)
        else:
            fdr.append(0.0)
    assert abs(np.mean(fdr) - alpha * m0 / m) < 0.002
    # The per-null step of the proof: with others fixed, the chance of rejecting is R alpha / m.
    other = rng.random(m - 1)

    def rejected(pi):
        p = np.append(other, pi)
        s = np.sort(p)
        hits = np.nonzero(s <= (np.arange(1, m + 1)) * alpha / m)[0]
        if not hits.size:
            return 0, False
        k = hits[-1] + 1
        return k, pi <= s[k - 1]

    r0, _ = rejected(0.0)
    u = rng.random(200_000)
    flags = [rejected(v)[1] for v in u[:4000]]
    assert abs(np.mean(flags) - r0 * alpha / m) < 0.012
