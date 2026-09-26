"""Neural networks for noisy tabular data (One Quant Book 12, chapter 7).

Chapter 4's panel (500 stocks, forty ranked characteristics with factor risk, 360 months): multilayer perceptrons fitted
with AdamW and early stopping on a purged validation block (months 201-239, the training months 0-199), scored on
months 240-359 with firm.mlbase's report, as chapter 4's models were. Ten seeds of two architectures against the gap
between them; the ten-seed ensemble; dropout, weight decay and two normalisations; ridge on the same months.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("mlsynth", "mlbase", "nettab", "gbdt"):
    sys.path.insert(0, str(ROOT / c))
from firm_gbdt import make  # noqa: E402
from firm_mlbase import report  # noqa: E402
from firm_mlsynth import PanelConfig, panel  # noqa: E402
from firm_nettab import SeedEnsemble, fit  # noqa: E402,F401

FIT, VAL, TEST = np.arange(0, 200), np.arange(201, 240), np.arange(240, 360)
SMALL, LARGE = (32, 16), (64, 32, 16)


@functools.lru_cache(maxsize=1)
def data(seed=1):
    return panel(PanelConfig(n=500, months=360, k=40, seed=seed, style_vol=0.02))


def _xy(months):
    P = data()
    X = P.X[months].reshape(-1, P.X.shape[2])
    y = (P.r[months] - P.r[months].mean(axis=1, keepdims=True)).reshape(-1)
    return X, y


def _report(pred_flat):
    P = data()
    return report(pred_flat.reshape(len(TEST), -1), P.r[TEST])


@functools.lru_cache(maxsize=1)
def splits():
    return _xy(FIT), _xy(VAL), _xy(TEST)[0]


@functools.lru_cache(maxsize=64)
def fitted(hidden=SMALL, seed=1, dropout=0.0, weight_decay=0.0, norm=None, lr=1e-3):
    (X, y), (Xv, yv), Xt = splits()
    m = fit(X, y, Xv, yv, hidden=hidden, dropout=dropout, weight_decay=weight_decay, norm=norm, lr=lr, seed=seed)
    return m, m.predict(Xt)


@functools.lru_cache(maxsize=64)
def net(hidden=SMALL, seed=1, dropout=0.0, weight_decay=0.0, norm=None, lr=1e-3):
    m, p = fitted(hidden, seed, float(dropout), float(weight_decay), norm, float(lr))
    rep = _report(p)
    rep["best_epoch"] = m.best_epoch
    rep["hash"] = m.state_hash()
    return rep


@functools.lru_cache(maxsize=2)
def seed_study(n=10):
    a = np.array([net(SMALL, s)["ic"] for s in range(1, n + 1)])
    b = np.array([net(LARGE, s)["ic"] for s in range(1, n + 1)])
    gap = b.mean() - a.mean()
    sd = float(np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2))
    need = (2 * np.sqrt(2) * sd / abs(gap)) ** 2 if gap != 0 else np.inf   # seeds per arm for a 2-se difference
    return {"small": a, "large": b, "gap": float(gap), "sd": sd, "seeds_needed": float(need)}


@functools.lru_cache(maxsize=4)
def ensemble(n=10, hidden=SMALL):
    """The average of the first n seeds' predictions (firm.nettab.SeedEnsemble does the same in one object)."""
    return _report(np.mean([fitted(hidden, s, 0.0, 0.0, None, 1e-3)[1] for s in range(1, n + 1)], axis=0))


@functools.lru_cache(maxsize=2)
def ablation(seeds=(1, 2, 3)):
    variants = {"plain": {}, "dropout 0.2": {"dropout": 0.2}, "weight decay 0.01": {"weight_decay": 0.01},
                "batch norm": {"norm": "batch"}, "layer norm": {"norm": "layer"}}
    return {k: np.array([net(SMALL, s, **kw)["ic"] for s in seeds]) for k, kw in variants.items()}


@functools.lru_cache(maxsize=1)
def baselines():
    """Ridge (chapter 4's penalty) and the firm's default boosted trees, trained on months 0-239 as in chapter 4."""
    from sklearn.linear_model import Ridge

    X, y = _xy(np.arange(0, 240))
    Xt, _ = _xy(TEST)
    return {"ridge": _report(Ridge(alpha=1e4).fit(X, y).predict(Xt)), "boosting": _report(make().fit(X, y).predict(Xt))}
