"""Portfolio Construction. Closed forms against solvers, simulations and limit cases."""
from math import sqrt

import numpy as np
from scipy.optimize import minimize

NONNUMERIC = {}
S3 = np.array([[0.04, 0.012, 0.012], [0.012, 0.09, 0.018], [0.012, 0.018, 0.0225]])
MU3 = np.array([0.06, 0.08, 0.12])
ONE3 = np.ones(3)


def var2(w, s1, s2, c):
    return w * w * s1 * s1 + (1 - w) ** 2 * s2 * s2 + 2 * w * (1 - w) * c


def test_q1():
    w = (0.09 - 0.03) / (0.13 - 0.06)
    assert abs(w - 6 / 7) < 1e-12 and round(sqrt(var2(w, 0.2, 0.3, 0.03)), 3) == 0.196
    # Grid search finds the same point; inverse variance is worse.
    g = np.linspace(-1, 2, 30001)
    assert abs(g[np.argmin(var2(g, 0.2, 0.3, 0.03))] - w) < 2e-4
    iv = (1 / 0.04) / (1 / 0.04 + 1 / 0.09)
    assert round(iv, 2) == 0.69 and var2(iv, 0.2, 0.3, 0.03) > var2(w, 0.2, 0.3, 0.03)
    assert round(var2(w, 0.2, 0.3, 0.03), 4) == 0.0386


def test_q2():
    assert abs(sqrt(0.04 * 0.6) - 0.1549) < 1e-4
    g = np.linspace(0, 1, 2001)
    assert abs(g[np.argmin(var2(g, 0.2, 0.2, 0.2 * 0.04))] - 0.5) < 1e-3


def test_q3():
    w = np.array([2 / 3, 1 / 3])
    for r in (-0.9, 0, 0.7):
        c = r * 0.1 * 0.2
        s = np.array([[0.01, c], [c, 0.04]])
        rc = w * (s @ w)
        assert abs(rc[0] - rc[1]) < 1e-14


def test_q4():
    assert round(0.05 * sqrt(100), 2) == 0.5 and round(0.05 * sqrt(252), 2) == 0.79
    # Simulation: 100 independent bets at IC 0.05, and an optimal linear book.
    rng = np.random.default_rng(1)
    irs = []
    z = rng.standard_normal((20000, 100))
    e = rng.standard_normal((20000, 100))
    r = 0.05 * z + sqrt(1 - 0.0025) * e
    pnl = (z * r).sum(axis=1)
    irs = pnl.mean() / pnl.std()
    assert abs(irs - 0.5) < 0.02


def test_q5():
    a, b = np.array([0.5, 0.3, 0.2]), np.array([0.4, 0.4, 0.2])
    d = np.abs(a - b).sum()
    assert round(d, 6) == 0.2 and round(d / 2, 6) == 0.1
    assert round(d * 10, 6) == 2 and round(d * 10 * 12, 6) == 24


def test_q6():
    assert round(10 * 1.2 / 0.8, 6) == 15 and round(10 - 15, 6) == -5
    assert round(10 * 1.2 - 15 * 0.8, 6) == 0


def test_q7():
    mu = np.array([0.08, 0.10])
    s = np.array([[0.04, 0.03], [0.03, 0.09]])
    x = np.linalg.solve(s, mu)
    assert [round(float(i), 3) for i in x] == [1.556, 0.593]
    w = x / x.sum()
    assert round(float(w[0]), 3) == 0.724 and round(float(sqrt(mu @ x)), 3) == 0.429
    h = x / 4
    assert round(float(h[0]), 3) == 0.389 and round(float(h[1]), 3) == 0.148
    assert round(float(mu @ h), 4) == 0.0459 and round(float(sqrt(h @ s @ h)), 3) == 0.107
    # A numerical maximum of the Sharpe agrees.
    res = minimize(lambda u: -(u[0] * 0.08 + (1 - u[0]) * 0.10) / sqrt(var2(u[0], 0.2, 0.3, 0.03)), [0.5])
    assert abs(res.x[0] - w[0]) < 1e-4


def test_q8():
    c = 0.8 * 0.2 * 0.3
    w = (0.09 - c) / (0.13 - 2 * c)
    assert round(w, 3) == 1.235 and round(sqrt(var2(w, 0.2, 0.3, c)), 3) == 0.195
    # The sign flips exactly at rho = s1/s2.
    r = 0.2 / 0.3
    c = r * 0.06
    assert abs((0.09 - c) / (0.13 - 2 * c) - 1) < 1e-12


def test_q9():
    mu = np.array([0.10, 0.05])
    s = np.array([[0.04, 0.05], [0.05, 0.09]])
    x = np.linalg.solve(s, mu)
    assert [round(float(i), 2) for i in x] == [5.91, -2.73]
    assert round(float(sqrt(mu @ x)), 3) == 0.674
    g = np.linspace(0, 1, 10001)
    sr = (g * 0.10 + (1 - g) * 0.05) / np.sqrt(var2(g, 0.2, 0.3, 0.05))
    assert g[np.argmax(sr)] == 1 and round(sr.max(), 3) == 0.5


def test_q10():
    f = lambda n: 0.3 * sqrt(1 / n + (1 - 1 / n) * 0.3)  # noqa: E731
    assert [round(f(n), 3) for n in (10, 30, 100)] == [0.182, 0.171, 0.166]
    assert round(0.3 * sqrt(0.3), 4) == 0.1643
    assert f(19) <= 0.3 * sqrt(0.3) + 0.01 < f(18)
    # Simulation at 10.
    rng = np.random.default_rng(2)
    z = rng.standard_normal((300000, 1))
    e = rng.standard_normal((300000, 10))
    x = 0.3 * (sqrt(0.3) * z + sqrt(0.7) * e)
    assert abs(x.mean(axis=1).std() - f(10)) < 1e-3


def test_q11():
    n_eff = 500 / (1 + 499 * 0.01)
    assert round(n_eff, 1) == 83.5 and round(0.02 * sqrt(n_eff), 3) == 0.183 and round(0.02 * sqrt(500), 2) == 0.45
    assert abs(1 / 0.01 - 100) < 1e-12
    # Variance of the mean of correlated errors.
    rng = np.random.default_rng(3)
    z = rng.standard_normal((40000, 1))
    e = rng.standard_normal((40000, 500))
    x = sqrt(0.01) * z + sqrt(0.99) * e
    assert abs(x.mean(axis=1).var() - 1 / n_eff) < 3e-4


def test_q12():
    assert round(0.3 * 0.05 * sqrt(500), 3) == 0.335
    assert round(sqrt(500), 2) == 22.36


def test_q13():
    se = 0.2 / sqrt(20)
    assert round(se, 4) == 0.0447 and round(0.15 / se, 1) == 3.4
    sed = sqrt(2) * se
    assert round(sed, 3) == 0.063 and round(0.20 / sed, 1) == 3.2
    assert 0.5 * 0.15 + 0.5 * 0.05 == 0.10 and abs(0.5 * -0.05 + 0.5 * 0.05) < 1e-12
    # Weights are linear in means at equal risk and zero correlation: the tilt halves.
    tilt = lambda a, b: (a - b) / 0.04  # noqa: E731
    assert abs(tilt(0.10, 0.0) / tilt(0.15, -0.05) - 0.5) < 1e-12


def test_q14():
    e = np.array([5.0, 1.0, 0.01])
    assert e[0] / e[2] == 500
    m = e.mean()
    d = 0.8 * e + 0.2 * m
    assert round(m, 3) == 2.003 and [round(float(i), 2) for i in d] == [4.4, 1.2, 0.41]
    assert round(float(d[0] / d[2]), 1) == 10.8
    assert round(float(d[2] / e[2])) == 41
    # Trace is kept.
    assert abs(d.sum() - e.sum()) < 1e-12


def test_q15():
    q = 0.1
    assert round((1 - sqrt(q)) ** 2, 3) == 0.468 and round((1 + sqrt(q)) ** 2, 3) == 1.732
    q = 0.5
    assert round((1 - sqrt(q)) ** 2, 3) == 0.086 and round((1 + sqrt(q)) ** 2, 3) == 2.914
    rng = np.random.default_rng(4)
    x = rng.standard_normal((1000, 100))
    ev = np.linalg.eigvalsh(np.corrcoef(x.T))
    assert abs(ev[-1] - 1.732) < 0.1 and abs(ev[0] - 0.468) < 0.06
    x = rng.standard_normal((1000, 500))
    ev = np.linalg.eigvalsh(np.corrcoef(x.T))
    assert abs(ev[-1] - 2.914) < 0.12 and abs(ev[0] - 0.086) < 0.04


def test_q16():
    assert 500 * 501 // 2 == 125_250 and 500 * 10 + 10 * 11 // 2 + 500 == 5_555
    # Invertible with fewer days than stocks, unlike the sample matrix.
    rng = np.random.default_rng(5)
    bb = rng.standard_normal((50, 3))
    sig = bb @ np.eye(3) @ bb.T + np.eye(50) * 0.1
    assert np.linalg.eigvalsh(sig)[0] > 0
    sam = np.cov(rng.standard_normal((30, 50)).T)
    assert np.linalg.matrix_rank(sam) < 50


def test_q17():
    assert abs(0 - 0.04 / 2 + 0.02) < 1e-12
    assert abs((0 - 0.02 / 2) + 0.01) < 1e-12
    assert abs(0.5 * (0.04 - 0.02) - 0.01) < 1e-12
    rng = np.random.default_rng(6)
    m, y = 40000, 30
    z = rng.standard_normal((m, y, 2)) * 0.2 - 0.02
    rb = np.log(0.5 * np.exp(z[:, :, 0]) + 0.5 * np.exp(z[:, :, 1])).sum(axis=1) / y
    bh = np.log(0.5 * np.exp(z[:, :, 0].sum(axis=1)) + 0.5 * np.exp(z[:, :, 1].sum(axis=1))) / y
    assert abs(rb.mean() + 0.01) < 5e-4 and abs(bh.mean() + 0.012) < 6e-4
    assert abs((rb.mean() - bh.mean()) - 0.002) < 6e-4
    # No extra return: expected final wealth is one either way, with independent walks and no reversion in them.
    wrb = np.exp(rb * y)
    wbh = np.exp(bh * y)
    assert abs(wrb.mean() - 1) < 0.02 and abs(wbh.mean() - 1) < 0.02
    # A trending asset: buy and hold has the higher expected wealth.
    assert 1.05**30 < (1.10**30 + 1) / 2
    # With correlation one, each year's two returns are the same, and rebalancing adds nothing.
    q = z[:, :, 0]
    r1 = np.log(0.5 * np.exp(q) + 0.5 * np.exp(q)).sum(axis=1) / y
    assert abs(r1 - q.sum(axis=1) / y).max() < 1e-12


def test_q18():
    n, tm, s, r = 10, 60, 0.05, 0.3
    mu = np.full(n, 0.005)
    c = s * s * (r * np.ones((n, n)) + (1 - r) * np.eye(n))
    el = np.linalg.cholesky(c)
    tr = lambda w: float((w @ mu) / sqrt(w @ c @ w) * sqrt(12))  # noqa: E731
    assert round(tr(np.ones(n) / n), 3) == 0.569
    assert round(5 * sqrt(0.1 + 0.9 * 0.3), 2) == 3.04
    # By symmetry, equal weights solve the true problem exactly.
    x = np.linalg.solve(c, mu)
    assert abs(x.max() - x.min()) < 1e-10
    rng = np.random.default_rng(7)
    ins, oos = [], []
    for _ in range(1500):
        d = mu + rng.standard_normal((tm, n)) @ el.T
        m = d.mean(axis=0)
        w = np.linalg.solve(np.cov(d.T), m)
        ins.append(sqrt(float(m @ w)) * sqrt(12))
        oos.append(tr(w))
    assert abs(np.mean(ins) - 1.65) < 0.03 and abs(np.mean(oos) - 0.19) < 0.03
    assert np.mean(oos) < tr(np.ones(n) / n) < np.mean(ins)


def bl(om, s, w, de, tau=0.05):
    pi = de * s @ w
    p = np.array([1.0, 0.0])
    gain = tau * s @ p / (tau * p @ s @ p + om)
    return pi, pi + gain * (0.10 - p @ pi)


def test_q19():
    s = np.array([[0.04, 0.03], [0.03, 0.09]])
    w = np.array([0.6, 0.4])
    pi, post = bl(0.05 * 0.04, s, w, 2.5)
    assert [round(float(i), 3) for i in pi] == [0.09, 0.135]
    assert [round(float(i), 5) for i in post] == [0.095, 0.13875]
    wp = np.linalg.solve(2.5 * s, post)
    assert [round(float(i), 6) for i in wp] == [0.65, 0.4]
    # Limits.
    _, p0 = bl(1e-14, s, w, 2.5)
    assert abs(p0[0] - 0.10) < 1e-9 and abs(p0[1] - 0.1425) < 1e-9
    w0 = np.linalg.solve(2.5 * s, p0)
    assert abs(w0[0] - 0.70) < 1e-8 and abs(w0[1] - 0.40) < 1e-8
    _, pi2 = bl(1e12, s, w, 2.5)
    assert abs(pi2 - pi).max() < 1e-9
    # Theil's mixed-estimation form agrees.
    tau = 0.05
    a = np.linalg.inv(np.linalg.inv(tau * s) + np.outer([1, 0], [1, 0]) / 0.002)
    alt = a @ (np.linalg.inv(tau * s) @ pi + np.array([1, 0]) * 0.10 / 0.002)
    assert abs(alt - post).max() < 1e-10


def test_q20():
    s = np.array([[0.04, 0.01, 0.0], [0.01, 0.01, 0.004], [0.0, 0.004, 0.09]])
    shares = lambda w: w * (s @ w) / (w @ s @ w)  # noqa: E731
    eq = np.ones(3) / 3
    assert [round(float(i), 3) for i in shares(eq)] == [0.298, 0.143, 0.56]
    iv = (1 / np.sqrt(np.diag(s))) / (1 / np.sqrt(np.diag(s))).sum()
    assert [round(float(i), 3) for i in shares(iv)] == [0.352, 0.383, 0.266]
    w = np.array([0.2763, 0.5119, 0.2117])
    assert abs(shares(w) - 1 / 3).max() < 3e-3
    assert [round(float(i), 4) for i in s @ w] == [0.0162, 0.0087, 0.0211]
    assert round(float(sqrt(w @ s @ w)), 3) == 0.116 and round(float(w @ s @ w), 4) == 0.0134
    assert abs(w * (s @ w) - 0.00447).max() < 1e-4
    # The log-barrier route reaches the same weights.
    res = minimize(lambda x: 0.5 * x @ s @ x - 0.01 * np.log(x).sum(), np.ones(3) / 3, bounds=[(1e-6, None)] * 3, tol=1e-12)
    wn = res.x / res.x.sum()
    assert abs(wn - w).max() < 2e-3


def test_q21():
    si = np.linalg.inv(S3)
    a, b, c = ONE3 @ si @ ONE3, ONE3 @ si @ MU3, MU3 @ si @ MU3
    d = a * c - b * b
    assert round(float(a), 2) == 51.29 and round(float(b), 3) == 5.243 and round(float(c), 4) == 0.6437
    assert round(float(d), 3) == 5.531
    assert round(float(b / a), 4) == 0.1022 and round(float(1 / sqrt(a)), 4) == 0.1396
    m = 0.12
    w = ((c - b * m) / d) * si @ ONE3 + ((a * m - b) / d) * si @ MU3
    assert [round(float(i), 3) for i in w] == [0.019, -0.029, 1.01]
    assert round(float(sqrt(w @ S3 @ w)), 3) == 0.15
    assert abs(w @ S3 @ w - (a * m * m - 2 * b * m + c) / d) < 1e-12
    # A numerical solver agrees.
    res = minimize(lambda x: x @ S3 @ x, ONE3 / 3, constraints=[{"type": "eq", "fun": lambda x: x.sum() - 1}, {"type": "eq", "fun": lambda x: x @ MU3 - m}], tol=1e-14)
    assert abs(res.x - w).max() < 1e-4
    # Two funds span the frontier: a mix of two solutions lands on the target's solution.
    wm = lambda mm: ((c - b * mm) / d) * si @ ONE3 + ((a * mm - b) / d) * si @ MU3  # noqa: E731
    assert abs(0.5 * wm(0.08) + 0.5 * wm(0.12) - wm(0.10)).max() < 1e-12
    # Below the minimum-variance return, risk rises again.
    assert sqrt(wm(0.08) @ S3 @ wm(0.08)) > 1 / sqrt(a)


def test_q22():
    i = np.linalg.solve(S3, ONE3)
    assert [round(float(x), 3) for x in i / i.sum()] == [0.268, 0.043, 0.689]
    w = np.array([0.4, 0.2, 0.4])
    assert round(float(sqrt(w @ S3 @ w)), 3) == 0.149
    g = S3 @ w
    assert [round(float(x), 4) for x in g] == [0.0232, 0.03, 0.0174]
    nu = g[1] - g
    assert round(float(nu[0]), 4) == 0.0068 and round(float(nu[2]), 4) == 0.0126 and nu.min() >= 0
    pro = i / i.sum()
    pr = np.array([pro[0], pro[1], 0.0]) / (pro[0] + pro[1]) * 0.6
    assert round(float(pr[0]), 3) == 0.517 and round(float(pr[1]), 3) == 0.083
    res = minimize(lambda x: x @ S3 @ x, ONE3 / 3, constraints=[{"type": "eq", "fun": lambda x: x.sum() - 1}], bounds=[(None, 0.4)] * 3, tol=1e-14)
    assert abs(res.x - w).max() < 1e-4
    # No feasible neighbour is better.
    rng = np.random.default_rng(8)
    for _ in range(2000):
        d = rng.standard_normal(3)
        d -= d.mean()
        q = w + 0.02 * d
        if q.max() <= 0.4:
            assert q @ S3 @ q >= w @ S3 @ w - 1e-12


def test_q23():
    rho = 2 ** (-1 / 5)
    assert round(rho, 4) == 0.8706 and round(2 / (1 - rho), 2) == 15.45
    assert round(10 * (1 - rho), 2) == 1.29
    tot = sum(2 * rho**t for t in range(5000))
    assert abs(tot - 2 / (1 - rho)) < 1e-9
    # Half of the total arrives within the half-life.
    assert abs(sum(2 * rho**t for t in range(5)) - 0.5 * 2 / (1 - rho)) < 1e-9


def test_q24():
    c = np.array([[1, 0.3], [0.3, 1]])
    s = np.array([1, 0.8])
    x = np.linalg.solve(c, s)
    assert [round(float(i), 3) for i in x] == [0.835, 0.549]
    assert round(float(x[0] / x.sum()), 3) == 0.603 and round(float(sqrt(s @ x)), 3) == 1.129
    assert round(sqrt((1 + 0.64 - 2 * 0.3 * 0.8) / (1 - 0.09)), 3) == 1.129
    assert abs(np.linalg.solve([[1, 0.8], [0.8, 1]], s)[1]) < 1e-12
    assert round(sqrt((1 + 0.64 + 2 * 0.3 * 0.8) / 0.91), 2) == 1.53
    # A scan of risk weights finds the same point.
    g = np.linspace(0, 1, 10001)
    sr = (g * 1 + (1 - g) * 0.8) / np.sqrt(g * g + (1 - g) ** 2 + 2 * g * (1 - g) * 0.3)
    assert abs(g[np.argmax(sr)] - x[0] / x.sum()) < 1e-3 and abs(sr.max() - 1.129) < 1e-3


def test_q25():
    al = np.array([0.06, 0.03, -0.04])
    v = np.array([0.25, 0.20, 0.30])
    r = 0.4 * np.ones((3, 3)) + 0.6 * np.eye(3)
    s = np.outer(v, v) * r
    be = np.array([1.2, 0.8, 1.0])
    lam = 5
    si = np.linalg.inv(s)
    fmt = lambda w: [round(float(i), 3) for i in w]  # noqa: E731
    wu = si @ al / lam
    assert fmt(wu) == [0.244, 0.155, -0.212] and round(float(be @ wu), 3) == 0.205
    assert round(float(wu @ al), 4) == 0.0277 and round(float(sqrt(wu @ s @ wu)), 4) == 0.0745
    assert round(float(wu @ al / sqrt(wu @ s @ wu)), 3) == 0.372
    g = (be @ si @ al) / (be @ si @ be)
    assert round(float(g), 4) == 0.0353
    wb = si @ (al - g * be) / lam
    assert fmt(wb) == [0.145, 0.078, -0.237] and abs(be @ wb) < 1e-12
    assert round(float(wb @ al), 4) == 0.0205 and round(float(sqrt(wb @ s @ wb)), 4) == 0.064
    assert round(float(wb @ al / sqrt(wb @ s @ wb)), 3) == 0.32
    gg = np.vstack([be, np.ones(3)])
    a = np.linalg.solve(gg @ si @ gg.T, gg @ si @ al)
    wd = si @ (al - gg.T @ a) / lam
    assert fmt(wd) == [0.119, 0.119, -0.237] and abs(gg @ wd).max() < 1e-12
    assert round(float(wd @ al), 4) == 0.0202 and round(float(sqrt(wd @ s @ wd)), 4) == 0.0635
    assert round(float(wd @ al / sqrt(wd @ s @ wd)), 3) == 0.318
    k = 0.1 / sqrt(wb @ s @ wb)
    assert round(float(k), 3) == 1.562 and fmt(k * wb) == [0.226, 0.122, -0.369]
    assert round(float(k * wb @ al), 4) == 0.032
    # A solver check for the constrained neutral book.
    res = minimize(lambda w: -(w @ al - lam / 2 * w @ s @ w), wu, constraints=[{"type": "eq", "fun": lambda w: be @ w}], tol=1e-14)
    assert abs(res.x - wb).max() < 1e-4
    # Costs with signs known, closed form against a solver.
    c = 0.002
    ap = al - c * np.sign(wb)
    assert fmt(ap) == [0.058, 0.028, -0.038]
    gc = (be @ si @ ap) / (be @ si @ be)
    wc = si @ (ap - gc * be) / lam
    assert fmt(wc) == [0.142, 0.069, -0.225] and np.all(np.sign(wc) == np.sign(wb))
    net = wc @ al - lam / 2 * wc @ s @ wc - c * np.abs(wc).sum()
    assert round(float(net), 4) == 0.0094
    res = minimize(lambda w: -(w @ al - lam / 2 * w @ s @ w - c * np.abs(w).sum()), wc, constraints=[{"type": "eq", "fun": lambda w: be @ w}], tol=1e-12, method="SLSQP")
    assert abs(res.x - wc).max() < 2e-3
    # Doubling risk aversion halves the book.
    assert abs(si @ (al - g * be) / (2 * lam) - wb / 2).max() < 1e-12
    # High cost: the smallest position has the least alpha net of cost.
    assert abs(wc).argmin() == 1
