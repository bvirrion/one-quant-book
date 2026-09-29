"""Book 18, chapter 15: linear algebra and calculus answers (sympy for exact results, numpy for checks)."""
from math import sqrt

import numpy as np
import sympy as sp


def third_correlation_range(r12: float, r13: float):
    """Values of r23 that keep the 3x3 correlation matrix positive semidefinite."""
    half = sqrt((1 - r12 * r12) * (1 - r13 * r13))
    return r12 * r13 - half, r12 * r13 + half


def nearest_correlation(a, iters: int = 2000, tol: float = 1e-12):
    """Higham (2002) alternating projections with Dykstra's correction, Frobenius norm."""
    y = np.array(a, dtype=float)
    ds = np.zeros_like(y)
    for _ in range(iters):
        r = y - ds
        w, v = np.linalg.eigh((r + r.T) / 2)
        x = v @ np.diag(np.maximum(w, 0)) @ v.T
        ds = x - r
        y_new = x.copy()
        np.fill_diagonal(y_new, 1.0)
        if np.linalg.norm(y_new - y) < tol:
            y = y_new
            break
        y = y_new
    return y


def clip_eigenvalues(a, floor: float = 0.0):
    w, v = np.linalg.eigh(np.array(a, dtype=float))
    x = v @ np.diag(np.maximum(w, floor)) @ v.T
    d = np.sqrt(np.diag(x))
    return x / np.outer(d, d)


def min_variance_two(s1, s2, rho):
    c = rho * s1 * s2
    w1 = (s2 * s2 - c) / (s1 * s1 + s2 * s2 - 2 * c)
    var = w1 * w1 * s1 * s1 + (1 - w1) ** 2 * s2 * s2 + 2 * w1 * (1 - w1) * c
    return w1, sqrt(var)


def max_return_at_vol(mu, sigma_diag, target_vol):
    w = np.array(mu) / np.array(sigma_diag) ** 2
    vol = sqrt(float(np.sum(w**2 * np.array(sigma_diag) ** 2)))
    w = w * target_vol / vol
    return w, float(np.dot(w, mu))


def sym():
    x, k = sp.symbols("x k", real=True)
    z = sp.Symbol("z", real=True)
    phi = sp.exp(-z * z / 2) / sp.sqrt(2 * sp.pi)
    return {
        "E_expZ": sp.integrate(sp.exp(z) * phi, (z, -sp.oo, sp.oo)),
        "E_Z4": sp.integrate(z**4 * phi, (z, -sp.oo, sp.oo)),
        "E_Zplus": sp.integrate(z * phi, (z, 0, sp.oo)),
        "sum_k_2k": sp.summation(k / 2**k, (k, 1, sp.oo)),
    }
