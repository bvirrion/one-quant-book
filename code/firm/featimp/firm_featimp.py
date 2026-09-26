"""firm.featimp -- feature transforms, selection and importance (build of One Quant Book 12, chapter 6).

Importance answers "what did the model use?", selection answers "what should it use?", and both are fooled by the same
thing: features that carry the same information. This module computes the standard importances on held-out data,
their clustered versions (correlated features permuted or dropped together), SHAP attributions of LightGBM models, and
stability selection with Meinshausen and Buhlmann's bound on the expected number of false selections.

API (stable):
    winsorise(x, q)                               clip at the q and 1 - q quantiles
    rank_gauss(x)                                 ranks mapped to normal scores
    mdi(model)                                    LightGBM gain importance, normalised to sum 1
    permutation_importance(predict, X, y, score, reps, seed, groups)   mean score drop when a column (or a group of
                                                  columns) is shuffled, on held-out data; (k,) array
    drop_column_importance(fit_predict, X, y, Xt, yt, score, groups)   score drop when the column(s) are removed and
                                                  the model refitted
    shap_values(model, X)                         (n, p) TreeSHAP contributions (LightGBM pred_contrib), bias dropped
    cluster_features(X, threshold)                groups of features whose |correlation| exceeds 1 - threshold, by
                                                  average-linkage hierarchical clustering on 1 - |corr|
    stability_selection(select, X, y, n_sub, frac, seed) -> (p,) selection frequencies over half-samples
    false_selection_bound(q, p, threshold)        Meinshausen-Buhlmann bound q^2 / ((2 threshold - 1) p)
"""
from __future__ import annotations

import numpy as np


def winsorise(x, q: float = 0.01):
    lo, hi = np.quantile(x, [q, 1 - q])
    return np.clip(x, lo, hi)


def rank_gauss(x):
    from scipy.stats import norm

    r = (np.argsort(np.argsort(x)) + 0.5) / len(x)
    return norm.ppf(r)


def mdi(model):
    g = model.booster_.feature_importance(importance_type="gain").astype(float)
    return g / g.sum()


def _groups(p, groups):
    return [[j] for j in range(p)] if groups is None else [list(g) for g in groups]


def permutation_importance(predict, X, y, score, reps: int = 5, seed: int = 0, groups=None):
    rng = np.random.default_rng(seed)
    base = score(y, predict(X))
    out = []
    for g in _groups(X.shape[1], groups):
        drops = []
        for _ in range(reps):
            Z = X.copy()
            perm = rng.permutation(len(X))
            Z[:, g] = X[perm][:, g]                                      # a group is shuffled jointly
            drops.append(base - score(y, predict(Z)))
        out.append(np.mean(drops))
    return np.array(out)


def drop_column_importance(fit_predict, X, y, Xt, yt, score, groups=None):
    """fit_predict(X, y, Xt) -> predictions on Xt of a model fitted on (X, y)."""
    base = score(yt, fit_predict(X, y, Xt))
    out = []
    for g in _groups(X.shape[1], groups):
        keep = [j for j in range(X.shape[1]) if j not in g]
        out.append(base - score(yt, fit_predict(X[:, keep], y, Xt[:, keep])))
    return np.array(out)


def shap_values(model, X):
    return model.predict(X, pred_contrib=True)[:, :-1]


def cluster_features(X, threshold: float = 0.5):
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform

    C = np.corrcoef(X, rowvar=False)
    D = 1.0 - np.abs(C)
    np.fill_diagonal(D, 0.0)
    Z = linkage(squareform(D, checks=False), method="average")
    lab = fcluster(Z, t=threshold, criterion="distance")
    return [list(np.flatnonzero(lab == k)) for k in np.unique(lab)]


def stability_selection(select, X, y, n_sub: int = 50, frac: float = 0.5, seed: int = 0):
    """select(X, y) -> boolean (p,) mask of selected features; run on n_sub random subsamples of size frac * n."""
    rng = np.random.default_rng(seed)
    n = len(y)
    freq = np.zeros(X.shape[1])
    for _ in range(n_sub):
        idx = rng.choice(n, int(frac * n), replace=False)
        freq += np.asarray(select(X[idx], y[idx]), float)
    return freq / n_sub


def false_selection_bound(q: float, p: int, threshold: float) -> float:
    """Expected number of falsely selected variables when each subsample selects q of p variables and the selection
    frequency threshold is in (0.5, 1] (Meinshausen and Buhlmann, 2010, under exchangeability)."""
    return q * q / ((2.0 * threshold - 1.0) * p)
