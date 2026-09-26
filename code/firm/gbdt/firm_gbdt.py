"""firm.gbdt -- gradient-boosted trees the way the firm fits them (build of One Quant Book 12, chapter 5).

A thin layer over LightGBM that fixes the choices a research team should not make twice: deterministic single-threaded
fits, early stopping on a purged validation block, monotonic constraints declared by feature name, seed ensembles,
selection of a configuration from the plateau of a search rather than its peak, and an export of the fitted trees to a
plain dictionary that a pure NumPy evaluator (and, in chapter 26, a compiler) can read.

API (stable):
    make(params=None, monotone=None, names=None, seed=1) -> lightgbm.LGBMRegressor   deterministic, one thread
    DEFAULTS                                             the firm's default parameters
    fit_early_stop(params, X, y, Xv, yv, max_trees, patience, monotone, names, seed) -> (model, best_iter, curve)
    SeedEnsemble(params, seeds, monotone, names).fit(X, y).predict(X)
    plateau_select(scores, se, complexity)               index of the least complex candidate within `se` of the best
    to_dict(model) -> dict                               LightGBM's model dump (trees, splits, leaf values)
    predict_dict(d, X) -> ndarray                        NumPy evaluation of a dumped model (parity with predict)
"""
from __future__ import annotations

import numpy as np

DEFAULTS = dict(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=200, subsample=0.7,
                subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0)


def make(params=None, monotone=None, names=None, seed: int = 1):
    """monotone: {feature name: +1 or -1}; names: the feature names in column order."""
    import lightgbm as lgb

    p = dict(DEFAULTS)
    p.update(params or {})
    if monotone:
        p["monotone_constraints"] = [int(monotone.get(n, 0)) for n in names]
        p.setdefault("monotone_constraints_method", "advanced")
    return lgb.LGBMRegressor(**p, verbose=-1, n_jobs=1, num_threads=1, deterministic=True, force_row_wise=True,
                             seed=seed)


def fit_early_stop(params, X, y, Xv, yv, max_trees: int = 1000, patience: int = 50, monotone=None, names=None,
                   seed: int = 1):
    """Fit up to max_trees and keep the number of trees with the best validation loss; `curve` is the validation MSE
    after each tree. The validation block must be purged from the training rows by the caller."""
    import lightgbm as lgb

    m = make(dict(params or {}, n_estimators=max_trees), monotone, names, seed)
    m.fit(X, y, eval_X=(Xv,), eval_y=(yv,), eval_metric="l2",
          callbacks=[lgb.early_stopping(patience, verbose=False), lgb.record_evaluation(rec := {})])
    curve = np.asarray(rec["valid_0"]["l2"])
    return m, int(m.best_iteration_), curve


class SeedEnsemble:
    def __init__(self, params=None, seeds=(1, 2, 3, 4, 5), monotone=None, names=None):
        self.params, self.seeds, self.monotone, self.names = params, seeds, monotone, names

    def fit(self, X, y):
        self.models = [make(self.params, self.monotone, self.names, s).fit(X, y) for s in self.seeds]
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.models], axis=0)


def plateau_select(scores, se: float, complexity) -> int:
    """Among candidates whose score is within `se` of the best, the one with the lowest complexity."""
    scores, complexity = np.asarray(scores, float), np.asarray(complexity, float)
    ok = np.flatnonzero(scores >= scores.max() - se)
    return int(ok[np.argmin(complexity[ok])])


def to_dict(model) -> dict:
    return model.booster_.dump_model()


def _eval_tree(node, X, out, idx):
    if "leaf_value" in node:
        out[idx] += node["leaf_value"]
        return
    f, thr, mt = node["split_feature"], node["threshold"], node.get("missing_type", "None")
    x = X[idx, f]
    miss = np.isnan(x)
    if mt == "NaN":                                                     # learned direction for missing values
        left = np.where(miss, node["default_left"], x <= thr)
    elif mt == "Zero":                                                  # zeros (and NaN) follow the default side
        z = miss | (x == 0.0)
        left = np.where(z, node["default_left"], x <= thr)
    else:                                                               # no missing values in training: NaN -> 0
        left = np.where(miss, 0.0, x) <= thr
    _eval_tree(node["left_child"], X, out, idx[left])
    _eval_tree(node["right_child"], X, out, idx[~left])


def predict_dict(d: dict, X) -> np.ndarray:
    """Sum of the trees' leaf values (LightGBM stores the initial score inside the first tree's leaves)."""
    X = np.asarray(X, float)
    out = np.zeros(len(X))
    for t in d["tree_info"]:
        _eval_tree(t["tree_structure"], X, out, np.arange(len(X)))
    return out
