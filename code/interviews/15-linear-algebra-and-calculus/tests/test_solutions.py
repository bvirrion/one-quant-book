"""Numbers gate: every numerical answer printed in Book 18, chapter 15 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import sympy as sp

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_linalg import (
    clip_eigenvalues,
    max_return_at_vol,
    min_variance_two,
    nearest_correlation,
    sym,
    third_correlation_range,
)

BAD = [[1, 0.9, 0.9], [0.9, 1, -0.9], [0.9, -0.9, 1]]


def test_q1_eigen():
    assert np.allclose(np.linalg.eigvalsh([[2, 1], [1, 2]]), [1, 3])


def test_q2_invalid():
    assert round(np.linalg.det(BAD), 3) == -2.888
    assert np.allclose(np.linalg.eigvalsh(BAD), [-0.8, 1.9, 1.9])


def test_q3_q4_symbolic():
    s = sym()
    assert sp.simplify(s["E_expZ"].rewrite(sp.erf) - sp.exp(sp.Rational(1, 2))) == 0
    assert s["E_Z4"] == 3 and s["sum_k_2k"] == 2
    assert round(math.exp(0.5), 4) == 1.6487
    assert sp.simplify(s["E_Zplus"] - 1 / sp.sqrt(2 * sp.pi)) == 0 and round(1 / math.sqrt(2 * math.pi), 4) == 0.3989


def test_q5_range():
    lo, hi = third_correlation_range(0.8, 0.6)
    assert round(lo, 6) == 0 and round(hi, 2) == 0.96


def test_q6_equicorrelation():
    rho = 0.3
    m = (1 - rho) * np.eye(10) + rho * np.ones((10, 10))
    w = np.sort(np.linalg.eigvalsh(m))
    assert np.allclose(w[:9], 1 - rho) and math.isclose(w[9], 1 + 9 * rho)
    m_min = (1 + 1 / 9) * np.eye(10) - (1 / 9) * np.ones((10, 10))
    assert abs(np.linalg.eigvalsh(m_min).min()) < 1e-12


def test_q7_hat_matrix():
    rng = np.random.default_rng(0)
    x = np.column_stack([np.ones(250), rng.standard_normal((250, 4))])
    h = x @ np.linalg.solve(x.T @ x, x.T)
    assert math.isclose(np.trace(h), 5, rel_tol=1e-9)
    assert np.allclose(h @ h, h) and math.isclose(np.trace(h) / 250, 0.02)


def test_q8_min_variance():
    w1, vol = min_variance_two(0.2, 0.1, 0.3)
    assert round(w1, 3) == 0.105 and round(vol, 4) == 0.0979


def test_q10_nearest():
    n = nearest_correlation(BAD)
    assert np.allclose(n, [[1, 0.5, 0.5], [0.5, 1, -0.5], [0.5, -0.5, 1]], atol=1e-6)
    assert np.linalg.eigvalsh(n).min() > -1e-9
    assert round(np.linalg.norm(n - np.array(BAD)), 3) == 0.980
    assert np.allclose(clip_eigenvalues(BAD), n, atol=1e-6)


def test_q11_rank_one():
    v = np.array([1.0, 2.0, 2.0])
    m = np.eye(3) + np.outer(v, v)
    assert np.allclose(np.sort(np.linalg.eigvalsh(m)), [1, 1, 10])
    assert np.allclose(np.linalg.inv(m), np.eye(3) - np.outer(v, v) / 10)


def test_q12_lagrange():
    w, ret = max_return_at_vol([0.05, 0.03], [0.2, 0.1], 0.1)
    assert np.allclose(np.round(w, 3), [0.32, 0.768]) and round(ret, 4) == 0.0391


def test_q13_taylor():
    actual = math.exp(0.1) - (1 + 0.1 + 0.005)
    bound = 0.1**3 / 6 * math.exp(0.1)
    assert round(actual, 6) == 0.000171 and round(bound, 6) == 0.000184 and actual < bound


def test_extra_numbers():
    lo, hi = third_correlation_range(0.9, 0.9)
    assert round(lo, 2) == 0.62 and round(hi, 2) == 1.0
    assert (0.05 / 0.2, 0.03 / 0.1) == (0.25, 0.3)
    assert round(math.sqrt(6 * 0.16), 2) == 0.98


def test_worked_answers():
    cov = np.array([[0.04, 0.9 * 0.2 * 0.25], [0.9 * 0.2 * 0.25, 0.0625]])
    w = np.array([1.0, -1.0])
    v = w @ cov @ w
    assert round(v, 4) == 0.0125 and round(100 * math.sqrt(v), 1) == 11.2
    assert round(100 * math.sqrt(0.1025)) == 32
    w2 = np.array([1.0, -0.8])
    assert round(w2 @ cov @ w2, 4) == 0.008 and round(100 * math.sqrt(0.008), 1) == 8.9
    z = sp.symbols("z")
    dens = sp.exp(-(z**2) / 2) / sp.sqrt(2 * sp.pi)
    val = sp.integrate(z * sp.sin(z) * dens, (z, -sp.oo, sp.oo))
    assert sp.simplify(val - sp.exp(-sp.Rational(1, 2))) == 0 and round(float(val), 3) == 0.607
    x = 0.5
    assert round(0.5 * math.exp(0.5) - 1, 4) == -0.1756 and round(math.exp(0.5), 4) == 1.6487
    x = x - (x * math.exp(x) - 1) / ((1 + x) * math.exp(x))
    assert round(x, 4) == 0.5710
    x = x - (x * math.exp(x) - 1) / ((1 + x) * math.exp(x))
    assert round(x, 5) == 0.56716
    x3 = x - (x * math.exp(x) - 1) / ((1 + x) * math.exp(x))
    assert abs(x3 - x) < 1e-4 and round(x3, 4) == 0.5671
