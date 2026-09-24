"""Acceptance tests of firm.optim."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_optim import (
    Bounded,
    admm_nearest_correlation,
    gradient_descent,
    identifiability,
    lbfgs,
    levenberg_marquardt,
    multistart,
    newton,
    prox_l1,
    proximal_gradient,
    sgd,
    tikhonov,
)


def _rosen(x):
    return float(100 * (x[1] - x[0] ** 2) ** 2 + (1 - x[0]) ** 2)


def _rosen_grad(x):
    return np.array([-400 * x[0] * (x[1] - x[0] ** 2) - 2 * (1 - x[0]), 200 * (x[1] - x[0] ** 2)])


def test_gradient_rates_and_newton():
    H = np.diag([1.0, 50.0])
    it = gradient_descent(lambda x: H @ x, np.array([1.0, 1.0]), 1 / 50, 100)
    f = np.array([0.5 * x @ H @ x for x in it])
    assert f[100] <= (1 - 1 / 50) ** 200 * f[0] * 1.0001 and f[100] > 0       # linear rate (1 - 1/kappa)^(2k)
    nes = gradient_descent(lambda x: H @ x, np.array([1.0, 1.0]), 1 / 50, 100, nesterov=True)
    assert 0.5 * nes[100] @ H @ nes[100] < f[100]
    x, k = newton(_rosen_grad, lambda x: np.array([[1200 * x[0] ** 2 - 400 * x[1] + 2, -400 * x[0]],
                                                     [-400 * x[0], 200.0]]), np.array([1.2, 1.2]))
    assert np.allclose(x, [1, 1], atol=1e-10) and k < 10


def test_lbfgs_rosenbrock():
    r = lbfgs(_rosen, _rosen_grad, np.array([-1.2, 1.0]), tol=1e-9)
    assert r["status"] == "optimal" and np.allclose(r["x"], [1, 1], atol=1e-6)


def test_levenberg_marquardt_and_diagnostics():
    t = np.linspace(0, 5, 40)
    y = 2.0 * np.exp(-0.7 * t) + 0.5

    def res(p):
        return p[0] * np.exp(-p[1] * t) + p[2] - y
    out = levenberg_marquardt(res, np.array([1.0, 0.1, 0.0]))
    assert np.allclose(out["x"], [2.0, 0.7, 0.5], atol=1e-6)
    d = identifiability(out["jac"])
    assert d["cond"] > 1 and np.allclose(np.diag(d["corr"]), 1)
    pen = levenberg_marquardt(tikhonov(res, np.array([2.0, 1.0, 0.5]), [1e6, 1e6, 1e6]), np.array([1.0, 0.1, 0.0]))
    assert abs(pen["x"][1] - 1.0) < 0.01                                          # a heavy penalty pins the parameters


def test_proximal_and_admm():
    assert np.allclose(prox_l1(np.array([3.0, -0.5, 1.0]), 1.0), [2.0, 0.0, 0.0])
    rng = np.random.default_rng(1)
    X = rng.standard_normal((100, 10))
    y = X[:, 0] - 2 * X[:, 1] + 0.1 * rng.standard_normal(100)
    L = float(np.linalg.eigvalsh(X.T @ X / 100)[-1])
    b = proximal_gradient(lambda v: X.T @ (X @ v - y) / 100, lambda v, s: prox_l1(v, 0.05 * s), np.zeros(10), L, 2000)[-1]
    assert abs(b[0] - 0.95) < 0.05 and abs(b[1] + 1.95) < 0.05 and np.sum(np.abs(b[2:]) > 1e-8) <= 3
    C = np.array([[1.0, 0.9, 0.2], [0.9, 1.0, 0.9], [0.2, 0.9, 1.0]])
    Z, _ = admm_nearest_correlation(C)
    assert np.linalg.eigvalsh(Z).min() > -1e-8 and np.allclose(np.diag(Z), 1)


def test_sgd_bounds_and_multistart():
    rng = np.random.default_rng(2)
    X = rng.standard_normal((500, 2))
    y = X @ [1.0, -1.0]
    b = sgd(lambda v, i: X[i] * (X[i] @ v - y[i]), np.zeros(2), 500, 20_000, 1.0, 10.0, rng)
    assert np.allclose(b, [1, -1], atol=0.02)
    B = Bounded([0.0, 1.0], [1.0, np.inf])
    p = np.array([0.3, 5.0])
    assert np.allclose(B.from_free(B.to_free(p)), p)
    out = multistart(lambda s: {"cost": (s - 2.0) ** 2, "x": s}, [0.0, 3.0, 1.9])
    assert out[0]["x"] == 1.9
    _ = math
