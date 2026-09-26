"""Interpretability and model governance (One Quant Book 12, chapter 21).

(1) A gradient-boosted model (firm.gbdt) on y = x1 + x2^2 + 2 x3 x4 + noise, with x2 a noisy copy of x1 at three
levels of correlation: partial dependence and accumulated local effects of x1 against its true (linear) effect; ICE
curves of x3, whose effect is all interaction; a depth-three global surrogate; a counterfactual. (2) The stability of
the top five features by mean |SHAP| across ten bootstrap retrains, on a problem with three strong, five weak and
twelve null features, at a high and a low signal-to-noise ratio. (3) A model card and a validation checklist, with
implementation parity and an outcomes test run through Book 6's firm.modelval."""
from __future__ import annotations

import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("modelcard", "gbdt", "featimp"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_featimp import shap_values  # noqa: E402
from firm_gbdt import make, predict_dict, to_dict  # noqa: E402
from firm_modelcard import (  # noqa: E402
    ModelCard,
    ale,
    benchmark_check,
    counterfactual,
    global_surrogate,
    ice,
    outcome_check,
    partial_dependence,
    rank_stability,
    validation_checklist,
)

NOISE_X2 = {"independent": None, "correlation 0.9": 0.25, "correlation 0.99": 0.08}


def dataset(x2_noise, n=6000, seed=0):
    rng = np.random.default_rng(seed)
    x1 = rng.uniform(-1, 1, n)
    x2 = rng.uniform(-1, 1, n) if x2_noise is None else x1 + x2_noise * rng.standard_normal(n)
    x3, x4 = rng.uniform(-1, 1, n), rng.uniform(-1, 1, n)
    X = np.column_stack([x1, x2, x3, x4])
    y = x1 + x2**2 + 2 * x3 * x4 + 0.3 * rng.standard_normal(n)
    return X, y


@functools.lru_cache(maxsize=4)
def model(case):
    X, y = dataset(NOISE_X2[case])
    return make(seed=1).fit(X, y), X, y


GRID = np.linspace(-0.9, 0.9, 19)


def _centred(v, x_at, weights):
    return v - float(np.average(np.interp(x_at, GRID, v), weights=weights)) if weights is not None else v - v.mean()


@functools.lru_cache(maxsize=1)
def effects():
    """RMSE, over the data's x1 values, of the centred partial dependence and ALE of x1 against its true effect x1."""
    out = {}
    for case in NOISE_X2:
        m, X, y = model(case)
        pd = partial_dependence(m.predict, X, 0, GRID)
        edges, a = ale(m.predict, X, 0, bins=20)
        x = X[:, 0]
        pd_x = np.interp(x, GRID, pd)
        ale_x = np.interp(x, edges, a)
        truth = x - x.mean()
        out[case] = {"PD": float(np.sqrt(np.mean((pd_x - pd_x.mean() - truth) ** 2))),
                     "ALE": float(np.sqrt(np.mean((ale_x - ale_x.mean() - truth) ** 2))),
                     "corr": float(np.corrcoef(X[:, 0], X[:, 1])[0, 1])}
    return out


def curves(case="correlation 0.99"):
    m, X, _ = model(case)
    edges, a = ale(m.predict, X, 0, bins=20)
    pd = partial_dependence(m.predict, X, 0, GRID)
    return GRID, pd - np.mean(np.interp(X[:, 0], GRID, pd)), edges, a


def ice_x3(case="independent", rows=range(0, 3000, 100)):
    """ICE curves of x3 on 30 observations, and their slopes against x4 (the true slope is 2 x4)."""
    m, X, _ = model(case)
    rows = list(rows)
    C = ice(m.predict, X, 2, GRID, rows)
    slopes = np.polyfit(GRID, C.T, 1)[0]
    pd = partial_dependence(m.predict, X, 2, GRID)
    return C, float(np.polyfit(GRID, pd, 1)[0]), slopes, X[rows, 3]


def surrogate(case="independent"):
    m, X, _ = model(case)
    tree, fid = global_surrogate(m.predict, X, depth=3)
    return tree, fid


def counterfactual_example(case="independent", i=7, target=0.0):
    """The smallest change of x1 that moves one observation's prediction across zero."""
    m, X, _ = model(case)
    x = X[i].copy()
    v = counterfactual(m.predict, x, 0, target, np.linspace(-1, 1, 201))
    return float(x[0]), float(m.predict(x[None])[0]), v


# ---------------------------------------------------------------------------------------------------- stability
def stability_data(noise, n=4000, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, 20))
    beta = np.r_[1.0, 0.7, 0.5, [0.2] * 5, [0.0] * 12]
    return X, X @ beta + noise * rng.standard_normal(n)


@functools.lru_cache(maxsize=4)
def stability(noise, retrains=10, disjoint=False):
    """Top features by mean |SHAP| in each of ten models fitted on bootstrap resamples (or on disjoint tenths)."""
    X, y = stability_data(noise)
    rng = np.random.default_rng(1)
    rankings = []
    for r in range(retrains):
        idx = np.arange(r * 400, (r + 1) * 400) if disjoint else rng.integers(0, len(y), len(y))
        m = make(seed=1).fit(X[idx], y[idx])
        imp = np.abs(shap_values(m, X[:1000])).mean(0)
        rankings.append(np.argsort(-imp))
    r2 = float(1 - noise**2 / (noise**2 + 1.0 + 0.49 + 0.25 + 5 * 0.04))
    return rank_stability(rankings, 5) + (r2, rankings)


# ---------------------------------------------------------------------------------------------------- governance
@functools.lru_cache(maxsize=1)
def validation():
    """Implementation parity of the dumped model, a challenger, a 90% interval's outcomes, and the checklist."""
    from sklearn.linear_model import Ridge

    m, X, y = model("independent")
    Xt, yt = dataset(None, n=2000, seed=5)
    d = to_dict(m)
    parity = benchmark_check(lambda i: float(predict_dict(d, Xt[i:i + 1])[0]),
                             lambda i: float(m.predict(Xt[i:i + 1])[0]), {"i": range(200)}, 1e-9, 1e-9)
    r2 = lambda p: 1 - np.mean((yt - p) ** 2) / np.var(yt)                                     # noqa: E731
    ridge = Ridge(1.0).fit(X, y)
    res = y - m.predict(X)
    lo, hi = np.quantile(res, [0.05, 0.95])
    rt = (yt - m.predict(Xt))[:250]                                    # a year of daily outcomes
    exc = int(((rt < lo) | (rt > hi)).sum())
    ok, tail = outcome_check(len(rt), exc, 0.10)
    checks = {"out-of-sample performance": (True, f"R2 {r2(m.predict(Xt)):.3f} on 2,000 new rows"),
              "challenger comparison": (r2(m.predict(Xt)) > r2(ridge.predict(Xt)),
                                        f"ridge R2 {r2(ridge.predict(Xt)):.3f}"),
              "implementation parity": (parity["failures"] == 0, f"max abs error {parity['max_abs']:.1e} on 200 rows"),
              "outcomes analysis": (ok, f"{exc} of 250 outside the 90% interval, tail probability {tail:.2f}")}
    return {"parity": parity, "r2": r2(m.predict(Xt)), "ridge r2": r2(ridge.predict(Xt)), "exceptions": exc,
            "tail": tail, "checklist": validation_checklist(checks)}


def card():
    v = validation()
    return ModelCard({"name": "chapter-21 demonstration model", "version": "1", "owner": "research",
                      "purpose": "illustration", "target": "y", "horizon": "one step", "data": "synthetic, 6,000 rows",
                      "features": "x1..x4", "training": "firm.gbdt defaults, seed 1",
                      "validation": f"2,000 new rows, R2 {v['r2']:.3f}",
                      "performance": f"challenger ridge R2 {v['ridge r2']:.3f}",
                      "explanations": "ALE for x1, ICE for x3 (interaction with x4)",
                      "limitations": "x1 and x2 correlated in some variants: use ALE, not PD", "monitoring": "",
                      "approvals": ""})
