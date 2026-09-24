"""Acceptance tests of firm.covest."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_covest import (
    clip,
    lw_constant_corr,
    lw_identity,
    min_var_weights,
    mp_density,
    mp_edges,
    nonlinear_shrinkage,
    pca_factor,
    portfolio_risk,
    sample_cov,
)


def _frob(A, B):
    return float(np.sum((A - B) ** 2))


def test_marchenko_pastur():
    q = 0.4
    lo, hi = mp_edges(q)
    x = np.linspace(lo, hi, 20001)
    assert abs(np.trapezoid(mp_density(x, q), x) - 1) < 1e-3
    lam = np.linalg.eigvalsh(sample_cov(np.random.default_rng(1).standard_normal((2500, 1000))))
    assert lam.min() > lo - 0.05 and lam.max() < hi + 0.05


def test_ledoit_wolf_identity():
    rng = np.random.default_rng(2)
    X = rng.standard_normal((60, 20)) * np.linspace(0.8, 1.2, 20)
    Y = X - X.mean(0)
    S = Y.T @ Y / 60
    brute = sum(np.sum((np.outer(y, y) - S) ** 2) for y in Y) / 3600 / 20
    m = np.trace(S) / 20
    d2 = np.sum((S - m * np.eye(20)) ** 2) / 20
    Sig, a = lw_identity(X)
    assert abs(a - min(brute, d2) / d2) < 1e-10 and 0 < a < 1
    true = np.diag(np.linspace(0.8, 1.2, 20) ** 2)
    assert _frob(Sig, true) < _frob(S, true)


def test_constant_correlation_target():
    rng = np.random.default_rng(3)
    N, rho = 50, 0.3
    C = np.full((N, N), rho) + (1 - rho) * np.eye(N)
    X = rng.standard_normal((100, N)) @ np.linalg.cholesky(C).T
    Sig, a = lw_constant_corr(X)
    assert 0 < a <= 1 and _frob(Sig, C) < _frob(sample_cov(X), C)


def test_nonlinear_shrinkage_tracks_the_oracle():
    rng = np.random.default_rng(4)
    N, T = 200, 500
    Sigma = np.diag(np.linspace(0.5, 2, N))
    X = rng.standard_normal((T, N)) * np.sqrt(np.diag(Sigma))
    Y = X - X.mean(0)
    lam, U = np.linalg.eigh(Y.T @ Y / (T - 1))
    oracle = np.einsum("ij,jk,ki->i", U.T, Sigma, U)
    d = np.einsum("ij,jk,ki->i", U.T, nonlinear_shrinkage(X), U)
    assert np.mean((d - oracle) ** 2) < 0.02 * np.mean((lam - oracle) ** 2)


def test_clip_factor_and_min_var():
    rng = np.random.default_rng(5)
    X = rng.standard_normal((300, 60)) @ np.diag(np.linspace(1, 2, 60))
    S = sample_cov(X)
    assert np.allclose(np.diag(clip(X)), np.diag(S)) and np.allclose(np.diag(pca_factor(X, 3)), np.diag(S))
    D = np.diag([1.0, 4.0])
    w = min_var_weights(D)
    assert np.allclose(w, [0.8, 0.2]) and abs(portfolio_risk(w, D) - math.sqrt(0.64 + 0.04 * 4)) < 1e-12
