"""Every number printed in the answers of "Continuous and Geometric Probability": exact, then a seeded simulation."""
import math

import numpy as np
from scipy import integrate

NONNUMERIC = {}
PI = math.pi


def test_q1():
    rng = np.random.default_rng(1)
    u = rng.random(2_000_000)
    long_ = np.maximum(u, 1 - u)
    assert abs(long_.mean() - 0.75) < 0.001
    ratio = (1 - long_) / long_
    assert abs(ratio.mean() - (2 * math.log(2) - 1)) < 0.001
    assert round(2 * math.log(2) - 1, 3) == 0.386
    value, _ = integrate.quad(lambda x: 2 * (1 - x) / x, 0.5, 1)
    assert abs(value - (2 * math.log(2) - 1)) < 1e-10


def test_q2():
    exact = 0.5 + 0.5 * math.log(2)
    assert round(exact, 3) == 0.847
    value, _ = integrate.quad(lambda x: min(1, 0.5 / x), 0, 1, points=[0.5])
    assert abs(value - exact) < 1e-9
    rng = np.random.default_rng(2)
    x, y = rng.random((2, 2_000_000))
    assert abs((x * y < 0.5).mean() - exact) < 0.001


def test_q3():
    rng = np.random.default_rng(3)
    d = np.abs(rng.random(4_000_000) - rng.random(4_000_000))
    assert abs(d.mean() - 1 / 3) < 0.001
    assert abs(d.var() - 1 / 18) < 0.001
    assert abs(1 / 6 - 1 / 9 - 1 / 18) < 1e-15
    # Density 2(1-x) on [0,1] agrees.
    assert abs(integrate.quad(lambda x: 2 * x * (1 - x), 0, 1)[0] - 1 / 3) < 1e-12


def test_q4():
    assert 1 - (3 / 4) ** 2 == 7 / 16
    rng = np.random.default_rng(4)
    a, b = rng.random((2, 2_000_000))
    assert abs((np.abs(a - b) < 0.25).mean() - 7 / 16) < 0.001
    # Waiting the whole hour always works; not waiting at all never does.
    assert 1 - (1 - 1) ** 2 == 1 and 1 - (1 - 0) ** 2 == 0


def test_q5():
    assert round(1 - 0.9**1, 2) == 0.1
    assert round(1 - 0.9**10, 3) == 0.651
    assert round(1 - 0.9**100, 5) == 0.99997
    assert round(PI / 6, 4) == 0.5236
    ball10 = PI**5 / (math.gamma(6) * 2**10)
    assert round(ball10, 4) == 0.0025
    rng = np.random.default_rng(5)
    x = rng.random((400_000, 10))
    assert abs((((x - 0.5) ** 2).sum(axis=1) <= 0.25).mean() - ball10) < 0.0005
    near = ((x < 0.05) | (x > 0.95)).any(axis=1).mean()
    assert abs(near - (1 - 0.9**10)) < 0.003
    # The typical distance from the centre in d dimensions, sqrt(d/12).
    assert abs(math.sqrt(100 / 12) - 2.887) < 0.001


def test_q6():
    rng = np.random.default_rng(6)
    u, v = rng.random((2, 2_000_000))
    a, b = np.minimum(u, v), np.maximum(u, v)
    good = (a < 0.5) & (b - a < 0.5) & (1 - b < 0.5)
    assert abs(good.mean() - 0.25) < 0.001
    c = rng.random(2_000_000)
    long_ = np.maximum(c, 1 - c)
    cut = rng.random(2_000_000) * long_
    longer = (1 - long_ < 0.5) & (cut < 0.5) & (long_ - cut < 0.5)
    exact = 2 * math.log(2) - 1
    assert abs(longer.mean() - exact) < 0.001
    # A random piece: half the time the longer, and the shorter never works.
    pick_long = rng.random(2_000_000) < 0.5
    assert abs((longer & pick_long).mean() - exact / 2) < 0.001
    assert round(exact / 2, 3) == 0.193


def test_q7():
    rng = np.random.default_rng(7)
    x, y, z = rng.random((3, 3_000_000))
    ok = (x + y > z) & (x + z > y) & (y + z > x)
    assert abs(ok.mean() - 0.5) < 0.001
    assert 1 - 3 * (1 / 6) == 0.5


def test_q8():
    assert round(2 / PI, 3) == 0.637
    assert round(2 * 3 / PI, 3) == 1.910
    rng = np.random.default_rng(8)
    n = 3_000_000
    x = rng.random(n)
    theta = rng.random(n) * PI
    for length, want in ((1, 2 / PI), (3, 6 / PI)):
        end = x + length * np.sin(theta)
        crossings = np.floor(end) - np.floor(x)
        assert abs(crossings.mean() - want) < 0.002
    # A circle of diameter 1 has length pi and always crosses exactly 2 times: the formula must give 2.
    assert 2 * PI / PI == 2


def test_q9():
    rng = np.random.default_rng(9)
    for k, want in ((3, 3 / 4), (5, 5 / 16), (2, 1)):
        assert k / 2 ** (k - 1) == want
        pts = np.sort(rng.random((400_000, k)), axis=1)
        gaps = np.diff(np.c_[pts, pts[:, 0] + 1], axis=1)
        assert abs((gaps.max(axis=1) >= 0.5).mean() - want) < 0.002
    assert 1 - 3 / 4 == 1 / 4


def test_q10():
    rng = np.random.default_rng(10)
    p = rng.random((1_000_000, 4))
    a, b = np.minimum(p[:, 0], p[:, 1]), np.maximum(p[:, 0], p[:, 1])
    inside = (a < p[:, 2]) & (p[:, 2] < b)
    other = (a < p[:, 3]) & (p[:, 3] < b)
    assert abs((inside != other).mean() - 1 / 3) < 0.002
    assert math.comb(10, 2) / 3 == 15
    points = rng.random((20_000, 20))
    lo = np.minimum(points[:, ::2], points[:, 1::2])
    hi = np.maximum(points[:, ::2], points[:, 1::2])
    total = 0
    for i in range(10):
        for j in range(i + 1, 10):
            ci = (lo[:, i] < lo[:, j]) & (lo[:, j] < hi[:, i])
            cj = (lo[:, i] < hi[:, j]) & (hi[:, j] < hi[:, i])
            total += (ci != cj).sum()
    assert abs(total / 20_000 - 15) < 0.1


def test_q11():
    side = math.sqrt(3)
    rng = np.random.default_rng(11)
    n = 3_000_000
    t = rng.random(n) * 2 * PI
    assert abs((2 * np.sin(t / 2) > side).mean() - 1 / 3) < 0.001
    d = rng.random(n)
    assert abs((2 * np.sqrt(1 - d**2) > side).mean() - 1 / 2) < 0.001
    r = np.sqrt(rng.random(n))
    assert abs((2 * np.sqrt(1 - r**2) > side).mean() - 1 / 4) < 0.001
    # A chord of that length sits at distance 1/2 from the centre.
    assert abs(2 * math.sqrt(1 - 0.25) - side) < 1e-12


def test_q12():
    rng = np.random.default_rng(12)
    x, y = rng.normal(size=(2, 3_000_000))
    assert abs(((x > 0) & (y > math.sqrt(3) * x)).mean() - 1 / 12) < 0.001
    assert abs(((x + y > 0)[x > 0]).mean() - 3 / 4) < 0.001
    assert abs((90 - 60) / 360 - 1 / 12) < 1e-12
    assert 135 / 180 == 3 / 4
    # A fully correlated variable moves that to one.
    assert abs(0.5 + math.asin(1 / math.sqrt(2)) / PI - 3 / 4) < 1e-12


def test_q13():
    assert round(math.exp(-2), 3) == 0.135
    assert round(1 / math.sqrt(PI), 3) == 0.564
    assert round(1 - 1 / PI, 3) == 0.682
    rng = np.random.default_rng(13)
    x, y = rng.normal(size=(2, 4_000_000))
    assert abs((x**2 + y**2 > 4).mean() - math.exp(-2)) < 0.0006
    big = np.maximum(x, y)
    assert abs(big.mean() - 1 / math.sqrt(PI)) < 0.001
    assert abs(big.var() - (1 - 1 / PI)) < 0.001
    assert abs((big**2).mean() - 1) < 0.002


def test_q14():
    last1 = (2 / 6) * (3 / 4) + (3 / 6) * (2 / 3)
    assert abs(last1 - 7 / 12) < 1e-12
    mean_all = 1 + 1 / 2 + 1 / 3 - 1 / 3 - 1 / 4 - 1 / 5 + 1 / 6
    assert abs(mean_all - 73 / 60) < 1e-12
    assert round(73 / 60, 3) == 1.217
    # Second route: the order-based sum over the first failure and the rest.
    route = 1 / 6 + (1 / 6) * (1 / (2 + 3) + (2 / 5) * (1 / 3) + (3 / 5) * (1 / 2))
    route += (2 / 6) * (1 / (1 + 3) + (1 / 4) * (1 / 3) + (3 / 4) * 1)
    route += (3 / 6) * (1 / (1 + 2) + (1 / 3) * (1 / 2) + (2 / 3) * 1)
    assert abs(route - 73 / 60) < 1e-12
    rng = np.random.default_rng(14)
    t = rng.exponential(1, (3_000_000, 3)) / np.array([1, 2, 3])
    assert abs((t.argmax(axis=1) == 0).mean() - 7 / 12) < 0.001
    assert abs(t.max(axis=1).mean() - 73 / 60) < 0.002


def test_q15():
    assert round(1 - math.exp(-1), 3) == 0.632
    assert 0.5**3 == 1 / 8
    rng = np.random.default_rng(15)
    n = rng.poisson(2, 3_000_000)
    assert abs((rng.poisson(1, 3_000_000) >= 1).mean() - (1 - math.exp(-1))) < 0.001
    keep = np.flatnonzero(n == 3)[:300_000]
    times = np.sort(rng.random((len(keep), 3)), axis=1)
    assert abs(times[:, 0].mean() - 1 / 4) < 0.002
    assert abs((times[:, 0] > 0.5).mean() - 1 / 8) < 0.002
    # Direct simulation of gaps, keeping only minutes with exactly three arrivals.
    gaps = rng.exponential(1 / 2, (1_000_000, 5))
    cum = gaps.cumsum(axis=1)
    three = (cum[:, 2] < 1) & (cum[:, 3] > 1)
    assert abs(cum[three, 0].mean() - 1 / 4) < 0.003


def test_q16():
    rng = np.random.default_rng(16)
    x, y = rng.random((2, 3_000_000))
    r = np.minimum(x, y) / np.maximum(x, y)
    assert abs(r.mean() - 0.5) < 0.001
    for t in (0.1, 0.5, 0.9):
        assert abs((r < t).mean() - t) < 0.001
    ratio = x / y
    assert abs(np.median(ratio) - 1) < 0.003
    # The truncated mean keeps growing with the cut-off: log growth of a divergent integral.
    means = [np.minimum(ratio, c).mean() for c in (10, 100, 1000)]
    assert means[0] < means[1] < means[2]
    assert abs(means[1] - means[0] - 0.5 * math.log(10)) < 0.1


def test_q17():
    p = PI / 4
    se = 4 * math.sqrt(p * (1 - p))
    assert round(se, 3) == 1.642
    n = (1.96 * se / 0.001) ** 2
    assert round(n / 1e7, 2) == 1.04
    rng = np.random.default_rng(17)
    size = 10_000
    runs = 2_000
    x, y = rng.random((2, runs, size))
    est = 4 * ((x**2 + y**2) < 1).mean(axis=1)
    assert abs(est.std() - se / 100) < 0.002
    assert abs(est.mean() - PI) < 0.002


def orthant(rho):
    return 1 / 8 + 3 * math.asin(rho) / (4 * PI)


def test_q18():
    assert abs(orthant(0.5) - 1 / 4) < 1e-12
    assert abs(orthant(0) - 1 / 8) < 1e-12
    assert abs(orthant(1) - 1 / 2) < 1e-12
    assert abs(orthant(-0.5)) < 1e-12
    rng = np.random.default_rng(18)
    for rho in (0.5, 0.2, -0.3):
        cov = np.full((3, 3), rho) + (1 - rho) * np.eye(3)
        z = rng.multivariate_normal(np.zeros(3), cov, 2_000_000, method="cholesky")
        assert abs((z > 0).all(axis=1).mean() - orthant(rho)) < 0.001
    # A matrix at rho below -1/2 is not a covariance matrix.
    assert np.linalg.eigvalsh(np.full((3, 3), -0.6) + 1.6 * np.eye(3)).min() < 0
    assert abs(np.linalg.eigvalsh(np.full((3, 3), -0.5) + 1.5 * np.eye(3)).min()) < 1e-12


def test_q19():
    assert 1 / 100 == 1 / 10**2
    h10 = sum(1 / k for k in range(1, 11))
    assert round(h10 / 10, 4) == 0.2929
    rng = np.random.default_rng(19)
    cuts = np.sort(rng.random((1_000_000, 9)), axis=1)
    pieces = np.diff(np.c_[np.zeros(1_000_000), cuts, np.ones(1_000_000)], axis=1)
    assert abs(pieces.min(axis=1).mean() - 0.01) < 0.0002
    assert abs(pieces.max(axis=1).mean() - h10 / 10) < 0.0005
    # Exponentials, normalised, as a second route: the same spacings.
    e = rng.exponential(1, (1_000_000, 10))
    s = e / e.sum(axis=1, keepdims=True)
    assert abs(s.min(axis=1).mean() - 0.01) < 0.0002
    assert abs(s.max(axis=1).mean() - h10 / 10) < 0.0005
    # One piece has to be the whole stick.
    assert sum(1 / k for k in range(1, 2)) / 1 == 1


def test_q20():
    assert 1 - 5 / 2**4 == 11 / 16
    rng = np.random.default_rng(20)
    for k, want in ((5, 11 / 16), (3, 1 / 4), (4, 1 / 2)):
        assert 1 - k / 2 ** (k - 1) == want
        cuts = np.sort(rng.random((1_000_000, k - 1)), axis=1)
        pieces = np.diff(np.c_[np.zeros(1_000_000), cuts, np.ones(1_000_000)], axis=1)
        assert abs((pieces.max(axis=1) < 0.5).mean() - want) < 0.002
    # One piece at least 1/2 has chance (1/2)^(k-1), and two cannot both be: the tail is exact.
    cuts = np.sort(rng.random((1_000_000, 4)), axis=1)
    first = cuts[:, 0]
    assert abs((first >= 0.5).mean() - 1 / 16) < 0.001


def test_q21():
    assert round(3 / (2 * PI), 3) == 0.477
    # E[sin of one arc] = 1/pi with density (1/pi)(1 - a / (2 pi)) on (0, 2 pi).
    value, _ = integrate.quad(lambda a: math.sin(a) * (1 - a / (2 * PI)) / PI, 0, 2 * PI)
    assert abs(value - 1 / PI) < 1e-10
    rng = np.random.default_rng(21)
    t = np.sort(rng.random((3_000_000, 3)) * 2 * PI, axis=1)
    x, y = np.cos(t), np.sin(t)
    area = 0.5 * np.abs((x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0]))
    assert abs(area.mean() - 3 / (2 * PI)) < 0.001
    gaps = np.diff(np.c_[t, t[:, 0] + 2 * PI], axis=1)
    formula = 0.5 * np.sin(gaps).sum(axis=1)
    assert np.allclose(formula, area, atol=1e-9)
    # The largest inscribed triangle, the equilateral one, has area about 1.30: the mean stays well below it.
    assert round(3 * math.sqrt(3) / 4, 2) == 1.30


def test_q22():
    exact = (4 * math.sqrt(2) - 5) / 3
    assert round(exact, 3) == 0.219
    y0 = (math.sqrt(2) - 1) / 2
    assert abs(y0**2 + y0 - 0.25) < 1e-12
    assert round(y0, 3) == 0.207
    slice_area = 2 * (y0 / 4 - y0**3 / 3 - y0**2 / 2)
    assert abs(4 * slice_area - exact) < 1e-12
    rng = np.random.default_rng(22)
    x, y = rng.random((2, 4_000_000)) - 0.5
    to_centre = np.hypot(x, y)
    to_edge = 0.5 - np.maximum(np.abs(x), np.abs(y))
    assert abs((to_centre < to_edge).mean() - exact) < 0.0005
    # The disc of radius 1/4 lies inside the region; the inscribed disc of radius 1/2 contains it.
    assert PI / 16 < exact < PI / 4


def test_q23():
    unpainted = 1 - 2 * (1 / 4) + 1 / 9
    painted = 1 - unpainted
    # A gap is painted unless each neighbouring gap is shorter; with L having density L e^-L after size-biasing.
    assert abs(unpainted - 11 / 18) < 1e-12 and abs(painted - 7 / 18) < 1e-12
    assert round(7 / 18, 3) == 0.389
    rng = np.random.default_rng(23)
    x = np.sort(rng.random(2_000_000))
    gaps = np.diff(x)
    left = np.r_[np.inf, gaps[:-1]]
    right = np.r_[gaps[1:], np.inf]
    frac = gaps[(gaps < left) | (gaps < right)].sum() / gaps.sum()
    assert abs(frac - 7 / 18) < 0.002
    # The integral with the exponential density, as a check on the formula.
    value, _ = integrate.quad(lambda s: s * math.exp(-s) * (1 - (1 - math.exp(-s)) ** 2), 0, 50)
    assert abs(value - 7 / 18) < 1e-9
    # Three birds, exactly: two gaps; each end bird paints its one gap, so everything is painted.
    assert frac < 1


def test_q24():
    assert 1 / 8 == 1 - 7 / 8
    # Wendel's sum: 2^-(n-1) * sum of C(n-1, k) for k below the dimension.
    assert sum(math.comb(3, k) for k in range(3)) / 2**3 == 7 / 8
    rng = np.random.default_rng(24)
    p = rng.normal(size=(1_000_000, 4, 3))
    p /= np.linalg.norm(p, axis=2, keepdims=True)
    a = p[:, :3, :].transpose(0, 2, 1)
    # The centre is inside exactly when 0 is a positive combination of the four corners.
    w = np.linalg.solve(a, -p[:, 3:, :].transpose(0, 2, 1))[:, :, 0]
    assert abs((w > 0).all(axis=1).mean() - 1 / 8) < 0.001
    # The circle's version with the same argument: 1/4.
    assert sum(math.comb(2, k) for k in range(2)) / 2**2 == 3 / 4


def test_q25():
    assert round(4 / PI, 3) == 1.273
    assert round(3 / PI, 3) == 0.955
    no_cross, _ = integrate.quad(lambda t: (1 - math.cos(t)) * (1 - math.sin(t)) * 2 / PI, 0, PI / 2)
    assert abs(no_cross - (1 - 3 / PI)) < 1e-10
    both, _ = integrate.quad(lambda t: math.cos(t) * math.sin(t) * 2 / PI, 0, PI / 2)
    assert abs(both - 1 / PI) < 1e-10
    assert abs(2 * (2 / PI) - 1 / PI - 3 / PI) < 1e-12
    rng = np.random.default_rng(25)
    n = 4_000_000
    x, y = rng.random((2, n))
    t = rng.random(n) * PI / 2
    cx = np.floor(x + np.cos(t))
    cy = np.floor(y + np.sin(t))
    assert abs((cx + cy).mean() - 4 / PI) < 0.001
    assert abs(((cx + cy) >= 1).mean() - 3 / PI) < 0.001


def test_printed_numbers_in_follow_ups() -> None:
    rng = np.random.default_rng(1207)
    n = 1_000_000
    # Q2: median of the product of two uniforms solves t(1 - ln t) = 1/2.
    product = rng.random(n) * rng.random(n)
    assert abs(float(np.median(product)) - 0.187) < 0.002
    # Q7 follow-up: four uniform sticks form a quadrilateral with chance 5/6.
    sticks = rng.random((n, 4))
    ok = 2 * sticks.max(axis=1) < sticks.sum(axis=1)
    assert abs(float(ok.mean()) - 5 / 6) < 0.002
    # Q18 second route and follow-up: correlation 1/2 gives 1/(n+1), both ways.
    for k in (3, 4, 5):
        w = rng.standard_normal((n, k + 1))
        direct = np.sqrt(0.5) * w[:, 0:1] + np.sqrt(0.5) * w[:, 1:]
        assert abs(float((direct > 0).all(axis=1).mean()) - 1 / (k + 1)) < 0.002
    # Q18 wrong answer: P(Z > 0 | X, Y > 0) = (1/4) / (1/3).
    assert abs(0.25 / (1 / 3) - 0.75) < 1e-12
    # Q23 follow-up: two thirds of the gaps, by count, are painted.
    gaps = rng.exponential(size=n)
    left_paints = gaps[1:-1] < gaps[:-2]
    right_paints = gaps[1:-1] < gaps[2:]
    assert abs(float((left_paints | right_paints).mean()) - 2 / 3) < 0.002
    # Q22 wrong answer: the corner of the region lies sqrt(2) y0 from the centre.
    assert abs(math.sqrt(2) * (math.sqrt(2) - 1) / 2 - 0.293) < 0.001
