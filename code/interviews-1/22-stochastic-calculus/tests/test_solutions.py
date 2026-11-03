"""Every number printed in the answers of "Stochastic Calculus": exact values, walks with exact stopping, simulations."""
import math

import numpy as np
from scipy import integrate, stats

NONNUMERIC = {}
PHI = stats.norm.cdf
PI = math.pi


def paths(rng, n_paths, n_steps, t=1.0):
    dt = t / n_steps
    a = rng.normal(0, math.sqrt(dt), (n_paths, n_steps))
    np.cumsum(a, axis=1, out=a)
    return a, dt


def test_q1():
    assert 1 + 2 + 2 * 1 == 5
    assert 1 / math.sqrt(4) == 0.5
    v = 0.25 + math.asin(1 / math.sqrt(2)) / (2 * PI)
    assert v == 0.375
    rng = np.random.default_rng(1)
    a = rng.standard_normal(4_000_000)
    b = a + rng.standard_normal(4_000_000)
    assert abs(((a > 0) & (b > 0)).mean() - 0.375) < 0.001
    assert abs((a + b).var() - 5) < 0.02
    # Follow-up: sum to n has variance n(n+1)(2n+1)/6.
    assert sum(min(i, j) for i in range(1, 11) for j in range(1, 11)) == 385


def _cond(f, s, x, t, order=40):
    z, w = np.polynomial.hermite_e.hermegauss(order)
    return (w * f(t, x + math.sqrt(t - s) * z)).sum() / math.sqrt(2 * PI)


def test_q2():
    good = [
        lambda t, x: x,
        lambda t, x: x**2 - t,
        lambda t, x: np.exp(x - t / 2),
        lambda t, x: x**3 - 3 * t * x,
        lambda t, x: x**4 - 6 * t * x**2 + 3 * t**2,
    ]
    bad = [lambda t, x: x**2, lambda t, x: t * x, lambda t, x: x**3]
    for f in good:
        for s, x, t in ((0.5, 0.7, 1.5), (1.0, -1.2, 3.0)):
            assert abs(_cond(f, s, x, t) - f(s, x)) < 1e-9
    for f in bad:
        assert abs(_cond(f, 0.5, 0.7, 1.5) - f(0.5, 0.7)) > 0.1


def test_q3():
    assert round(math.exp(0.1), 3) == 1.105
    assert round(math.exp(0.08), 3) == 1.083
    assert round(1 - PHI(0.1), 2) == 0.46
    rng = np.random.default_rng(3)
    n, m = 400, 200_000
    s = np.ones(m)
    for _ in range(n):
        s *= 1 + 0.1 / n + 0.2 * rng.standard_normal(m) / math.sqrt(n)
    assert abs(s.mean() - 1.105) < 0.002
    assert abs(np.median(s) - 1.083) < 0.003
    assert abs((s > 1.105).mean() - 0.46) < 0.005
    assert round(math.sqrt(0.2), 3) == 0.447


def test_q4():
    z = np.random.default_rng(4).standard_normal(4_000_000)
    assert abs((z**4).mean() - 3) < 0.03
    assert round(math.exp(2), 2) == 7.39
    # The correlation of the squares is the squared correlation.
    a = z[:2_000_000]
    b = a + math.sqrt(3) * z[2_000_000:]
    assert abs(np.corrcoef(a**2, b**2)[0, 1] - 0.25) < 0.005
    assert abs(2 / math.sqrt(2 * 2 * 16) - 0.25) < 1e-12
    assert 15 * 1 == abs(round(integrate.quad(lambda u: u**6 * stats.norm.pdf(u), -20, 20)[0]))


def test_q5():
    assert round(1 - PHI(1), 4) == 0.1587
    assert round(0.01 * math.sqrt(252) * 100, 1) == 15.9
    assert round(0.05 * math.sqrt(12) * 100, 1) == 17.3
    c = 3.0
    s, t = 2.0, 5.0
    assert c**2 * min(s / c**2, t / c**2) == min(s, t)


def test_q6():
    rng = np.random.default_rng(6)
    d = rng.normal(0, math.sqrt(1 / 1000), (20000, 1000))
    q = (d**2).sum(1)
    a = np.abs(d).sum(1)
    assert abs(q.mean() - 1) < 0.002
    assert abs(q.std() - math.sqrt(2 / 1000)) < 0.002
    assert round(math.sqrt(2 / 1000), 3) == 0.045
    assert round(math.sqrt(2 * 1000 / PI), 1) == 25.2
    assert abs(a.mean() - 25.2) < 0.05
    assert round(math.sqrt(2 / 252), 3) == 0.089


def test_q7():
    rng = np.random.default_rng(7)
    n, m = 1000, 20000
    d = rng.normal(0, math.sqrt(1 / n), (m, n))
    w = np.cumsum(d, 1)
    left = np.column_stack([np.zeros(m), w[:, :-1]])
    li = (left * d).sum(1)
    ri = (w * d).sum(1)
    assert abs(li.mean()) < 0.01 and abs(ri.mean() - 1) < 0.01
    assert abs(li.var() - 0.5) < 0.02
    assert np.abs(li - (w[:, -1] ** 2 - 1) / 2).mean() < 0.03
    mid = ((left + w) / 2 * d).sum(1)
    assert np.allclose(mid, w[:, -1] ** 2 / 2)
    assert abs(mid.mean() - 0.5) < 0.01


def test_q8():
    rng = np.random.default_rng(8)
    w, dt = paths(rng, 20000, 2000, 3.0)
    i = w.sum(1) * dt
    assert abs(i.var() - 9) < 0.3
    assert abs(np.corrcoef(i, w[:, -1])[0, 1] - math.sqrt(3) / 2) < 0.01
    assert round(math.sqrt(3) / 2, 3) == 0.866
    v = integrate.dblquad(lambda s, t: min(s, t), 0, 3, 0, 3)[0]
    assert abs(v - 9) < 1e-6
    assert round(0.2 / math.sqrt(3), 3) == 0.115


def test_q9():
    assert round(2 * (1 - PHI(1)), 4) == 0.3173
    assert round(math.sqrt(2 / PI), 3) == 0.798
    rng = np.random.default_rng(9)
    n = 252
    w, dt = paths(rng, 100_000, n)
    m = np.maximum(w.max(1), 0)
    # The shift 0.5826 sqrt(dt) gets the daily-close chance right.
    daily = (m >= 1).mean()
    shifted = 2 * (1 - PHI(1 + 0.5826 * math.sqrt(dt)))
    assert abs(daily - shifted) < 0.003
    assert round(shifted, 3) == 0.3
    assert round(0.5826 / math.sqrt(252), 3) == 0.037
    assert daily < 0.3173 - 0.01
    assert abs(m.mean() - (math.sqrt(2 / PI) - 0.5826 * math.sqrt(dt))) < 0.003


def test_q10():
    assert round(1 / stats.norm.ppf(0.75) ** 2, 2) == 2.2
    assert round(1 - 2 * (1 - PHI(1 / 10)), 4) == 0.0797
    z = np.random.default_rng(10).standard_normal(4_000_000)
    t = 1 / z**2
    assert abs(np.median(t) - 2.198) < 0.01
    assert abs((t > 100).mean() - 0.0797) < 0.001
    # The tail is about 0.8 a / sqrt(t), so partial means grow without limit.
    assert round(2 * stats.norm.pdf(0), 3) == 0.798
    m1 = t[t < 1e4].mean()
    m2 = t[t < 1e6].mean()
    assert m2 > 3 * m1
    w, dt = paths(np.random.default_rng(110), 20000, 2000, 2.198)
    assert abs((w.max(1) >= 1).mean() - 0.5) < 0.02


def _exit(rng, up, down, m, p=0.5):
    # Simple walk with exact stopping, in lattice units.
    pos = np.zeros(m, int)
    alive = np.ones(m, bool)
    t = np.zeros(m)
    while alive.any():
        k = alive.sum()
        pos[alive] += np.where(rng.random(k) < p, 1, -1)
        t[alive] += 1
        alive[(pos >= up) | (pos <= -down)] = False
    return pos, t


def test_q11():
    rng = np.random.default_rng(11)
    d = 0.1
    pos, t = _exit(rng, 20, 10, 20000)
    assert abs((pos == 20).mean() - 1 / 3) < 0.01
    assert abs((t * d * d).mean() - 2) < 0.05


def test_q12():
    assert round(math.exp(-1), 3) == 0.368
    assert round(math.exp(-2.5), 3) == 0.082
    # A walk with step d and matching mean and variance: exact gambler's ruin.
    d = 0.001
    p = 0.5 * (1 + 0.1 * d / 0.04)
    assert abs(((1 - p) / p) ** (0.2 / d) - math.exp(-1)) < 1e-4
    rng = np.random.default_rng(12)
    m, n, dt = 20000, 6000, 0.01
    x = np.zeros(m)
    low = np.zeros(m)
    for _ in range(n):
        x += 0.1 * dt + 0.2 * math.sqrt(dt) * rng.standard_normal(m)
        low = np.minimum(low, x)
    # Discrete checks shift the barrier by 0.5826 sigma sqrt(dt).
    v = (low <= -0.2).mean()
    assert abs(v - math.exp(-2 * 0.1 * (0.2 + 0.5826 * 0.02) / 0.04)) < 0.01


def test_q13():
    assert 1 - 2 * 0.1 / 0.04 == -4
    assert round(math.exp(0.24), 3) == 1.271
    q = (16 - 1) / (16 - 1 / 16)
    assert round(q, 3) == 0.941
    rng = np.random.default_rng(13)
    m = 20000
    dt = 0.002
    x = np.zeros(m)
    res = np.zeros(m, bool)
    alive = np.ones(m, bool)
    a = math.log(2)
    while alive.any():
        x[alive] += 0.08 * dt + 0.2 * math.sqrt(dt) * rng.standard_normal(alive.sum())
        hit = alive & (np.abs(x) >= a)
        res[hit] = x[hit] > 0
        alive &= ~hit
    assert abs(res.mean() - q) < 0.01
    # Second moment by simulation of the exact law.
    z = rng.standard_normal(4_000_000)
    assert abs((np.exp(2 * (0.08 + 0.2 * z))).mean() - math.exp(0.24)) < 0.002
    # Log-drift route to the same probability.
    th = 2 * 0.08 / 0.04
    assert abs((1 - math.exp(th * a)) / (math.exp(-th * a) - math.exp(th * a)) - q) < 1e-9


def test_q14():
    assert round(math.exp(-2), 3) == 0.135
    assert round(math.exp(-4), 3) == 0.018
    rng = np.random.default_rng(14)
    n, m = 2000, 20000
    w, dt = paths(rng, m, n)
    t = np.arange(1, n + 1) * dt
    br = w - t[None, :] * w[:, -1:]
    assert abs(br[:, n // 2 - 1].var() - 0.25) < 0.01
    v = (br.max(1) >= 1).mean()
    assert abs(v - math.exp(-2 * (1 + 0.5826 * math.sqrt(dt)) ** 2)) < 0.006


def test_q15():
    k, s = 2.0, 1.0
    assert round(3 * math.exp(-2), 3) == 0.406
    assert round(s**2 * (1 - math.exp(-4)) / 4, 3) == 0.245
    assert 1 / 4 == s**2 / (2 * k)
    assert round(math.log(2) / 2, 3) == 0.347
    rng = np.random.default_rng(15)
    m, n = 400000, 500
    x = np.full(m, 3.0)
    dt = 1 / n
    phi = math.exp(-k * dt)
    sd = s * math.sqrt((1 - phi**2) / (2 * k))
    for _ in range(n):
        x = phi * x + sd * rng.standard_normal(m)
    assert abs(x.mean() - 0.406) < 0.002 and abs(x.var() - 0.245) < 0.002
    # Euler, a different route.
    y = np.full(m, 3.0)
    for _ in range(n):
        y += -k * y * dt + s * math.sqrt(dt) * rng.standard_normal(m)
    assert abs(y.mean() - 0.406) < 0.004 and abs(y.var() - 0.245) < 0.004
    assert round(-math.log(0.98), 4) == 0.0202
    assert round(math.log(2) / -math.log(0.98), 1) == 34.3


def test_q16():
    assert 2 * 1.5 == 3
    rng = np.random.default_rng(16)
    a = rng.standard_normal(4_000_000)
    b = 0.5 * a + math.sqrt(0.75) * rng.standard_normal(4_000_000)
    assert abs((a * b).mean() - 0.5) < 0.002
    assert abs((a + b).var() - 3) < 0.01
    assert abs((a**2 * b**2).mean() - 1.5) < 0.02
    assert 1 + 2 * 0.25 == 1.5
    assert 2 * (1 - 0.5) == 1


def test_q17():
    rng = np.random.default_rng(17)
    z = rng.standard_normal(1_000_000)
    assert abs(((z + 1 > 0)).mean() - PHI(1)) < 0.001
    assert abs(((z > 0) * np.exp(z - 0.5)).mean() - PHI(1)) < 0.003
    p = 1 - PHI(4)
    assert f"{p:.2e}" == "3.17e-05"
    plain = math.sqrt(p * (1 - p) / 1e6) / p
    assert round(plain, 2) == 0.18
    y = z + 4
    v = (y > 4) * np.exp(-4 * y + 8)
    assert abs(v.mean() / p - 1) < 0.02
    rel = v.std() / math.sqrt(1e6) / p
    assert 0.0015 < rel < 0.003
    assert 60 < plain / rel < 110
    # The formula for the tilted second moment gives the same ratio.
    m2 = integrate.quad(lambda u: stats.norm.pdf(u) * math.exp(-8 * (u + 4) + 16), 0, 20)[0]
    assert abs(math.sqrt(m2 - p * p) / 1e3 / p - rel) < 2e-4


def test_q18():
    assert round(PHI((0.1 - 0.02) / 0.2), 3) == 0.655
    assert round(PHI(-0.02 / 0.2), 3) == 0.46
    lam = 0.1 / 0.2
    assert lam == 0.5
    rng = np.random.default_rng(18)
    w = rng.standard_normal(4_000_000)
    up = 0.08 + 0.2 * w > 0
    assert abs(up.mean() - 0.655) < 0.001
    dq = np.exp(-lam * w - lam**2 / 2)
    assert abs((up * dq).mean() - 0.46) < 0.001
    assert abs(dq.mean() - 1) < 0.002
    assert round(0.5 - PHI(-0.1), 2) == 0.04


def test_q19():
    def u1(t, x, big=2.0):
        return x * x + big - t

    def u2(t, x, big=2.0):
        return math.exp(x + (big - t) / 2)

    h = 1e-3
    for u in (u1, u2):
        for t, x in ((0.3, 0.4), (1.0, -1.0)):
            ut = (u(t + h, x) - u(t - h, x)) / (2 * h)
            uxx = (u(t, x + h) - 2 * u(t, x) + u(t, x - h)) / h**2
            assert abs(ut + 0.5 * uxx) < 1e-4
    rng = np.random.default_rng(19)
    z = rng.standard_normal(4_000_000)
    assert abs(((0.4 + math.sqrt(1.7) * z) ** 2).mean() - u1(0.3, 0.4)) < 0.01
    assert abs(np.exp(0.4 + math.sqrt(1.7) * z).mean() - u2(0.3, 0.4)) < 0.02


def test_q20():
    assert round(PHI(0.5), 2) == 0.69
    assert round(PHI(5) * 1e7) / 1e7 == 0.9999997
    assert round(math.exp(-0.5), 3) == 0.607
    assert f"{math.exp(-50):.1e}" == "1.9e-22"
    rng = np.random.default_rng(20)
    x = np.exp(rng.standard_normal(4_000_000) - 0.5)
    assert abs(x.mean() - 1) < 0.003
    assert abs(np.median(x) - 0.607) < 0.002
    assert abs((x < 1).mean() - 0.691) < 0.001
    # At T = 100 a million paths give nothing like the mean.
    y = np.exp(10 * rng.standard_normal(1_000_000) - 50)
    assert y.mean() < 0.9 or y.std() > 10 * y.mean()
    assert round(math.exp(1), 2) == 2.72
    assert f"{math.exp(100):.1e}" == "2.7e+43"


def test_q21():
    assert round(1 / 12, 4) == 0.0833
    assert abs(1 / 3 - 1 / 4 - 1 / 12) < 1e-15
    rng = np.random.default_rng(21)
    w, dt = paths(rng, 40000, 1000)
    i = w.sum(1) * dt
    b = np.polyfit(w[:, -1], i, 1)
    assert abs(b[0] - 0.5) < 0.005
    assert abs((i - b[0] * w[:, -1]).var() - 1 / 12) < 0.002
    assert abs(np.corrcoef(i, w[:, -1])[0, 1] ** 2 - 0.75) < 0.01


def test_q22():
    assert round(2 / PI * math.asin(math.sqrt(0.1)), 3) == 0.205
    assert round(2 * 2 / PI * math.asin(math.sqrt(0.1)), 2) == 0.41
    assert round(math.sqrt(1 / 8), 3) == 0.354
    assert round(math.sqrt(1 / 12), 3) == 0.289
    rng = np.random.default_rng(22)
    w, _ = paths(rng, 10000, 2000)
    a = (w > 0).mean(1)
    assert abs(a.mean() - 0.5) < 0.01
    assert abs(a.var() - 1 / 8) < 0.005
    assert abs((a <= 0.1).mean() - 0.205) < 0.015
    # Middle is the least likely: mass within 0.45 to 0.55.
    assert round(2 / PI * (math.asin(math.sqrt(0.55)) - math.asin(math.sqrt(0.45))), 3) == 0.064


def test_q23():
    rng = np.random.default_rng(23)
    w, dt = paths(rng, 40000, 1000)
    m = np.maximum(w.max(1), 0)
    gap = m - w[:, -1]
    shift = 0.5826 * math.sqrt(dt)
    assert abs(gap.mean() + shift - math.sqrt(2 / PI)) < 0.006
    assert abs((gap >= 1 - shift).mean() - 0.3173) < 0.006
    assert round(0.798 * 0.2, 3) == 0.16
    assert round(2 * (1 - PHI(1)), 3) == 0.317
    # The joint law: chance of max above a and end below x.
    a, x = 1.0, 0.5
    assert abs(((m >= a - shift) & (w[:, -1] <= x)).mean() - (1 - PHI(2 * a - x))) < 0.006
    assert round(1 - PHI(1.5), 3) == 0.067
    # Two years scales by the root.
    assert round(0.16 * math.sqrt(2), 3) == 0.226


def test_q24():
    a, mu, s = 1.0, 0.1, 0.2
    assert a / mu == 10
    assert round(a * s * s / mu**3, 6) == 40
    lam = a * a / s**2
    assert round(lam, 9) == 25
    rng = np.random.default_rng(24)
    t = rng.wald(10.0, 25.0, 4_000_000)
    assert abs(t.mean() - 10) < 0.02
    assert abs(t.var() - 40) < 0.5
    p = (t > 20).mean()
    d1 = (mu * 20 - a) / (s * math.sqrt(20))
    d2 = -(mu * 20 + a) / (s * math.sqrt(20))
    exact = PHI(d1) + math.exp(2 * mu * a / s**2) * PHI(d2)
    assert abs(p - (1 - exact)) < 0.001
    assert round(1 - exact, 3) == 0.073
    # A direct run of the process.
    m, dt = 20000, 0.005
    x = np.zeros(m)
    tau = np.zeros(m)
    alive = np.ones(m, bool)
    while alive.any():
        k = alive.sum()
        x[alive] += mu * dt + s * math.sqrt(dt) * rng.standard_normal(k)
        tau[alive] += dt
        alive &= x < a
    assert abs(tau.mean() - 10) < 0.2
    assert abs(tau.var() - 40) < 3
    # Without drift the mean diverges as mu falls.
    assert round(a * 0.04 / 0.01**3) == 40000


def test_q25():
    assert round(math.exp(-1), 4) == 0.3679
    z = np.random.default_rng(25).standard_normal(4_000_000)
    t = 1 / z**2
    assert abs(np.exp(-0.5 * t).mean() - math.exp(-1)) < 0.0005
    # Limit at lambda small, then the derivative: (1 - E e^{-lambda T}) / lambda grows.
    vals = [(1 - math.exp(-math.sqrt(2 * v))) / v for v in (1e-2, 1e-4, 1e-6)]
    assert vals[0] < vals[1] < vals[2]
    # A drifted version, via the same martingale: E exp(-lambda tau) with drift.
    mu = 0.5
    r = np.random.default_rng(125).wald(1 / mu, 1.0, 4_000_000)
    assert abs(np.exp(-0.5 * r).mean() - math.exp(mu - math.sqrt(mu**2 + 1))) < 0.001


def test_q26():
    assert round(math.log(2) / 0.08, 2) == 8.66
    nu = 0.01 - 0.02
    p = math.exp(2 * nu * math.log(2) / 0.04)
    assert round(p, 3) == 0.707
    assert abs(p - 2**-0.5) < 1e-12
    q = 1 - 2 * 0.01 / 0.04
    assert q == 0.5
    assert abs(2**-q - p) < 1e-12
    # Exact walk in log space.
    d = 0.0005
    up = 0.5 * (1 + nu * d / 0.04)
    assert abs((up / (1 - up)) ** (math.log(2) / d) - p) < 1e-3
    rng = np.random.default_rng(26)
    t = rng.wald(math.log(2) / 0.08, (math.log(2) / 0.2) ** 2, 2_000_000)
    assert abs(t.mean() - 8.66) < 0.02
    # Simulation over a long horizon: most runners get there by year 400.
    m, dt = 40000, 0.05
    x = np.zeros(m)
    best = np.zeros(m)
    for _ in range(8000):
        x += nu * dt + 0.2 * math.sqrt(dt) * rng.standard_normal(m)
        best = np.maximum(best, x)
    v = (best >= math.log(2) - 0.5826 * 0.2 * math.sqrt(dt)).mean()
    sd = 0.2 * 20
    hit = PHI((nu * 400 - math.log(2)) / sd) + p * PHI((-nu * 400 - math.log(2)) / sd)
    assert round(hit, 3) == 0.683
    assert abs(v - hit) < 0.012
    assert round(math.log(2) / 0.001) == 693


def test_q27():
    rng = np.random.default_rng(27)
    n, m = 2000, 10000
    d = rng.normal(0, math.sqrt(1 / n), (m, n))
    w = np.cumsum(d, 1)
    prev = np.column_stack([np.zeros(m), w[:, :-1]])
    integ = (np.sign(prev) * d).sum(1)
    assert abs(integ.mean()) < 0.01
    lt = np.abs(w[:, -1]) - integ
    assert abs(lt.mean() - math.sqrt(2 / PI)) < 0.02
    eps = 0.03
    occ = (np.abs(w) < eps).sum(1) / n / (2 * eps)
    assert abs(occ.mean() - math.sqrt(2 / PI)) < 0.04
    assert abs(np.corrcoef(lt, occ)[0, 1]) > 0.9
    # The law of L: as the running maximum, or |W_1|.
    mx = np.maximum(w.max(1), 0)
    q = [0.25, 0.5, 0.75]
    assert np.allclose(np.quantile(lt, q), np.quantile(np.abs(w[:, -1]), q), atol=0.04)
    assert np.allclose(np.quantile(mx + 0.5826 * math.sqrt(1 / n), q), np.quantile(np.abs(w[:, -1]), q), atol=0.04)


def test_q28():
    v = integrate.dblquad(lambda s, t: 2 * min(s, t) ** 2, 0, 1, 0, 1)[0]
    assert abs(v - 1 / 3) < 1e-7
    lam = ((np.arange(1, 200001) - 0.5) * PI) ** -2
    assert abs(lam.sum() - 0.5) < 1e-5
    assert abs((lam**2).sum() - 1 / 6) < 1e-12
    assert abs(2 * (lam**2).sum() - 1 / 3) < 1e-12
    rng = np.random.default_rng(28)
    w, dt = paths(rng, 40000, 1000)
    q = (w**2).sum(1) * dt
    assert abs(q.mean() - 0.5) < 0.01
    assert abs(q.var() - 1 / 3) < 0.03
    # Share of the variance taken by the first term.
    assert round(2 * lam[0] ** 2 / (1 / 3), 3) == 0.986


def test_q29():
    assert round(1 / math.sqrt(math.cosh(1)), 3) == 0.805
    th = 1.0
    t = 0.3
    a = th * math.tanh(th * (1 - t))
    h = 1e-5
    da = (th * math.tanh(th * (1 - t - h)) - th * math.tanh(th * (1 - t + h))) / (2 * h)
    assert abs(da - (a * a - th * th)) < 1e-8
    bi = integrate.quad(lambda s: 0.5 * th * math.tanh(th * (1 - s)), 0, 1)[0]
    assert abs(math.exp(-bi) - 0.8050) < 1e-3
    lam = ((np.arange(1, 400001) - 0.5) * PI) ** -2
    prod = np.exp(-0.5 * np.log1p(th**2 * lam).sum())
    assert abs(prod - 1 / math.sqrt(math.cosh(th))) < 1e-5
    rng = np.random.default_rng(29)
    w, dt = paths(rng, 40000, 1000)
    q = (w**2).sum(1) * dt
    assert abs(np.exp(-0.5 * q).mean() - 0.805) < 0.003
    # Small theta: 1 - theta^2 / 4.
    s = 0.01
    assert abs((1 / math.sqrt(math.cosh(s)) - 1) / s**2 + 0.25) < 1e-3
    # Fourth-order: a variance from the series.
    v = (1 / math.sqrt(math.cosh(0.5)) + 1 / math.sqrt(math.cos(0.5)) - 2) / 0.5**4
    assert abs(v - 2 * (1 / 3 + 1 / 4) / 8) < 0.02


def test_q30():
    rng = np.random.default_rng(30)
    d = 0.1
    pos, t = _exit(rng, 10, 10, 100000)
    tau = t * d * d
    assert abs(tau.mean() - 1) < 0.01
    # Walks carry a small lattice correction in the variance, of order d squared.
    assert abs(tau.var() - 2 / 3) < 0.03
    assert abs(5 / 3 - 1 - 2 / 3) < 1e-12
    assert (6 - 1) / 3 == 5 / 3
    v = 1 / math.cosh(1.0)
    assert round(v, 3) == 0.648
    assert abs(np.exp(-0.5 * tau).mean() - v) < 0.003
    rate = PI**2 / 8
    assert round(rate, 3) == 1.234
    tail = 4 / PI * math.exp(-rate * 4)
    assert round(tail, 4) == 0.0092
    assert abs((tau > 4).mean() - tail) < 0.002
    # 1 / cosh expansion, by a small-x check.
    x = 0.1
    assert abs(1 / math.cosh(x) - (1 - x**2 / 2 + 5 * x**4 / 24)) < 1e-7
