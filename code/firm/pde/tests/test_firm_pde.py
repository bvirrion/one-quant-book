"""Acceptance tests of firm.pde (Python)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_pde import (  # noqa: E402
    amplification,
    douglas_adi_2d,
    interp,
    operator,
    richardson,
    sinh_grid,
    solve_1d,
    thomas,
    uniform_grid,
)

K, R, SIG, T = 100.0, 0.03, 0.2, 0.5


def ncdf(z):
    return 0.5 * math.erfc(-z / math.sqrt(2))


def bs_call(S):
    d1 = (math.log(S / K) + (R + 0.5 * SIG**2) * T) / (SIG * math.sqrt(T))
    return S * ncdf(d1) - K * math.exp(-R * T) * ncdf(d1 - SIG * math.sqrt(T))


def price(n, theta, rannacher, grid="uniform", right=("gamma0",)):
    lo, hi = math.log(K) - 5 * SIG * math.sqrt(T), math.log(K) + 5 * SIG * math.sqrt(T)
    x = uniform_grid(lo, hi, n) if grid == "uniform" else sinh_grid(lo, hi, n, math.log(K), 0.1)
    u = solve_1d(x, lambda z: np.maximum(np.exp(z) - K, 0.0), 0.5 * SIG**2, R - 0.5 * SIG**2, R, T, n // 8,
                 theta=theta, rannacher=rannacher, right=right)
    return abs(interp(x, u, math.log(K)) - bs_call(K))


def test_thomas_and_operator():
    rng = np.random.default_rng(0)
    n = 30
    lo, up = rng.uniform(-1, 0, n), rng.uniform(-1, 0, n)
    di = 3 + rng.uniform(0, 1, n)
    rhs = rng.standard_normal(n)
    M = np.diag(di) + np.diag(lo[1:], -1) + np.diag(up[:-1], 1)
    assert np.allclose(thomas(lo, di, up, rhs), np.linalg.solve(M, rhs), atol=1e-13)
    x = sinh_grid(-1.0, 2.0, 60, 0.3, 0.2)
    assert np.all(np.diff(x) > 0) and abs(x[0] + 1) < 1e-12 and abs(x[-1] - 2) < 1e-12
    assert np.diff(x).min() < 0.3 * np.diff(x).max()                 # finer near the centre
    lo_, di_, up_ = operator(x, 0.5, 0.2, 0.1)                       # exact on quadratics: L x^2 = 1 + 0.4 x - 0.1 x^2
    xi = x[1:-1]
    q = x**2
    assert np.allclose(lo_ * q[:-2] + di_ * xi**2 + up_ * q[2:], 1 + 0.4 * xi - 0.1 * xi**2, atol=1e-10)


def test_orders_of_the_schemes():
    e = {k: [price(n, th, ran) for n in (160, 320, 640)] for k, (th, ran) in
         {"implicit": (1.0, 0), "cn4": (0.5, 4)}.items()}
    ratio = {k: v[1] / v[2] for k, v in e.items()}
    assert 1.8 < ratio["implicit"] < 2.2 and 3.5 < ratio["cn4"] < 4.5
    assert price(320, 0.5, 4, grid="sinh") < price(320, 0.5, 4)
    dirichlet = ("dirichlet", lambda x, tau: math.exp(x) - K * math.exp(-R * tau))
    assert price(320, 0.5, 4, right=dirichlet) < 2e-3


def test_richardson_and_amplification():
    assert abs(richardson(1.0 + 4e-2, 1.0 + 1e-2, 2) - 1.0) < 1e-15
    xi = np.linspace(0, math.pi, 50)
    lam = 0.3
    # direct: the explicit step multiplies exp(i k x) by 1 + lam (e^{i xi} - 2 + e^{-i xi})
    assert np.allclose(amplification(0.0, lam, xi), 1 + lam * (2 * np.cos(xi) - 2))
    assert np.all(np.abs(amplification(0.5, 50.0, xi)) <= 1) and abs(amplification(0.5, 50.0, math.pi) + 99 / 101) < 1e-15
    assert amplification(0.0, 0.51, math.pi) < -1 < amplification(0.0, 0.49, math.pi)


def test_upwind_restores_m_matrix():
    x = uniform_grid(-1.0, 1.0, 50)
    lo, di, up = operator(x, 0.0002, 0.05, 0.05)
    assert lo.min() < 0                                              # central differences break the sign pattern
    lo, di, up = operator(x, 0.0002, 0.05, 0.05, upwind=True)
    assert lo.min() >= 0 and up.min() >= 0 and np.all(di < 0)


def test_douglas_adi_exchange_option():
    s1, s2, r1 = 0.3, 0.2, 0.5
    s = math.sqrt(s1**2 + s2**2 - 2 * r1 * s1 * s2)
    exact = 100 * ncdf(0.5 * s) - 100 * ncdf(-0.5 * s)
    errs = []
    for n in (40, 80):
        x = np.linspace(math.log(100) - 4 * s1, math.log(100) + 4 * s1, n + 1)
        y = np.linspace(math.log(100) - 4 * s2, math.log(100) + 4 * s2, n + 1)
        u = douglas_adi_2d(x, y, lambda a, b: np.maximum(np.exp(a) - np.exp(b), 0.0), 0.5 * s1**2, -0.5 * s1**2,
                           0.5 * s2**2, -0.5 * s2**2, r1 * s1 * s2, 0.0, 1.0, n // 2)
        errs.append(abs(u[n // 2, n // 2] - exact))
    assert errs[1] < 0.03 and 1.5 < errs[0] / errs[1] < 2.2
