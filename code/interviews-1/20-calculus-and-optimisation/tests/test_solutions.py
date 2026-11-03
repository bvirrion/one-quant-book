"""Every number printed in the answers of "Calculus and Optimisation": exact values, quadrature and direct runs."""
import math
from fractions import Fraction as Fr

import numpy as np
from scipy import integrate, optimize

NONNUMERIC = {}
PI = math.pi
EPS = 2.0**-52


def test_q1():
    r = optimize.minimize_scalar(lambda x: x**x, bounds=(0.01, 2), method="bounded")
    assert abs(r.x - 1 / math.e) < 1e-4
    assert round(math.exp(-1 / math.e), 3) == 0.692
    assert round(math.e**PI, 2) == 23.14 and round(PI**math.e, 2) == 22.46
    r2 = optimize.minimize_scalar(lambda x: -math.log(x) / x, bounds=(1, 5), method="bounded")
    assert abs(r2.x - math.e) < 1e-4
    # The limit at 0 is 1, so the function falls and then rises.
    assert abs(1e-9**1e-9 - 1) < 1e-6


def test_q2():
    v = integrate.quad(lambda x: math.exp(-x * x), -np.inf, np.inf)[0]
    assert abs(v - math.sqrt(PI)) < 1e-9
    assert abs(integrate.quad(lambda x: math.exp(-x * x / 2), -np.inf, np.inf)[0] - math.sqrt(2 * PI)) < 1e-9
    assert abs(math.sqrt(2 / PI) - 0.798) < 0.001
    rng = np.random.default_rng(2)
    assert abs(np.abs(rng.standard_normal(4_000_000)).mean() - math.sqrt(2 / PI)) < 0.001


def test_q3():
    x = Fr(1)
    seq = []
    for _ in range(4):
        x = (x + 2 / x) / 2
        seq.append(x)
    assert seq[:3] == [Fr(3, 2), Fr(17, 12), Fr(577, 408)]
    errs = [abs(float(v) - math.sqrt(2)) for v in seq]
    assert round(errs[0], 3) == 0.086
    assert round(errs[1], 4) == 0.0025
    assert errs[2] < 2.2e-6
    assert errs[1] / errs[0] ** 2 < 0.36 and errs[2] / errs[1] ** 2 < 0.36


def test_q4():
    x = 0.1
    assert round(x - x**2 / 2 + x**3 / 3, 4) == 0.0953
    assert round(math.log(1.1), 4) == 0.0953
    assert round(1 + x + x**2 / 2, 3) == 1.105
    assert round(math.exp(0.1), 3) == 1.105
    assert round(1 + 0.02 - 0.0002, 4) == 1.0198
    assert round(math.sqrt(1.04), 4) == 1.0198
    assert round((math.exp(-0.1) - 1) * 100, 2) == -9.52
    assert -10 + 0.5 == -9.5
    # The percentage change does not depend on the starting yield, and no yield is given.
    for y in (0.0, 0.01, 0.05, 0.2):
        assert abs((math.exp(-10 * (y + 0.01)) - math.exp(-10 * y)) / math.exp(-10 * y) - (math.exp(-0.1) - 1)) < 1e-12
    # A two-point move: the convexity term is four times as large, at 2%.
    assert abs((10 * 0.02) ** 2 / 2 - 0.02) < 1e-12
    # Better off than the duration estimate on either side, even though a rise still loses money.
    for dy in (0.01, -0.01, 0.02, -0.02):
        assert math.exp(-10 * dy) - 1 > -10 * dy
    assert math.exp(-0.1) - 1 < 0


def test_q5():
    for n in (1, 2, 5, 13):
        v = integrate.quad(lambda x, m=n: math.sin(x) ** m / (math.sin(x) ** m + math.cos(x) ** m), 0, PI / 2)[0]
        assert abs(v - PI / 4) < 1e-9
    w = integrate.quad(lambda x: math.log(1 + x) / (1 + x * x), 0, 1)[0]
    assert abs(w - PI / 8 * math.log(2)) < 1e-10
    assert round(PI / 8 * math.log(2), 3) == 0.272


def test_q6():
    c = math.comb(100, 50)
    assert f"{c:.3e}" == "1.009e+29"
    app = 4.0**50 / math.sqrt(50 * PI)
    assert f"{app:.3e}" == "1.011e+29"
    assert round(c / 2**100, 4) == 0.0796
    assert round(1 / math.sqrt(50 * PI), 4) == 0.0798
    for n in (10, 100, 1000):
        ln = 0.5 * math.log(2 * PI * n) + n * math.log(n) - n
        assert abs(math.exp(ln - math.lgamma(n + 1)) - 1) < 1 / (10 * n)
    # n = 10 gives about 0.8% below.
    assert round(math.sqrt(20 * PI) * (10 / math.e) ** 10 / math.factorial(10), 3) == 0.992


def test_q7():
    v = PI / 2
    for n in (2, 4, 6, 8, 10):
        v *= (n - 1) / n
    assert abs(v - 63 * PI / 512) < 1e-12
    assert round(v, 4) == 0.3866
    q = integrate.quad(lambda x: math.sin(x) ** 10, 0, PI / 2)[0]
    assert abs(q - v) < 1e-10
    a = math.sqrt(PI / 20)
    assert round(a, 4) == 0.3963
    assert round(a / v - 1, 3) == 0.025
    assert round(math.sqrt(PI / (2 * 10.5)), 4) == 0.3868
    assert Fr(9, 10) * Fr(7, 8) * Fr(5, 6) * Fr(3, 4) * Fr(1, 2) == Fr(63, 256)


def test_q8():
    r = optimize.minimize(lambda v: -v[0] * v[1] * (1 - v[0] - v[1]), [0.2, 0.5], bounds=[(0, 1), (0, 1)])
    assert abs(-r.fun - 1 / 27) < 1e-6

    def value(b):
        return math.sqrt(2 * b)

    assert value(2) == 2
    h = 1e-6
    assert abs((value(2 + h) - value(2 - h)) / (2 * h) - 0.5) < 1e-6
    assert 1 / (2 * math.sqrt(1)) == 0.5
    # A grid over the split at B = 2.
    grid = np.linspace(0, 2, 20001)
    v = np.sqrt(grid) + np.sqrt(2 - grid)
    assert abs(grid[v.argmax()] - 1) < 1e-3
    # Corner solutions lose.
    assert math.sqrt(2) < 2


def test_q9():
    rng = np.random.default_rng(9)
    hess = np.array([[0, 1], [1, 0.0]])
    assert np.allclose(np.linalg.eigvalsh(hess), [-1, 1])
    r = rng.normal(0.1, 0.2, 4_000_000)
    r = r[r > -0.95]
    v = np.log1p(r).mean()
    # The integral, against the second-order 0.079: the next Taylor term accounts for the gap.
    density = lambda u: math.log1p(u) * math.exp(-((u - 0.1) ** 2) / 0.08) / (0.2 * math.sqrt(2 * math.pi))  # noqa: E731
    exact = integrate.quad(density, -0.9, 1.6, limit=200)[0]
    assert round(exact, 3) == 0.078 and abs(v - exact) < 3e-4
    assert round(math.expm1(exact), 3) == 0.081
    assert abs(math.log(1.1) - 0.04 / (2 * 1.1**2) - 3 * 0.2**4 / (4 * 1.1**4) - exact) < 2e-4
    assert abs(v - 0.079) > 5e-4
    assert abs((0.1 - 0.02) - 0.08) < 1e-12
    second = math.log(1.1) - 0.04 / (2 * 1.1**2)
    assert round(second, 3) == 0.079
    # Lognormal exact: arithmetic mean 10% with volatility of logs set near 18%.
    assert 0.1 > v
    # Convexity spot checks, midpoints.
    for f in (lambda x: -math.log(x), lambda x: x * x, abs):
        for a, b in ((0.5, 2.0), (1.0, 3.0)):
            assert f((a + b) / 2) <= (f(a) + f(b)) / 2 + 1e-12
    assert math.sqrt(1.25) > (math.sqrt(0.5) + math.sqrt(2)) / 2


def test_q10():
    assert 2 / 100 == 0.02
    assert round(2 / 101, 4) == 0.0198
    rate = 99 / 101
    assert round(rate, 4) == 0.9802
    steps = math.log(1e-6) / math.log(rate)
    assert math.ceil(steps) == 691
    a = np.array([1.0, 100.0])
    x = np.array([1.0, 1.0])
    k = 0
    while np.linalg.norm(x) > 1e-6 * math.sqrt(2):
        x = x - 2 / 101 * a * x
        k += 1
    assert abs(k - 691) <= 1
    # Just above the limit: diverges.
    y = np.array([1.0, 1.0])
    for _ in range(100):
        y = y - 0.0201 * a * y
    assert abs(y[1]) > 1
    # Heavy ball, best parameters: rate (sqrt k - 1) / (sqrt k + 1).
    assert round(9 / 11, 3) == 0.818
    n = math.log(1e-6) / math.log(9 / 11)
    assert round(n) == 69
    alpha = 4 / (1 + 10) ** 2
    beta = (9 / 11) ** 2
    x0 = np.array([1.0, 1.0])
    prev = x0.copy()
    cur = x0.copy()
    steps_hb = 0
    while np.linalg.norm(cur) > 1e-6 * math.sqrt(2):
        cur, prev = cur - alpha * a * cur + beta * (cur - prev), cur
        steps_hb += 1
    assert 80 <= steps_hb <= 110
    # Newton in one step.
    z = np.array([1.0, 1.0])
    assert np.allclose(z - np.linalg.solve(np.diag(a), np.diag(a) @ z), 0)


def test_q11():
    x = 1.0
    for _ in range(10):
        f = math.copysign(abs(x) ** (1 / 3), x)
        d = (1 / 3) * abs(x) ** (-2 / 3)
        new = x - f / d
        assert abs(new + 2 * x) < 1e-9
        x = new
    r = optimize.brentq(lambda t: math.atan(t) - 2 * t / (1 + t * t), 1, 2)
    assert round(r, 3) == 1.392

    def iterate(s):
        z = s
        for _ in range(30):
            z = z - math.atan(z) * (1 + z * z)
            if abs(z) > 1e6:
                return math.inf
        return z

    assert abs(iterate(1.3)) < 1e-9
    assert iterate(1.5) == math.inf


def test_q12():
    b = 1e8
    naive = (b - math.sqrt(b * b - 4)) / 2
    big = (b + math.sqrt(b * b - 4)) / 2
    stable = 1 / big
    assert abs(stable - 1e-8) < 1e-20
    assert abs(naive - 1e-8) / 1e-8 > 0.2
    assert round(naive * 1e9, 2) == 7.45
    s = 1e-8
    assert 1 - math.cos(s) == 0
    assert abs(2 * math.sin(s / 2) ** 2 - s * s / 2) < 1e-30
    data = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    assert np.var([4, 7, 13, 16], ddof=1) == 30
    big_data = [1e15 + 4, 1e15 + 7, 1e15 + 13, 1e15 + 16]

    def naive_var(v):
        tot = sum(v)
        sq = sum(u * u for u in v)
        return (sq - tot * tot / len(v)) / (len(v) - 1)

    def welford(v):
        m, s2 = 0.0, 0.0
        for k, u in enumerate(v, 1):
            d = u - m
            m += d / k
            s2 += d * (u - m)
        return s2 / (len(v) - 1)

    assert abs(welford(big_data) - 30) < 1e-6
    assert abs(naive_var(big_data) - 30) > 1
    assert 1.4e-8 < np.spacing(1e8) < 1.5e-8
    assert abs(welford(data) - 30) < 1e-6
    # 1 is exactly half the spacing at 1e16, and ties go to the even neighbour: 1e16 + 1 falls back, 1e16 + 3 goes up.
    assert np.spacing(1e16) == 2
    assert 1e16 + 1 == 1e16 and 1e16 + 3 == 1e16 + 4
    assert 1e16 + 1 + 1 - 1e16 == 0

    def kahan(values):
        total, carry = 0.0, 0.0
        for v in values:
            y = v - carry
            t = total + y
            carry = (t - total) - y
            total = t
        return total

    assert kahan([1e16, 1.0, 1.0, -1e16]) == 2


def test_q13():
    f, d = math.exp, math.exp(1)
    hs = 10.0 ** np.arange(-15, -1, 0.25)
    fwd = np.array([abs((f(1 + h) - f(1)) / h - d) for h in hs])
    cen = np.array([abs((f(1 + h) - f(1 - h)) / (2 * h) - d) for h in hs])
    hf = hs[fwd.argmin()]
    hc = hs[cen.argmin()]
    assert 1e-9 < hf < 1e-7
    assert 1e-6 < hc < 1e-4
    assert fwd.min() < 1e-7
    assert cen.min() < 1e-9
    assert round(math.sqrt(EPS), 9) == 1.5e-8
    assert 5e-6 < EPS ** (1 / 3) < 7e-6
    z = (np.exp(1 + 1e-30j).imag) / 1e-30
    assert abs(z - d) < 1e-15


def test_q14():
    v = integrate.quad(lambda x: math.log(math.sin(x)), 0, PI / 2)[0]
    assert abs(v + PI / 2 * math.log(2)) < 1e-8
    assert round(v, 4) == -1.0888
    # The mean of ln sin over the quarter period, as a limit check.
    assert round(v / (PI / 2), 4) == round(-math.log(2), 4)


def test_q15():
    for t in (0.5, 1.0, 2.0):
        v = integrate.quad(lambda x, c=t: math.exp(-c * x) * (math.sin(x) / x), 0, 200, limit=500)[0]
        assert abs(v - (PI / 2 - math.atan(t))) < 1e-8
    assert abs(PI / 2 - math.atan(1) - PI / 4) < 1e-12
    # Partial integrals of sin(x)/x close in on pi / 2, with error about 1/R.
    from scipy.special import sici

    for r in (100.0, 1000.0, 10000.0):
        assert abs(sici(r)[0] - PI / 2) < 1.5 / r
    # Not absolutely: the integral of |sin x| / x grows like (2 / pi) ln R.
    a = sum(integrate.quad(lambda x: abs(math.sin(x)) / x, k * PI, (k + 1) * PI)[0] for k in range(1, 300))
    b = sum(2 / ((k + 0.5) * PI) for k in range(1, 300))
    assert abs(a - b) < 0.02


def test_q16():
    a = np.array([[2.0, 1], [1, 2]])
    val = 2 * PI / math.sqrt(np.linalg.det(a))
    assert round(val, 3) == 3.628
    num = integrate.dblquad(
        lambda y, x: math.exp(-0.5 * (2 * x * x + 2 * x * y + 2 * y * y)), -8, 8, -8, 8
    )[0]
    assert abs(num - val) < 1e-6
    c = np.linalg.inv(a)
    assert np.allclose(c, np.array([[2, -1], [-1, 2]]) / 3)
    assert abs(c[0, 1] / c[0, 0] + 0.5) < 1e-12
    rng = np.random.default_rng(16)
    x = rng.multivariate_normal([0, 0], c, 2_000_000)
    assert abs(np.corrcoef(x.T)[0, 1] + 0.5) < 0.002


def test_q17():
    n = np.array([0.2, 0.5, 1.0])

    def solve(cap):
        lo, hi = 0.0, 100.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if np.maximum(mid - n, 0).sum() > cap:
                hi = mid
            else:
                lo = mid
        return lo, np.maximum(lo - n, 0)

    nu, x = solve(1.0)
    assert abs(nu - 0.85) < 1e-9
    assert np.allclose(x, [0.65, 0.35, 0], atol=1e-9)
    assert (1 + 0.7) / 2 == 0.85
    nu3, x3 = solve(3.0)
    assert abs(nu3 - 4.7 / 3) < 1e-9
    assert np.allclose(x3, np.array([4.7, 4.7, 4.7]) / 3 - n, atol=1e-9)
    assert np.allclose(np.round(x3, 2), [1.37, 1.07, 0.57])

    r = optimize.minimize(
        lambda v: -np.log(1 + v / n).sum(),
        [0.3, 0.3, 0.4],
        bounds=[(0, 1)] * 3,
        constraints={"type": "eq", "fun": lambda v: v.sum() - 1},
    )
    assert np.allclose(r.x, [0.65, 0.35, 0], atol=1e-3)
    # Marginal value check: 1/(n + x) is equal on funded lines, and lower on the last.
    assert abs(1 / (0.2 + 0.65) - 1 / (0.5 + 0.35)) < 1e-12
    assert 1 / 1.0 < 1 / 0.85


def test_q18():
    x = 1.0
    errs = []
    for _ in range(5):
        x = x - (x * x - 2) / (2 * x)
        errs.append(abs(x - math.sqrt(2)))
    assert errs[2] / errs[1] ** 2 < 0.4
    assert abs(errs[1] / errs[0] ** 2 - 1 / (2 * math.sqrt(2))) < 0.1
    y = 2.0
    prev = abs(y - 1)
    for _ in range(10):
        y = y - (y - 1) ** 2 / (2 * (y - 1))
        assert abs(abs(y - 1) / prev - 0.5) < 1e-9
        prev = abs(y - 1)
    z = 2.0
    z = z - 2 * (z - 1) ** 2 / (2 * (z - 1))
    assert z == 1.0
    # A perturbed double root: the modified step is quadratic at first.
    assert round(math.log(1e-6) / math.log(0.5)) == 20


def test_q19():
    v = integrate.dblquad(lambda y, x: 1 / (1 - x * y), 0, 1 - 1e-12, 0, 1 - 1e-12, epsabs=1e-6)[0]
    assert abs(v - PI**2 / 6) < 1e-3
    a = integrate.quad(lambda u: math.asin(u) / math.sqrt(1 - u * u), 0, 0.5)[0]
    b = integrate.quad(lambda u: 0.5 * math.acos(u) / math.sqrt(1 - u * u), 0.5, 1)[0]
    assert abs(4 * a - PI**2 / 18) < 1e-9
    assert abs(4 * b - PI**2 / 9) < 1e-7
    assert abs(sum(1 / k**2 for k in range(1, 2_000_000)) - PI**2 / 6) < 1e-6
    # Inner integral check at a point.
    u = 0.3
    inner = integrate.quad(lambda w: 1 / (1 - u * u + w * w), 0, u)[0]
    assert abs(inner - math.asin(u) / math.sqrt(1 - u * u)) < 1e-10
    u = 0.7
    inner = integrate.quad(lambda w: 1 / (1 - u * u + w * w), 0, 1 - u)[0]
    assert abs(inner - 0.5 * math.acos(u) / math.sqrt(1 - u * u)) < 1e-10


def test_q20():
    def d(n):
        return math.lgamma(n + 1) - (n + 0.5) * math.log(n) + n

    vals = [d(n) for n in range(1, 2000)]
    assert all(vals[i] > vals[i + 1] for i in range(len(vals) - 1))
    assert abs(math.exp(vals[-1]) - math.sqrt(2 * PI)) < 1e-3
    assert vals[-1] > 0.5 * math.log(2 * PI) - 1e-3
    # d_n - d_{n+1} matches the log-series formula.
    for n in (1, 5, 50):
        t = 1 / (2 * n + 1)
        series = sum(t ** (2 * k) / (2 * k + 1) for k in range(1, 30))
        assert abs(d(n) - d(n + 1) - series) < 1e-12
    assert abs(math.exp(1) - math.exp(d(1))) < 1e-12
    # Wallis: the product 2k.2k / ((2k-1)(2k+1)) tends to pi/2.
    p = 1.0
    for k in range(1, 200_000):
        p *= 4 * k * k / (4 * k * k - 1)
    assert abs(p - PI / 2) < 1e-4
    # Ratio form: (2^(2n) (n!)^2 / (2n)!)^2 / n tends to pi.
    n = 100_000
    ln = 2 * (2 * n * math.log(2) + 2 * math.lgamma(n + 1) - math.lgamma(2 * n + 1)) - math.log(n)
    assert abs(math.exp(ln) - PI) < 1e-4


def test_follow_ups():
    # 1: past e the function ln x / x falls.
    assert 100 * math.log(99) > 99 * math.log(100)
    # 2
    assert abs(integrate.quad(lambda x: x * x * math.exp(-x * x), 0, np.inf)[0] - math.sqrt(PI) / 4) < 1e-9
    # 3: reciprocal without division.
    v = 0.3
    v = v * (2 - 3 * v)
    assert abs(v - 0.33) < 1e-12
    v = v * (2 - 3 * v)
    assert abs(v - 0.3333) < 1e-12
    # 4: rule of 72.
    assert round(math.log(2) / math.log(1.08), 2) == 9.01
    # 5
    w = integrate.quad(lambda x: x * math.sin(x) / (1 + math.cos(x) ** 2), 0, PI)[0]
    assert abs(w - PI**2 / 4) < 1e-9
    # 6: ties in 1000 flips.
    assert round(1 / math.sqrt(PI * 500), 4) == 0.0252
    assert round(math.exp(math.lgamma(1001) - 2 * math.lgamma(501) - 1000 * math.log(2)), 4) == 0.0252
    # 7
    assert abs(2 / PI * (63 * PI / 512) - 63 / 256) < 1e-15
    assert Fr(math.comb(10, 5), 2**10) == Fr(63, 256)
    # 8
    assert round(math.sqrt(4.2), 4) == 2.0494
    # 9: growth-optimal leverage.
    assert 0.1 / 0.04 == 2.5
    assert abs(0.1 * 2.5 - 0.04 * 2.5**2 / 2 - 0.125) < 1e-12
    assert round(math.exp(math.log(1.1) - 0.04 / (2 * 1.21)) - 1, 3) == 0.082
    # 10: conjugate gradient ends in two steps on two eigenvalues.
    a = np.diag([1.0, 100.0])
    x = np.array([1.0, 1.0])
    r = -a @ x
    p = r.copy()
    for _ in range(2):
        step = (r @ r) / (p @ a @ p)
        x = x + step * p
        new = r - step * a @ p
        p = new + (new @ new) / (r @ r) * p
        r = new
    assert np.linalg.norm(x) < 1e-12
    # 11: bisection steps.
    assert math.ceil(math.log2(4.99 / 0.0001)) == 16
    # 12: cancellation in a sum, and Kahan.
    vals = [1e16, 1.0, -1e16]
    assert sum(vals) == 0.0
    tot, comp = 0.0, 0.0
    for u in [1e16, 1.0, 1.0, -1e16]:
        y = u - comp
        t = tot + y
        comp = (t - tot) - y
        tot = t
    assert sum([1e16, 1.0, 1.0, -1e16]) == 0.0
    assert tot == 2.0
    # 13: second derivative, central.
    hs = 10.0 ** np.arange(-8, -1, 0.25)
    err = np.array([abs((math.exp(1 + h) - 2 * math.exp(1) + math.exp(1 - h)) / h**2 - math.e) for h in hs])
    assert 1e-5 < hs[err.argmin()] < 1e-3
    assert 1e-10 < err.min() < 1e-6
    assert 1e-4 < EPS**0.25 < 2e-4
    # 14
    w = integrate.quad(lambda x: x / math.tan(x), 0, PI / 2)[0]
    assert abs(w - PI / 2 * math.log(2)) < 1e-9
    # 15: sin squared over x squared.
    from scipy.special import sici

    q = integrate.quad(lambda x: (math.sin(x) / x) ** 2, 0, 50, limit=500)[0]
    assert abs(q - (sici(100.0)[0] - math.sin(50.0) ** 2 / 50)) < 1e-8
    assert abs(sici(1e6)[0] - math.sin(5e5) ** 2 / 5e5 - PI / 2) < 1e-5
    # 16: conditional law.
    c = np.array([[2, -1], [-1, 2]]) / 3
    assert abs(c[0, 1] / c[1, 1] + 0.5) < 1e-12
    assert abs(c[0, 0] - c[0, 1] ** 2 / c[1, 1] - 0.5) < 1e-12
    # 17: capital at which the third line starts.
    assert abs((1 - 0.2) + (1 - 0.5) - 1.3) < 1e-12
    # 18: Newton on f / f' for a pure power, and the noise floor at a double root.
    z = 3.0
    z = z - ((z - 1) / 2) / (1 / 2)
    assert z == 1.0
    y = 1 + 1e-9
    assert abs((y * y - 2 * y + 1) - (y - 1) ** 2) >= 0.5 * (y - 1) ** 2
    # 19
    assert abs(sum(1 / (2 * k - 1) ** 2 for k in range(1, 1_000_000)) - PI**2 / 8) < 1e-6
    assert round(6 / PI**2, 3) == 0.608
    n = 1000
    cnt = sum(1 for i in range(1, n + 1) for j in range(1, n + 1) if math.gcd(i, j) == 1)
    assert abs(cnt / n**2 - 6 / PI**2) < 0.002
    # 20: the lower bound and the next term.
    t = 1 / 11
    assert sum(t ** (2 * k) / (2 * k + 1) for k in range(1, 30)) < 1 / (12 * 5 * 6)
    s = math.sqrt(20 * PI) * (10 / math.e) ** 10
    assert round(s) == 3598696
    assert round(s * (1 + 1 / 120)) == 3628685


def test_implied_vol_start():
    from scipy.stats import norm

    def call(sig):
        d1 = (0 - math.log(1.5) + sig * sig / 2) / sig
        return norm.cdf(d1) - 1.5 * norm.cdf(d1 - sig)

    def vega(sig):
        d1 = (0 - math.log(1.5) + sig * sig / 2) / sig
        return norm.pdf(d1)

    target = call(0.2)
    # A low start has almost no vega: the first step flies off.
    low = 0.05
    assert low + (target - call(low)) / vega(low) > 100
    # The inflection start converges from above, step by step.
    s = math.sqrt(2 * math.log(1.5))
    assert round(s, 2) == 0.9
    path = [s]
    for _ in range(12):
        s = s + (target - call(s)) / vega(s)
        path.append(s)
    assert abs(path[-1] - 0.2) < 1e-9
    assert all(path[i] >= path[i + 1] - 1e-12 for i in range(len(path) - 1))
    # The inflection really is there: the numerical second derivative changes sign.
    h = 1e-4
    def sec(v):
        return (call(v + h) - 2 * call(v) + call(v - h)) / h**2

    assert sec(0.8) > 0 > sec(1.0)
