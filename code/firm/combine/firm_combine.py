"""firm.combine -- blending many signals into one (build of One Quant Book 7, chapter 14).

Signals are panels (T dates x N names), stacked into X (T, N, K); the target is y (T, N). Every signal is z-scored
across names on each date before blending. Blenders: equal weights, IC weights, the maximum-ICIR rule on the IC
history with a shrunk covariance, ridge and lasso regressions pooled over the panel, and stacking of other blenders'
out-of-fold forecasts under non-negativity. Orthogonalisers work on one date's cross-section: sequential
(Gram-Schmidt in a chosen order), symmetric (Lowdin, X S^{-1/2}), and residualisation on a book's exposures. NumPy only.

API (stable):
    zscore(X)                               cross-sectional z-scores, NaN-safe, per date (and per signal)
    ic_series(F, y)                         (T,) rank IC of a composite F (T, N) with y each date
    ic_matrix(X, y)                         (T, K) rank IC of each signal each date
    equal(X)                                composite of the z-scored signals, equal weights
    blend(X, w)                             composite with weights w (K,)
    ic_weights(ic)                          weights proportional to the positive part of the mean ICs
    max_icir(ic, shrink)                    weights prop. to ((1 - shrink) S + shrink diag S)^{-1} mean IC
    toward_equal(w, lam)                    (1 - lam) w + lam / K, both scaled to unit absolute sum
    ridge(X, y, alpha)                      pooled ridge coefficients on z-scored signals and target
    lasso(X, y, alpha, iters)               pooled lasso coefficients (coordinate descent)
    nnls(A, b)                              non-negative least squares (Lawson and Hanson active set)
    stack(preds, y, folds)                  non-negative weights on base forecasts, fitted on held-out dates
    time_folds(T, k)                        k expanding-window (train, test) index pairs in time order
    orth_sequential(X)                      Gram-Schmidt of the columns of X (N, K), in order
    orth_symmetric(X)                       X S^{-1/2}: orthonormal columns closest to the originals
    residualise_on(X, B)                    X minus its least-squares projection on the columns of B
"""
from __future__ import annotations

import numpy as np


def zscore(X) -> np.ndarray:
    X = np.asarray(X, float)
    m = np.nanmean(X, axis=1, keepdims=True)
    s = np.nanstd(X, axis=1, keepdims=True)
    return np.where(s > 0, (X - m) / np.where(s > 0, s, 1.0), 0.0)


def _rank(a: np.ndarray) -> np.ndarray:
    return np.argsort(np.argsort(a, axis=-1), axis=-1).astype(float)


def ic_series(F, y) -> np.ndarray:
    rf, ry = _rank(np.asarray(F, float)), _rank(np.asarray(y, float))
    rf -= rf.mean(axis=1, keepdims=True)
    ry -= ry.mean(axis=1, keepdims=True)
    return (rf * ry).sum(axis=1) / np.sqrt((rf * rf).sum(axis=1) * (ry * ry).sum(axis=1))


def ic_matrix(X, y) -> np.ndarray:
    X = np.asarray(X, float)
    return np.column_stack([ic_series(X[:, :, k], y) for k in range(X.shape[2])])


def blend(X, w) -> np.ndarray:
    return zscore(X) @ np.asarray(w, float)


def equal(X) -> np.ndarray:
    return blend(X, np.full(np.asarray(X).shape[2], 1.0 / np.asarray(X).shape[2]))


def ic_weights(ic) -> np.ndarray:
    m = np.maximum(np.asarray(ic, float).mean(axis=0), 0.0)
    return m / m.sum() if m.sum() > 0 else np.full(len(m), 1.0 / len(m))


def max_icir(ic, shrink: float = 0.0) -> np.ndarray:
    """The weights that maximise the mean over the standard deviation of the blended IC, with the IC covariance
    shrunk toward its diagonal (shrink = 1: each signal weighted by its own mean IC over its IC variance)."""
    ic = np.asarray(ic, float)
    S = np.cov(ic, rowvar=False)
    S = (1.0 - shrink) * S + shrink * np.diag(np.diag(S))
    w = np.linalg.solve(S, ic.mean(axis=0))
    return w / np.abs(w).sum()


def toward_equal(w, lam: float) -> np.ndarray:
    w = np.asarray(w, float)
    w = w / np.abs(w).sum()
    return (1.0 - lam) * w + lam / len(w)


def _pooled(X, y):
    Z = zscore(X).reshape(-1, np.asarray(X).shape[2])
    t = zscore(np.asarray(y, float)[:, :, None])[:, :, 0].ravel()
    return Z, t


def ridge(X, y, alpha: float) -> np.ndarray:
    Z, t = _pooled(X, y)
    n = len(t)
    return np.linalg.solve(Z.T @ Z / n + alpha * np.eye(Z.shape[1]), Z.T @ t / n)


def lasso(X, y, alpha: float, iters: int = 200) -> np.ndarray:
    Z, t = _pooled(X, y)
    n = len(t)
    G, c = Z.T @ Z / n, Z.T @ t / n
    b = np.zeros(len(c))
    for _ in range(iters):
        for j in range(len(b)):
            rho = c[j] - G[j] @ b + G[j, j] * b[j]
            b[j] = np.sign(rho) * max(abs(rho) - alpha, 0.0) / G[j, j]
    return b


def nnls(A, b, tol: float = 1e-10, max_iter: int = 500) -> np.ndarray:
    A, b = np.asarray(A, float), np.asarray(b, float)
    n = A.shape[1]
    x, P = np.zeros(n), np.zeros(n, bool)
    for _ in range(max_iter):
        w = A.T @ (b - A @ x)
        if P.all() or w[~P].max() <= tol:
            break
        P[np.argmax(np.where(P, -np.inf, w))] = True
        while True:
            z = np.zeros(n)
            z[P] = np.linalg.lstsq(A[:, P], b, rcond=None)[0]
            if (z[P] > tol).all():
                x = z
                break
            neg = P & (z <= tol)
            a = np.min(x[neg] / (x[neg] - z[neg]))
            x = x + a * (z - x)
            P &= x > tol
    return x


def time_folds(T: int, k: int, min_train: int | None = None) -> list[tuple[np.ndarray, np.ndarray]]:
    min_train = min_train or T // (k + 1)
    edges = np.linspace(min_train, T, k + 1).astype(int)
    return [(np.arange(0, a), np.arange(a, b)) for a, b in zip(edges[:-1], edges[1:], strict=True)]


def stack(preds, y, folds) -> np.ndarray:
    """preds: list of functions train_idx -> composite on all dates (T, N). The stacking weights are the non-negative
    least squares of the z-scored target on each base's z-scored forecasts over the held-out dates of each fold."""
    A, b = [], []
    for tr, te in folds:
        F = np.stack([zscore(p(tr))[te] for p in preds], axis=-1)
        A.append(F.reshape(-1, len(preds)))
        b.append(zscore(np.asarray(y, float)[te][:, :, None])[:, :, 0].ravel())
    w = nnls(np.vstack(A), np.concatenate(b))
    return w / w.sum() if w.sum() > 0 else np.full(len(preds), 1.0 / len(preds))


def orth_sequential(X) -> np.ndarray:
    X = np.asarray(X, float) - np.asarray(X, float).mean(axis=0)
    Q = np.empty_like(X)
    for k in range(X.shape[1]):
        v = X[:, k] - Q[:, :k] @ (Q[:, :k].T @ X[:, k])
        Q[:, k] = v / np.linalg.norm(v)
    return Q * np.sqrt(len(X))


def orth_symmetric(X) -> np.ndarray:
    X = np.asarray(X, float) - np.asarray(X, float).mean(axis=0)
    S = X.T @ X / len(X)
    val, vec = np.linalg.eigh(S)
    return X @ (vec @ np.diag(val ** -0.5) @ vec.T)


def residualise_on(X, B) -> np.ndarray:
    X, B = np.asarray(X, float), np.asarray(B, float)
    A = np.column_stack([np.ones(len(B)), B])
    return X - A @ np.linalg.lstsq(A, X, rcond=None)[0]
