"""Acceptance tests of firm.portopt."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_portopt import PortfolioProblem, admm, farkas, nearest_correlation, qp


def test_qp_small_and_kkt():
    r = qp(2 * np.eye(2), np.array([-2.0, -4.0]), G=np.array([[1.0, 1.0], [-1.0, 0.0]]), h=np.array([1.0, 0.0]))
    assert r["status"] == "optimal" and np.allclose(r["x"], [0, 1], atol=1e-6) and abs(r["z"][0] - 2) < 1e-5
    assert r["kkt"]["stationarity"] < 1e-8 and r["kkt"]["complementarity"] < 1e-8


def test_min_variance_closed_form():
    rng = np.random.default_rng(1)
    B = rng.standard_normal((30, 30))
    S = B @ B.T / 30 + 0.1 * np.eye(30)
    r = qp(S, np.zeros(30), np.ones((1, 30)), np.ones(1))
    w = np.linalg.solve(S, np.ones(30))
    assert np.allclose(r["x"], w / w.sum(), atol=1e-8)
    assert abs(r["y"][0] + 1 / w.sum()) < 1e-8                        # multiplier = minus the minimum variance


def test_farkas():
    A, b = np.zeros((0, 2)), np.zeros(0)
    assert farkas(A, b, np.array([[1.0, 0.0], [-1.0, 0.0]]), np.array([1.0, 0.0])) is None
    G, h = np.array([[1.0, 0.0], [-1.0, 0.0]]), np.array([-1.0, 0.0])      # x <= -1 and x >= 0
    lam, nu, t = farkas(A, b, G, h)
    assert np.all(lam >= -1e-9) and np.linalg.norm(G.T @ lam) < 1e-8 and h @ lam < 0 and abs(t - 0.5) < 1e-6


def test_admm_second_order_cone():
    C = np.vstack([np.eye(3), np.eye(3)])
    lo = np.array([1.0, -np.inf, -np.inf, -np.inf, -np.inf, -np.inf])
    up = np.array([1.0, np.inf, np.inf, np.inf, np.inf, np.inf])
    r = admm(np.zeros((3, 3)), np.array([0.0, -1.0, -1.0]), C, lo, up, cones=[np.array([3, 4, 5])])
    assert r["status"] == "optimal" and np.allclose(r["x"][1:], [1 / math.sqrt(2)] * 2, atol=1e-5)


def test_portfolio_constraints_and_shadow_price():
    rng = np.random.default_rng(2)
    n = 30
    B = rng.standard_normal((n, 3)) * 0.1
    S = B @ B.T + np.diag(rng.uniform(0.01, 0.04, n))
    alpha = 0.05 * rng.standard_normal(n)
    sector = np.arange(n) // 10

    def solve(limit):
        p = PortfolioProblem(alpha, S, 5.0, w0=np.zeros(n))
        p.add_budget(0.0)
        for k in range(3):
            p.add_neutral((sector == k).astype(float), f"s{k}")
        p.add_box(0.1)
        p.add_gross(1.0)
        p.add_turnover(limit)
        return p.solve()
    r = solve(0.5)
    w = r["w"]
    assert abs(w.sum()) < 1e-7 and all(abs(w[sector == k].sum()) < 1e-7 for k in range(3))
    assert np.abs(w).max() <= 0.1 + 1e-7 and r["turnover"] <= 0.5 + 1e-7
    slope = (solve(0.51)["objective"] - solve(0.49)["objective"]) / 0.02
    assert abs(slope - r["duals"]["turnover"]) < 0.05 * abs(slope) + 1e-6


def test_nearest_correlation():
    C = np.array([[1.0, 0.9, 0.2], [0.9, 1.0, 0.9], [0.2, 0.9, 1.0]])
    assert np.linalg.eigvalsh(C).min() < 0
    Y, _ = nearest_correlation(C)
    assert np.linalg.eigvalsh(Y).min() > -1e-8 and np.allclose(np.diag(Y), 1)
    Z, _ = nearest_correlation(np.array([[1.0, 0.3], [0.3, 1.0]]))
    assert np.allclose(Z, [[1.0, 0.3], [0.3, 1.0]])
