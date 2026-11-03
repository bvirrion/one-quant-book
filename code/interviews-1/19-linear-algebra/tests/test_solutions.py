"""Every number printed in the answers of "Linear Algebra": direct eigenproblems and seeded simulations."""
import math
from itertools import product

import numpy as np
from scipy import special

NONNUMERIC = {}


def eig(a):
    return np.sort(np.linalg.eigvals(np.asarray(a, float)).real)


def test_q1():
    u = np.array([1.0, 2, 3])
    v = np.ones(3)
    a = np.outer(u, v)
    assert np.linalg.matrix_rank(a) == 1
    assert np.allclose(eig(a), [0, 0, 6], atol=1e-8)
    n = 6
    assert np.allclose(eig(np.ones((n, n))), [0] * (n - 1) + [n], atol=1e-8)
    assert np.allclose(eig(np.ones((n, n)) - np.eye(n)), [-1] * (n - 1) + [n - 1], atol=1e-8)


def test_q2():
    n, rho = 10, 0.2
    a = (1 - rho) * np.eye(n) + rho * np.ones((n, n))
    w = np.linalg.eigvalsh(a)
    assert np.allclose(w, [0.8] * 9 + [2.8])
    assert abs(np.ones(n) @ a @ np.ones(n) / n**2 - 0.28) < 1e-12
    low = -1 / (n - 1)
    assert abs(np.linalg.eigvalsh((1 - low) * np.eye(n) + low * np.ones((n, n)))[0]) < 1e-10
    for big in (10, 100, 1000):
        assert abs(rho + (1 - rho) / big - (1 + (big - 1) * rho) / big) < 1e-12


def test_q3():
    a = np.array([[1, 0.9, 0], [0.9, 1, 0.9], [0, 0.9, 1]])
    assert round(np.linalg.det(a), 2) == -0.62
    w = np.linalg.eigvalsh(a)
    assert np.allclose(w, [1 - 0.9 * math.sqrt(2), 1, 1 + 0.9 * math.sqrt(2)])
    assert round(w[0], 3) == -0.273
    p = np.array([1, -math.sqrt(2), 1])
    assert round(p @ a @ p, 3) == round(4 - 3.6 * math.sqrt(2), 3)
    assert round(p @ a @ p, 2) == -1.09


def test_q4():
    rng = np.random.default_rng(4)
    x = rng.normal(size=(20, 3))
    h = x @ np.linalg.solve(x.T @ x, x.T)
    assert np.allclose(h @ h, h)
    assert abs(np.trace(h) - 3) < 1e-9
    assert np.linalg.matrix_rank(h) == 3
    assert np.allclose(eig(h), [0] * 17 + [1] * 3, atol=1e-7)
    # A non-symmetric idempotent matrix: the same rule holds.
    p = np.array([[1.0, 1], [0, 0]])
    assert np.allclose(p @ p, p) and np.trace(p) == 1 and np.linalg.matrix_rank(p) == 1


def test_q5():
    a = np.array([[2, 1], [1, 2]], dtype=object)
    p = a
    for _ in range(9):
        p = p.dot(a)
    assert 3**10 == 59049
    assert p[0, 0] == (59049 + 1) // 2 == 29525
    assert p[0, 1] == (59049 - 1) // 2 == 29524
    inv = np.linalg.inv(np.array([[2.0, 1], [1, 2]]))
    assert np.allclose(inv, np.array([[2, -1], [-1, 2]]) / 3)
    assert abs((1 + 1 / 3) / 2 - 2 / 3) < 1e-12 and abs((1 - 1 / 3) / 2 - 1 / 3) < 1e-12


def test_q6():
    a, b = 0.9, 0.9
    s = math.sqrt((1 - a * a) * (1 - b * b))
    lo, hi = a * b - s, a * b + s
    assert abs(lo - 0.62) < 1e-12 and abs(hi - 1) < 1e-12
    assert abs(math.cos(2 * math.acos(0.9)) - 0.62) < 1e-12
    assert round(math.degrees(math.acos(0.9)), 1) == 25.8
    for c, ok in ((0.62, True), (0.61, False), (1.0, True), (0.8, True)):
        m = np.array([[1, a, c], [a, 1, b], [c, b, 1]])
        assert (np.linalg.eigvalsh(m)[0] > -1e-9) == ok
    # Small correlations give almost no constraint: 0.1 and 0.1 give about plus or minus 0.98.
    assert abs(0.01 - 0.99 + 0.98) < 1e-12


def test_q7():
    n = 5
    p = np.roll(np.eye(n), 1, axis=1)
    w = np.linalg.eigvals(p)
    assert np.allclose(np.abs(w), 1)
    assert abs(np.linalg.cond(p) - 1) < 1e-12
    want = np.exp(2j * np.pi * np.arange(n) / n)
    for z in want:
        assert np.abs(w - z).min() < 1e-9
    c = np.array([[2, 1, 0, 0], [0, 2, 1, 0], [0, 0, 2, 1], [1, 0, 0, 2]], float)
    ww = np.linalg.eigvals(c)
    for z in (3, 1, 2 + 1j, 2 - 1j):
        assert np.abs(ww - z).min() < 1e-9


def test_q8():
    n = 3
    t = 2 * np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)
    assert np.allclose(np.linalg.eigvalsh(t), [2 - math.sqrt(2), 2, 2 + math.sqrt(2)])
    for n in (5, 50):
        t = 2 * np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)
        form = np.sort([2 - 2 * math.cos(k * math.pi / (n + 1)) for k in range(1, n + 1)])
        assert np.allclose(np.linalg.eigvalsh(t), form)
    n = 100
    t = 2 * np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)
    c = np.linalg.cond(t)
    assert abs(c - 4 * (n + 1) ** 2 / math.pi**2) / c < 0.001
    assert round(c, -2) == 4100


def test_q9():
    a = np.array([[1, 0.5], [0.5, 1]])
    w, v = np.linalg.eigh(a)
    assert np.allclose(w, [0.5, 1.5])
    assert abs(abs(v[0, 1]) - 1 / math.sqrt(2)) < 1e-12
    assert 1.5 / 2 == 0.75
    b = np.array([[4, 1], [1, 1]])
    x = np.linalg.eigvalsh(b)
    assert abs(x[1] - (5 + math.sqrt(13)) / 2) < 1e-12
    assert round(x[1], 2) == 4.30
    assert round(x[1] / 5, 2) == 0.86
    u = np.linalg.eigh(b)[1][:, 1]
    assert round(math.degrees(math.atan2(abs(u[1]), abs(u[0]))), 1) == 16.8
    assert abs(math.tan(2 * math.atan2(abs(u[1]), abs(u[0]))) - 2 / 3) < 1e-9


def test_q10():
    a = np.array([[3, 0], [4, 5.0]])
    s = np.linalg.svd(a, compute_uv=False)
    assert np.allclose(s, [3 * math.sqrt(5), math.sqrt(5)])
    assert np.allclose(np.linalg.eigvalsh(a.T @ a), [5, 45])
    assert abs(np.linalg.cond(a) - 3) < 1e-9
    assert np.allclose(eig(a), [3, 5])
    assert round(5 / 3, 2) == 1.67
    # PCA: squared singular values over n - 1 are the covariance eigenvalues.
    rng = np.random.default_rng(10)
    x = rng.normal(size=(200, 4)) @ rng.normal(size=(4, 4))
    x = x - x.mean(axis=0)
    sv = np.linalg.svd(x, compute_uv=False)
    assert np.allclose(np.sort(sv**2 / 199), np.linalg.eigvalsh(np.cov(x.T)))


def test_q11():
    a = np.array([[1, 1], [1, 1.0001]])
    assert np.allclose(np.linalg.solve(a, [2, 2]), [2, 0])
    assert np.allclose(np.linalg.solve(a, [2, 2.0001]), [1, 1])
    c = np.linalg.cond(a)
    assert 3.9e4 < c < 4.1e4
    assert round(math.log10(c), 1) == 4.6
    assert abs(np.linalg.cond(a.T @ a) / c**2 - 1) < 1e-3


def test_q12():
    rng = np.random.default_rng(12)
    t, n = 250, 500
    r = rng.normal(size=(t, n))
    s = np.cov(r.T)
    assert np.linalg.matrix_rank(s) == 249
    w, v = np.linalg.eigh(s)
    null = v[:, 0]
    assert abs(null @ s @ null) < 1e-9
    # True risk of that "riskless" portfolio is unchanged.
    assert abs(null @ null - 1) < 1e-9
    # Shrinkage restores full rank.
    f = 0.5 * s + 0.5 * np.eye(n) * np.trace(s) / n
    assert np.linalg.matrix_rank(f) == n
    # A one-factor model has full rank.
    b = np.ones(n)
    fac = np.outer(b, b) * 0.1 + np.eye(n)
    assert np.linalg.matrix_rank(fac) == n


def test_q13():
    w = np.array([5, 1, 0.1])
    mu = w.mean()
    assert round(mu, 3) == 2.033
    new = 0.7 * w + 0.3 * mu
    assert np.allclose(np.round(new, 2), [4.11, 1.31, 0.68])
    assert w.max() / w.min() == 50
    assert round(new.max() / new.min(), 2) == 6.04
    assert abs(new.sum() - w.sum()) < 1e-12
    # Matrix version: same eigenvectors.
    rng = np.random.default_rng(13)
    q = np.linalg.qr(rng.normal(size=(3, 3)))[0]
    a = q @ np.diag(w) @ q.T
    b = 0.7 * a + 0.3 * mu * np.eye(3)
    assert np.allclose(np.linalg.eigvalsh(b), np.sort(new))
    assert np.allclose(b @ q[:, 0], new[0] * q[:, 0])


def test_q14():
    s1, s2 = 0.1, 0.2

    def weights(rho):
        c = np.array([[s1**2, rho * s1 * s2], [rho * s1 * s2, s2**2]])
        w = np.linalg.solve(c, np.ones(2))
        w = w / w.sum()
        return w, math.sqrt(w @ c @ w)

    w, v = weights(0.5)
    assert abs(w[1]) < 1e-12 and abs(v - 0.1) < 1e-12
    w, v = weights(0.8)
    assert np.allclose(w, [4 / 3, -1 / 3])
    assert round(v, 4) == 0.0894
    w0, v0 = weights(0.0)
    assert np.allclose(w0, [0.8, 0.2])
    # Second route: a grid search on the weight.
    grid = np.linspace(-1, 2, 30001)
    var = grid**2 * 0.01 + (1 - grid) ** 2 * 0.04 + 2 * grid * (1 - grid) * 0.8 * 0.02
    assert abs(grid[var.argmin()] - 4 / 3) < 1e-3
    assert round(0.0894**2, 3) == 0.008


def test_q15():
    p = np.array([[0.9, 0.1], [0.2, 0.8]])
    assert np.allclose(eig(p), [0.7, 1])
    pi = np.array([2 / 3, 1 / 3])
    assert np.allclose(pi @ p, pi)
    assert np.allclose(np.linalg.matrix_power(p, 200)[0], pi)
    assert round(math.log(0.5) / math.log(0.7), 2) == 1.94
    # After one step the gap between the starting states shrinks by 0.7.
    assert abs(p[0, 0] - p[1, 0] - 0.7) < 1e-12


def test_q16():
    phi = (1 + math.sqrt(5)) / 2
    fib = [0, 1]
    for _ in range(100):
        fib.append(fib[-1] + fib[-2])
    assert fib[30] == 832040
    m = np.array([[1, 1], [1, 0]], dtype=object)
    power = np.linalg.matrix_power(m, 30)
    assert power[0, 1] == 832040
    first_bad = next(n for n in range(100) if round(phi**n / math.sqrt(5)) != fib[n])
    assert first_bad == 71
    assert 2 * math.floor(math.log2(1000)) == 18
    assert np.allclose(eig([[1, 1], [1, 0]]), [(1 - math.sqrt(5)) / 2, phi])


def test_q17():
    n = 100
    i = np.arange(1, n + 1.0)
    a = i[:, None] + i[None, :]
    assert np.linalg.matrix_rank(a) == 2
    eu = i.sum()
    root = math.sqrt(n * (i**2).sum())
    assert eu == 5050 and (i**2).sum() == 338350
    assert round(root, 1) == 5816.8
    w = np.linalg.eigvalsh(a)
    assert abs(w[-1] - (eu + root)) < 1e-7 and abs(w[0] - (eu - root)) < 1e-7
    assert round(eu + root, 1) == 10866.8 and round(eu - root, 1) == -766.8
    assert abs(np.trace(a) - 10100) < 1e-9


def test_q18():
    n, t = 500, 1000
    q = n / t
    lo, hi = (1 - math.sqrt(q)) ** 2, (1 + math.sqrt(q)) ** 2
    assert round(lo, 3) == 0.086 and round(hi, 3) == 2.914
    rng = np.random.default_rng(18)
    r = rng.normal(size=(t, n))
    s = r.T @ r / t
    w = np.linalg.eigvalsh(s)
    assert abs(w[0] - lo) < 0.03 and abs(w[-1] - hi) < 0.1
    # Minimum-variance: true optimum 1/n, in sample (1 - q)/n, out of sample 1/((1 - q) n).
    ins, outs = [], []
    for seed in range(20):
        x = np.random.default_rng(seed).normal(size=(t, n))
        c = x.T @ x / t
        y = np.linalg.solve(c, np.ones(n))
        y = y / y.sum()
        ins.append(y @ c @ y)
        outs.append(y @ y)
    assert abs(np.mean(ins) * n - (1 - q)) < 0.02
    assert abs(np.mean(outs) * n - 1 / (1 - q)) < 0.05


def test_q19():
    n = 1000
    rng = np.random.default_rng(19)
    beta = rng.uniform(0.2, 2, n) * 0.2
    d = rng.uniform(0.01, 0.09, n)
    sigma = np.diag(d) + np.outer(beta, beta)
    x = beta / d
    inv = np.diag(1 / d) - np.outer(x, x) / (1 + beta @ x)
    assert np.allclose(inv @ sigma, np.eye(n), atol=1e-7)
    # Weights: the fast formula against a direct solve.
    e = np.ones(n)
    fast = e / d - x * (e @ x) / (1 + beta @ x)
    direct = np.linalg.solve(sigma, e)
    assert np.allclose(fast, direct, atol=1e-6)
    # Weights fall with beta, and can go negative for high beta.
    # Equal residual risk: then w is linear in beta.
    d2 = np.full(n, 0.04)
    x2 = beta / d2
    w2 = e / d2 - x2 * (e @ x2) / (1 + beta @ x2)
    assert (np.corrcoef(w2, beta)[0, 1] + 1) < 1e-9
    assert w2[beta.argmax()] < w2[beta.argmin()]


def test_q20():
    a = np.array([[1, 0.5, 0.5], [0.5, 1, 0.5], [0.5, 0.5, 1]])
    p = np.linalg.inv(a)
    assert abs(-p[0, 1] / math.sqrt(p[0, 0] * p[1, 1]) - 1 / 3) < 1e-12
    assert abs((0.5 - 0.25) / (1 - 0.25) - 1 / 3) < 1e-12
    rng = np.random.default_rng(20)
    x = rng.multivariate_normal(np.zeros(3), a, 2_000_000)
    r1 = x[:, 0] - 0.5 * x[:, 2]
    r2 = x[:, 1] - 0.5 * x[:, 2]
    assert abs(np.corrcoef(r1, r2)[0, 1] - 1 / 3) < 0.002
    for rho in (-0.3, 0.0, 0.2, 0.9):
        b = (1 - rho) * np.eye(3) + rho * np.ones((3, 3))
        q = np.linalg.inv(b)
        assert abs(-q[0, 1] / math.sqrt(q[0, 0] * q[1, 1]) - rho / (1 + rho)) < 1e-12


def test_q21():
    assert math.ceil(math.log(1e-6) / math.log(0.5)) == 20
    assert math.ceil(math.log(1e-6) / math.log(0.25)) == 10
    assert round(math.log(1e-6) / math.log(0.99)) == 1375
    n = 1000
    rng = np.random.default_rng(21)
    q = np.linalg.qr(rng.normal(size=(n, n)))[0]
    w = np.ones(n)
    w[0], w[1] = 10, 5
    a = (q * w) @ q.T
    x = rng.normal(size=n)
    x /= np.linalg.norm(x)
    for k in range(1, 31):
        x = a @ x
        x /= np.linalg.norm(x)
        if k in (10, 20):
            err = np.linalg.norm(x - q[:, 0] * np.sign(x @ q[:, 0]))
            lam = x @ a @ x
            if k == 20:
                assert err < 5e-5
            if k == 10:
                assert abs(lam - 10) < 1e-3
    # A start orthogonal to the top vector stays there.
    y = q[:, 1] + q[:, 3]
    for _ in range(40):
        y = a @ y
        y -= q[:, 0] * (q[:, 0] @ y)
        y /= np.linalg.norm(y)
    assert abs(y @ q[:, 0]) < 1e-9
    # Tied top eigenvalues: it still converges, to the start's projection on the plane, so the start decides.
    w = np.array([10.0, 10.0, 5.0, 3.0, 1.0])
    basis = np.linalg.qr(rng.normal(size=(5, 5)))[0]
    tied = (basis * w) @ basis.T
    ends = []
    for _ in range(2):
        start = rng.normal(size=5)
        z = start / np.linalg.norm(start)
        for _ in range(200):
            z = tied @ z
            z /= np.linalg.norm(z)
        plane = basis[:, :2] @ (basis[:, :2].T @ start)
        assert abs(abs(z @ plane) / np.linalg.norm(plane) - 1) < 1e-12
        assert np.linalg.norm(tied @ z - 10 * z) < 1e-9
        ends.append(z)
    assert abs(ends[0] @ ends[1]) < 0.999


def test_q22():
    rng = np.random.default_rng(22)
    a = rng.normal(size=(5, 12))
    b = rng.normal(size=(12, 5))
    w1 = np.sort(np.abs(np.linalg.eigvals(a @ b)))
    w2 = np.sort(np.abs(np.linalg.eigvals(b @ a)))[-5:]
    assert np.allclose(w1, w2)
    t, n = 250, 5000
    x = rng.normal(size=(t, n))
    x -= x.mean(axis=0)
    g = x @ x.T
    wg, ug = np.linalg.eigh(g)
    u1 = ug[:, -1]
    v1 = x.T @ u1 / math.sqrt(wg[-1])
    assert abs(v1 @ v1 - 1) < 1e-9
    assert np.allclose(x.T @ (x @ v1), wg[-1] * v1)
    u = rng.normal(size=6)
    v = rng.normal(size=6)
    assert abs(np.linalg.det(np.eye(6) + np.outer(u, v)) - (1 + v @ u)) < 1e-9
    assert round(250**3 / 5000**3, 6) == 0.000125


def test_q23():
    a = np.array([[1, 0.9, 0], [0.9, 1, 0.9], [0, 0.9, 1]])
    w, v = np.linalg.eigh(a)
    assert round(w[0], 3) == -0.273 and round(w[2], 3) == 2.273
    clip = (v * np.maximum(w, 0)) @ v.T
    d = np.sqrt(np.diag(clip))
    fix = clip / np.outer(d, d)
    assert round(fix[0, 1], 3) == 0.729
    assert round(fix[0, 2], 3) == 0.064
    assert round(fix[1, 2], 3) == 0.729
    assert np.linalg.eigvalsh(fix)[0] > -1e-9
    assert abs(np.linalg.eigvalsh(fix)[0]) < 1e-9
    assert round(np.linalg.norm(a - clip), 3) == 0.273
    # Alternating projection reaches a matrix at least as close, in Frobenius norm, to the original.
    x = a.copy()
    ds = np.zeros((3, 3))
    for _ in range(3000):
        r = x - ds
        e, q = np.linalg.eigh(r)
        p = (q * np.maximum(e, 0)) @ q.T
        ds = p - r
        x = p.copy()
        np.fill_diagonal(x, 1)
    assert np.linalg.norm(a - x) <= np.linalg.norm(a - fix) + 1e-9
    assert round(x[0, 1], 2) == 0.74
    assert round(x[0, 2], 3) == 0.105


def test_q24():
    total = 0
    count = 0
    for bits in product([-1, 1], repeat=9):
        total += round(np.linalg.det(np.array(bits).reshape(3, 3))) ** 2
        count += 1
    assert count == 512
    assert total / count == 6
    rng = np.random.default_rng(24)
    for n in (2, 4, 5):
        x = rng.normal(size=(300_000, n, n))
        assert abs((np.linalg.det(x) ** 2).mean() / math.factorial(n) - 1) < 0.06
    # Typical size against the largest of the 3 by 3 case.
    best = max(abs(round(np.linalg.det(np.array(b).reshape(3, 3)))) for b in product([-1, 1], repeat=9))
    assert best == 4
    assert round(3 ** (3 / 2), 2) == 5.2
    assert round(math.sqrt(6), 2) == 2.45
    # The ratio of the typical size to Hadamard's bound falls like e^(-n/2).
    n = 100
    log_ratio = 0.5 * math.lgamma(n + 1) - n / 2 * math.log(n)
    assert abs(log_ratio / (-n / 2) - 1) < 0.05
    # Mean 0 with a skewed entry, 2 with chance 1/5 and -1/2 with chance 4/5: flipping a row changes that row's law,
    # since the third moment is not zero, but every term of the expansion still has mean zero, and E[det^2] is still 3!.
    vals, probs = (2.0, -0.5), (0.2, 0.8)
    assert abs(sum(p * v for v, p in zip(vals, probs, strict=True))) < 1e-12
    assert abs(sum(p * v * v for v, p in zip(vals, probs, strict=True)) - 1) < 1e-12
    assert abs(sum(p * v**3 for v, p in zip(vals, probs, strict=True)) - 1.5) < 1e-12
    m1 = m2 = 0.0
    for choice in product((0, 1), repeat=9):
        weight = float(np.prod([probs[c] for c in choice]))
        det = np.linalg.det(np.array([vals[c] for c in choice]).reshape(3, 3))
        m1 += weight * det
        m2 += weight * det**2
    assert abs(m1) < 1e-9 and abs(m2 - 6) < 1e-9
    # The root-mean-square size against a typical value, for normal entries, from det^2 = a product of chi-squares.
    for k, printed in ((5, 3.9), (10, 5.4), (20, 7.6), (100, 17.0)):
        mean_log = 0.5 * sum(special.digamma(j / 2) + math.log(2) for j in range(1, k + 1))
        factor = math.exp(0.5 * math.lgamma(k + 1) - mean_log)
        assert abs(factor - printed) < 0.06
        assert abs(factor / math.sqrt(k) - 1.7) < 0.03
    x = rng.normal(size=(40_000, 5, 5))
    assert abs(math.exp(np.linalg.slogdet(x)[1].mean()) * 3.86 / math.sqrt(120) - 1) < 0.02


def test_q25():
    rng = np.random.default_rng(25)
    for _ in range(200):
        n = 6
        a = rng.normal(size=(n, 4))
        b = rng.normal(size=(n, 3))
        x, y = a @ a.T, b @ b.T
        z = x * y
        assert np.linalg.eigvalsh(z)[0] > -1e-9
        x2 = x + 0.5 * np.eye(n)
        low = np.linalg.eigvalsh(x2)[0] * np.diag(y).min()
        assert np.linalg.eigvalsh(x2 * y)[0] >= low - 1e-9
    # The taper is itself positive definite: it is the AR(1) correlation matrix.
    n = 8
    taper = np.exp(-0.3 * np.abs(np.arange(n)[:, None] - np.arange(n)[None, :]))
    assert np.linalg.eigvalsh(taper)[0] > 0
    c = np.corrcoef(rng.normal(size=(50, n)).T)
    t = c * taper
    assert np.allclose(np.diag(t), 1)
    assert np.linalg.eigvalsh(t)[0] > 0
    # A hard cut-off is not PSD: a banded version of a strong one-factor matrix goes negative.
    rho = 0.9
    one = np.full((n, n), rho) + (1 - rho) * np.eye(n)
    band = np.where(np.abs(np.arange(n)[:, None] - np.arange(n)[None, :]) <= 1, one, 0)
    assert np.linalg.eigvalsh(band)[0] < 0
