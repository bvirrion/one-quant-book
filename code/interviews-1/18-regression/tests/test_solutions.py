"""Every number and claim printed in the answers of "Regression": exact algebra where it exists, and a seeded numerical demonstration."""
import math
from fractions import Fraction as F

import numpy as np
import scipy.stats as st
import sympy as sp
from scipy.optimize import minimize
from sklearn.linear_model import Lasso

NONNUMERIC = {}


def ols(x, y):
    """OLS with intercept. Returns coefficients, classical standard errors, residuals and R-squared."""
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = x[:, None]
    design = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    e = y - design @ beta
    s2 = e @ e / (len(y) - design.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(design.T @ design)))
    r2 = 1 - e @ e / ((y - y.mean()) @ (y - y.mean()))
    return beta, se, e, r2


def slope_t(x, y):
    """Slope, t-statistic and R-squared of many simple regressions at once, one per row."""
    x = x - x.mean(axis=1, keepdims=True)
    y = y - y.mean(axis=1, keepdims=True)
    sxx = (x * x).sum(axis=1)
    b = (x * y).sum(axis=1) / sxx
    e = y - b[:, None] * x
    s2 = (e * e).sum(axis=1) / (x.shape[1] - 2)
    return b, b / np.sqrt(s2 / sxx), 1 - (e * e).sum(axis=1) / (y * y).sum(axis=1)


def test_q1():
    rng = np.random.default_rng(1)
    x = rng.standard_normal(500)
    y = 0.7 * x + rng.standard_normal(500)
    b1 = ols(x, y)[0][1]
    b2 = ols(y, x)[0][1]
    r = np.corrcoef(x, y)[0, 1]
    assert abs(b1 * b2 - r**2) < 1e-12
    assert np.sign(b1) == np.sign(b2)
    # The numbers in the answer: b2 = rho^2 / 2.
    assert F(36, 100) / 2 == F(18, 100)
    assert round(math.sqrt(2 * 0.18), 6) == 0.6
    # y = 2x exactly gives the upper end of the range.
    b_top = ols(2 * x, x)[0][1]
    assert abs(b_top - 0.5) < 1e-12
    # Noisy data with slope 2: reverse slope well under 1/2.
    y = 2 * x + rng.standard_normal(500) * 2.67
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    assert abs(ols(y, x)[0][1] - r2 / ols(x, y)[0][1]) < 1e-12


def test_q2():
    rng = np.random.default_rng(2)
    n = 250
    x = rng.standard_normal(n)
    y = 0.3 * x + rng.standard_normal(n)
    b, se, _, r2 = ols(x, y)
    b2, se2, _, r22 = ols(np.tile(x, 2), np.tile(y, 2))
    assert np.allclose(b, b2) and abs(r2 - r22) < 1e-12
    assert np.allclose(se2 / se, math.sqrt((n - 2) / (2 * n - 2)))
    assert round(math.sqrt(248 / 498), 3) == 0.706
    assert round(1 / math.sqrt(2), 3) == 0.707
    assert abs(np.corrcoef(x, y)[0, 1] - np.corrcoef(np.tile(x, 2), np.tile(y, 2))[0, 1]) < 1e-12
    assert round(math.sqrt(20), 1) == 4.5


def test_q3():
    rho, ss, si = 0.8, 30.0, 15.0
    assert round(rho * ss / si, 6) == 1.6
    assert round(ss * math.sqrt(1 - rho**2), 6) == 18
    assert round(rho**2, 6) == 0.64
    assert round(rho * si / ss, 6) == 0.4
    assert round(1 / 0.4, 6) == 2.5
    cov = rho * ss * si
    assert cov == 360
    var = ss**2 + 2.5**2 * si**2 - 2 * 2.5 * cov
    assert var == 506.25 and math.sqrt(var) == 22.5
    rng = np.random.default_rng(3)
    idx = rng.standard_normal(400_000) * si
    stock = 1.6 * idx + rng.standard_normal(400_000) * 18
    assert abs(ols(idx, stock)[0][1] - 1.6) < 0.01
    assert abs(np.std(stock - 1.6 * idx) - 18) < 0.1
    assert abs(np.std(stock - 2.5 * idx) - 22.5) < 0.1


def test_q4():
    rng = np.random.default_rng(4)
    x = rng.standard_normal((200, 5))
    y = x[:, 0] + rng.standard_normal(200)
    last = -1
    for k in range(1, 6):
        r2 = ols(x[:, :k], y)[3]
        assert r2 >= last
        last = r2
    b, _, _, r2 = ols(x[:, :2], y)
    fitted = np.column_stack([np.ones(200), x[:, :2]]) @ b
    assert abs(np.corrcoef(y, fitted)[0, 1] ** 2 - r2) < 1e-12
    # No intercept with a large mean: 1 - RSS / TSS is far below zero.
    z = rng.standard_normal(200)
    w = 5 + rng.standard_normal(200)
    coef = (z @ w) / (z @ z)
    e = w - coef * z
    assert 1 - e @ e / ((w - w.mean()) @ (w - w.mean())) < -5
    # R-squared of one: every residual is zero.
    assert ols(x[:, 0], 3 * x[:, 0] + 1)[3] > 1 - 1e-12


def test_q5():
    assert round(2 / (10 / math.sqrt(4)), 6) == 0.4
    assert round(0.2 * math.sqrt(4), 6) == 0.4
    assert round((2 / 0.2) ** 2, 6) == 100
    assert round((2 / 1) ** 2, 6) == 4
    rng = np.random.default_rng(5)
    t = 48
    resid = rng.standard_normal((20_000, t)) * 10 / math.sqrt(12)
    mkt = rng.standard_normal((20_000, t)) * 15 / math.sqrt(12)
    y = 2 / 12 + 0.8 * mkt + resid
    b, _, _ = slope_t(mkt, y)
    alpha = y.mean(axis=1) - b * mkt.mean(axis=1)
    assert abs(alpha.mean() * 12 - 2) < 0.1
    assert abs(alpha.std() * 12 - 5) < 0.15


def test_q6():
    n, r2 = 2500, 0.005
    t = math.sqrt(r2 * (n - 2) / (1 - r2))
    assert round(t, 2) == 3.54
    rho = math.sqrt(r2)
    assert round(rho, 3) == 0.071
    assert round(rho * math.sqrt(252), 2) == 1.12
    assert round(t / math.sqrt(n / 252), 2) == 1.12
    rng = np.random.default_rng(6)
    x = rng.standard_normal(n)
    y = 0.1 * x + rng.standard_normal(n)
    b, se, _, r = ols(x, y)
    assert abs(abs(b[1] / se[1]) - math.sqrt(r * (n - 2) / (1 - r))) < 1e-9
    # Sharpe of holding the standardised signal: rho per day.
    x = rng.standard_normal(2_000_000)
    y = rho * x + math.sqrt(1 - r2) * rng.standard_normal(2_000_000)
    pnl = x * y
    assert abs(pnl.mean() / pnl.std() * math.sqrt(252) - 1.12) < 0.03


def test_q7():
    rng = np.random.default_rng(7)
    x = np.column_stack([np.ones(300), rng.standard_normal((300, 3))])
    y = x @ [1, 2, -1, 0.5] + rng.standard_normal(300)
    b = np.linalg.solve(x.T @ x, x.T @ y)
    assert np.allclose(b, np.linalg.lstsq(x, y, rcond=None)[0])
    e = y - x @ b
    assert np.allclose(x.T @ e, 0, atol=1e-9)
    assert abs(e.sum()) < 1e-9
    assert abs(np.linalg.cond(x.T @ x) / np.linalg.cond(x) ** 2 - 1) < 1e-6
    # Streaming: accumulate X'X and X'y over chunks.
    xx, xy = np.zeros((4, 4)), np.zeros(4)
    for i in range(0, 300, 37):
        xx += x[i : i + 37].T @ x[i : i + 37]
        xy += x[i : i + 37].T @ y[i : i + 37]
    assert np.allclose(np.linalg.solve(xx, xy), b)
    # A repeated column has no unique solution: the matrix is singular.
    dup = np.column_stack([x, x[:, 1]])
    assert np.linalg.matrix_rank(dup.T @ dup) == 4


def test_q8():
    rng = np.random.default_rng(8)
    n = 5000
    z = rng.standard_normal(n)
    x = 0.8 * z + 0.6 * rng.standard_normal(n)
    y = 1.0 * x + 0.5 * z + rng.standard_normal(n)
    z0, x0, y0 = z - z.mean(), x - x.mean(), y - y.mean()
    full = ols(np.column_stack([x, z]), y)[0][1]
    xr = x0 - (x0 @ z0) / (z0 @ z0) * z0
    yr = y0 - (y0 @ z0) / (z0 @ z0) * z0
    both = (xr @ yr) / (xr @ xr)
    assert abs(full - both) < 1e-10
    only_y = (x0 @ yr) / (x0 @ x0)
    r2 = np.corrcoef(x, z)[0, 1] ** 2
    assert abs(only_y - full * (1 - r2)) < 1e-10
    assert round(1 - 0.8**2, 2) == 0.36
    assert abs(only_y - 0.36) < 0.03


def test_q9():
    assert 1 + (-3) * 0.5 == -0.5
    assert 1 + 2 * 0.5 == 2
    rng = np.random.default_rng(9)
    n = 400_000
    z = rng.standard_normal(n)
    x = 0.5 * z + math.sqrt(0.75) * rng.standard_normal(n)
    y = x - 3 * z + rng.standard_normal(n)
    assert abs(ols(x, y)[0][1] + 0.5) < 0.02
    assert abs(ols(np.column_stack([x, z]), y)[0][1] - 1) < 0.01
    # With rho = 0 the short regression is unbiased again.
    x2 = rng.standard_normal(n)
    y2 = x2 - 3 * z + rng.standard_normal(n)
    assert abs(ols(x2, y2)[0][1] - 1) < 0.02


def test_q10():
    assert F(1, 1 + 1) == F(1, 2)
    rng = np.random.default_rng(10)
    n = 400_000
    truth = rng.standard_normal(n)
    x = truth + rng.standard_normal(n)
    y = truth + rng.standard_normal(n)
    b1, b2 = ols(x, y)[0][1], ols(y, x)[0][1]
    assert abs(b1 - 0.5) < 0.01 and abs(1 / b2 - 2) < 0.04
    # Noise in y alone leaves the slope at 1.
    assert abs(ols(truth, y)[0][1] - 1) < 0.01
    # Total least squares: the leading eigenvector of the covariance matrix.
    w, v = np.linalg.eigh(np.cov(x, y))
    assert abs(v[1, 1] / v[0, 1] - 1) < 0.01
    # Change units of y and the total least squares line does not follow.
    w, v = np.linalg.eigh(np.cov(x, 10 * y))
    assert abs(v[1, 1] / v[0, 1] - 10) > 3
    # The formula.
    sxx, syy, sxy = 2.0, 2.0, 1.0
    assert ((syy - sxx) + math.sqrt((syy - sxx) ** 2 + 4 * sxy**2)) / (2 * sxy) == 1


def test_q11():
    rho = 0.9
    vif = 1 / (1 - rho**2)
    assert round(vif, 2) == 5.26 and round(math.sqrt(vif), 2) == 2.29
    # Variance of the sum and of the difference, in units of sigma^2 / n.
    inv = np.linalg.inv([[1, rho], [rho, 1]])
    assert abs(np.array([1, 1]) @ inv @ np.array([1, 1]) - 2 / (1 + rho)) < 1e-12
    assert abs(np.array([1, -1]) @ inv @ np.array([1, -1]) - 2 / (1 - rho)) < 1e-12
    assert round(2 / (1 + rho), 2) == 1.05 and round(2 / (1 - rho), 2) == 20
    assert round((2 / (1 - rho)) / (2 / (1 + rho)), 6) == 19
    assert round((0.2 / 2) / (0.8 / 97), 2) == 12.12
    assert round(st.f.ppf(0.95, 2, 97), 1) == 3.1
    rng = np.random.default_rng(11)
    n, reps = 100, 3000
    both_small, f_big = 0, 0
    bs = []
    for _ in range(reps):
        a = rng.standard_normal(n)
        b = 0.95 * a + math.sqrt(1 - 0.95**2) * rng.standard_normal(n)
        y = 0.2 * a + 0.2 * b + rng.standard_normal(n)
        beta, se, _, r2 = ols(np.column_stack([a, b]), y)
        t = beta[1:] / se[1:]
        f = (r2 / 2) / ((1 - r2) / (n - 3))
        both_small += max(abs(t)) < 2
        f_big += (max(abs(t)) < 2) and f > 3.1
        bs.append(beta[1:])
    assert both_small / reps > 0.5
    assert f_big / both_small > 0.5
    bs = np.array(bs)
    # Empirical check of the sum-versus-difference ratio at rho = 0.95: 39 to 1.
    ratio = np.var(bs[:, 0] - bs[:, 1]) / np.var(bs[:, 0] + bs[:, 1])
    assert abs(ratio - (1.95 / 0.05)) < 5


def test_q12():
    x, y = sp.symbols("x y")
    area = sp.Rational(1, 2)
    ex = sp.integrate(sp.integrate(x, (y, 0, x)), (x, 0, 1)) / area
    ey = sp.integrate(sp.integrate(y, (y, 0, x)), (x, 0, 1)) / area
    exx = sp.integrate(sp.integrate(x**2, (y, 0, x)), (x, 0, 1)) / area
    eyy = sp.integrate(sp.integrate(y**2, (y, 0, x)), (x, 0, 1)) / area
    exy = sp.integrate(sp.integrate(x * y, (y, 0, x)), (x, 0, 1)) / area
    assert (ex, ey) == (sp.Rational(2, 3), sp.Rational(1, 3))
    vx, vy, c = exx - ex**2, eyy - ey**2, exy - ex * ey
    assert vx == vy == sp.Rational(1, 18) and c == sp.Rational(1, 36)
    assert c / vx == sp.Rational(1, 2) and c / vy == sp.Rational(1, 2)
    assert ey - sp.Rational(1, 2) * ex == 0
    assert ex - sp.Rational(1, 2) * ey == sp.Rational(1, 2)
    assert (c / sp.sqrt(vx * vy)) == sp.Rational(1, 2)
    rng = np.random.default_rng(12)
    u = rng.random((400_000, 2))
    pts = np.column_stack([u.max(axis=1), u.min(axis=1)])
    assert abs(ols(pts[:, 0], pts[:, 1])[0][1] - 0.5) < 0.005
    assert abs(ols(pts[:, 1], pts[:, 0])[0][1] - 0.5) < 0.005
    assert abs(ols(pts[:, 1], pts[:, 0])[0][0] - 0.5) < 0.005


def lasso_cd(x, y, lam, start=None, sweeps=500):
    """Coordinate descent for 0.5 ||y - Xb||^2 + lam ||b||_1, cyclic from the given start."""
    b = np.zeros(x.shape[1]) if start is None else start.copy()
    for _ in range(sweeps):
        for j in range(x.shape[1]):
            r = y - x @ b + x[:, j] * b[j]
            z = x[:, j] @ r
            b[j] = np.sign(z) * max(abs(z) - lam, 0) / (x[:, j] @ x[:, j])
    return b


def test_q13():
    rng = np.random.default_rng(13)
    n, lam = 400, 10.0
    x = rng.standard_normal(n)
    y = 0.5 * x + rng.standard_normal(n)
    both = np.column_stack([x, x])
    assert np.linalg.matrix_rank(both.T @ both) == 1
    ridge = np.linalg.solve(both.T @ both + lam * np.eye(2), both.T @ y)
    assert abs(ridge[0] - ridge[1]) < 1e-12
    assert abs(ridge[0] - (x @ y) / (2 * x @ x + lam)) < 1e-12
    assert abs(ridge.sum() - (x @ y) / (x @ x + lam / 2)) < 1e-12
    # Lasso: every split with the same sign and sum has the same objective.
    single = lasso_cd(x[:, None], y, lam)[0]

    def objective(b):
        return 0.5 * np.sum((y - both @ b) ** 2) + lam * np.abs(b).sum()

    for split in (0.0, 0.25, 0.5, 1.0):
        assert abs(objective(np.array([split * single, (1 - split) * single])) - objective(np.array([single, 0.0]))) < 1e-9
    # Coordinate descent from zero loads the first column and leaves the other at zero.
    cd = lasso_cd(both, y, lam)
    assert abs(cd[0] - single) < 1e-8 and abs(cd[1]) < 1e-8
    # OLS: minimum-norm answer splits equally.
    mn = np.linalg.pinv(both) @ y
    assert abs(mn[0] - mn[1]) < 1e-10


def test_q14():
    rng = np.random.default_rng(14)
    q, _ = np.linalg.qr(rng.standard_normal((50, 4)))
    x, u = q[:, :3], q[:, 3]
    target = np.array([3.0, -0.5, 1.2])
    y = x @ target + 2 * u
    assert np.allclose(x.T @ y, target)
    assert np.allclose(lasso_cd(x, y, 1.0, sweeps=20), [2, 0, 0.2])
    ridge = np.linalg.solve(x.T @ x + np.eye(3), x.T @ y)
    assert np.allclose(ridge, [1.5, -0.25, 0.6])

    # Lasso as a bound-constrained quadratic program in b+ and b-.
    def split_obj(v):
        b = v[:3] - v[3:]
        return 0.5 * np.sum((y - x @ b) ** 2) + v.sum()

    res = minimize(split_obj, np.ones(6), bounds=[(0, None)] * 6, method="L-BFGS-B")
    assert np.allclose(res.x[:3] - res.x[3:], [2, 0, 0.2], atol=1e-4)
    # Without the half, the threshold is lam / 2.
    res = minimize(lambda v: np.sum((y - x @ v[:3]) ** 2) + 2 * np.abs(v[:3]).sum(), target, method="Powell")
    assert np.allclose(res.x[:3], [2, 0, 0.2], atol=1e-3)


def test_q15():
    rng = np.random.default_rng(15)
    n, reps = 200, 4000
    # Heteroskedastic noise and fat tails: slope still unbiased.
    x = rng.standard_normal((reps, n))
    noise = rng.standard_t(3, (reps, n)) * np.abs(x)
    b, t, _ = slope_t(x, 0.5 * x + noise)
    assert abs(b.mean() - 0.5) < 0.02
    # But the classical test is wrong: |t| > 1.96 too often at the true slope.
    t0 = (b - 0.5) / (b / t)
    assert (abs(t0) > 1.96).mean() > 0.1
    # Fat tails alone: the test is still about right, thanks to the central limit theorem.
    b2, t2, _ = slope_t(x, 0.5 * x + rng.standard_t(5, (reps, n)))
    t02 = (b2 - 0.5) / (b2 / t2)
    assert abs((abs(t02) > 1.96).mean() - 0.05) < 0.015
    # An omitted correlated variable: biased however large the sample.
    z = 0.5 * x + math.sqrt(0.75) * rng.standard_normal((reps, n))
    b3, _, _ = slope_t(x, 0.5 * x + z + rng.standard_normal((reps, n)))
    assert abs(b3.mean() - 1.0) < 0.02


def test_q16():
    n, p = 100, 20
    assert F(p, n - 1) == F(20, 99) and round(20 / 99, 2) == 0.20
    rng = np.random.default_rng(16)
    r2s, adj = [], []
    hits = 0
    for _ in range(4000):
        x = rng.standard_normal((n, p))
        y = rng.standard_normal(n)
        b, se, _, r2 = ols(x, y)
        r2s.append(r2)
        adj.append(1 - (1 - r2) * (n - 1) / (n - p - 1))
        hits += (np.abs(b[1:] / se[1:]) > 2).sum()
    assert abs(np.mean(r2s) - 20 / 99) < 0.005
    assert abs(np.mean(adj)) < 0.005
    assert abs(hits / 4000 - 20 * 2 * st.t.sf(2, 79)) < 0.05
    assert round(20 * 2 * st.t.sf(2, 79), 1) == 1.0


def test_q17():
    rng = np.random.default_rng(17)
    t_levels = {}
    for t in (250, 1000):
        x = rng.standard_normal((3000, t)).cumsum(axis=1)
        y = rng.standard_normal((3000, t)).cumsum(axis=1)
        b, ts, r2 = slope_t(x, y)
        t_levels[t] = (abs(ts) > 1.96).mean(), ts.std(), r2.mean(), b.std()
        db, dts, dr2 = slope_t(np.diff(x, axis=1), np.diff(y, axis=1))
        assert abs((abs(dts) > 1.96).mean() - 0.05) < 0.012
        assert dr2.mean() < 0.01
    assert abs(t_levels[250][0] - 0.85) < 0.03
    assert abs(t_levels[1000][0] - 0.93) < 0.03
    assert abs(t_levels[1000][1] / t_levels[250][1] - 2) < 0.2
    assert abs(t_levels[250][2] - 0.24) < 0.02
    assert abs(t_levels[1000][2] - 0.24) < 0.02
    assert abs(t_levels[1000][3] / t_levels[250][3] - 1) < 0.1


def test_q18():
    n, p = 1250, 500
    dense_r, dense_l, sparse_r, sparse_l = [], [], [], []

    def data(rng, beta):
        f = rng.standard_normal((2 * n, 10))
        load = rng.standard_normal((p, 10)) * math.sqrt(0.5 / 10)
        x = f @ load.T + math.sqrt(0.5) * rng.standard_normal((2 * n, p))
        return x, x @ beta + rng.standard_normal(2 * n)

    def best_oos(x, y):
        tr, te = slice(0, n), slice(n, 2 * n)
        best_ridge, best_lasso = -9.0, -9.0
        tot = (y[te] - y[te].mean()) @ (y[te] - y[te].mean())
        xx, xy = x[tr].T @ x[tr], x[tr].T @ y[tr]
        for lam in (30, 100, 300, 1000, 3000, 10000):
            b = np.linalg.solve(xx + lam * np.eye(p), xy)
            e = y[te] - x[te] @ b
            best_ridge = max(best_ridge, 1 - e @ e / tot)
        for a in (0.01, 0.02, 0.03, 0.05, 0.08, 0.12):
            b = Lasso(alpha=a, fit_intercept=False, max_iter=1000, tol=1e-3).fit(x[tr], y[tr]).coef_
            e = y[te] - x[te] @ b
            best_lasso = max(best_lasso, 1 - e @ e / tot)
        return best_ridge, best_lasso

    for seed in range(3):
        rng = np.random.default_rng(1800 + seed)
        r, la = best_oos(*data(rng, rng.standard_normal(p) * 0.008))
        dense_r.append(r)
        dense_l.append(la)
        b = np.zeros(p)
        b[:5] = rng.choice([-1, 1], 5) * 0.08
        r, la = best_oos(*data(rng, b))
        sparse_r.append(r)
        sparse_l.append(la)
    # Many weak signals favour ridge; a few strong ones favour lasso.
    assert np.mean(dense_r) > np.mean(dense_l)
    assert np.mean(sparse_l) > np.mean(sparse_r)
    assert abs(np.mean(dense_r) - 0.011) < 0.004
    assert abs(np.mean(dense_l) - 0.008) < 0.004


def test_q19():
    # With a stale chance of 1/2: slope 1/2 at lag 0, 1/4 at lag 1, 1/8 at lag 2.
    assert sum(F(1, 2 ** (k + 1)) for k in range(0, 40)) < 1
    assert 1 - sum(F(1, 2 ** (k + 1)) for k in range(0, 40)) == F(1, 2**40)
    rng = np.random.default_rng(19)
    n = 400_000
    beta = 1.2
    mkt = rng.standard_normal(n)
    true_ret = beta * mkt
    trades = rng.random(n) < 0.5
    cum = true_ret.cumsum()
    # Forward-fill the last traded price.
    idx = np.where(trades, np.arange(n), 0)
    np.maximum.accumulate(idx, out=idx)
    seen = cum[idx]
    obs = np.diff(seen)
    m = mkt[1:]
    slope0 = ols(m, obs)[0][1]
    assert abs(slope0 - beta / 2) < 0.01
    lags = np.column_stack([m[5:], m[4:-1], m[3:-2], m[2:-3], m[1:-4], m[:-5]])
    coefs = ols(lags, obs[5:])[0][1:]
    assert abs(coefs[0] - beta / 2) < 0.01
    assert abs(coefs[1] - beta / 4) < 0.01
    assert abs(coefs[2] - beta / 8) < 0.01
    assert abs(coefs.sum() - beta) < 0.05
    # The longer horizon cure: weekly returns recover most of the beta.
    weekly = seen[5::5][1:] - seen[5::5][:-1]
    w_mkt = (cum[5::5][1:] - cum[5::5][:-1]) / beta
    assert abs(ols(w_mkt, weekly)[0][1] - 0.97) < 0.03
    assert sum(F(1, 2**k) for k in range(1, 6)) == F(31, 32)
    assert F(31, 32) / 5 == F(31, 160)
    assert round(1.2 * (1 - 31 / 160), 2) == 0.97


def test_q20():
    rng = np.random.default_rng(20)
    n, reps = 500, 5000
    x = rng.standard_normal((reps, n))
    y = np.abs(x) * rng.standard_normal((reps, n))
    b, t, _ = slope_t(x, y)
    classical = (b / t).mean()
    assert abs(b.std() * math.sqrt(n) - math.sqrt(3)) < 0.1
    assert abs(classical * math.sqrt(n) - 1) < 0.03
    assert round(math.sqrt(3), 2) == 1.73
    assert abs(st.norm.moment(4) - 3) < 1e-9
    assert F(1, 3) == F(1, 3)
    # White standard errors recover the truth.
    xd = x - x.mean(axis=1, keepdims=True)
    e = y - y.mean(axis=1, keepdims=True) - b[:, None] * xd
    hc = np.sqrt(((xd * xd) * (e * e)).sum(axis=1)) / (xd * xd).sum(axis=1)
    assert abs(hc.mean() / b.std() - 1) < 0.05
    # WLS with the true weights: mean of y/x has variance 1/n, three times lower.
    w = (y / x).mean(axis=1)
    assert abs(w.std() * math.sqrt(n) - 1) < 0.05
    # Inverse-variance averaging of two estimates with standard errors 2 and 1.
    assert (F(1, 4) / (F(1, 4) + 1), 1 / (F(1, 4) + 1)) == (F(1, 5), F(4, 5))
    assert round(math.sqrt(0.8), 2) == 0.89
    # Averages of m_i observations: weights proportional to m_i beat equal weights.
    m = rng.integers(1, 50, 300)
    xs = rng.standard_normal(300)
    wls = 1 / np.sum(m * xs**2)
    equal = np.sum(xs**2 / m) / np.sum(xs**2) ** 2
    assert wls < equal


def test_q21():
    h = 20

    def factor(phi):
        return 1 + 2 * sum(phi**k * (1 - k / h) for k in range(1, h))

    assert factor(0) == 1
    assert abs(factor(1) - 20) < 1e-9 and round(math.sqrt(20), 2) == 4.47
    assert round(factor(0.9), 1) == 11.1 and round(math.sqrt(factor(0.9)), 2) == 3.33
    rng = np.random.default_rng(21)
    n, reps = 2000, 500
    out = {}
    for phi in (0.0, 0.9):
        bs, ses, nw = [], [], []
        for _ in range(reps):
            e = rng.standard_normal(n + h).cumsum()
            y = e[h:] - e[:-h]
            eps = rng.standard_normal(n)
            x = np.empty(n)
            x[0] = eps[0] / math.sqrt(1 - phi**2)
            for t in range(1, n):
                x[t] = phi * x[t - 1] + eps[t]
            xd, yd = x - x.mean(), y - y.mean()
            b = xd @ yd / (xd @ xd)
            u = yd - b * xd
            bs.append(b)
            ses.append(math.sqrt(u @ u / (n - 2) / (xd @ xd)))
            s = xd * u
            lag = 40
            acc = s @ s
            for k in range(1, lag + 1):
                acc += 2 * (1 - k / (lag + 1)) * (s[k:] @ s[:-k])
            nw.append(math.sqrt(acc) / (xd @ xd))
        out[phi] = np.std(bs) / np.mean(ses), np.mean(nw) / np.std(bs)
    assert abs(out[0.0][0] - 1) < 0.1
    assert abs(out[0.9][0] - 3.33) < 0.35
    # Newey-West with a long enough lag gets close to the true standard error.
    assert abs(out[0.9][1] - 1) < 0.2
    # AR(1) regressor with AR(1) errors.
    f = (1 + 0.81) / (1 - 0.81)
    assert round(f, 2) == 9.53 and round(math.sqrt(f), 2) == 3.09
    # Durbin-Watson is about 2(1 - rho).
    u = np.empty(100_000)
    eps = rng.standard_normal(100_000)
    u[0] = eps[0]
    for t in range(1, 100_000):
        u[t] = 0.9 * u[t - 1] + eps[t]
    dw = np.sum(np.diff(u) ** 2) / np.sum(u**2)
    assert abs(dw - 2 * (1 - 0.9)) < 0.01


def joint_r2(r1, r2, rho):
    return (r1**2 + r2**2 - 2 * r1 * r2 * rho) / (1 - rho**2)


def test_q22():
    r = 0.6
    assert abs(joint_r2(r, r, 0.5) - 2 * r**2 / 1.5) < 1e-12
    assert abs(joint_r2(r, r, 0.9999) - 0.36) < 1e-3
    low = 2 * r**2 - 1
    assert round(low, 2) == -0.28
    assert abs(joint_r2(r, r, low) - 1) < 1e-12
    assert round(joint_r2(r, r, 0.0), 2) == 0.72
    # The correlation matrix is PSD exactly on the allowed range.
    for rho, ok in [(-0.28, True), (-0.29, False), (0.99, True)]:
        m = np.array([[1, rho, r], [rho, 1, r], [r, r, 1]])
        assert (np.linalg.eigvalsh(m).min() >= -1e-12) == ok
    assert round(joint_r2(0, 0.4, 0.9), 3) == 0.842
    assert round(0.16 / 0.19, 3) == 0.842
    assert 2 * 0.36 == 0.72
    assert round(0.4**2, 2) == 0.16
    # Suppressor: x2 has zero correlation with y, yet adds a lot.
    rng = np.random.default_rng(22)
    n = 300_000
    cov = np.array([[1, 0.9, 0.0], [0.9, 1, 0.4], [0.0, 0.4, 1]])
    d = rng.multivariate_normal([0, 0, 0], cov, n)
    assert abs(ols(d[:, :2], d[:, 2])[3] - 0.842) < 0.005
    assert abs(ols(d[:, 1], d[:, 2])[3] - 0.16) < 0.005


def test_q23():
    a = 0.05
    assert round(math.sqrt(joint_r2(a, a, 0.5)), 4) == 0.0577
    assert round(math.sqrt(joint_r2(a, a, 0.0)), 4) == 0.0707
    assert round(math.sqrt(joint_r2(a, a, -0.5)), 4) == 0.1
    # Second part: unequal correlations.
    r = np.array([0.05, 0.02])
    s = np.array([[1, 0.5], [0.5, 1]])
    w = np.linalg.solve(s, r)
    assert w[0] > 0 and w[1] < 0
    assert round(w[0], 4) == 0.0533 and round(w[1], 4) == -0.0067
    assert round(math.sqrt(joint_r2(0.05, 0.02, 0.5)), 4) == 0.0503
    # Regression recovers those weights.
    rng = np.random.default_rng(23)
    n = 2_000_000
    cov = np.array([[1, 0.5, 0.05], [0.5, 1, 0.02], [0.05, 0.02, 1]])
    d = rng.multivariate_normal([0, 0, 0], cov, n)
    b = ols(d[:, :2], d[:, 2])[0][1:]
    assert abs(b[0] - 0.0533) < 0.002 and abs(b[1] + 0.0067) < 0.002
    # Sharpe of a daily position in the best combination, against the single signal.
    assert round(0.0577 * math.sqrt(252), 2) == 0.92
    assert round(0.05 * math.sqrt(252), 2) == 0.79
    assert 0.5 * 0.05 == 0.025


def test_q24():
    lam, beta, sigma = sp.symbols("lambda beta sigma", positive=True)
    mse = (sigma**2 + lam**2 * beta**2) / (1 + lam) ** 2
    opt = sp.solve(sp.diff(mse, lam), lam)
    assert opt == [sigma**2 / beta**2]
    best = sp.simplify(mse.subs(lam, sigma**2 / beta**2))
    assert sp.simplify(best - sigma**2 * beta**2 / (sigma**2 + beta**2)) == 0
    assert mse.subs({lam: 4, beta: sp.Rational(1, 2), sigma: 1}) == sp.Rational(1, 5)
    assert sp.Rational(1, 1 + 4) == sp.Rational(1, 5)
    rng = np.random.default_rng(24)
    ols_est = 0.5 + rng.standard_normal(400_000)
    assert abs(np.mean((ols_est - 0.5) ** 2) - 1) < 0.01
    assert abs(np.mean((ols_est / 5 - 0.5) ** 2) - 0.2) < 0.003
    # The Bayesian reading: prior N(0, 0.25), noise 1, posterior mean shrinks by 1/5.
    prior_var = 0.25
    assert abs(prior_var / (prior_var + 1) - 0.2) < 1e-12
    # A strong signal should barely shrink: beta = 5, lambda* = 0.04.
    assert 1 / 25 == 0.04
    # Eigen directions shrink by d^2 / (d^2 + lambda).
    x = rng.standard_normal((100, 5))
    u, d, vt = np.linalg.svd(x, full_matrices=False)
    y = rng.standard_normal(100)
    direct = np.linalg.solve(x.T @ x + 3 * np.eye(5), x.T @ y)
    via = vt.T @ np.diag(d / (d**2 + 3)) @ u.T @ y
    assert np.allclose(direct, via)


def test_q25():
    v = 1 - 2 / math.pi
    assert round(v, 3) == 0.363
    rho = 0.5
    assert round(math.sqrt(rho**2 * v / (rho**2 * v + 1 - rho**2)), 3) == 0.329
    assert round(rho * v / (rho**2 * v + 1 - rho**2), 3) == 0.216
    rng = np.random.default_rng(25)
    n = 2_000_000
    x = rng.standard_normal(n)
    y = rho * x + math.sqrt(1 - rho**2) * rng.standard_normal(n)
    keep = x > 0
    assert abs(ols(x[keep], y[keep])[0][1] - 0.5) < 0.005
    assert abs(np.corrcoef(x[keep], y[keep])[0, 1] - 0.329) < 0.003
    keep = y > 0
    assert abs(ols(x[keep], y[keep])[0][1] - 0.216) < 0.003
    assert abs(np.corrcoef(x[keep], y[keep])[0, 1] - 0.329) < 0.003
    assert abs(np.var(x[x > 0]) - v) < 0.002
    # Selecting on y with a strongly negative cut for the other sign.
    keep = y > 1
    assert ols(x[keep], y[keep])[0][1] < 0.216


def test_q26():
    n = 1000
    sxx, xi, ei = 1000.0, 10.0, 2.0
    h = 1 / n + xi**2 / sxx
    assert round(h, 3) == 0.101
    assert round(ei / (1 - h), 2) == 2.22
    assert round(xi * ei / ((1 - h) * sxx), 4) == 0.0222
    assert round(h / (2 / n), 1) == 50.5
    rng = np.random.default_rng(26)
    x = rng.standard_normal(n)
    x[0] = xi
    x[1:] *= math.sqrt((sxx - xi**2) / (x[1:] @ x[1:]))  # about the printed sum of squares
    x -= x.mean()  # the deletion formulas below hold exactly once the column has mean zero
    y = 0.2 * x + rng.standard_normal(n)
    b, _, e, _ = ols(x, y)
    sxx_real = x @ x
    h_real = 1 / n + x[0] ** 2 / sxx_real
    b_out = ols(x[1:], y[1:])[0]
    # The deletion formulas are exact.
    assert abs((b[1] - b_out[1]) - x[0] * e[0] / ((1 - h_real) * sxx_real)) < 1e-9
    assert abs((y[0] - (b_out[0] + b_out[1] * x[0])) - e[0] / (1 - h_real)) < 1e-9
    # The hat matrix diagonal sums to p.
    design = np.column_stack([np.ones(n), x])
    hat = design @ np.linalg.inv(design.T @ design) @ design.T
    assert abs(np.trace(hat) - 2) < 1e-9
    assert abs(hat[0, 0] - h_real) < 1e-9
    # Huber downweights it: the influence of the point is bounded.
    y2 = y.copy()
    y2[0] += 40
    b_ols = ols(x, y2)[0][1]
    b_h = b[1]
    for _ in range(50):
        r = y2 - np.column_stack([np.ones(n), x]) @ np.array([0.0, b_h])
        w = np.minimum(1, 1.345 / np.maximum(np.abs(r), 1e-9))
        xw = x - (w * x).sum() / w.sum()
        b_h = (w * xw * y2).sum() / (w * xw * xw).sum()
    assert abs(b_h - b[1]) < abs(b_ols - b[1]) / 4
    # But only because that residual stayed large. A point of higher leverage has dragged the line onto itself:
    # its residual sits in the quadratic zone, so Huber keeps its whole pull, and limiting x is what removes it.
    x3 = rng.standard_normal(n)
    y3 = rng.standard_normal(n)
    without = ols(x3[1:], y3[1:])[0][1]
    x3[0], y3[0] = 100.0, 10.0
    b_ols3 = ols(x3, y3)[0][1]
    d3 = np.column_stack([np.ones(n), x3])
    coef = ols(x3, y3)[0]
    for _ in range(200):
        w = np.minimum(1, 1.345 / np.maximum(np.abs(y3 - d3 @ coef), 1e-9))
        coef = np.linalg.solve(d3.T @ (w[:, None] * d3), d3.T @ (w * y3))
    assert abs(y3[0] - d3[0] @ coef) < 1.345
    assert abs(coef[1] - b_ols3) < 0.01
    assert abs(coef[1] - without) > 5 * abs(coef[1] - b_ols3)
    b_win = ols(np.clip(x3, *np.quantile(x3, [0.01, 0.99])), y3)[0][1]
    assert abs(b_win - without) < abs(b_ols3 - without) / 3


def test_q27():
    # y = x + u, x = z + u + v, unit variances.
    var_x = 3
    cov_xy = 3 + 1
    assert F(cov_xy, var_x) == F(4, 3) and round(4 / 3, 2) == 1.33
    assert F(1, 1) == 1
    rng = np.random.default_rng(27)
    n = 500_000
    z, u, v = rng.standard_normal((3, n))
    x = z + u + v
    y = x + u
    assert abs(ols(x, y)[0][1] - 4 / 3) < 0.005
    iv = np.cov(z, y)[0, 1] / np.cov(z, x)[0, 1]
    assert abs(iv - 1) < 0.01
    # Two-stage least squares gives the same point estimate.
    fs = ols(z, x)[0]
    xhat = fs[0] + fs[1] * z
    assert abs(ols(xhat, y)[0][1] - iv) < 1e-9
    assert abs(np.corrcoef(z, x)[0, 1] ** 2 - 1 / 3) < 0.005
    # Weak instrument, small sample: the distribution is wide and centred towards OLS.
    ests = []
    for _ in range(4000):
        z, u, v = rng.standard_normal((3, 200))
        x = 0.1 * z + u + v
        y = x + u
        ests.append(np.cov(z, y)[0, 1] / np.cov(z, x)[0, 1])
    ests = np.array(ests)
    assert 1.05 < np.median(ests) < 4 / 3 + 0.1
    assert np.median(ests) > 1.15
    assert np.percentile(ests, 75) - np.percentile(ests, 25) > 0.5


def test_q28():
    n, p, r2 = 1000, 20, 0.01
    assert round(r2 - (p / n) * (1 - r2), 4) == -0.0098
    assert round(p * (1 - r2) / r2) == 1980
    assert round(1 * (1 - r2) / r2) == 99
    rng = np.random.default_rng(28)
    beta = np.full(p, math.sqrt(r2 / (1 - r2) / p))
    sigma2 = 1.0

    def oos(n_obs, reps):
        vals = []
        for _ in range(reps):
            x = rng.standard_normal((n_obs, p))
            y = x @ beta + rng.standard_normal(n_obs)
            b = np.linalg.lstsq(x, y, rcond=None)[0]
            mse = sigma2 + (b - beta) @ (b - beta)
            total = sigma2 + beta @ beta
            vals.append(1 - mse / total)
        return np.mean(vals)

    assert abs(oos(1000, 500) + 0.0098) < 0.0015
    assert abs(oos(1980, 500)) < 0.001
    # In-sample the same fit looks good: about R^2 + p/n, so 3%.
    in_sample = []
    for _ in range(200):
        x = rng.standard_normal((1000, p))
        y = x @ beta + rng.standard_normal(1000)
        in_sample.append(ols(x, y)[3])
    assert abs(np.mean(in_sample) - 0.03) < 0.002


def test_q29():
    t, rho, c = 120, 0.95, -0.9
    assert round(-(1 + 3 * rho) / t, 3) == -0.032
    assert round(1 + 3 * rho, 2) == 3.85
    assert round(0.9 * (1 + 3 * rho) / t, 3) == 0.029
    assert round(math.log(2) / -math.log(0.95), 1) == 13.5
    rng = np.random.default_rng(29)
    reps = 20_000
    v = rng.standard_normal((reps, t + 1))
    w = rng.standard_normal((reps, t))
    u = c * v[:, 1:] + math.sqrt(1 - c * c) * w
    x = np.empty((reps, t + 1))
    x[:, 0] = v[:, 0] / math.sqrt(1 - rho * rho)
    for k in range(1, t + 1):
        x[:, k] = rho * x[:, k - 1] + v[:, k]
    b, ts, _ = slope_t(x[:, :-1], u)
    rhohat, _, _ = slope_t(x[:, :-1], x[:, 1:])
    assert abs(rhohat.mean() - rho + 0.036) < 0.003
    assert abs(b.mean() - 0.032) < 0.002
    assert abs(ts.mean() - 0.7) < 0.05
    assert abs((ts > 1.645).mean() - 0.16) < 0.01
    # The board estimate: long-run variance of x, the standard error it implies, the range of rejection rates.
    assert round(1 / (1 - rho * rho), 1) == 10.3
    assert round(1 / (3.2 * math.sqrt(120)), 3) == 0.029
    assert round(st.norm.sf(1.645 - 0.7), 2) == 0.17 and round(st.norm.sf(1.645 - 1), 2) == 0.26
    # The simulated rate is below that range, and a spread under 1 is what closes the gap.
    assert (ts > 1.645).mean() < st.norm.sf(1.645 - 0.7)
    assert ts.std() < 1
    assert abs(st.norm.sf((1.645 - ts.mean()) / ts.std()) - (ts > 1.645).mean()) < 0.01
    # The slope error is the persistence error times the regression of u on v.
    e_rho = rhohat - rho
    assert abs(np.polyfit(e_rho, b, 1)[0] + 0.9) < 0.02
    assert round(np.log(2) / -np.log(rhohat.mean()), 1) == 7.8
    assert round(rhohat.mean(), 3) == 0.915
    assert round(float(np.mean(b)), 3) == 0.032
    # With c = 0 the bias disappears.
    b0, ts0, _ = slope_t(x[:, :-1], w)
    assert abs(b0.mean()) < 0.002 and abs((ts0 > 1.645).mean() - 0.05) < 0.01


def test_q30():
    b1 = sp.Rational(36, 100) / (1 + sp.Rational(1, 2) - sp.Rational(64, 100))
    b2 = sp.Rational(4, 5) * sp.Rational(1, 2) / (1 + sp.Rational(1, 2) - sp.Rational(64, 100))
    assert b1 == sp.Rational(18, 43) and round(float(b1), 2) == 0.42
    assert b2 == sp.Rational(20, 43) and round(float(b2), 2) == 0.47
    # Solve the normal equations symbolically.
    rho, s2, a, c = sp.symbols("rho s2 a c")
    sol = sp.solve([(1 + s2) * a + rho * c - 1, rho * a + c - rho], [a, c])
    assert sp.simplify(sol[a] - (1 - rho**2) / (1 + s2 - rho**2)) == 0
    assert sp.simplify(sol[c] - rho * s2 / (1 + s2 - rho**2)) == 0
    assert sp.limit(sol[c], s2, sp.oo) == rho
    assert sol[c].subs(s2, 0) == 0
    rng = np.random.default_rng(30)
    n = 500_000
    x1 = rng.standard_normal(n)
    x2 = 0.8 * x1 + 0.6 * rng.standard_normal(n)
    noisy = x1 + math.sqrt(0.5) * rng.standard_normal(n)
    y = x1 + rng.standard_normal(n)
    coefs = ols(np.column_stack([noisy, x2]), y)[0][1:]
    assert abs(coefs[0] - 18 / 43) < 0.005 and abs(coefs[1] - 20 / 43) < 0.005
    # A t-statistic that grows with the sample, though x2 has no effect on y.
    x1s = rng.standard_normal(2500)
    x2s = 0.8 * x1s + 0.6 * rng.standard_normal(2500)
    ns = x1s + math.sqrt(0.5) * rng.standard_normal(2500)
    ys = x1s + rng.standard_normal(2500)
    b, se, _, _ = ols(np.column_stack([ns, x2s]), ys)
    assert b[2] / se[2] > 8
