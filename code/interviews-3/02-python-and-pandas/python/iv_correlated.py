import numpy as np


def correlated_normals(corr, n, rng):
    lower = np.linalg.cholesky(corr)               # corr = lower @ lower.T
    z = rng.standard_normal((n, len(corr)))        # one row per draw
    return z @ lower.T


def nearest_correlation(corr):
    """Clip negative eigenvalues and rescale: valid, close, not the true nearest."""
    w, v = np.linalg.eigh(corr)
    fixed = v @ np.diag(np.clip(w, 1e-8, None)) @ v.T
    d = np.sqrt(np.diag(fixed))
    return fixed / np.outer(d, d)
