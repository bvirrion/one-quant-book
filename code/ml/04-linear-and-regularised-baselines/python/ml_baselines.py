"""Linear and regularised baselines (One Quant Book 12, chapter 4).

firm.mlsynth's panel with forty ranked characteristics (six carry a planted expected return, half of its variance
nonlinear) and zero-mean factor returns on every characteristic (monthly volatility 2%, so that characteristic-sorted
portfolios carry factor risk): 500 stocks, twenty years of training months and ten of test. Ordinary least squares,
ridge, the lasso, the elastic net, principal-component regression and partial least squares, each with its penalty or
number of components chosen by purged cross-validation along its path; a logistic regression on the sign; ridge on a
spline basis expansion; and gradient-boosted trees as the nonlinear challenger. All through firm.mlbase's harness and
report.
"""
from __future__ import annotations

import functools
import pathlib
import sys
import warnings

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("mlsynth", "mlbase"):
    sys.path.insert(0, str(ROOT / c))
from firm_mlbase import cv_path, fit, predict, report  # noqa: E402
from firm_mlsynth import PanelConfig, ceiling, panel  # noqa: E402

TRAIN, TEST = np.arange(0, 240), np.arange(240, 360)
ALPHAS = (1e2, 1e3, 1e4, 1e5)
LASSO = (1e-4, 3e-4, 1e-3, 3e-3)
COMPS = (1, 3, 10, 40)
STYLE = 0.02


@functools.lru_cache(maxsize=3)
def data(seed=1, n=500, k=40, style=STYLE):
    return panel(PanelConfig(n=n, k=k, seed=seed, style_vol=style))


def ols():
    from sklearn.linear_model import LinearRegression

    return LinearRegression()


def ridge(a):
    from sklearn.linear_model import Ridge

    return Ridge(alpha=a)


def lasso(a):
    from sklearn.linear_model import Lasso

    return Lasso(alpha=a, max_iter=5000)


def enet(a):
    from sklearn.linear_model import ElasticNet

    return ElasticNet(alpha=2 * a, l1_ratio=0.5, max_iter=5000)


def pcr(k):
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import make_pipeline

    return make_pipeline(PCA(n_components=k), LinearRegression())


def pls(k):
    from sklearn.cross_decomposition import PLSRegression

    class _PLS(PLSRegression):
        def predict(self, X, copy=True):
            return super().predict(X, copy=copy).ravel()

    return _PLS(n_components=k, scale=False)


def splines(a):
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import SplineTransformer

    return make_pipeline(SplineTransformer(n_knots=4, degree=2), Ridge(alpha=a))


def gbm(seed=1):
    import lightgbm as lgb

    return lgb.LGBMRegressor(n_estimators=300, learning_rate=0.02, num_leaves=15, min_child_samples=500,
                             subsample=0.5, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1,
                             n_jobs=1, deterministic=True, force_row_wise=True, seed=seed)


class _Logit:
    """A logistic regression on the sign of the demeaned return; its prediction is P(up) - 1/2 scaled to returns by a
    regression of the demeaned return on it in the training data."""

    def __init__(self, C=1e-3):
        from sklearn.linear_model import LogisticRegression

        self.m = LogisticRegression(C=C, max_iter=1000)

    def fit(self, X, y):
        self.m.fit(X, (y > 0).astype(int))
        p = self.m.predict_proba(X)[:, 1] - 0.5
        self.b = float(p @ y / (p @ p))
        return self

    def predict(self, X):
        return self.b * (self.m.predict_proba(X)[:, 1] - 0.5)


PATHS = {"ridge": (ridge, ALPHAS), "lasso": (lasso, LASSO), "elastic net": (enet, LASSO), "PCR": (pcr, COMPS),
         "PLS": (pls, COMPS), "ridge on splines": (splines, ALPHAS)}


@functools.lru_cache(maxsize=4)
def paths(seed=1):
    P = data(seed)
    out = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, (make, grid) in PATHS.items():
            out[name] = cv_path(make, grid, P.X, P.r, TRAIN, n_folds=3)
    return out


@functools.lru_cache(maxsize=4)
def table(seed=1, style=STYLE):
    """Every model refitted on the training months with its CV-chosen parameter (chosen on the panel with factor
    risk), scored on the test months."""
    P = data(seed, style=style)
    rows = {"ceiling": {"r2": ceiling(P, TEST)}}
    chosen = {}
    models = {"OLS": ols(), "logistic": _Logit(), "boosted trees": gbm()}
    for name, (make, _grid) in PATHS.items():
        params, scores = paths(seed)[name]
        chosen[name] = params[int(np.argmax(scores))]
        models[name] = make(chosen[name])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, m in models.items():
            m = fit(m, P.X, P.r, TRAIN)
            pred = predict(m, P.X, TEST)
            rows[name] = report(pred, P.r[TEST])
            rows[name]["pred"] = pred
            if name == "lasso":
                rows[name]["nonzero"] = int(np.sum(m.coef_ != 0))
    return rows, chosen


def net_difference(seed=1):
    """Monthly net long-short returns of the lasso minus the trees: mean and standard deviation."""
    from firm_mlbase import long_short

    rows, _ = table(seed)
    r = data(seed).r[TEST]
    out = []
    for name in ("lasso", "boosted trees"):
        ls, w = long_short(rows[name]["pred"], r)
        traded = np.r_[np.abs(w[0]).sum(), np.abs(np.diff(w, axis=0)).sum(axis=1)]
        out.append(ls - traded * 20e-4)
    d = out[0] - out[1]
    return float(d.mean()), float(d.std(ddof=1))


@functools.lru_cache(maxsize=2)
def crossing(seed=1, months=(24, 60, 120, 240)):
    """Out-of-sample R-squared of ridge (its CV-chosen penalty) and boosted trees on the ten test years, by length of
    the training window (the most recent months before the test)."""
    P = data(seed)
    a = table(seed)[1]["ridge"]
    rows = []
    for m in months:
        tr = np.arange(240 - m, 240)
        rg = report(predict(fit(ridge(a), P.X, P.r, tr), P.X, TEST), P.r[TEST])
        gb = report(predict(fit(gbm(), P.X, P.r, tr), P.X, TEST), P.r[TEST])
        rows.append((m, rg["r2"], gb["r2"], rg["ls_sr_net"], gb["ls_sr_net"], ceiling(P, TEST)))
    return rows
