"""Risk, Validation and Regulation. Closed forms checked by simulation, by a second route, and at the limits."""
from math import exp, log, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize
from scipy.stats import binom, chi2, norm, t
from scipy.stats import multivariate_normal as mvn

N, n, Q = norm.cdf, norm.pdf, norm.ppf
Z99, Z975 = Q(0.99), Q(0.975)
NONNUMERIC = {23: "A validation plan: the answer leads with the recommended order and the grounds for refusal; the steps carry no number."}


def lr_uc(x, m, p):
    ph = x / m
    a = (m - x) * log(1 - p) + (x * log(p) if x else 0)
    b = (m - x) * log(1 - ph) + (x * log(ph) if x else 0) if x else 0
    return -2 * (a - b)


def lr_ind(a, b, c, d):
    p01, p11, pi = b / (a + b), d / (c + d), (b + d) / (a + b + c + d)
    ll0 = (a + c) * log(1 - pi) + (b + d) * log(pi)
    ll1 = a * log(1 - p01) + b * log(p01) + c * log(1 - p11) + d * log(p11)
    return -2 * (ll0 - ll1), p01, p11, pi


def test_q1():
    assert round(100 * 0.01 * Z99, 2) == 2.33 and round(100 * 0.01 * Z99 * sqrt(10), 2) == 7.36
    x = np.random.default_rng(1).standard_normal(4_000_000)
    assert abs(-np.quantile(x, 0.01) - Z99) < 5e-3


def test_q2():
    s = sqrt(0.25 + 0.2025 + 2 * 0.8 * 0.5 * 0.45)
    assert round(s, 3) == 0.901 and round(s * Z99, 2) == 2.10 and round(0.95 * Z99, 2) == 2.21
    assert round(0.95 * Z99 - s * Z99, 2) == 0.11
    # Perfect correlation removes the saving.
    assert abs(sqrt(0.25 + 0.2025 + 2 * 0.5 * 0.45) - 0.95) < 1e-12


def test_q3():
    assert round(n(Z975) / 0.025, 3) == 2.338 and round(n(Z99) / 0.01, 3) == 2.665 and round(Z99, 3) == 2.326
    x = np.random.default_rng(2).standard_normal(4_000_000)
    assert abs(-x[x < -Z975].mean() - n(Z975) / 0.025) < 5e-3


def test_q4():
    assert (8 + 6 + 0.5 * 5) / 2.5 == 6.6 and (5 + 6) / 2 == 5.5
    assert round(0.01 * 250, 1) == 2.5


def test_q5():
    addon = {5: 0.40, 6: 0.50, 7: 0.65, 8: 0.75, 9: 0.85}
    assert 3 + addon[7] == 3.65


def test_q6():
    assert round(log(0.5) / log(0.94), 1) == 11.2
    v = sqrt(0.94 * 1e-4 + 0.06 * 4e-4)
    assert round(v * 100, 3) == 1.086 and round(0.94 * 1 + 0.06 * 2, 2) == 1.06
    # A return equal to the old volatility leaves the estimate where it was.
    assert abs(sqrt(0.94 * 1e-4 + 0.06 * 1e-4) - 0.01) < 1e-15


def test_q7():
    assert round(sqrt(0.18**2 + 0.04), 3) == 0.269 and round(0.18**2 / (0.18**2 + 0.04), 3) == 0.448
    assert round(sqrt(0.18**2 + 0.04 / 100), 3) == 0.181
    # By simulation.
    rng = np.random.default_rng(3)
    m = rng.standard_normal((200_000, 1)) * 0.15
    e = rng.standard_normal((200_000, 100)) * 0.2
    assert abs((1.2 * m + e).mean(axis=1).std() - sqrt(0.18**2 + 0.04 / 100)) < 1e-3


def mdd(path):
    peak, worst = path[0], 0.0
    for x in path:
        peak = max(peak, x)
        worst = max(worst, 1 - x / peak)
    return worst


def test_q8():
    assert mdd([100, 120, 90, 130, 65, 80]) == 0.5
    # Brute force on random paths agrees with the one-pass algorithm.
    rng = np.random.default_rng(4)
    for _ in range(50):
        p = list(np.exp(rng.standard_normal(30).cumsum()))
        b = max(1 - p[j] / p[i] for i in range(30) for j in range(i, 30))
        assert abs(mdd(p) - b) < 1e-12
    # A rising path has no drawdown.
    assert mdd([1, 2, 3]) == 0


def test_q9():
    mv = Z99 * 2
    assert round(mv, 2) == 4.65 and round(0.5 * mv, 2) == 2.33
    assert round(-0.5 * mv + 0.5 * 0.02 * mv**2, 2) == -2.11
    # Gamma share, and a short option is hurt in the opposite sense.
    assert round(0.5 * 0.02 * mv**2 / (0.5 * mv), 1) == 0.1
    assert -0.5 * mv - 0.5 * 0.02 * mv**2 < -0.5 * mv


def test_q10():
    assert round(50_000 * 6 * Z99, -3) == 698_000 and round(50_000 * 6 * 2.326) == 697_800


def test_q11():
    assert round(1 - 0.96**2, 4) == 0.0784
    assert round(0.04 * 100 / 0.05, 6) == 80
    es2 = (0.0016 * 200 + (0.05 - 0.0016) * 100) / 0.05
    assert round(es2, 1) == 103.2 and es2 < 160
    # Empirical check.
    rng = np.random.default_rng(5)
    a, b = rng.random(4_000_000) < 0.04, rng.random(4_000_000) < 0.04
    assert np.quantile(100.0 * a, 0.95) == 0 and np.quantile(100.0 * a + 100.0 * b, 0.95) == 100


def test_q12():
    assert round(lr_uc(7, 250, 0.01), 2) == 5.50 and round(chi2.ppf(0.95, 1), 2) == 3.84
    assert round(1 - chi2.cdf(lr_uc(7, 250, 0.01), 1), 3) == 0.019
    assert round(1 - binom.cdf(6, 250, 0.01), 4) == 0.0137
    assert round(lr_uc(4, 250, 0.01), 2) == 0.77
    assert round(lr_uc(0, 250, 0.01), 2) == 5.03 and abs(lr_uc(0, 250, 0.01) + 500 * log(0.99)) < 1e-12
    # An exact hit on the rate has a zero statistic.
    assert abs(lr_uc(5, 500, 0.01)) < 1e-9


def test_q13():
    lr, p01, p11, pi = lr_ind(238, 5, 4, 3)
    assert round(p01 * 100, 2) == 2.06 and round(p11 * 100, 1) == 42.9 and pi == 8 / 250
    assert round(lr, 1) == 12.5 and round(1 - chi2.cdf(lr, 1), 4) == 0.0004
    # Rates equal in both states give a zero statistic.
    assert abs(lr_ind(99 * 3, 3, 99, 1)[0]) < 1e-9


def test_q14():
    def fac(m, r):
        return m + 2 * sum((m - k) * r**k for k in range(1, m))

    assert round(fac(10, 0.2), 3) == 14.375 and round(sqrt(fac(10, 0.2)), 2) == 3.79
    assert round(sqrt(fac(10, 0.2)) / sqrt(10), 2) == 1.20
    assert fac(10, 0) == 10 and fac(10, -0.2) < 10
    # Simulated AR(1).
    rng = np.random.default_rng(6)
    e = rng.standard_normal((400_000, 10))
    x = np.empty_like(e)
    x[:, 0] = e[:, 0]
    for i in range(1, 10):
        x[:, i] = 0.2 * x[:, i - 1] + sqrt(1 - 0.04) * e[:, i]
    assert abs(x.sum(axis=1).std() - sqrt(fac(10, 0.2))) < 0.02


def test_q15():
    nu, q = 4, t.ppf(0.01, 4)
    assert round(q, 3) == -3.747
    sc = sqrt((nu - 2) / nu)
    assert round(-q * sc, 2) == 2.65
    es = t.pdf(q, nu) / 0.01 * (nu + q * q) / (nu - 1) * sc
    assert round(es, 2) == 3.69
    # Second route, by integrating the tail.
    i = quad(lambda x: x * t.pdf(x, nu), -np.inf, q)[0] / 0.01
    assert abs(-i * sc - es) < 1e-7
    assert round(-q * sc / Z99 - 1, 2) == 0.14 and round(es / (n(Z99) / 0.01) - 1, 2) == 0.39


def test_q16():
    se = sqrt(0.01 * 0.99 / 1e4) / n(Z99)
    assert round(se, 4) == 0.0373 and round(se / Z99, 3) == 0.016
    assert round((sqrt(0.01 * 0.99) / n(Z99) / (0.005 * Z99)) ** 2, -3) == 103_000
    x = np.random.default_rng(7).standard_normal((1500, 10_000))
    est = -np.quantile(x, 0.01, axis=1)
    assert abs(est.std() - se) < 0.003 and abs(est.mean() - Z99) < 0.005


def test_q17():
    s = sqrt(0.25 + 0.2025 + 2 * 0.8 * 0.5 * 0.45)
    c1, c2 = (0.25 + 0.18) / s * Z99, (0.2025 + 0.18) / s * Z99
    assert round(c1, 2) == 1.11 and round(c2, 3) == 0.987 and round(c1 + c2, 3) == 2.097
    v = lambda a, b: sqrt(a * a + b * b + 2 * 0.8 * a * b) * Z99  # noqa: E731
    assert abs((v(0.505, 0.45) - v(0.5, 0.45)) - 0.01 * c1) < 1e-4
    assert round(0.01 * c1, 4) == 0.0111


def test_q18():
    assert 50 * -0.20 + 0.04 * 100 - 0.03 * 150 == -10.5
    assert round((15 - 10.5) / 50, 2) == 0.09


def test_q19():
    bb = np.array([[1.2, 0.3], [0.8, -0.2], [1.0, 0.5]])
    f = np.array([[0.04, 0.006], [0.006, 0.01]])
    d = np.diag([0.03, 0.02, 0.04])
    w = np.array([0.5, 0.3, 0.2])
    b = bb.T @ w
    assert [round(float(x), 2) for x in b] == [1.04, 0.19]
    vf, vi = b @ f @ b, w @ d @ w
    assert round(float(vf), 4) == 0.0460 and round(float(vi), 4) == 0.0109
    assert round(float(sqrt(vf + vi)), 3) == 0.239 and round(float(vf / (vf + vi)), 2) == 0.81
    # The full covariance gives the same number.
    assert abs(w @ (bb @ f @ bb.T + d) @ w - vf - vi) < 1e-14


def test_q20():
    a, b = [0.2 * sqrt(2 - 2 * r) * Z99 for r in (0.9, 0.5)]
    assert round(a, 3) == 0.208 and round(b, 3) == 0.465 and round(b / a, 1) == 2.2
    # Correlation one has no risk.
    assert 0.2 * sqrt(2 - 2 * 1.0) == 0
    # VaR falls as correlation rises, so the position is long correlation.
    assert a < b and 0.2 * sqrt(2 - 2 * 0.95) * Z99 < a


def test_q21():
    # Exact quantile and tail of the mixture.
    q = -Q(0.005 / 0.995)
    assert round(q, 2) == 2.57
    es = (0.005 * 50 + 0.995 * n(q)) / 0.01
    assert round(es, 1) == 26.4
    # Simulation of the mixture.
    rng = np.random.default_rng(8)
    m = 8_000_000
    x = rng.standard_normal(m)
    x[rng.random(m) < 0.005] = 50.0
    x = np.where(x == 50.0, 50.0, -x)
    v = np.quantile(x, 0.99)
    assert abs(v - q) < 0.02 and abs(x[x >= v].mean() - es) < 0.4


def test_q22():
    var1 = 10 * 0.02 * Z99
    assert round(var1, 3) == 0.465
    fac = sum(((6 - k) / 5) ** 2 for k in range(1, 6))
    assert round(fac, 1) == 2.2 and abs(fac - 6 * 11 / (6 * 5)) < 1e-12
    assert round(sqrt(fac), 3) == 1.483 and round(var1 * sqrt(fac), 2) == 0.69
    assert round(var1 * sqrt(fac) + 0.02, 2) == 0.71 and round(var1 + 0.02, 3) == 0.485
    # The sure cost: 20 basis points of the amount sold, whichever way it is split.
    assert abs(sum(2 * 0.002 for _ in range(5)) - 10 * 0.002) < 1e-12 and round(10 * 0.002, 3) == 0.02
    # Simulated liquidation.
    rng = np.random.default_rng(9)
    r = rng.standard_normal((2_000_000, 5)) * 0.02
    held = np.array([1, 0.8, 0.6, 0.4, 0.2]) * 10
    assert abs(-np.quantile((r * held).sum(axis=1), 0.01) - var1 * sqrt(fac)) < 3e-3
    # One-day sale: the factor is one.
    assert sqrt(2 * 3 / 6) == 1


def test_q24():
    assert round(binom.cdf(4, 250, 0.01), 3) == 0.892
    assert round(binom.cdf(4, 250, 0.02), 3) == 0.439 and round(1 - binom.cdf(9, 250, 0.02), 3) == 0.030
    assert round(binom.cdf(4, 250, 0.03), 3) == 0.128 and round(1 - binom.cdf(9, 250, 0.03), 3) == 0.221
    x = np.random.default_rng(10).random((100_000, 250)) < 0.02
    assert abs((x.sum(axis=1) <= 4).mean() - binom.cdf(4, 250, 0.02)) < 5e-3


def test_q25():
    assert round(max(12, 3.65 * 10) + max(18, 3.65 * 20), 1) == 109.5
    assert round(3.65 * 10, 1) == 36.5 and round(3.65 * 20, 1) == 73.0
    # A big enough yesterday does win the max.
    assert max(40, 3.65 * 10) == 40


def test_q26():
    assert round(1000 * chi2.ppf(0.99, 1)) == 6635
    assert round(Q(0.995), 3) == 2.576 and abs(Q(0.995) ** 2 - chi2.ppf(0.99, 1)) < 1e-9
    assert round((1000 + Z99 * 1000 * sqrt(2)), -1) == 4290
    assert round(1 - (1000 + Z99 * 1000 * sqrt(2)) / (1000 * chi2.ppf(0.99, 1)), 2) == 0.35
    x = np.random.default_rng(11).standard_normal(4_000_000) * 2
    assert abs(np.quantile(250 * x * x, 0.99) - 6635) < 40


def cf(z, s, k):
    return z + (z * z - 1) * s / 6 + (z**3 - 3 * z) * k / 24 - (2 * z**3 - 5 * z) * s * s / 36


def test_q27():
    assert round(cf(-Z99, -0.5, 3), 2) == -3.30
    assert cf(-Z99, 0, 0) == -Z99
    truth = t.ppf(0.01, 6) * sqrt(4 / 6)
    assert round(t.ppf(0.01, 6), 3) == -3.143 and round(truth, 2) == -2.57
    assert round(cf(-Z99, 0, 3), 2) == -3.03
    assert round(-Z99 + 0.70 - 2 * 0.70, 2) == -3.03
    assert round(cf(-Z99, 0, 3) / truth - 1, 2) == 0.18
    assert round(truth - cf(-Z99, 0, 3), 2) == 0.46 and round(Z99 + truth, 2) * -1 == 0.24


def test_q28():
    v, es = Z975, n(Z975) / 0.025

    def mean(s):
        return 1 - s * n(v / s) / (0.025 * es)

    assert abs(mean(1.0)) < 1e-12 and round(mean(1.2), 3) == -1.158
    rng = np.random.default_rng(12)
    x = rng.standard_normal((100_000, 250))
    z0 = (x * (x < -v)).sum(axis=1) / (250 * 0.025 * es) + 1
    cut = np.quantile(z0, 0.05)
    assert abs(z0.mean()) < 5e-3 and round(cut, 1) == -0.7
    x2 = x * 1.2
    z1 = (x2 * (x2 < -v)).sum(axis=1) / (250 * 0.025 * es) + 1
    assert abs(z1.mean() - mean(1.2)) < 5e-3
    assert abs((z1 < cut).mean() - 0.77) < 0.01


def test_q29():
    r = N(-Z99 / 2)
    assert round(r, 3) == 0.122 and round(20 * r, 2) == 2.45
    w = 1 - 0.94**10
    assert round(w, 2) == 0.46
    var = (1 - w) + w * 4
    assert round(var, 2) == 2.38 and round(sqrt(var), 2) == 1.54
    assert round(Z99 * sqrt(var) / 2, 2) == 1.80 and round(N(-1.80), 3) == 0.036
    # Full simulation of the historical window.
    rng = np.random.default_rng(13)
    m = 20000
    old = rng.standard_normal((m, 250))
    new = rng.standard_normal((m, 20)) * 2
    full = np.concatenate([old, new], axis=1)
    breach = np.zeros(m)
    for d in range(20):
        win = full[:, d : d + 250]
        thr = np.sort(win, axis=1)[:, 2]
        breach += new[:, d] < thr
    assert 2.05 < breach.mean() < 2.3
    assert breach.mean() < 20 * r


def test_q30():
    xi, be, u = 0.2, 1, 2
    va = u + be / xi * ((0.01 / 0.05) ** (-xi) - 1)
    es = (va + be - xi * u) / (1 - xi)
    assert round(va, 2) == 3.90 and round(es, 2) == 5.62
    # Direct integration of the tail against the formula.
    surv = lambda x: 0.05 * (1 + xi * (x - u) / be) ** (-1 / xi)  # noqa: E731
    assert abs(surv(va) - 0.01) < 1e-12
    i = quad(surv, va, np.inf)[0] / 0.01
    assert abs(va + i - es) < 1e-6
    # Limit of shape zero.
    assert round(2 + log(5), 2) == 3.61
    assert abs((2 + 1e-7 ** -1 * ((0.2) ** (-1e-7) - 1)) - (2 + log(5))) < 1e-5


def test_q31():
    c = Q(0.01)
    g = mvn(mean=[0, 0], cov=[[1, 0.5], [0.5, 1]]).cdf([c, c])
    assert round(g * 100, 2) == 0.13 and round(0.01**2 * 100, 2) == 0.01
    lam = 2 * t.cdf(-sqrt(5 * 0.5 / 1.5), 5)
    assert round(lam, 3) == 0.253
    rng = np.random.default_rng(14)
    m = 3_000_000
    z = rng.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], m)
    w = np.sqrt(4 / rng.chisquare(4, m))
    x = z * w[:, None]
    q = t.ppf(0.01, 4)
    p = ((x[:, 0] < q) & (x[:, 1] < q)).mean()
    gl, gw = np.polynomial.legendre.leggauss(60)
    chis = chi2.ppf((gl + 1) / 2, 4)
    ex = sum(wi / 2 * mvn(mean=[0, 0], cov=[[1, 0.5], [0.5, 1]]).cdf([q * sqrt(si / 4)] * 2) for si, wi in zip(chis, gw, strict=True))
    assert round(ex * 100, 2) == 0.29 and abs(p - ex) < 1e-4
    # Gaussian conditional falls as the level goes out; the t holds up.
    c2 = Q(1e-4)
    g2 = mvn(mean=[0, 0], cov=[[1, 0.5], [0.5, 1]]).cdf([c2, c2]) / 1e-4
    q2 = t.ppf(1e-3, 4)
    p2 = ((x[:, 0] < q2) & (x[:, 1] < q2)).mean() / 1e-3
    assert g2 < g / 0.01 and p2 > lam * 0.9


def cascade(es, lh=(10, 20, 40, 60, 120), base=10):
    tot = es[0] ** 2
    for j in range(1, 5):
        tot += (es[j] * sqrt((lh[j] - lh[j - 1]) / base)) ** 2
    return sqrt(tot)


def test_q32():
    assert abs(cascade([10, 8, 5, 3, 2]) - 16) < 1e-12
    assert cascade([10, 0, 0, 0, 0]) == 10
    assert abs(cascade([10, 10, 10, 10, 10]) - 10 * sqrt(12)) < 1e-12 and round(10 * sqrt(12), 1) == 34.6
    # The same holds for one factor on a true Brownian motion with a 120-day horizon: scaling is sqrt(LH/T).
    assert abs(sqrt(120 / 10) - sqrt(12)) < 1e-15


def test_q33():
    rng = np.random.default_rng(15)
    x = 100 * np.exp(0.01 * rng.standard_normal(1_000_000).cumsum() * 0.01)
    good = np.diff(x) / ((x[1:] + x[:-1]) / 2)
    bad = np.diff(x) / (x[1:] + x[:-1])
    assert abs(good.std() / bad.std() - 2) < 1e-9
    r = N(-Z99 / 2)
    assert round(r * 250, 1) == 30.6
    # Exact: the fraction is two, whatever the move.
    for a, b in ((100, 101), (100, 150), (3, 900)):
        assert abs(((b - a) / ((a + b) / 2)) / ((b - a) / (a + b)) - 2) < 1e-12


def ead(v, add=10):
    return 1.4 * (max(v, 0) + min(1, 0.05 + 0.95 * exp(v / (2 * 0.95 * add))) * add)


def test_q34():
    assert round(ead(5), 6) == 21
    assert round(0.05 + 0.95 * exp(-20 / 19), 3) == 0.382 and round(ead(-20), 2) == 5.34
    assert abs(ead(-1e6) - 0.7) < 1e-9
    # At V - C = 0 the multiplier is one.
    assert round(ead(0), 6) == 14


def test_q35():
    b = np.array([2.0, -1.0])
    s = np.array([[4.0, 1.0], [1.0, 1.0]])
    x = -10 * s @ b / (b @ s @ b)
    assert [round(float(i), 2) for i in x] == [-5.38, -0.77]
    assert abs(b @ x + 10) < 1e-12
    si = np.linalg.inv(s)
    dist = sqrt(x @ si @ x)
    assert round(dist, 2) == 2.77 and abs(dist - 10 / sqrt(13)) < 1e-12 and round(sqrt(13), 2) == 3.61
    # Numerical optimiser agrees.
    res = minimize(lambda y: y @ si @ y, np.array([-5.0, 0.0]), constraints={"type": "eq", "fun": lambda y: b @ y + 10})
    assert np.abs(res.x - x).max() < 1e-3
    alt = np.array([-5.0, 0.0])
    assert b @ alt == -10 and round(sqrt(alt @ si @ alt), 2) == 2.89 and sqrt(alt @ si @ alt) > dist


def test_q36():
    c = lambda r: np.array([[1, 0.9, r], [0.9, 1, 0.9], [r, 0.9, 1]])  # noqa: E731
    e = np.linalg.eigvalsh(c(-0.5))
    assert round(float(e[0]), 3) == -0.547
    lo, hi = 0.81 - sqrt(0.19 * 0.19), 0.81 + 0.19
    assert round(lo, 2) == 0.62 and round(hi, 2) == 1.0
    assert abs(np.linalg.eigvalsh(c(lo))[0]) < 1e-9 and np.linalg.eigvalsh(c(lo - 0.01))[0] < 0
    # Negative-variance portfolio.
    w = np.linalg.eigh(c(-0.5))[1][:, 0]
    assert w @ c(-0.5) @ w < 0
    # Clip and rescale gives a valid matrix.
    val, vec = np.linalg.eigh(c(-0.5))
    fix = vec @ np.diag(np.maximum(val, 1e-8)) @ vec.T
    dd = np.sqrt(np.diag(fix))
    assert np.linalg.eigvalsh(fix / np.outer(dd, dd))[0] > 0


def test_q37():
    rng = np.random.default_rng(16)
    r = rng.standard_normal((4000, 259))
    cs = np.cumsum(np.concatenate([np.zeros((4000, 1)), r], axis=1), axis=1)
    roll = cs[:, 10:] - cs[:, :-10]
    b = (roll / sqrt(10) < -Z99).sum(axis=1)
    assert abs(b.mean() - 2.5) < 0.15
    assert 9.5 < b.var() < 11.7
    assert round(250 * 0.01 * 0.99, 3) == 2.475
    assert round(250 / (10.6 / 2.475)) == 58
    # With non-overlapping windows the variance returns to binomial.
    nb = (roll[:, ::10] / sqrt(10) < -Z99).sum(axis=1)
    assert abs(nb.var() - 25 * 0.01 * 0.99) < 0.03


def test_q38():
    assert round(lr_uc(9, 500, 0.01), 2) == 2.61 and round(1 - chi2.cdf(lr_uc(9, 500, 0.01), 1), 3) == 0.106
    assert round(1 - binom.cdf(8, 500, 0.01), 3) == 0.067
    lr, p01, p11, _ = lr_ind(485, 5, 5, 4)
    assert round(p01 * 100, 2) == 1.02 and round(p11 * 100, 1) == 44.4 and round(lr, 1) == 21.9
    assert round((1 - chi2.cdf(lr, 1)) * 100, 4) == 0.0003
    assert p11 / p01 > 40


def book(x, dv):
    return 22_500 - 10_000 * x * x - 40_000 * dv


def test_q39():
    assert round(0.5 * 20_000 * 1.5**2) == 22_500
    rng = np.random.default_rng(17)
    m = 3_000_000
    z, e = rng.standard_normal(m), rng.standard_normal(m)
    dv = -0.7 * z + sqrt(0.51) * e
    loss = -book(1.5 * z, dv)
    q = np.quantile(loss, 0.99)
    assert abs(loss.mean()) < 300
    assert abs(q - 174_000) < 1500 and abs(loss[loss >= q].mean() - 223_000) < 2000
    # Exact: gamma alone, by the chi-square quantile.
    assert round(2.25 * 10_000 * chi2.ppf(0.99, 1) - 22_500, -2) == 126_800
    assert round(10_000 * 2.25 * chi2.ppf(0.99, 1)) == 149_285 and round(40_000 * Z99, -3) == 93_000
    assert np.quantile(-book(1.5 * z, 0 * dv), 0.99) < q < 126_800 + 93_100
    # The Student-t case, with one shared scale.
    w = np.sqrt(4 / rng.chisquare(4, m)) * sqrt(0.5)
    lt = -book(1.5 * z * w, dv * w)
    qt = np.quantile(lt, 0.99)
    assert abs(qt - 252_000) < 3000 and abs(lt[lt >= qt].mean() - 525_000) < 25_000
    assert abs(qt / q - 1.45) < 0.03
    assert -book(-10, 5) == 1_177_500 and -book(10, -3) == 857_500
    assert round(1_177_500 / 174_000, 1) == 6.8 and round(10 / 1.5, 1) == 6.7


def crr(s, k, r, v, tm, m, put=False):
    dt = tm / m
    u = exp(v * sqrt(dt))
    d = 1 / u
    p = (exp(r * dt) - d) / (u - d)
    st = s * d ** np.arange(m, -1, -1) * u ** np.arange(0, m + 1)
    val = np.maximum((k - st) if put else (st - k), 0)
    for _ in range(m):
        val = exp(-r * dt) * (p * val[1:] + (1 - p) * val[:-1])
    return float(val[0]), p


def bs(s, k, r, v, tm):
    d1 = (log(s / k) + (r + v * v / 2) * tm) / (v * sqrt(tm))
    return float(s * N(d1) - k * exp(-r * tm) * N(d1 - v * sqrt(tm)))


def test_q40():
    b = bs(100, 100, 0.05, 0.2, 1)
    assert round(b, 4) == 10.4506
    vals = {m: crr(100, 100, 0.05, 0.2, 1, m)[0] for m in (50, 51, 100, 101, 200, 201, 1000)}
    assert [round(vals[m], 4) for m in (50, 51, 100, 101, 200, 201)] == [10.4107, 10.4850, 10.4306, 10.4680, 10.4406, 10.4593]
    errs = [round(vals[m] - b, 4) for m in (50, 51, 100, 101, 200, 201)]
    assert errs == [-0.0399, 0.0344, -0.02, 0.0174, -0.01, 0.0087]
    avg = (vals[100] + vals[101]) / 2
    assert round(avg, 4) == 10.4493 and round(avg - b, 4) == -0.0013 and round(vals[1000] - b, 4) == -0.0020
    otm = bs(100, 180, 0.05, 0.2, 1)
    assert round(otm, 4) == 0.0286
    a50, a200 = crr(100, 180, 0.05, 0.2, 1, 50)[0], crr(100, 180, 0.05, 0.2, 1, 200)[0]
    assert round(a50, 4) == 0.0249 and round(a200, 4) == 0.0276
    assert round(a50 / otm - 1, 3) == -0.129 and round(a200 / otm - 1, 3) == -0.036
    # Low volatility: p leaves [0, 1] and the tree blows up.
    v, p = crr(100, 100, 0.05, 0.001, 1, 500)
    assert p > 1 and v > 1e150
    assert round(0.05 * sqrt(1 / 500), 5) == 0.00224
    # With enough steps it recovers the limit.
    v2, p2 = crr(100, 100, 0.05, 0.001, 1, 3000)
    assert p2 < 1 and abs(v2 - (100 - 100 * exp(-0.05))) < 1e-3
    assert round(100 - 100 * exp(-0.05), 2) == 4.88
    assert round((0.05 / 0.001) ** 2) == 2500
    # Parity at these inputs.
    assert abs(crr(100, 100, 0.05, 0.2, 1, 100)[0] - crr(100, 100, 0.05, 0.2, 1, 100, True)[0] - (100 - 100 * exp(-0.05))) < 1e-10
