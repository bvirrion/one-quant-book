"""firm.cvsplit -- validation that respects time, and leak detectors (build of One Quant Book 12, chapter 3).

Book 7's firm.overfit computes purged k-fold, combinatorial purged and walk-forward splits from label spans. This module
wraps them as scikit-learn cross-validators (so that GridSearchCV, cross_val_score and friends use them), adds nested
cross-validation, and the four detectors of the chapter's leakage audit:

* fold_overlap: training labels whose spans overlap a test fold (the leak purging removes);
* truncation_test: a feature recomputed on the data available at each date must equal the stored feature (catches
  period-end joins, full-sample statistics and any other look-ahead in feature construction);
* canary: the whole pipeline run on a target that is noise by construction, with the real target's structure; a
  score above chance means the pipeline, not the data, produces the result;
* adversarial_validation: how well a classifier tells training rows from test rows (features that locate time make
  shuffled folds leak and signal drift).

API (stable):
    PurgedKFold(t0, t1, n_splits, embargo)          scikit-learn splitter on label spans (rows in time order)
    CPCVSplit(t0, t1, n_folds, n_test, embargo)     combinatorial purged splits
    WalkForwardSplit(n, train, test, step, anchored)
    nested_cv(make_model, grid, X, y, outer, inner, score) -> dict(outer_scores, chosen, flat_best, flat_scores)
    fold_overlap(t0, t1, train, test)              number of training labels overlapping the test span
    truncation_test(feature_fn, data, checkpoints)  max |feature on data[:t+1] at t - feature on all data at t|
    canary(pipeline, make_noise_target, reps, seed) -> (mean score, standard error) of the pipeline on noise targets
    adversarial_validation(X_train, X_test, seed)   AUC of a boosted classifier separating the two (0.5 = same)
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "overfit"))
from firm_overfit import cpcv, purged_kfold, walk_forward  # noqa: E402


class _Splitter:
    def __init__(self, splits):
        self._splits = splits

    def split(self, X=None, y=None, groups=None):
        yield from self._splits

    def get_n_splits(self, X=None, y=None, groups=None):
        return len(self._splits)


class PurgedKFold(_Splitter):
    def __init__(self, t0, t1, n_splits: int = 5, embargo: int = 0):
        super().__init__(purged_kfold(t0, t1, n_splits, embargo))


class CPCVSplit(_Splitter):
    def __init__(self, t0, t1, n_folds: int = 6, n_test: int = 2, embargo: int = 0):
        super().__init__(cpcv(t0, t1, n_folds, n_test, embargo))


class WalkForwardSplit(_Splitter):
    def __init__(self, n: int, train: int, test: int, step: int | None = None, anchored: bool = False):
        super().__init__(walk_forward(n, train, test, step, anchored))


def _grid(grid: dict):
    keys = list(grid)
    out = [{}]
    for k in keys:
        out = [dict(o, **{k: v}) for o in out for v in grid[k]]
    return out


def nested_cv(make_model, grid: dict, X, y, outer, inner, score) -> dict:
    """outer: a splitter over rows; inner(train_idx) -> a splitter over positions 0..len(train_idx)-1.
    For each outer fold, the configuration with the best mean inner score is refitted on the outer training rows and
    scored on the outer test rows. flat_best is the best mean score over the outer folds themselves -- the optimistic
    number a flat search reports."""
    X, y = np.asarray(X), np.asarray(y)
    cands = _grid(grid)
    outer_scores, chosen = [], []
    flat = np.zeros((len(cands), outer.get_n_splits()))
    for f, (tr, te) in enumerate(outer.split(X)):
        inner_means = []
        for c in cands:
            s = [score(y[tr][b], make_model(**c).fit(X[tr][a], y[tr][a]).predict(X[tr][b]))
                 for a, b in inner(tr).split(X[tr])]
            inner_means.append(np.mean(s))
        for j, c in enumerate(cands):
            flat[j, f] = score(y[te], make_model(**c).fit(X[tr], y[tr]).predict(X[te]))
        best = int(np.argmax(inner_means))
        chosen.append(cands[best])
        outer_scores.append(flat[best, f])
    flat_means = flat.mean(axis=1)
    return {"outer_scores": np.array(outer_scores), "chosen": chosen, "flat_best": float(flat_means.max()),
            "flat_scores": flat_means}


def fold_overlap(t0, t1, train, test) -> int:
    t0, t1 = np.asarray(t0), np.asarray(t1)
    a, b = t0[test].min(), t1[test].max()
    tr0, tr1 = t0[train], t1[train]
    return int(np.sum((tr1 >= a) & (tr0 <= b)))


def truncation_test(feature_fn, data, checkpoints) -> float:
    """feature_fn(data) -> array whose first axis is time. Recompute it on data truncated after each checkpoint and
    compare row t with the full computation's row t. Zero means the feature at t used nothing after t."""
    full = np.asarray(feature_fn(data), float)
    worst = 0.0
    for t in checkpoints:
        part = np.asarray(feature_fn(data[: t + 1]), float)
        d = np.nanmax(np.abs(part[t] - full[t]))
        worst = max(worst, float(d))
    return worst


def canary(pipeline, make_noise_target, reps: int = 5, seed: int = 0):
    """pipeline(y) -> out-of-sample score using the given target; make_noise_target(rng) -> a target with the real
    target's structure (overlap, shape) but no relation to anything. Returns the mean score and its standard error."""
    rng = np.random.default_rng(seed)
    s = np.array([pipeline(make_noise_target(rng)) for _ in range(reps)])
    return float(s.mean()), float(s.std(ddof=1) / np.sqrt(reps))


def adversarial_validation(X_train, X_test, seed: int = 0) -> float:
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold

    X = np.vstack([X_train, X_test])
    y = np.r_[np.zeros(len(X_train)), np.ones(len(X_test))]
    p = np.zeros(len(y))
    for tr, te in StratifiedKFold(4, shuffle=True, random_state=seed).split(X, y):
        m = lgb.LGBMClassifier(n_estimators=100, num_leaves=15, learning_rate=0.1, verbose=-1, n_jobs=1,
                               deterministic=True, force_row_wise=True, seed=seed).fit(X[tr], y[tr])
        p[te] = m.predict_proba(X[te])[:, 1]
    return float(roc_auc_score(y, p))
