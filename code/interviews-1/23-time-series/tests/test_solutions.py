"""Every number printed in the answers of "Time Series": exact values and simulated series."""
import math

import numpy as np
from scipy import stats

NONNUMERIC = {}


def ar1(rng, phi, t, m, s=1.0, burn=None):
    x = rng.normal(0, s / math.sqrt(1 - phi * phi), m) if burn is None else np.zeros(m)
    out = np.empty((m, t))
    for i in range(t):
        x = phi * x + rng.normal(0, s, m)
        out[:, i] = x
    return out


def acf(x, k):
    x = x - x.mean()
    return (x[k:] * x[:-k]).sum() / (x * x).sum()


def garch(rng, n, a=0.1, b=0.85, w=2e-6, burn=2000):
    v = w / (1 - a - b)
    s2 = v
    z = rng.standard_normal(n + burn)
    r = np.empty(n + burn)
    h = np.empty(n + burn)
    for i in range(n + burn):
        h[i] = s2
        r[i] = math.sqrt(s2) * z[i]
        s2 = w + a * r[i] ** 2 + b * s2
    return r[burn:], h[burn:]


def test_q1():
    rng = np.random.default_rng(1)
    # (f): the variance at every t is the same, cos^2 + sin^2 = 1.
    a, b = rng.standard_normal((2, 2_000_000))
    for t in (0.0, 1.0, 7.3):
        assert abs((a * math.cos(t) + b * math.sin(t)).var() - 1) < 0.005
    u = a * math.cos(2.0) + b * math.sin(2.0)
    v = a * math.cos(5.0) + b * math.sin(5.0)
    assert abs((u * v).mean() - math.cos(3.0)) < 0.005
    # (b): the variance grows.
    w = np.cumsum(rng.standard_normal((20000, 100)), axis=1)
    assert abs(w[:, 99].var() / w[:, 24].var() - 4) < 0.2
    # (f) along one path: the mean is recovered, the second moment is not. Across paths it averages to 1.
    days = np.arange(2_000_000)
    for p, q in ((1.5, 0.2), (0.3, 0.1), (2.0, 2.0)):
        path = p * np.cos(days) + q * np.sin(days)
        assert abs(path.mean()) < 0.001
        assert abs((path**2).mean() - (p * p + q * q) / 2) < 0.001
    assert abs(((a * a + b * b) / 2).mean() - 1) < 0.005


def test_q2():
    assert round(1 / (1 - 0.49), 2) == 1.96
    assert round(0.7**3, 3) == 0.343
    assert round(math.log(2) / -math.log(0.7), 2) == 1.94
    assert round(0.7**2, 2) == 0.49 and round(0.7**4, 2) == 0.24
    rng = np.random.default_rng(2)
    x = ar1(rng, 0.7, 2000, 1)[0]
    x = ar1(rng, 0.7, 400_000, 1)[0]
    assert abs(x.var() - 1.96) < 0.03
    assert abs(acf(x, 3) - 0.343) < 0.01
    assert abs(np.corrcoef(x[:-2], x[2:])[0, 1] ** 2 - 0.24) < 0.01


def test_q3():
    assert 1 + 0.25 == 1.25
    assert 0.5 / 1.25 == 0.4
    assert 2.0 / (1 + 4.0) == 0.4
    assert max(t / (1 + t * t) for t in np.linspace(-3, 3, 6001)) == 0.5
    rng = np.random.default_rng(3)
    e = rng.standard_normal(2_000_001)
    x = e[1:] + 0.5 * e[:-1]
    assert abs(x.var() - 1.25) < 0.01
    assert abs(acf(x, 1) - 0.4) < 0.005
    assert abs(acf(x, 2)) < 0.005


def test_q4():
    assert round(1 - 0.94, 2) == 0.06
    assert round(math.log(0.5) / math.log(0.94), 1) == 11.2
    assert round((1 + 0.94) / (1 - 0.94), 1) == 32.3
    assert round(1 / (1 - 0.94), 1) == 16.7
    assert round(math.sqrt(0.94 + 0.06 * 25), 2) == 1.56
    w = 0.06 * 0.94 ** np.arange(5000)
    assert abs(w.sum() - 1) < 1e-9
    assert round(1 / (w * w).sum(), 1) == 32.3
    assert abs(w[:11].sum() - 0.5) < 0.03


def test_q5():
    r = np.roots([1, -1.2, 0.5])
    assert abs(abs(r[0]) - math.sqrt(0.5)) < 1e-12
    assert round(abs(r[0]), 3) == 0.707
    ang = abs(np.angle(r[0]))
    assert round(ang, 3) == 0.558
    assert round(2 * math.pi / ang, 1) == 11.3
    rho1 = 1.2 / 1.5
    rho2 = 1.2 * rho1 - 0.5
    assert round(rho1, 9) == 0.8 and round(rho2, 2) == 0.46
    rng = np.random.default_rng(5)
    e = rng.standard_normal(400_000)
    x = np.zeros(400_000)
    for t in range(2, 400_000):
        x[t] = 1.2 * x[t - 1] - 0.5 * x[t - 2] + e[t]
    assert abs(acf(x, 1) - 0.8) < 0.005 and abs(acf(x, 2) - 0.46) < 0.01
    # The impulse response oscillates and decays.
    g = [1.0, 1.2]
    for _ in range(14):
        g.append(1.2 * g[-1] - 0.5 * g[-2])
    assert round(max(g), 2) == 1.2 and min(g) < -0.1 and g[1] > g[0]
    assert g[4] > 0 > g[5] and abs(g[15]) < 0.1


def test_q6():
    assert round(2 / math.sqrt(500), 3) == 0.089
    rng = np.random.default_rng(6)
    x = ar1(rng, 0.6, 400_000, 1)[0]
    assert abs(acf(x, 1) - 0.6) < 0.005 and abs(acf(x, 2) - 0.36) < 0.005 and abs(acf(x, 3) - 0.216) < 0.006
    # Partial autocorrelation at lag 2 of the AR(1) is zero.
    c = np.linalg.lstsq(np.column_stack([x[1:-1], x[:-2]]), x[2:], rcond=None)[0]
    assert abs(c[1]) < 0.005 and abs(c[0] - 0.6) < 0.005
    # MA(1): the partial autocorrelations alternate and decay, lag 2 is -theta^2 / (1 + theta^2 + theta^4).
    e = rng.standard_normal(400_001)
    y = e[1:] + 0.5 * e[:-1]
    d = np.linalg.lstsq(np.column_stack([y[1:-1], y[:-2]]), y[2:], rcond=None)[0]
    assert abs(d[1] + 0.25 / (1 + 0.25 + 0.0625)) < 0.005


def test_q7():
    def vr(q, rho=0.1):
        return 1 + 2 * sum((1 - k / q) * rho**k for k in range(1, q))

    assert round(vr(2), 2) == 1.1
    assert round(vr(5), 3) == 1.173
    lim = (1 + 0.1) / (1 - 0.1)
    assert round(lim, 3) == 1.222
    assert round(math.sqrt(lim) - 1, 3) == 0.106
    rng = np.random.default_rng(7)
    x = ar1(rng, 0.1, 1_000_000, 1)[0]
    s5 = np.convolve(x, np.ones(5), "valid")
    assert abs(s5.var() / (5 * x.var()) - vr(5)) < 0.01
    assert abs(vr(250) - lim) < 0.003
    # The long horizon directly: the ratio of the real volatility to the square-root figure.
    y = ar1(rng, 0.1, 250, 200_000)
    assert abs(y.sum(axis=1).std() / (math.sqrt(250) * y[:, -1].std()) - 1.106) < 0.008
    assert round(1 / math.sqrt(lim), 1) == 0.9
    # With no autocorrelation, nothing is understated.
    assert vr(250, 0.0) == 1
    assert round((1 + 0.3) / (1 - 0.3), 3) == 1.857
    assert round(math.sqrt(1.857), 2) == 1.36


def test_q8():
    v = 2e-6 / 0.05
    assert abs(v - 4e-5) < 1e-18
    assert round(math.sqrt(v * 252), 3) == 0.100
    assert round(math.log(0.5) / math.log(0.95), 1) == 13.5
    f = v + 0.95**10 * (4 * v - v)
    assert round(f / v, 2) == 2.8
    assert round(math.sqrt(f * 252), 3) == 0.168
    rng = np.random.default_rng(8)
    r, _ = garch(rng, 600_000)
    assert abs(r.var() / v - 1) < 0.04
    # Conditional forecast by simulation from four times the long-run variance.
    m = 400_000
    s2 = np.full(m, 4 * v)
    for _ in range(10):
        ri = np.sqrt(s2) * rng.standard_normal(m)
        s2 = 2e-6 + 0.1 * ri**2 + 0.85 * s2
    assert abs(s2.mean() / v - 2.8) < 0.03


def test_q9():
    v = math.log(1.02) ** 2 / (4 * math.log(2))
    assert round(math.sqrt(v) * 100, 2) == 1.19
    rng = np.random.default_rng(9)
    n, m = 2000, 40000
    d = rng.normal(0, math.sqrt(1 / n), (m, n))
    np.cumsum(d, axis=1, out=d)
    high = np.maximum(d.max(1), 0)
    low = np.minimum(d.min(1), 0)
    pk = (high - low) ** 2 / (4 * math.log(2))
    # Discrete sampling biases the range down, by 2 * 0.5826 * sqrt(dt).
    assert abs(((high - low + 2 * 0.5826 * math.sqrt(1 / n)) ** 2).mean() / (4 * math.log(2)) - 1) < 0.015
    c = d[:, -1] ** 2
    ratio = c.var() / pk.var()
    assert 4.3 < ratio < 5.5
    assert round(2 / 0.407, 1) == 4.9
    # Coarse sampling: only 78 prints a day. The shortfall is in the variance, half of it in the volatility.
    def coarse(prints):
        path = np.cumsum(rng.normal(0, math.sqrt(1 / prints), (m, prints)), axis=1)
        rng_hi = np.maximum(path.max(1), 0)
        rng_lo = np.minimum(path.min(1), 0)
        return ((rng_hi - rng_lo) ** 2).mean() / (4 * math.log(2)), (rng_hi - rng_lo).mean()

    var78, mean78 = coarse(78)
    assert round(1 - var78, 2) == 0.14
    assert round(1 - math.sqrt(var78), 2) == 0.07
    # Second route, the discrete-range correction on the mean range. And more prints close the gap.
    assert abs(mean78 + 2 * 0.5826 * math.sqrt(1 / 78) - math.sqrt(8 / math.pi)) < 0.01
    assert var78 < coarse(390)[0] < 1


def test_q10():
    s2, eta2 = 1e-4, 0.0005**2
    assert round(2 * 78 * eta2 / s2, 2) == 0.39
    assert round(2 * 390 * eta2 / s2, 2) == 1.95
    rng = np.random.default_rng(10)
    for n in (78, 390):
        m = 40000
        d = rng.normal(0, math.sqrt(s2 / n), (m, n))
        p = np.cumsum(d, axis=1)
        p = np.column_stack([np.zeros(m), p]) + rng.normal(0, 0.0005, (m, n + 1))
        ret = np.diff(p, axis=1)
        rv = (ret**2).sum(1)
        assert abs(rv.mean() / (s2 + 2 * n * eta2) - 1) < 0.01
        cov = (ret[:, 1:] * ret[:, :-1]).mean()
        assert abs(cov + eta2) < 2e-8
    # Roll: the spread from the autocovariance.
    assert abs(2 * math.sqrt(eta2) - 0.001) < 1e-12


def _df(rng, t, m, const):
    w = np.cumsum(rng.standard_normal((m, t + 1)), axis=1)
    x = w[:, :-1]
    y = w[:, 1:]
    if const:
        xd = x - x.mean(1, keepdims=True)
        yd = y - y.mean(1, keepdims=True)
    else:
        xd, yd = x, y
    b = (xd * yd).sum(1) / (xd * xd).sum(1)
    res = yd - b[:, None] * xd
    s2 = (res * res).sum(1) / (t - 1 - (1 if const else 0))
    tt = (b - 1) / np.sqrt(s2 / (xd * xd).sum(1))
    return b, tt


def test_q11():
    rng = np.random.default_rng(11)
    b0, t0 = _df(rng, 250, 40000, False)
    b1, t1 = _df(rng, 250, 40000, True)
    assert abs(np.quantile(t0, 0.05) + 1.95) < 0.03
    assert abs(np.quantile(t1, 0.05) + 2.87) < 0.03
    assert abs(b1.mean() - (1 - 5.3 / 250)) < 0.002
    assert round(1 - 5.3 / 250, 3) == 0.979
    assert abs(((t1 < -1.645).mean()) - 0.45) < 0.03
    assert round(math.log(0.5) / math.log(0.979), 0) == 33


def test_q12():
    t = 0.02 / (0.2 / math.sqrt(400))
    assert round(t, 2) == 2.0
    lrv = 1 + 2 * 0.2 / 0.8
    assert lrv == 1.5
    assert round(t / math.sqrt(lrv), 2) == 1.63
    assert round(2 * (1 - stats.norm.cdf(2.0)), 3) == 0.046
    assert round(2 * (1 - stats.norm.cdf(1.633)), 3) == 0.102
    rng = np.random.default_rng(12)
    x = ar1(rng, 0.2, 400, 200_000, s=0.2 * math.sqrt(1 - 0.04))
    assert abs(x.mean(1).std() / (0.2 / 20 * math.sqrt(1.5)) - 1) < 0.01
    # Best of 20 null comparisons reaches t of about 1.87.
    assert abs(rng.standard_normal((200_000, 20)).max(1).mean() - 1.867) < 0.005


def test_q13():
    assert round(math.log(2) / -math.log(0.9), 1) == 6.6
    rng = np.random.default_rng(13)

    def slope_err(t, m=800):
        out = []
        for _ in range(m):
            x = np.cumsum(rng.standard_normal(t))
            u = np.zeros(t)
            e = rng.standard_normal(t)
            for i in range(1, t):
                u[i] = 0.9 * u[i - 1] + e[i]
            y = 2 * x + u
            out.append(np.polyfit(x, y, 1)[0] - 2)
        return np.std(out)

    a, b = slope_err(200), slope_err(800)
    assert 3.0 < a / b < 5.0
    # Engle-Granger step two on independent walks: residual unit-root test.
    t, m = 500, 8000
    x = np.cumsum(rng.standard_normal((m, t)), axis=1)
    y = np.cumsum(rng.standard_normal((m, t)), axis=1)
    xd = x - x.mean(1, keepdims=True)
    yd = y - y.mean(1, keepdims=True)
    beta = (xd * yd).sum(1) / (xd * xd).sum(1)
    u = yd - beta[:, None] * xd
    du = u[:, 1:] - u[:, :-1]
    lag = u[:, :-1]
    g = (lag * du).sum(1) / (lag * lag).sum(1)
    res = du - g[:, None] * lag
    s2 = (res * res).sum(1) / (t - 2)
    stat = g / np.sqrt(s2 / (lag * lag).sum(1))
    assert abs(np.quantile(stat, 0.05) + 3.37) < 0.08
    # Spurious regression: slope does not settle, t explodes.
    se = np.sqrt(((yd - beta[:, None] * xd) ** 2).sum(1) / (t - 2) / (xd * xd).sum(1))
    assert (np.abs(beta / se) > 1.96).mean() > 0.7


def test_q14():
    a, b = 0.1, 0.85
    s = a + b
    k = 3 * (1 - s * s) / (1 - s * s - 2 * a * a)
    assert round(k, 2) == 3.77
    assert round(1 - s * s, 4) == 0.0975
    assert round(1 - s * s - 2 * a * a, 4) == 0.0775
    r1 = a * (1 - a * b - b * b) / (1 - 2 * a * b - b * b)
    assert round(r1, 3) == 0.179
    rng = np.random.default_rng(14)
    r, _ = garch(rng, 2_000_000)
    assert abs((r**4).mean() / (r**2).mean() ** 2 - k) < 0.12
    q = r**2
    assert abs(acf(q, 1) - r1) < 0.012
    assert abs(acf(q, 2) / acf(q, 1) - 0.95) < 0.04
    assert abs(acf(r, 1)) < 0.003
    # The boundary for a finite fourth moment.
    assert round(math.sqrt(1 - 2 * 0.01), 3) == 0.99
    # Doubling alpha with the sum fixed, and the edge. The coefficient of m in the derivation reaches 1 at the same point.
    assert round(3 * 0.0975 / (0.0975 - 2 * 0.2**2), 1) == 16.7

    def coef(alpha):
        beta = s - alpha
        return 3 * alpha**2 + 2 * alpha * beta + beta**2

    edge = math.sqrt(0.0975 / 2)
    assert round(edge, 3) == 0.221
    assert abs(coef(edge) - 1) < 1e-12
    assert coef(0.22) < 1 < coef(0.221)
    assert round(3 * 0.0975 / (0.0975 - 2 * 0.22**2)) == 418


def test_q15():
    k = 3.7742
    bound = (k / 3 - 1) / (k - 1)
    assert round(bound, 3) == 0.093
    assert round(3.77 / 3 - 1, 3) == 0.257
    assert round(0.257 / 2.77, 3) == 0.093
    rng = np.random.default_rng(15)
    r, h = garch(rng, 2_000_000)
    assert abs(np.corrcoef(r**2, h)[0, 1] ** 2 - bound) < 0.012
    # A proxy with less noise: the sum of 78 equal normal sub-returns.
    m = len(h)
    rv = h * rng.chisquare(78, m) / 78
    assert np.corrcoef(rv, h)[0, 1] ** 2 > 0.6
    r2 = (k / 3 - 1) / (k / 3 - 1 + (k / 3) * (2 / 78))
    assert round(r2, 2) == 0.89
    assert abs(np.corrcoef(rv, h)[0, 1] ** 2 - r2) < 0.05


def test_q16():
    phi, big = 0.9, 0.01
    rho1 = big * phi
    assert round(rho1, 3) == 0.009
    assert round(big * phi**10, 4) == 0.0035
    rng = np.random.default_rng(16)
    n = 4_000_000
    e = rng.standard_normal(n)
    from scipy.signal import lfilter

    mu = lfilter([1], [1, -phi], e)
    mu = mu / mu.std() * math.sqrt(0.01)
    r = mu + rng.normal(0, math.sqrt(0.99), n)
    assert abs(acf(r, 1) - 0.009) < 0.0015
    # Sum-of-autocorrelations: variance ratio at a long horizon.
    vr = 1 + 2 * big * phi / (1 - phi)
    assert round(vr, 2) == 1.18
    assert round((2 / 0.009) ** 2) == 49383
    assert round(49383 / 252) == 196
    # ARMA(1,1) parameter: theta solves theta / (1 + theta^2) = c.
    c = (phi - rho1) / (1 + phi * phi - 2 * phi * rho1)
    th = (1 - math.sqrt(1 - 4 * c * c)) / (2 * c)
    assert round(th, 3) == 0.891
    arma = (1 - phi * th) * (phi - th) / (1 + th * th - 2 * phi * th)
    assert abs(arma - rho1) < 1e-9
    # With the sign convention x_t = phi x_{t-1} + e_t - th e_{t-1}, the best forecast from past returns alone.
    sig_e2 = (1 - phi * phi) / (1 + th * th - 2 * phi * th)
    assert round((1 - sig_e2) * 100, 2) == 0.04
    # The same number from the steady-state Kalman filter.
    q, obs = 0.01 * (1 - phi * phi), 0.99
    p = 0.01
    for _ in range(5000):
        p = phi * phi * (p - p * p / (p + obs)) + q
    assert abs((0.01 - p) - (1 - sig_e2)) < 1e-5


def test_q17():
    p = 0.05 / (0.05 + 0.1)
    assert abs(p - 1 / 3) < 1e-12
    c, s = 2 / 3, 1 / 3
    v = c * 0.01 + s * 0.09
    assert round(math.sqrt(v), 3) == 0.191
    k = 3 * (c * 0.01**2 + s * 0.09**2) / v**2
    assert round(k, 2) == 6.17
    lam = 0.95 + 0.9 - 1
    assert round(lam, 2) == 0.85
    rng = np.random.default_rng(17)
    n = 4_000_000
    u = rng.random(n)
    st = np.zeros(n, int)
    for t in range(1, n):
        st[t] = (u[t] < 0.05) if st[t - 1] == 0 else (u[t] < 0.9)
    r = np.where(st == 0, 0.1, 0.3) * rng.standard_normal(n)
    assert abs(st.mean() - 1 / 3) < 0.005
    assert abs(r.std() - 0.1915) < 0.002
    assert abs((r**4).mean() / (r**2).mean() ** 2 - k) < 0.1
    q = r**2
    assert abs(acf(q, 2) / acf(q, 1) - 0.85) < 0.03
    assert abs(acf(q, 5) / acf(q, 1) - 0.85**4) < 0.04
    assert round(math.log(0.5) / math.log(0.85), 1) == 4.3
    a = c * s * (0.09 - 0.01) ** 2
    assert round(a / ((k - 1) * v**2), 3) == 0.204
    assert abs(acf(q, 1) - 0.204 * 0.85) < 0.012

    # The filter, in calm-state variances: a move matters through the state, up to a cap.
    def update(prior, move, calm=1.0, stressed=3.0):
        ratio = stats.norm.pdf(move, 0, stressed) / stats.norm.pdf(move, 0, calm)
        post = prior * ratio / (prior * ratio + 1 - prior)
        ahead = 0.9 * post + 0.05 * (1 - post)
        return post, ahead * stressed**2 + (1 - ahead) * calm**2

    def no_move(prior):
        ahead = 0.9 * prior + 0.05 * (1 - prior)
        return ahead * 9 + 1 - ahead

    post, after = update(0.05, 4)
    assert round(post, 3) == 0.956
    assert round(after / no_move(0.05), 1) == 4.5
    assert round(update(1 / 3, 4)[1] / no_move(1 / 3), 1) == 2.2
    # Capped below the stressed variance, not proportional to r^2: four times r^2 adds almost nothing more.
    assert update(0.05, 12)[1] <= 0.9 * 9 + 0.1 < 9
    assert abs(update(0.05, 12)[1] - 8.2) < 0.001
    assert update(0.05, 8)[1] - update(0.05, 4)[1] < 0.2 * (update(0.05, 4)[1] - no_move(0.05))
    # A GARCH with alpha = 0.1 moves far less on this return, and with equal volatilities nothing is learned.
    assert 0.1 * 4**2 < after - no_move(0.05)
    assert abs(update(0.05, 4, 1.0, 1.0)[0] - 0.05) < 1e-12
    assert update(0.05, 0)[0] < 0.05
    # The same by drawing states and keeping the days with such a return.
    n2 = 8_000_000
    today = rng.random(n2) < 0.05
    move = np.where(today, 3.0, 1.0) * rng.standard_normal(n2)
    near = (np.abs(move) > 3.9) & (np.abs(move) < 4.1)
    assert abs(today[near].mean() - post) < 0.01
    next_state = rng.random(n2) < np.where(today, 0.9, 0.05)
    assert abs(np.where(next_state[near], 9.0, 1.0).mean() - after) < 0.15


def test_q18():
    bias = -(1 + 3 * 0.95) / 100
    assert round(bias, 4) == -0.0385
    assert round(0.95 + bias, 4) == 0.9115
    assert round(math.log(0.5) / math.log(0.95), 1) == 13.5
    assert round(math.log(0.5) / math.log(0.9115), 1) == 7.5
    rng = np.random.default_rng(18)
    x = ar1(rng, 0.95, 100, 200_000)
    a = x[:, :-1] - x[:, :-1].mean(1, keepdims=True)
    b = x[:, 1:] - x[:, 1:].mean(1, keepdims=True)
    est = (a * b).sum(1) / (a * a).sum(1)
    assert abs(est.mean() - 0.906) < 0.001
    assert abs(np.median(math.log(0.5) / np.log(np.clip(est, 0.01, 0.9999))) - 7.9) < 0.1
    # Two sources. With the mean known, the estimate is still biased, and demeaning adds the rest.
    assert round(-2 * 0.95 / 100, 3) == -0.019
    assert round(-(1 + 0.95) / 100, 4) == -0.0195
    assert abs(-2 * 0.95 / 100 - (1 + 0.95) / 100 - bias) < 1e-12
    known = (x[:, :-1] * x[:, 1:]).sum(1) / (x[:, :-1] ** 2).sum(1)
    assert abs(known.mean() - 0.95 + 0.017) < 0.001
    assert abs(est.mean() - known.mean() + 0.027) < 0.001
    assert est.mean() - known.mean() < 0.5 * (est.mean() - 0.95)
    # Limit case: at phi = 0 the first source vanishes, and the second is -1/T.
    w = ar1(rng, 0.0, 100, 100_000)
    known0 = (w[:, :-1] * w[:, 1:]).sum(1) / (w[:, :-1] ** 2).sum(1)
    p0 = w[:, :-1] - w[:, :-1].mean(1, keepdims=True)
    q0 = w[:, 1:] - w[:, 1:].mean(1, keepdims=True)
    assert abs(known0.mean()) < 0.001
    assert abs(((p0 * q0).sum(1) / (p0 * p0).sum(1)).mean() + 0.01) < 0.001
    # Half-sample jackknife removes most of the bias.
    half = 50
    def fit(lo, hi):
        p = x[:, lo:hi - 1] - x[:, lo:hi - 1].mean(1, keepdims=True)
        q = x[:, lo + 1:hi] - x[:, lo + 1:hi].mean(1, keepdims=True)
        return (p * q).sum(1) / (p * p).sum(1)

    jack = 2 * est - 0.5 * (fit(0, half) + fit(half, 100))
    assert abs(jack.mean() - 0.953) < 0.001
    assert abs(jack.mean() - 0.95) < abs(est.mean() - 0.95) / 2
    assert abs(((est * 100 + 1) / 97).mean() - 0.945) < 0.001
    # The cost in variance.
    assert jack.std() > est.std() and ((est * 100 + 1) / 97).std() > est.std()
    assert round((0.9115 * 100 + 1) / 97, 2) == 0.95


def test_q19():
    rng = np.random.default_rng(19)
    t = 500
    b, tt = _df(rng, t, 40000, False)
    stat = t * (b - 1)
    assert abs(stat.mean() + 1.78) < 0.1
    assert abs(np.quantile(tt, 0.05) + 1.95) < 0.03
    # Numerator: (W1^2 - 1) / 2 is negative with chance P(|Z| < 1).
    assert round(2 * stats.norm.cdf(1) - 1, 3) == 0.683
    assert abs((b < 1).mean() - 0.683) < 0.01
    # Direct functional on a fine grid.
    n, m = 1000, 40000
    w = rng.normal(0, math.sqrt(1 / n), (m, n))
    np.cumsum(w, axis=1, out=w)
    num = (w[:, -1] ** 2 - 1) / 2
    den = (w**2).sum(1) / n
    assert abs((num / den).mean() + 1.78) < 0.1
    assert abs(np.quantile(num / np.sqrt(den), 0.05) + 1.95) < 0.04
    assert abs(((num / np.sqrt(den)) < -1.645).mean() - 0.095) < 0.01
    assert abs(den.mean() - 0.5) < 0.01
    # Each shock is uncorrelated with its regressor, yet the scaled conditional variance stays random:
    # the variance of the integral of W^2 is 1/3 whatever the grid, and does not shrink with T.
    w0 = np.column_stack([np.zeros(m), w[:, :-1]])
    dw = w - w0
    assert abs((w0 * dw).mean()) < 0.001
    assert abs(den.var() - 1 / 3) < 0.02
    assert abs(((w[:, 3::4] ** 2).sum(1) / 250).var() - 1 / 3) < 0.02
    # With a constant. The numerator is the integral of the demeaned W against W, computed term by term.
    avg = w0.mean(1)
    true_num = (w[:, -1] ** 2 - 1) / 2 - w[:, -1] * avg
    literal = ((w[:, -1] - avg) ** 2 - 1) / 2
    assert np.abs(((w0 - avg[:, None]) * dw).sum(1) - true_num).mean() < 0.05
    # Substituting into the closed form gives a different law: means -1/2 and -1/3.
    assert abs(true_num.mean() + 0.5) < 0.01
    assert abs(literal.mean() + 1 / 3) < 0.01
    den_mu = ((w0 - avg[:, None]) ** 2).mean(1)
    q_true = np.quantile(true_num / np.sqrt(den_mu), 0.05)
    q_lit = np.quantile(literal / np.sqrt(den_mu), 0.05)
    assert abs(q_true + 2.86) < 0.03
    assert abs(q_lit + 2.47) < 0.04
    # The regression itself agrees with the true form, not the literal one.
    q_reg = np.quantile(_df(rng, t, 40000, True)[1], 0.05)
    assert abs(q_reg - q_true) < 0.04 and abs(q_reg - q_lit) > 0.3


def test_q20():
    s2, e2 = 1e-4, 0.0005**2
    assert round((s2 * s2 / (4 * e2 * e2)) ** (1 / 3), 1) == 34.2
    # The MSE curve, with all terms in n.
    def mse(n):
        return 2 * s2 * s2 / n + 4 * n * n * e2 * e2 + 8 * s2 * e2 + 12 * n * e2 * e2

    ns = np.arange(2, 400)
    assert 25 <= ns[np.argmin([mse(k) for k in ns])] <= 36
    rng = np.random.default_rng(20)
    big, m = 23400, 800
    res = {"rv5": [], "rvn": [], "tsrv": []}
    k = 300
    for _ in range(m):
        d = rng.normal(0, math.sqrt(s2 / big), big)
        p = np.concatenate([[0], np.cumsum(d)]) + rng.normal(0, 0.0005, big + 1)
        all_rv = (np.diff(p) ** 2).sum()
        sub = np.mean([(np.diff(p[o::k]) ** 2).sum() for o in range(k)])
        nbar = (big - k + 1) / k
        res["tsrv"].append(sub - nbar / big * all_rv)
        res["rvn"].append((np.diff(p[::big // 34]) ** 2).sum())
        res["rv5"].append(all_rv)
    assert abs(np.mean(res["rv5"]) / (s2 + 2 * big * e2) - 1) < 0.01
    assert round((s2 + 2 * big * e2) / s2, 1) == 118.0
    # First-order bias gone.
    assert abs(np.mean(res["tsrv"]) / s2 - 1) < 0.03
    # RMSE: two-scale beats the best sparse estimator.
    r_ts = math.sqrt(np.mean((np.array(res["tsrv"]) - s2) ** 2)) / s2
    r_sp = math.sqrt(np.mean((np.array(res["rvn"]) - s2) ** 2)) / s2
    assert r_ts < r_sp
    assert 0.1 < r_ts < 0.3
    assert 0.2 < r_sp < 0.4


def test_follow_ups():
    # 2
    assert round(1 + 0.49, 2) == 1.49
    assert abs(1.49 - (1 - 0.7**4) / 0.51) < 1e-9
    # 7
    assert round(math.sqrt(1.3 / 0.7), 2) == 1.36
    assert round(1.3 / 0.7, 3) == 1.857
    assert round(1 / math.sqrt(1.222), 2) == 0.90
    # 14
    assert round(3 * 0.0975 / (0.0975 - 2 * 0.2**2), 1) == 16.7
    assert round(math.sqrt(0.0975 / 2), 3) == 0.221
    # 18
    assert abs((0.9115 * 100 + 1) / 97 - 0.95) < 1e-3
    # 20
    assert round(2 ** (4 / 3), 2) == 2.52
    assert round(34.2 / 2 ** (4 / 3)) == 14
    assert round(390 / 34.2, 1) == 11.4
