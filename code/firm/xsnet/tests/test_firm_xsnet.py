import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_xsnet import IPCA, CondAE, PCAModel, managed, with_constant


def _linear_panel(T=120, n=200, L=4, K=2, seed=0):
    rng = np.random.default_rng(seed)
    Z = with_constant(rng.uniform(-1, 1, (T, n, L)))
    G = rng.standard_normal((L + 1, K))
    f = 0.02 * rng.standard_normal((T, K)) + 0.005
    r = np.einsum("tnl,lk,tk->tn", Z, G, f) + 0.01 * rng.standard_normal((T, n))
    return Z, r, G


def test_ipca_recovers_a_linear_beta_model():
    Z, r, G = _linear_panel()
    m = IPCA(2, iters=40).fit(Z, r)
    # the fitted Gamma spans the true Gamma's column space
    P = m.G @ np.linalg.pinv(m.G)
    assert np.linalg.norm(G - P @ G) / np.linalg.norm(G) < 0.05
    tot, _ = m.score(Z, r)
    assert tot > 0.6


def test_pca_static_loadings():
    rng = np.random.default_rng(1)
    B = rng.standard_normal((50, 2))
    f = rng.standard_normal((400, 2))
    r = f @ B.T + 0.05 * rng.standard_normal((400, 50))
    m = PCAModel(2).fit(r)
    assert m.score(r)[0] > 0.99


def test_managed_portfolios_are_permutation_invariant():
    Z, r, _ = _linear_panel(T=5)
    p = np.random.default_rng(2).permutation(Z.shape[1])
    assert np.allclose(managed(Z, r), managed(Z[:, p], r[:, p]))


def test_conditional_autoencoder_fits_a_nonlinear_beta():
    rng = np.random.default_rng(3)
    T, n = 100, 150
    Z = with_constant(rng.uniform(-1, 1, (T, n, 3)))
    beta = 1.0 + Z[:, :, 1] ** 2 - Z[:, :, 2]
    f = 0.03 * rng.standard_normal(T)
    r = beta * f[:, None] + 0.005 * rng.standard_normal((T, n))
    m = CondAE(4, K=1, hidden=(16,), seed=1, epochs=150).fit(Z[:80], r[:80], Z[80:90], r[80:90])
    tot, _ = m.score(Z[90:], r[90:])
    assert tot > 0.8
