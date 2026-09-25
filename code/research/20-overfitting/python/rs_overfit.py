"""Overfitting (One Quant Book 7, chapter 20).

A thousand moving-average trend systems (fast window 2 to 40 days, slow 50 to 540) run on 25 years of synthetic daily
returns, twice: on pure noise, and with a planted persistent drift (a trend a trend-follower can earn). The first 20
years are the search, the last 5 the out-of-sample test. The probability of backtest overfitting by CSCV on the
search years; the chosen system's out-of-sample Sharpe ratio against the deflated expectation; walk-forward
re-selection; the minimum backtest length. And a model with overlapping labels (20-day forward returns predicted from
the trailing 20-day return by nearest neighbours, on noise) scored by naive, purged and embargoed k-fold. NumPy only.
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("overfit", "multitest"):
    sys.path.insert(0, str(ROOT / c))
from firm_multitest import expected_max_sr  # noqa: E402
from firm_overfit import cscv, min_backtest_length, purged_kfold, walk_forward  # noqa: E402

YEAR, YEARS, SEARCH = 252, 25, 20
FAST, SLOW = np.arange(2, 42, 2), np.arange(50, 550, 10)
VOL, TREND_SD, TREND_HL, SEED = 0.01, 0.0006, 120.0, 20


@functools.lru_cache(maxsize=2)
def returns(world: str):
    rng = np.random.default_rng(SEED)
    n = YEARS * YEAR
    eps = VOL * rng.standard_normal(n)
    if world == "noise":
        return eps
    phi = 0.5 ** (1.0 / TREND_HL)
    mu = np.empty(n)
    mu[0] = 0.0
    shocks = TREND_SD * math.sqrt(1 - phi * phi) * rng.standard_normal(n)
    for t in range(1, n):
        mu[t] = phi * mu[t - 1] + shocks[t]
    return mu + eps


def _ma(p, w):
    c = np.cumsum(np.r_[0.0, p])
    out = np.full(len(p), np.nan)
    out[w - 1:] = (c[w:] - c[:-w]) / w
    return out


@functools.lru_cache(maxsize=2)
def systems(world: str):
    """(T, 1000) daily returns of each system: long when the fast average of the price is above the slow one, short
    otherwise, decided at each close and held the next day."""
    r = returns(world)
    p = np.cumsum(r)
    out, params = [], []
    fast = {f: _ma(p, f) for f in FAST}
    for s in SLOW:
        ms = _ma(p, s)
        for f in FAST:
            pos = np.sign(fast[f] - ms)
            out.append(np.r_[0.0, np.nan_to_num(pos[:-1]) * r[1:]])
            params.append((int(f), int(s)))
    return np.column_stack(out), params


def sharpe(x) -> float:
    return float(np.mean(x) / np.std(x) * math.sqrt(YEAR))


def search(world: str):
    M, params = systems(world)
    start, cut = max(SLOW), SEARCH * YEAR
    ins, oos = M[start:cut], M[cut:]
    sr_is = np.array([sharpe(ins[:, j]) for j in range(ins.shape[1])])
    best = int(np.argmax(sr_is))
    c = cscv(ins, 16, max_splits=3000, seed=1)
    years = (cut - start) / YEAR
    var = float(np.var(sr_is))
    return {"best": params[best], "is_best": float(sr_is[best]), "oos_best": sharpe(oos[:, best]),
            "is_median": float(np.median(sr_is)),
            "oos_mean": float(np.mean([sharpe(oos[:, j]) for j in range(M.shape[1])])),
            "pbo": c["pbo"], "slope": c["slope"], "years": years,
            "expected_max_iid": expected_max_sr(M.shape[1], 1.0 / years),
            "expected_max_obs": expected_max_sr(M.shape[1], var),
            "sr_sd": math.sqrt(var)}


def ranking(world: str, top: int = 50):
    """Across the systems: the correlation of in-sample and out-of-sample Sharpe ratios, and the mean out-of-sample
    Sharpe ratio of the `top` best in sample."""
    M, _ = systems(world)
    start, cut = max(SLOW), SEARCH * YEAR
    a = np.array([sharpe(M[start:cut, j]) for j in range(M.shape[1])])
    b = np.array([sharpe(M[cut:, j]) for j in range(M.shape[1])])
    return float(np.corrcoef(a, b)[0, 1]), float(b[np.argsort(-a)[:top]].mean())


def walk_forward_sr(world: str, train_years: int = 5):
    """Each year, choose the system with the best Sharpe ratio over the previous `train_years` and trade it for the
    year: the Sharpe ratio of the stitched out-of-sample returns."""
    M, _ = systems(world)
    start = max(SLOW)
    X = M[start:]
    pieces = []
    for tr, te in walk_forward(len(X), train_years * YEAR, YEAR):
        j = int(np.argmax([sharpe(X[tr, k]) for k in range(X.shape[1])]))
        pieces.append(X[te, j])
    return sharpe(np.concatenate(pieces))


def label_leak(k: int = 5, h: int = 20, neighbours: int = 5, embargo: int = 20, seed: int = 3):
    """R^2 of a nearest-neighbour forecast of the h-day forward return from a feature that moves as slowly as time
    itself (a regime variable; here the day's index, so nearest neighbours are neighbouring days), on noise, under
    shuffled k-fold, contiguous k-fold, purged k-fold, and purged k-fold with an embargo."""
    rng = np.random.default_rng(seed)
    r = VOL * rng.standard_normal(6 * YEAR + h)
    c = np.r_[0.0, np.cumsum(r)]
    idx = np.arange(0, len(r) - h)
    x = idx.astype(float)
    y = c[idx + h] - c[idx]
    start, end = idx, idx + h - 1                                       # the periods each label spans

    def knn_r2(train, test):
        order = np.argsort(x[train])
        xs, ys = x[train][order], y[train][order]
        pred = np.empty(len(test))
        for i, xv in enumerate(x[test]):
            j = np.searchsorted(xs, xv)
            lo, hi = max(0, j - neighbours), min(len(xs), j + neighbours)
            cand = np.arange(lo, hi)
            near = cand[np.argsort(np.abs(xs[cand] - xv))[:neighbours]]
            pred[i] = ys[near].mean()
        return pred

    def score(splits):
        pred = np.empty(len(y))
        for tr, te in splits:
            pred[te] = knn_r2(tr, te)
        return float(1.0 - np.mean((y - pred) ** 2) / np.var(y))
    perm = rng.permutation(len(y))
    shuffled = [(np.setdiff1d(perm, f), f) for f in np.array_split(perm, k)]
    contiguous = [(np.setdiff1d(np.arange(len(y)), f), f) for f in np.array_split(np.arange(len(y)), k)]
    return {"shuffled": score(shuffled), "contiguous": score(contiguous),
            "purged": score(purged_kfold(start, end, k, 0)), "embargoed": score(purged_kfold(start, end, k, embargo))}


def minbtl(n_trials: int = 1000, targets=(0.5, 1.0, 1.8)):
    return {t: min_backtest_length(n_trials, t) for t in targets}


def pbo_hundred(seed: int = 7):
    """Exercise 7: the PBO of the first 100 trend systems (on noise), and of 100 independent noise strategies of the
    same length."""
    M, _ = systems("noise")
    start, cut = max(SLOW), SEARCH * YEAR
    first = cscv(M[start:cut, :100], 16, max_splits=3000, seed=1)["pbo"]
    rng = np.random.default_rng(seed)
    indep = cscv(VOL * rng.standard_normal((cut - start, 100)), 16, max_splits=3000, seed=1)["pbo"]
    return first, indep
