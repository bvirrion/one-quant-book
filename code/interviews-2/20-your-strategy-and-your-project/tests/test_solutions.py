"""Your Strategy and Your Project. Numbers a candidate has to defend, each checked by a second route or a simulation."""
from math import log, sqrt

import numpy as np
from scipy.integrate import quad
from scipy.stats import norm

Phi, phi = norm.cdf, norm.pdf
_ADVICE = "advice on how to answer, with blanks for the reader's own facts; nothing is calculated or stated as fact"
NONNUMERIC = {
    1: "walking through a project; " + _ADVICE,
    4: "what you would change; " + _ADVICE,
    5: "result you trust least; " + _ADVICE,
    7: "explaining a thesis; " + _ADVICE,
    8: "naming the counterparty; " + _ADVICE,
    9: "being corrected; ordered steps; " + _ADVICE,
    10: "confidentiality; " + _ADVICE,
    11: "credit; " + _ADVICE,
}


def emax(n):
    return quad(lambda z: z * n * Phi(z) ** (n - 1) * phi(z), -10, 12)[0]


def test_q2():
    assert round(1.4 * 20, 6) == 28 and round(30 - 1.4 * 20, 6) == 2
    # The general form needs the risk-free rate: alpha = r - rf - beta (m - rf). The stated zero gives the 2.
    alpha = lambda rf: 30 - rf - 1.4 * (20 - rf)  # noqa: E731
    assert round(alpha(0), 6) == 2 and round(alpha(5), 6) == 4
    # Holding beta alone on the same market earns all of the 28 and no more.
    rng = np.random.default_rng(1)
    m = 0.20 + 0.16 * rng.standard_normal(500000)
    assert abs((1.4 * m).mean() - 0.28) < 1e-3


def test_q3():
    se = sqrt(0.25 / 1000)
    assert round(se * 100, 2) == 1.58 and round(0.10 / se, 1) == 6.3
    wins = np.random.default_rng(2).binomial(1000, 0.5, 400000) / 1000
    assert abs(wins.std() - se) < 1e-4 and (wins >= 0.6).mean() < 1e-5


def test_q6():
    t = 1.5 * sqrt(1.5)
    assert round(t, 2) == 1.84 and round(Phi(-t), 3) == 0.033 and round(200 * Phi(-t), 1) == 6.6
    # Simulated monthly records with no skill, judged by their own sample volatility.
    rng = np.random.default_rng(3)
    r = rng.standard_normal((300000, 18))
    sr = r.mean(axis=1) / r.std(axis=1, ddof=1) * sqrt(12)
    # A t-distribution with 17 degrees of freedom is a little wider than the normal.
    assert 0.03 < (sr >= 1.5).mean() < 0.05


def test_q12():
    assert round(0.6 * 10 - 0.4 * 8, 6) == 2.8 and round(8 / 18, 3) == 0.444
    kelly = lambda p: p / 0.08 - (1 - p) / 0.10  # noqa: E731
    assert round(kelly(0.6), 6) == 3.5 and abs(kelly(8 / 18)) < 1e-9
    # Second route: the leverage that maximises expected log growth, by search.
    g = np.linspace(0, 10, 100001)
    best = g[(0.6 * np.log1p(0.10 * g) + 0.4 * np.log1p(-0.08 * g)).argmax()]
    assert abs(best - 3.5) < 1e-3
    assert round(3.5 * 8) == 28 and round(60 - 8 / 18 * 100) == 16


def test_q13():
    tp, fp = 0.8 * 0.01, 0.05 * 0.99
    assert round(tp / (tp + fp), 3) == 0.139
    assert round(1000 * tp) == 8 and round(1000 * fp, 1) == 49.5
    assert round(1000 * (tp + fp)) == 58
    # A base rate of one half would make the same model look very good.
    assert round(0.8 / (0.8 + 0.05), 2) == 0.94



def test_q14():
    se = sqrt(0.16 / 2000)
    em = emax(50)
    assert round(se * 100, 3) == 0.894 and round(em, 2) == 2.25 and round(em * se * 100, 1) == 2.0
    assert round(em * se * 100 * sqrt(0.1), 2) == 0.64
    rng = np.random.default_rng(4)
    for rho, want in ((0.0, 2.01), (0.9, 0.636)):
        common = rng.standard_normal((40000, 1))
        z = sqrt(rho) * common + sqrt(1 - rho) * rng.standard_normal((40000, 50))
        # The inflation is the best score against the average score.
        assert abs((z.max(axis=1) - z.mean(axis=1)).mean() * se * 100 - want) < 0.03
    n1, n2 = 2 * 0.16 * (1.96 / 0.003) ** 2, 2 * 0.16 * 0.2 * (1.96 / 0.003) ** 2
    assert round(n1, -2) == 136600 and round(n2, -2) == 27300
    # Simulated scores on paired rows at the stated correlation of errors.
    z1, z2 = rng.standard_normal((2, 200000))
    a = z1
    b = 0.8 * z1 + 0.6 * z2
    assert abs(np.corrcoef(a, b)[0, 1] - 0.8) < 0.01
    assert abs((a - b).var() - 2 * 0.2) < 0.01


def test_q15():
    rng = np.random.default_rng(5)

    def path(mu, m=6000):
        n = 252 * 5
        r = rng.standard_normal((m, n)) * 0.15 / sqrt(252) + mu / 252
        c = np.c_[np.zeros(m), r.cumsum(axis=1)]
        return np.maximum.accumulate(c, axis=1) - c

    d = path(0.2)
    mdd = d.max(axis=1)
    assert abs(mdd.mean() - 0.19) < 0.006 and abs(np.median(mdd) - 0.18) < 0.006
    assert abs(np.quantile(mdd, 0.95) - 0.31) < 0.012
    assert abs((mdd > 0.30).mean() - 0.06) < 0.012 and abs((mdd <= 0.12).mean() - 0.07) < 0.012
    # The long-run mean is the stationary exponential; discrete days and the start from zero sit a little under it.
    assert round(0.0225 / 0.4, 3) == 0.056
    assert 0.045 < d[:, 500:].mean() < 0.0565
    # Limits: halving the drift raises it, doubling the volatility quadruples the stationary mean.
    assert abs(path(0.1).max(axis=1).mean() - 0.26) < 0.01
    assert 0.09 / 0.4 == 4 * (0.0225 / 0.4)


def test_q16():
    # Closed loop: one second holds 990,000 one-microsecond messages and one stall.
    lat = np.r_[np.ones(990000), [10000.0]]
    assert round(lat.mean(), 2) == 1.01 and np.quantile(lat, 0.99) == 1 and lat.max() == 10000
    # Open loop at 100,000 messages a second: closed form for the wait in milliseconds.
    assert round(0.5 * 10 * (10 / 0.9) / 1000 * 1000, 1) == 55.6
    assert round(10 - 0.9 * 10, 6) == 1 and round(10 - 0.9, 6) == 9.1
    # Simulation with whole cycles, one stall in the middle of each second.
    rng = np.random.default_rng(6)
    tt = 8
    t = np.sort(rng.random(100000 * tt) * tt)
    w = np.zeros(len(t))
    free, si = 0.0, 0
    for i, a in enumerate(t):
        s = max(a, free)
        if si < tt and s >= si + 0.5:
            s = max(s, si + 0.51)
            si += 1
        free = s + 1e-6
        w[i] = free - a
    us = w * 1e6
    assert abs(us.mean() - 55.6) < 5
    assert abs(np.quantile(us, 0.999) - 9100) < 150
    assert abs(np.quantile(us, 0.99) - 1000) < 300
    assert np.quantile(us, 0.5) < 1.2


def test_q17():
    n = 1000
    rng = np.random.default_rng(7)
    # 995 ordinary days holding 20 points, 5 days of 8 points, total variance as stated.
    var_all = 1 + 0.06**2
    rest_sq = (n * var_all - 5 * 64) / 995
    sd_rest = sqrt(rest_sq - (20 / 995) ** 2)
    z = rng.standard_normal(995)
    z = (z - z.mean()) / z.std()
    r = 20 / 995 + sd_rest * z
    full = np.r_[r, np.full(5, 8.0)]
    assert abs(full.sum() - 60) < 1e-9 and abs(full.std() - 1) < 1e-9
    assert round(full.mean() / full.std() * sqrt(252), 2) == 0.95
    assert round(r.mean() / r.std() * sqrt(252), 3) == 0.385
    assert round(r.std(), 3) == 0.829 and round(n * var_all, 0) == 1004
    q = norm.ppf(0.995)
    assert round(q, 3) == 2.576 and round(phi(q) / 0.005, 2) == 2.89 and round(5 * phi(q) / 0.005, 1) == 14.5
    top = np.sort(rng.standard_normal((20000, 1000)), axis=1)[:, -5:].sum(axis=1)
    assert abs(top.mean() - 14.3) < 0.05


def test_q18():
    post = lambda a, base=0.05, power=0.5: base * power / (base * power + (1 - base) * a)  # noqa: E731
    assert round(post(0.01), 2) == 0.72 and round(post(0.05), 2) == 0.34 and round(post(0.001), 2) == 0.96
    assert abs(25 / 34.5 - post(0.01)) < 1e-12
    # Limits: certain truth stays true, and zero base rate never is.
    assert post(0.01, base=1.0) == 1 and post(0.01, base=0.0) == 0
    rng = np.random.default_rng(8)
    true = rng.random(2000000) < 0.05
    sig = np.where(true, rng.random(2000000) < 0.5, rng.random(2000000) < 0.01)
    assert abs(true[sig].mean() - post(0.01)) < 0.01


def test_q19():
    t = 0.05 / 0.6 * sqrt(500)
    infl = sqrt(1.3 / 0.7)
    assert round(t, 2) == 1.86 and round(infl**2, 3) == 1.857 and round(infl, 3) == 1.363 and round(t / infl, 2) == 1.37
    # Simulated AR(1) means: the variance of the mean matches the long-run formula.
    rng = np.random.default_rng(9)
    e = rng.standard_normal((6000, 500)) * sqrt(1 - 0.09)
    x = np.zeros_like(e)
    x[:, 0] = rng.standard_normal(6000)
    for i in range(1, 500):
        x[:, i] = 0.3 * x[:, i - 1] + e[:, i]
    ratio = x.mean(axis=1).var() * 500
    assert abs(ratio - infl**2) < 0.1
    # The factor needs the AR(1): the same first-order autocorrelation with nothing beyond lag 1 gives 1 + 2 rho.
    theta = 1 / 3
    assert abs(theta / (1 + theta**2) - 0.3) < 1e-12
    u = rng.standard_normal((6000, 501))
    ma = (u[:, 1:] + theta * u[:, :-1]) / sqrt(1 + theta**2)
    assert abs((ma[:, 1:] * ma[:, :-1]).mean() - 0.3) < 0.01
    assert abs(ma.mean(axis=1).var() * 500 - 1.6) < 0.1
    assert round(t / sqrt(1.6), 2) == 1.47 and abs(1.6 - infl**2) > 0.2



def test_q20():
    assert round(18 / 12 * sqrt(4), 6) == 3.0
    cost = 0.5 * 3 * 252 / 100
    assert round(cost, 2) == 3.78 and round(18 - cost, 2) == 14.22 and round((18 - cost) / 12, 2) == 1.19
    alpha = 18 - 0.3 * 12
    rv = sqrt(0.0144 - 0.09 * 0.0256)
    assert round(alpha, 6) == 14.4 and round(rv, 2) == 0.11 and round(alpha / 100 / rv, 2) == 1.31
    # The difference of two independent half-sample Sharpes, each over 2 years.
    rng = np.random.default_rng(10)
    r = rng.standard_normal((40000, 504)) * 0.12 / sqrt(252) + 0.18 / 252
    s = r.mean(axis=1) / r.std(axis=1) * sqrt(252)
    assert abs(s.std() - 1 / sqrt(2)) < 0.02
    assert abs((s[:20000] - s[20000:]).std() - 1) < 0.03
    assert round(2 * Phi(-1.4), 2) == 0.16
    p = Phi(-3)
    assert round(p * 100, 3) == 0.135 and round(0.05 / p) == 37 and round(log(0.95) / log(1 - p)) == 38
    assert abs(1 - (1 - p) ** 38 - 0.05) < 0.001

