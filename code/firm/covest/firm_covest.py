"""firm.covest -- covariance estimation in high dimension (One Quant Book 4, chapter 22).

Sample covariance, Ledoit-Wolf linear shrinkage toward the identity and toward constant correlation, analytical
nonlinear shrinkage (Ledoit-Wolf 2020), Marchenko-Pastur eigenvalue clipping, a PCA factor model with a diagonal
remainder, the Marchenko-Pastur density, and the risk of minimum-variance portfolios. Returns are T x N (rows are
dates). NumPy only.

API (stable):
    sample_cov(X)                          demeaned, divisor T
    mp_edges(q, sigma2=1), mp_density(x, q, sigma2=1)
    lw_identity(X)                         (Sigma, intensity)
    lw_constant_corr(X)                    (Sigma, intensity)
    nonlinear_shrinkage(X)                 analytical nonlinear shrinkage
    clip(X, sigma2=None)                   eigenvalues inside the Marchenko-Pastur bulk replaced by their mean
    pca_factor(X, k)                       k principal factors plus a diagonal specific variance
    min_var_weights(Sigma)                 w = Sigma^-1 1 / 1' Sigma^-1 1
    portfolio_risk(w, Sigma)               sqrt(w' Sigma w)
"""
from __future__ import annotations

import math

import numpy as np


def _demean(X):
    X = np.asarray(X, dtype=float)
    return X - X.mean(axis=0)


def sample_cov(X) -> np.ndarray:
    Y = _demean(X)
    return Y.T @ Y / Y.shape[0]


def mp_edges(q: float, sigma2: float = 1.0) -> tuple[float, float]:
    return sigma2 * (1 - math.sqrt(q)) ** 2, sigma2 * (1 + math.sqrt(q)) ** 2


def mp_density(x, q: float, sigma2: float = 1.0) -> np.ndarray:
    """Marchenko-Pastur density of sample eigenvalues for q = N / T < 1 and population variance sigma2."""
    x = np.asarray(x, dtype=float)
    lo, hi = mp_edges(q, sigma2)
    inside = (x > lo) & (x < hi)
    out = np.zeros_like(x)
    out[inside] = np.sqrt((hi - x[inside]) * (x[inside] - lo)) / (2 * math.pi * q * sigma2 * x[inside])
    return out


def lw_identity(X) -> tuple[np.ndarray, float]:
    """Ledoit-Wolf (2004) optimal convex combination of the sample covariance and m I, m = tr(S) / N."""
    Y = _demean(X)
    T, N = Y.shape
    S = Y.T @ Y / T
    m = np.trace(S) / N
    d2 = np.sum((S - m * np.eye(N)) ** 2) / N
    b2_bar = (float(np.sum(np.sum(Y * Y, axis=1) ** 2)) - T * float(np.sum(S * S))) / (T * T) / N  # sum ||yy' - S||^2
    b2 = min(b2_bar, d2)
    a = b2 / d2
    return a * m * np.eye(N) + (1 - a) * S, float(a)


def lw_constant_corr(X) -> tuple[np.ndarray, float]:
    """Ledoit-Wolf shrinkage toward the constant-correlation matrix, with intensity (pi - rho) / gamma / T."""
    Y = _demean(X)
    T, N = Y.shape
    S = Y.T @ Y / T
    sd = np.sqrt(np.diag(S))
    R = S / np.outer(sd, sd)
    rbar = (np.sum(R) - N) / (N * (N - 1))
    F = rbar * np.outer(sd, sd)
    np.fill_diagonal(F, np.diag(S))
    Y2 = Y * Y
    pi_mat = (Y2.T @ Y2) / T - S * S
    pi_hat = float(np.sum(pi_mat))
    theta = ((Y**3).T @ Y) / T - np.diag(S)[:, None] * S                   # vartheta_{ii,ij}, row i column j
    ratio = sd[None, :] / sd[:, None]                                        # sqrt(s_jj / s_ii)
    off = rbar / 2 * (ratio * theta + ratio.T * theta.T)
    np.fill_diagonal(off, 0.0)
    rho_hat = float(np.sum(np.diag(pi_mat)) + np.sum(off))
    gamma_hat = float(np.sum((F - S) ** 2))
    a = max(0.0, min(1.0, (pi_hat - rho_hat) / gamma_hat / T))
    return a * F + (1 - a) * S, float(a)


def nonlinear_shrinkage(X) -> np.ndarray:
    """Analytical nonlinear shrinkage (Ledoit and Wolf, 2020) for N <= T - 1: keep the sample eigenvectors, replace
    each eigenvalue lambda by lambda / ((pi c lambda f)^2 + (1 - c - pi c lambda Hf)^2), with f an Epanechnikov
    kernel estimate of the eigenvalue density, Hf its Hilbert transform and c = N / (T - 1)."""
    Y = _demean(X)
    T, N = Y.shape
    n = T - 1
    S = Y.T @ Y / n
    lam, U = np.linalg.eigh(S)
    lam = np.maximum(lam, 1e-300)
    c = N / n
    h = n ** (-1 / 3)
    L = np.tile(lam[:, None], (1, N))
    H = h * L.T
    x = (L - L.T) / H
    ftilde = (3 / 4 / math.sqrt(5)) * np.mean(np.maximum(1 - x**2 / 5, 0) / H, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        hf = (-3 / 10 / math.pi) * x + (3 / 4 / math.sqrt(5) / math.pi) * (1 - x**2 / 5) * np.log(
            np.abs((math.sqrt(5) - x) / (math.sqrt(5) + x)))
    edge = np.isclose(np.abs(x), math.sqrt(5))
    hf[edge] = (-3 / 10 / math.pi) * x[edge]
    Hftilde = np.mean(hf / H, axis=1)
    d = lam / ((math.pi * c * lam * ftilde) ** 2 + (1 - c - math.pi * c * lam * Hftilde) ** 2)
    return (U * d) @ U.T


def clip(X, sigma2: float | None = None) -> np.ndarray:
    """On the correlation matrix: eigenvalues below the Marchenko-Pastur upper edge are replaced by their average
    (the trace is kept); then rescaled back to covariances. sigma2 defaults to the share of variance not explained by
    the eigenvalues above the edge."""
    Y = _demean(X)
    T, N = Y.shape
    S = Y.T @ Y / T
    sd = np.sqrt(np.diag(S))
    C = S / np.outer(sd, sd)
    lam, U = np.linalg.eigh(C)
    q = N / T
    if sigma2 is None:
        sigma2 = 1.0
        for _ in range(20):
            big = lam > mp_edges(q, sigma2)[1]
            sigma2 = 1 - lam[big].sum() / N
    noise = lam <= mp_edges(q, sigma2)[1]
    lam2 = lam.copy()
    lam2[noise] = lam[noise].mean()
    C2 = (U * lam2) @ U.T
    d = np.sqrt(np.diag(C2))
    C2 = C2 / np.outer(d, d)
    return C2 * np.outer(sd, sd)


def pca_factor(X, k: int) -> np.ndarray:
    S = sample_cov(X)
    lam, U = np.linalg.eigh(S)
    B = U[:, -k:] * np.sqrt(lam[-k:])
    common = B @ B.T
    return common + np.diag(np.maximum(np.diag(S) - np.diag(common), 1e-12))


def min_var_weights(Sigma) -> np.ndarray:
    x = np.linalg.solve(np.asarray(Sigma, dtype=float), np.ones(len(Sigma)))
    return x / x.sum()


def portfolio_risk(w, Sigma) -> float:
    w = np.asarray(w, dtype=float)
    return math.sqrt(float(w @ np.asarray(Sigma) @ w))
