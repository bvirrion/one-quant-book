"""firm.mgtest -- martingale diagnostics for forecast series (One Quant Book 4, chapter 1).

A forecast of a fixed future quantity, revised as information arrives, is a Doob martingale when it
is an honest conditional expectation: its revisions have mean zero and cannot be predicted from
past revisions. The functions below test that on a panel of forecast paths, one row per day (or
deal), one column per revision time.

API (stable):
    revisions(paths)                        -> array of revisions, shape (n, k-1)
    revision_regression(paths, lag=1, col=None) -> dict(slope, se, t, n): pooled OLS of a revision on
                                               the revision `lag` steps earlier (or at column `col`)
    variance_ratio(increments, q)           -> Lo-MacKinlay variance ratio of q-step sums
    variance_shares(paths)                  -> share of the total revision variance at each step
    martingale_report(paths)                -> dict with the three diagnostics above
"""
from __future__ import annotations

import numpy as np


def revisions(paths: np.ndarray) -> np.ndarray:
    """Revisions M_k - M_{k-1} of each forecast path (rows are paths, columns revision times)."""
    p = np.asarray(paths, dtype=float)
    if p.ndim != 2 or p.shape[1] < 2:
        raise ValueError("paths must be a 2-D array with at least two columns")
    return np.diff(p, axis=1)


def revision_regression(paths: np.ndarray, lag: int = 1, col: int | None = None) -> dict:
    """Pooled regression (no intercept) of each revision on the revision `lag` steps before it.

    With `col` given, regress only the revision at column `col` (of the revision array) on the one
    `lag` steps before it. For a martingale the slope is zero; the t-statistic uses the iid
    standard error of a no-intercept regression."""
    d = revisions(paths)
    if col is None:
        y = d[:, lag:].ravel()
        x = d[:, :-lag].ravel()
    else:
        y = d[:, col]
        x = d[:, col - lag]
    sxx = float(x @ x)
    slope = float(x @ y) / sxx
    resid = y - slope * x
    n = y.size
    se = float(np.sqrt(resid @ resid / (n - 1) / sxx))
    return {"slope": slope, "se": se, "t": slope / se, "n": n}


def variance_ratio(increments: np.ndarray, q: int) -> float:
    """Lo-MacKinlay variance ratio Var(sum of q increments) / (q Var(one increment)).

    Uses overlapping q-sums and the sample mean; equals one in expectation for iid increments."""
    x = np.asarray(increments, dtype=float).ravel()
    mu = x.mean()
    v1 = np.mean((x - mu) ** 2)
    c = np.concatenate([[0.0], np.cumsum(x - mu)])
    sq = c[q:] - c[:-q]
    return float(np.mean(sq**2) / (q * v1))


def variance_shares(paths: np.ndarray) -> np.ndarray:
    """Share of the summed variance of revisions that falls at each revision step.

    For a martingale the revisions are orthogonal, so the shares sum to one and each is the part of
    the final value's variance resolved at that step."""
    d = revisions(paths)
    v = d.var(axis=0)
    return v / v.sum()


def martingale_report(paths: np.ndarray) -> dict:
    d = revisions(paths)
    return {
        "mean_revision": float(d.mean()),
        "regression": revision_regression(paths),
        "shares": variance_shares(paths),
    }
