"""Why financial machine learning is different (One Quant Book 12, chapter 1).

The same three models -- ridge regression, gradient-boosted trees (LightGBM) and a small neural network (scikit-learn's
multilayer perceptron) -- on two tasks: a monthly cross-section of 500 stocks from firm.mlsynth, whose planted expected
returns are known, and a generic regression task with a strong signal. Twenty years train, ten years test. The
predictability ceiling of the stock task (the R-squared of the truth itself), in-sample against out-of-sample R-squared,
learning curves, the months needed to tell the model from zero, the effective number of independent stocks in a month,
and what a decaying and a flipping signal do to a model trained before they change.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "mlsynth"))
from firm_mlsynth import PanelConfig, ceiling, months_to_detect, panel, r2_oos, task  # noqa: E402

TRAIN, TEST = np.arange(0, 240), np.arange(240, 360)


def xs_target(P, months):
    """Training target: each month's returns minus that month's cross-sectional mean (the model learns which stocks
    do better, not where the market goes)."""
    m = np.asarray(months)
    return (P.r[m] - P.r[m].mean(axis=1, keepdims=True)).reshape(-1)


def ridge(X, y, alpha=100.0):
    from sklearn.linear_model import Ridge

    return Ridge(alpha=alpha).fit(X, y)


def gbm(X, y, seed=1, trees=300):
    import lightgbm as lgb

    return lgb.LGBMRegressor(n_estimators=trees, learning_rate=0.02, num_leaves=15, min_child_samples=500,
                             subsample=0.5, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1,
                             n_jobs=1, deterministic=True, force_row_wise=True, seed=seed).fit(X, y)


def mlp(X, y, seed=1):
    import warnings

    from sklearn.exceptions import ConvergenceWarning
    from sklearn.neural_network import MLPRegressor

    s = y.std()
    m = MLPRegressor(hidden_layer_sizes=(32, 16), alpha=1e-3, learning_rate_init=1e-3, batch_size=512, max_iter=30,
                     early_stopping=True, validation_fraction=0.15, n_iter_no_change=4, random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)             # 30 epochs on purpose: a quick network
        m.fit(X, y / s)
    m.scale_ = s
    return m


def predict(model, X):
    return model.predict(X) * getattr(model, "scale_", 1.0)


FITS = {"ridge": ridge, "boosting": gbm, "network": mlp}


@functools.lru_cache(maxsize=4)
def stock_panel(seed=1, decay=False):
    cfg = PanelConfig(seed=seed, decay_from=240 if decay else None, decay_half_life=24.0,
                      regime_at=300 if decay else None)
    return panel(cfg)


@functools.lru_cache(maxsize=4)
def compare(seed=1, target="xs"):
    """In- and out-of-sample R-squared of the three models on the stock panel, and the ceiling. target 'xs' trains on
    cross-sectionally demeaned returns, 'raw' on the returns themselves (the intercept is then the training window's
    average market return)."""
    P = stock_panel(seed)
    X, r, mu, _ = P.flat(TRAIN)
    Xt, rt, mut, mt = P.flat(TEST)
    y = xs_target(P, TRAIN) if target == "xs" else r
    out = {"ceiling_is": ceiling(P, TRAIN), "ceiling_oos": ceiling(P, TEST), "months_oos": {}}
    for name, fit in FITS.items():
        m = fit(X, y)
        p, pt = predict(m, X), predict(m, Xt)
        out[name] = {"is": r2_oos(r, p), "oos": r2_oos(rt, pt), "corr_truth": float(np.corrcoef(pt, mut)[0, 1])}
        out["months_oos"][name] = np.array([r2_oos(rt[mt == t], pt[mt == t]) for t in TEST])
    out["months_truth"] = np.array([r2_oos(rt[mt == t], mut[mt == t]) for t in TEST])
    return out


def detect_months(name="boosting", seed=1):
    return months_to_detect(compare(seed)["months_oos"][name])


@functools.lru_cache(maxsize=2)
def strong_signal(n=20000, snr=19.0, seed=3):
    """The same three models on a task with a strong signal (Bayes R-squared 0.95)."""
    d = task(2 * n, p=20, snr=snr, kind="friedman", seed=seed)
    X, y = d["X"], d["y"]
    out = {"bayes": d["bayes_r2"]}
    for name, fit in FITS.items():
        m = fit(X[:n], y[:n])
        out[name] = {"is": r2_oos(y[:n] - y[:n].mean(), predict(m, X[:n]) - y[:n].mean()),
                     "oos": 1 - np.mean((y[n:] - predict(m, X[n:])) ** 2) / np.var(y[n:])}
    return out


@functools.lru_cache(maxsize=2)
def learning_curve(seed=1, months=(24, 48, 96, 144, 240)):
    """Out-of-sample R-squared of boosting and ridge on the last ten years, by length of the training window
    (the most recent months before the test)."""
    P = stock_panel(seed)
    Xt, rt, _, _ = P.flat(TEST)
    rows = []
    for m in months:
        X, _, _, _ = P.flat(np.arange(240 - m, 240))
        y = xs_target(P, np.arange(240 - m, 240))
        rows.append((m, r2_oos(rt, predict(gbm(X, y), Xt)), r2_oos(rt, predict(ridge(X, y), Xt))))
    return rows


def effective_stocks(seed=1):
    """Average pairwise correlation of the stocks' unexpected returns and the effective number of independent
    stocks in a month, n / (1 + (n - 1) rho)."""
    P = stock_panel(seed)
    e = P.r - P.mu
    C = np.corrcoef(e.T)
    n = C.shape[0]
    rho = (C.sum() - n) / (n * (n - 1))
    return float(rho), float(n / (1 + (n - 1) * rho))


@functools.lru_cache(maxsize=1)
def drift_by_year(seed=1):
    """Boosting trained on months 0-239 of a stationary panel and of one whose strongest linear signal decays from
    month 240 (half-life two years) and whose interaction flips sign at month 300: out-of-sample R-squared and the
    ceiling, year by year."""
    rows = []
    for decay in (False, True):
        P = stock_panel(seed, decay)
        X, _, _, _ = P.flat(TRAIN)
        m = gbm(X, xs_target(P, TRAIN))
        for y in range(10):
            months = np.arange(240 + 12 * y, 252 + 12 * y)
            Xt, rt, _, _ = P.flat(months)
            rows.append((decay, y + 1, r2_oos(rt, predict(m, Xt)), ceiling(P, months)))
    return rows
