"""firm.leadlag -- lead-lag and cross-sectional features (build of One Quant Book 7, chapter 10).

A lead-lag estimator for asynchronous tick data (the Hayashi-Yoshida cross-covariance with one series shifted, over a
grid of lags, its argmax and the lead-lag ratio), lagged cross-correlations of sampled returns in both directions, a
peer-relative return (leave-one-out peer mean), a feature that maps linked names' past returns onto each name, and
the mining of a lagged cross-correlation matrix for candidate pairs. The Hayashi-Yoshida sum is Book 4's
firm.hfvol. NumPy only.

API (stable):
    hy_ccf(t1, x1, t2, x2, lags, norm_step)      Hayashi-Yoshida correlation of x1 with x2 lagged by each lag
    lead_estimate(lags, ccf)                      the lag of the largest cross-correlation (> 0: series 1 leads)
    lead_symmetric(lags, ccf, half)               the lag about which the ccf is most symmetric over +/- half lags
    lead_lag_ratio(lags, ccf)                     sum of squared ccf at positive lags / at negative lags
    directional_corr(t1, x1, t2, x2, step)        (corr of 2's return with 1's previous, and the reverse) on a grid
    peer_relative(ret, group)                     each return minus the mean of the others in its group, per row
    linked_feature(values, link)                  values of each name's linked name (NaN where there is no link)
    lagged_corr_matrix(R, lag)                    C[i, j] = corr(R[t, i], R[t - lag, j]), columns standardised
    top_pairs(C, k)                               the k largest off-diagonal entries as (i, j) pairs
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "hfvol"))
from firm_hfvol import hayashi_yoshida, previous_tick  # noqa: E402


def _rv_grid(t, x, step: float) -> float:
    """Realised variance on a previous-tick grid of `step` seconds (robust to the tick-level noise)."""
    g = np.arange(t[0], t[-1] + 1e-9, step)
    return float(np.sum(np.diff(previous_tick(t, x, g)) ** 2))


def hy_ccf(t1, x1, t2, x2, lags, norm_step: float = 60.0) -> np.ndarray:
    """Cross-correlation at each lag: series 2's clock is moved back by the lag, so a peak at lag > 0 means series 2
    follows series 1 by that lag. Normalised by realised variances on a `norm_step` grid."""
    t1, x1, t2, x2 = (np.asarray(a, float) for a in (t1, x1, t2, x2))
    norm = np.sqrt(_rv_grid(t1, x1, norm_step) * _rv_grid(t2, x2, norm_step))
    return np.array([hayashi_yoshida(t1, x1, t2 - lag, x2) for lag in lags]) / norm


def lead_estimate(lags, ccf) -> float:
    return float(np.asarray(lags)[int(np.argmax(np.abs(ccf)))])


def lead_symmetric(lags, ccf, half: int = 20) -> float:
    """When both series react to a common price with the same spread of delays, the ccf is symmetric about the lead
    and flat near its top, so its argmax is noisy: take the centre that minimises the squared difference between the
    ccf `half` lags to the right and to the left."""
    c = np.asarray(ccf, float)
    cand = [i for i in range(half, len(c) - half) if c[i] >= 0.5 * c.max()]       # centres near the top only
    cost = [np.sum((c[i + 1:i + half + 1] - c[i - half:i][::-1]) ** 2) for i in cand]
    return float(np.asarray(lags)[cand[int(np.argmin(cost))]])


def lead_lag_ratio(lags, ccf) -> float:
    lags, c2 = np.asarray(lags), np.asarray(ccf) ** 2
    return float(c2[lags > 0].sum() / c2[lags < 0].sum())


def directional_corr(t1, x1, t2, x2, step: float) -> tuple[float, float]:
    """On a grid of `step` seconds: corr(r2[k], r1[k-1]) (1 leads 2) and corr(r1[k], r2[k-1]) (2 leads 1)."""
    g = np.arange(max(t1[0], t2[0]), min(t1[-1], t2[-1]) + 1e-9, step)
    r1, r2 = np.diff(previous_tick(t1, x1, g)), np.diff(previous_tick(t2, x2, g))
    return float(np.corrcoef(r2[1:], r1[:-1])[0, 1]), float(np.corrcoef(r1[1:], r2[:-1])[0, 1])


def peer_relative(ret, group) -> np.ndarray:
    """ret (T, N) with NaN for missing; group (N,) labels. Each entry minus the mean of the other names of its group
    on that row (leave-one-out: a name is not its own peer); NaN when it has no peer that day."""
    ret, group = np.asarray(ret, float), np.asarray(group)
    out = np.full(ret.shape, np.nan)
    for g in np.unique(group):
        cols = group == g
        x = ret[:, cols]
        ok = ~np.isnan(x)
        s, n = np.where(ok, x, 0.0).sum(axis=1, keepdims=True), ok.sum(axis=1, keepdims=True)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[:, cols] = np.where(ok & (n > 1), x - (s - np.where(ok, x, 0.0)) / (n - 1), np.nan)
    return out


def linked_feature(values, link) -> np.ndarray:
    """values (..., N); link (N,) index of each name's linked name or -1. Returns values[..., link] with NaN for -1."""
    values, link = np.asarray(values, float), np.asarray(link)
    out = values[..., np.maximum(link, 0)]
    return np.where(link >= 0, out, np.nan)


def lagged_corr_matrix(R, lag: int = 1) -> np.ndarray:
    R = np.asarray(R, float)
    Z = (R - R.mean(axis=0)) / R.std(axis=0)
    C = Z[lag:].T @ Z[:-lag] / (len(R) - lag)
    np.fill_diagonal(C, np.nan)
    return C


def top_pairs(C, k: int) -> list[tuple[int, int]]:
    v = np.where(np.isnan(C), -np.inf, C).ravel()
    idx = np.argpartition(-v, k)[:k]
    idx = idx[np.argsort(-v[idx])]
    return [(int(i // C.shape[1]), int(i % C.shape[1])) for i in idx]
