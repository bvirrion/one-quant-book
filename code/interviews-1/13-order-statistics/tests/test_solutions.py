"""Every number printed in the answers of "Order Statistics": exact, then a seeded simulation."""
import math
from fractions import Fraction as Fr
from math import comb

import numpy as np
from scipy import integrate, stats

NONNUMERIC = {}
PI = math.pi


def test_q1():
    rng = np.random.default_rng(1)
    n = 10
    x = rng.random((400_000, n))
    assert abs(x.max(axis=1).mean() - n / (n + 1)) < 0.001
    assert abs(x.min(axis=1).mean() - 1 / (n + 1)) < 0.001
    assert abs((x.max(axis=1) - x.min(axis=1)).mean() - (n - 1) / (n + 1)) < 0.001
    assert abs(0.9**10 - 0.349) < 0.001
    assert abs((x.max(axis=1) < 0.9).mean() - 0.9**10) < 0.003
    # n = 1 limit: the range is 0 and the largest and smallest both average one half.
    assert (1 - 1) / (1 + 1) == 0 and 1 / 2 == 1 / (1 + 1)


def test_q2():
    rng = np.random.default_rng(2)
    x = rng.random((1_000_000, 3))
    med = np.median(x, axis=1)
    assert abs(med.mean() - 0.5) < 0.001
    assert abs(med.var() - 1 / 20) < 0.0005
    assert abs(x.mean(axis=1).var() - 1 / 36) < 0.0003
    mean_exact = integrate.quad(lambda t: t * 6 * t * (1 - t), 0, 1)[0]
    second = integrate.quad(lambda t: t**2 * 6 * t * (1 - t), 0, 1)[0]
    assert abs(mean_exact - 0.5) < 1e-12
    assert abs(second - 0.25 - 1 / 20) < 1e-12
    assert abs((1 / 20) / (1 / 36) - 1.8) < 1e-12


def test_q3():
    assert abs(20 / 30 - 2 / 3) < 1e-12
    p = comb(20, 3) / comb(30, 3)
    assert abs(p - 57 / 203) < 1e-12
    assert round(p, 3) == 0.281
    # Same answer from a chain, and by simulation under two different distributions.
    assert abs(20 / 30 * 19 / 29 * 18 / 28 - p) < 1e-12
    rng = np.random.default_rng(3)
    for draw in (rng.random((300_000, 30)), rng.standard_cauchy((300_000, 30))):
        order = np.argsort(draw, axis=1)[:, :3]
        assert abs((order >= 10).all(axis=1).mean() - p) < 0.003


def test_q4():
    k, m = 5, 60
    assert m * (1 + 1 / k) - 1 == 71
    # Exact: E[max] = k (N+1)/(k+1) for every N, so the estimator is unbiased.
    for N in (5, 20, 71, 200):
        den = comb(N, k)
        emax = sum(x * comb(x - 1, k - 1) for x in range(k, N + 1)) / den
        assert abs(emax - k * (N + 1) / (k + 1)) < 1e-9
        assert abs(emax * (1 + 1 / k) - 1 - N) < 1e-9
    # Second route: compare the variance by simulation for N = 71.
    rng = np.random.default_rng(4)
    N = 71
    sample = np.argsort(rng.random((200_000, N)), axis=1)[:, :k] + 1
    a = sample.max(axis=1) * 1.2 - 1
    b = 2 * sample.mean(axis=1) - 1
    assert abs(a.mean() - N) < 0.1 and abs(b.mean() - N) < 0.1
    assert b.var() > 2.2 * a.var()
    va = (N + 1) * (N - k) / (k * (k + 2))
    vb = (N + 1) * (N - k) / (3 * k)
    assert abs(a.var() / va - 1) < 0.02 and abs(b.var() / vb - 1) < 0.02
    assert abs(vb / va - 7 / 3) < 1e-12
    assert round(math.sqrt(va), 0) == 12 and round(math.sqrt(vb), 0) == 18
    # A sample with a large gap: the mean rule can be below the maximum seen.
    assert 2 * np.mean([1, 2, 3, 4, 60]) - 1 == 27


def test_q5():
    n = 10
    assert abs((1 / (3 * n)) / (1 / (n * (n + 2))) - 4) < 1e-12
    rng = np.random.default_rng(5)
    x = rng.random((600_000, n))
    m = x.max(axis=1)
    assert abs((2 * x.mean(axis=1)).var() - 1 / 30) < 0.0003
    assert abs(((n + 1) / n * m).var() - 1 / 120) < 0.0001
    # Best multiple: minimise the MSE of c * max numerically and compare.
    grid = np.linspace(0.95, 1.2, 501)
    mse_exact = grid**2 * n / (n + 2) - 2 * grid * n / (n + 1) + 1
    best = grid[np.argmin(mse_exact)]
    assert abs(best - (n + 2) / (n + 1)) < 0.001
    assert abs(mse_exact.min() - 1 / (n + 1) ** 2) < 1e-5
    assert abs((((n + 2) / (n + 1) * m - 1) ** 2).mean() - 1 / 121) < 0.0001
    assert abs((1 / 120) / (1 / 121) - 121 / 120) < 1e-12
    # Raw maximum: MSE 2/((n+1)(n+2)).
    assert abs(((m - 1) ** 2).mean() - 2 / (11 * 12)) < 0.0001


def test_q6():
    rng = np.random.default_rng(6)
    x = np.sort(rng.random((600_000, 5)), axis=1)
    assert abs(x[:, 3].mean() - 2 / 3) < 0.001
    # Conditioning on the highest near 0.8.
    near = np.abs(x[:, 4] - 0.8) < 0.005
    assert abs(x[near, 3].mean() - 0.64) < 0.002
    # Average over the highest gives the same answer as the direct one.
    tot = integrate.quad(lambda h: 0.8 * h * 5 * h**4, 0, 1)[0]
    assert abs(tot - 2 / 3) < 1e-12
    # Dice: P(second >= k) = P(at least two of four show >= k).
    ex = 0.0
    for k in range(1, 7):
        p = (7 - k) / 6
        ex += 1 - (1 - p) ** 4 - 4 * p * (1 - p) ** 3
    d = rng.integers(1, 7, (1_000_000, 4))
    sim = np.sort(d, axis=1)[:, 2].mean()
    assert abs(sim - ex) < 0.003
    assert abs(ex - 5313 / 1296) < 1e-12
    assert round(ex, 2) == 4.10


def test_q7():
    rng = np.random.default_rng(7)
    n = 1001
    x = rng.standard_normal((20_000, n))
    ratio = np.median(x, axis=1).var() / x.mean(axis=1).var()
    assert abs(ratio - PI / 2) < 0.06
    assert round(PI / 2, 2) == 1.57
    lap = rng.laplace(size=(20_000, n))
    ratio_l = np.median(lap, axis=1).var() / lap.mean(axis=1).var()
    assert abs(ratio_l - 0.5) < 0.04
    # Formula 1 / (4 n f(m)^2) for both.
    assert abs(1 / (4 * (1 / math.sqrt(2 * PI)) ** 2) - PI / 2) < 1e-12
    assert abs((1 / (4 * 0.5**2)) / 2 - 0.5) < 1e-12
    # Cauchy limit: the mean has no finite variance, the median stays tame.
    assert abs(1 / (4 * (1 / PI) ** 2) - PI**2 / 4) < 1e-12


def test_q8():
    first = 1 / 5
    third = 1 / 5 + 1 / 4 + 1 / 3
    last = 1 / 5 + 1 / 4 + 1 / 3 + 1 / 2 + 1
    assert abs(third - 47 / 60) < 1e-12
    assert abs(last - 137 / 60) < 1e-12
    rng = np.random.default_rng(8)
    x = np.sort(rng.exponential(size=(600_000, 5)), axis=1)
    assert abs(x[:, 0].mean() - first) < 0.001
    assert abs(x[:, 2].mean() - third) < 0.002
    assert abs(x[:, 4].mean() - last) < 0.005
    rngspan = x[:, 4] - x[:, 0]
    assert abs(np.corrcoef(x[:, 0], rngspan)[0, 1]) < 0.005
    assert abs(rngspan.mean() - 25 / 12) < 0.005
    # Compare with uniforms, where min and range are clearly dependent.
    u = np.sort(rng.random((200_000, 5)), axis=1)
    assert np.corrcoef(u[:, 0], u[:, 4] - u[:, 0])[0, 1] < -0.3


def test_q9():
    rng = np.random.default_rng(9)
    x = rng.random((400_000, 21))
    beat = x[:, 1:] > x[:, :1]
    none = ~beat.any(axis=1)
    assert abs(none.mean() - 1 / 21) < 0.002
    # P(more than n further draws) = 1 / (n + 1): first draw is the largest of n + 1.
    for n in (1, 4, 9):
        assert abs((~beat[:, :n].any(axis=1)).mean() - 1 / (n + 1)) < 0.003
    # The smallest n with P(N <= n) >= 1/2 is 1, reached exactly, so the median is not unique.
    cdf = [Fr(n, n + 1) for n in range(20)]
    assert next(n for n, c in enumerate(cdf) if c >= Fr(1, 2)) == 1
    assert cdf[0] == 0 and cdf[1] == Fr(1, 2) and 1 - cdf[1] == Fr(1, 2)
    assert abs(beat[:, 0].mean() - 0.5) < 0.003
    # The partial sums of 1/(n+1), the tail sum of the mean, diverge.
    tail = sum(1 / (n + 1) for n in range(0, 10**6))
    assert tail > 14
    # Records at 5 and 10 are independent with chances 1/5 and 1/10.
    y = rng.random((1_000_000, 10))
    r5 = y[:, 4] == y[:, :5].max(axis=1)
    r10 = y[:, 9] == y.max(axis=1)
    assert abs(r5.mean() - 0.2) < 0.002
    assert abs(r10.mean() - 0.1) < 0.002
    assert abs((r5 & r10).mean() - 0.02) < 0.001


def test_q10():
    assert abs(1 - 2 / 2**10 - 511 / 512) < 1e-12
    p = sum(comb(10, k) for k in range(3, 8)) / 2**10
    assert abs(p - 912 / 1024) < 1e-12
    assert round(p, 3) == 0.891
    rng = np.random.default_rng(10)
    for x, med in ((rng.exponential(size=(300_000, 10)), math.log(2)), (rng.standard_normal((300_000, 10)), 0.0)):
        s = np.sort(x, axis=1)
        assert abs(((s[:, 2] < med) & (med < s[:, 7])).mean() - p) < 0.002
        assert abs(((s[:, 0] < med) & (med < s[:, 9])).mean() - 511 / 512) < 0.001


def test_q11():
    n = 1000
    exact = integrate.quad(lambda x: x * n * stats.norm.pdf(x) * stats.norm.cdf(x) ** (n - 1), -10, 10)[0]
    assert round(exact, 2) == 3.24
    assert round(exact / 3, 2) == 1.08
    assert round(math.sqrt(2 * math.log(n)), 2) == 3.72
    # Median of the best: tail ln(2)/n.
    q = stats.norm.isf(math.log(2) / n)
    assert abs(q - 3.2) < 0.01
    # Hand rule: tail of 1/n at about 3.1 standard deviations.
    assert abs(stats.norm.isf(1 / n) - 3.09) < 0.01
    rng = np.random.default_rng(11)
    sim = rng.standard_normal((20_000, n)).max(axis=1).mean()
    assert abs(sim - exact) < 0.01
    # Growth: ten times more trials adds only about 0.6 of a standard deviation.
    def best(size):
        return integrate.quad(lambda x: x * size * stats.norm.pdf(x) * stats.norm.cdf(x) ** (size - 1), -10, 10)[0]

    for a, b in ((100, 1000), (1000, 10000)):
        assert 0.6 < best(b) - best(a) < 0.75
    # n = 1 limit: nothing to select and the expected best is 0.
    e1 = integrate.quad(lambda x: x * stats.norm.pdf(x), -10, 10)[0]
    assert abs(e1) < 1e-9
    # The hand route: 3.2 times a third is about 1.07, below the exact 1.08.
    assert round(q / 3, 2) == 1.07 and round(3.2 / 3, 2) == 1.07


def test_q12():
    def tail(n, r=0.9):
        return n * r ** (n - 1) - (n - 1) * r**n

    assert tail(46) <= 0.05 < tail(45)
    assert round(tail(46), 3) == 0.048
    assert round(tail(45), 3) == 0.052
    rng = np.random.default_rng(12)
    x = rng.random((400_000, 46))
    assert abs(((x.max(axis=1) - x.min(axis=1)) < 0.9).mean() - tail(46)) < 0.002
    # n = 2 limit: P(|X-Y| < r) = 2r - r^2.
    assert abs(tail(2) - (2 * 0.9 - 0.81)) < 1e-12
    # Any continuous law: F(max) - F(min) is the uniform range.
    z = rng.lognormal(size=(200_000, 46))
    f = stats.lognorm.cdf(z, 1)
    assert abs(((f.max(axis=1) - f.min(axis=1)) < 0.9).mean() - tail(46)) < 0.002


def test_q13():
    n = 11
    v_mean = 1 / (12 * n)
    v_median = 1 / (4 * (n + 2))
    v_mid = 1 / (2 * (n + 1) * (n + 2))
    assert (v_mean, v_median, v_mid) == (1 / 132, 1 / 52, 1 / 312)
    rng = np.random.default_rng(13)
    x = rng.random((800_000, n))
    assert abs(x.mean(axis=1).var() / v_mean - 1) < 0.01
    assert abs(np.median(x, axis=1).var() / v_median - 1) < 0.01
    assert abs(((x.max(axis=1) + x.min(axis=1)) / 2).var() / v_mid - 1) < 0.01
    # A normal sample reverses it: the midrange loses to the mean.
    g = rng.standard_normal((200_000, n))
    assert ((g.max(axis=1) + g.min(axis=1)) / 2).var() > 1.5 * g.mean(axis=1).var()
    # n = 1 limit: all three coincide, at 1/12.
    assert 1 / 12 == 1 / (2 * 2 * 3)


def test_q14():
    n, d = 10, 0.01
    p = (1 - (n - 1) * d) ** n
    assert round(p, 3) == 0.389
    rng = np.random.default_rng(14)
    x = np.sort(rng.random((800_000, n)), axis=1)
    g = np.diff(x, axis=1).min(axis=1)
    assert abs((g >= d).mean() - p) < 0.002
    assert abs(g.mean() - 1 / (n**2 - 1)) < 0.0001
    assert round(1000 / 99, 1) == 10.1
    # E[gap] from the tail integral.
    assert abs(integrate.quad(lambda t: (1 - (n - 1) * t) ** n, 0, 1 / (n - 1))[0] - 1 / 99) < 1e-12
    # Limits: no gap requirement gives 1, and the widest possible requirement gives 0.
    assert (1 - (n - 1) * 0) ** n == 1 and abs(1 - (n - 1) * (1 / (n - 1))) < 1e-12
    # Birthday-style approximation gives about the same answer.
    assert abs(math.exp(-comb(n, 2) * 2 * d) - 0.407) < 0.001
    assert round((1 - 2 * d) ** 45, 2) == 0.40


def test_q15():
    e3 = 3 / (2 * math.sqrt(PI))
    e4 = e3 * (1 + 2 / PI * math.asin(1 / 3))
    assert round(e3, 3) == 0.846
    assert round(e4, 3) == 1.029
    for size, val in ((3, e3), (4, e4)):
        num = integrate.quad(
            lambda x, m=size: x * m * stats.norm.pdf(x) * stats.norm.cdf(x) ** (m - 1), -10, 10
        )[0]
        assert abs(num - val) < 1e-9
    # Second route for n = 3: pairwise distances add to twice the range.
    assert abs(3 * (2 / math.sqrt(PI)) / 2 / 2 - e3) < 1e-12
    # n = 5 uses the three-variable orthant formula at correlation 1/3.
    e5 = integrate.quad(lambda x: x * 5 * stats.norm.pdf(x) * stats.norm.cdf(x) ** 4, -10, 10)[0]
    assert round(e5, 3) == 1.163
    assert abs(e5 - 5 / (4 * math.sqrt(PI)) * (1 + 6 / PI * math.asin(1 / 3))) < 1e-9
    # The n = 2 base case.
    e2 = integrate.quad(lambda x: x * 2 * stats.norm.pdf(x) * stats.norm.cdf(x), -10, 10)[0]
    assert abs(e2 - 1 / math.sqrt(PI)) < 1e-9
    rng = np.random.default_rng(15)
    assert abs(rng.standard_normal((1_000_000, 4)).max(axis=1).mean() - e4) < 0.002
