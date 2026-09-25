"""firm.overfit -- measuring and preventing backtest overfitting (build of One Quant Book 7, chapter 20).

The probability of backtest overfitting by combinatorially symmetric cross-validation (Bailey, Borwein, Lopez de Prado
and Zhu): the rows of a performance matrix (periods x strategies) are cut into S blocks; for every way of choosing
half of them as the in-sample set, the strategy with the best in-sample Sharpe ratio is ranked among all strategies on
the other half; the PBO is the share of splits where it ranks below the median. Purged k-fold cross-validation with an
embargo for labels that span time, its combinatorial version and its number of paths, walk-forward splits, and the
minimum backtest length for a number of trials. NumPy only (the expected maximum Sharpe ratio is firm.multitest's).

API (stable):
    cscv(M, n_blocks, max_splits, seed)       {'pbo', 'logits', 'is_best', 'oos_of_best', 'slope'} (Sharpe per period)
    purged_kfold(start, end, k, embargo)      [(train, test)]: train drops labels overlapping the test span and the
                                              `embargo` observations after each test block
    cpcv(start, end, n_folds, n_test, embargo) [(train, test)] for every choice of n_test test folds
    cpcv_paths(n_folds, n_test)               number of backtest paths: C(n, k) * k / n
    walk_forward(n, train, test, step, anchored) [(train, test)] in time order
    min_backtest_length(n_trials, sr_target)  years for the expected best of n_trials null strategies (annual Sharpe
                                              variance 1 / years) to stay below sr_target
"""
from __future__ import annotations

import itertools
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "multitest"))
from firm_multitest import expected_max_sr  # noqa: E402


def cscv(M, n_blocks: int = 16, max_splits: int | None = None, seed: int = 0) -> dict:
    """M: (T, N) per-period returns of N strategies. Block sums and sums of squares make every split's in-sample and
    out-of-sample Sharpe ratios matrix products."""
    M = np.asarray(M, float)
    T, N = M.shape
    edges = np.linspace(0, T, n_blocks + 1).astype(int)
    s1 = np.array([M[a:b].sum(axis=0) for a, b in zip(edges[:-1], edges[1:], strict=True)])
    s2 = np.array([(M[a:b] ** 2).sum(axis=0) for a, b in zip(edges[:-1], edges[1:], strict=True)])
    n = np.diff(edges).astype(float)
    combos = [c for c in itertools.combinations(range(n_blocks), n_blocks // 2)]
    if max_splits is not None and len(combos) > max_splits:
        pick = np.random.default_rng(seed).choice(len(combos), max_splits, replace=False)
        combos = [combos[i] for i in sorted(pick)]
    A = np.zeros((len(combos), n_blocks))
    for i, c in enumerate(combos):
        A[i, list(c)] = 1.0

    def sharpe(W):
        cnt = W @ n
        mu = (W @ s1) / cnt[:, None]
        var = (W @ s2) / cnt[:, None] - mu ** 2
        return mu / np.sqrt(np.maximum(var, 1e-300))
    sr_is, sr_oos = sharpe(A), sharpe(1.0 - A)
    best = np.argmax(sr_is, axis=1)
    rows = np.arange(len(combos))
    oos_best = sr_oos[rows, best]
    rank = (sr_oos < oos_best[:, None]).sum(axis=1) + 1                    # 1 = worst ... N = best
    w = rank / (N + 1.0)
    logits = np.log(w / (1.0 - w))
    slope = np.polyfit(sr_is[rows, best], oos_best, 1)[0] if len(combos) > 2 else float("nan")
    return {"pbo": float(np.mean(logits <= 0.0)), "logits": logits, "is_best": sr_is[rows, best],
            "oos_of_best": oos_best, "slope": float(slope)}


def purged_kfold(start, end, k: int = 5, embargo: int = 0) -> list[tuple[np.ndarray, np.ndarray]]:
    """start, end: (n,) index of the first and last period each observation's label uses, observations in time
    order. Test folds are contiguous; a training observation is dropped if its label interval overlaps the test
    fold's span (purging) or it starts within `embargo` periods after the fold's last label (embargo)."""
    start, end = np.asarray(start), np.asarray(end)
    n = len(start)
    out = []
    for f in np.array_split(np.arange(n), k):
        lo, hi = start[f].min(), end[f].max()
        overlap = (end >= lo) & (start <= hi)
        embargoed = (start > hi) & (start <= hi + embargo)
        train = np.flatnonzero(~overlap & ~embargoed)
        out.append((train, f))
    return out


def cpcv(start, end, n_folds: int = 6, n_test: int = 2, embargo: int = 0) -> list[tuple[np.ndarray, np.ndarray]]:
    start, end = np.asarray(start), np.asarray(end)
    folds = np.array_split(np.arange(len(start)), n_folds)
    out = []
    for c in itertools.combinations(range(n_folds), n_test):
        keep = np.ones(len(start), bool)
        test = np.concatenate([folds[j] for j in c])
        for j in c:
            f = folds[j]
            lo, hi = start[f].min(), end[f].max()
            keep &= ~((end >= lo) & (start <= hi)) & ~((start > hi) & (start <= hi + embargo))
        out.append((np.flatnonzero(keep), test))
    return out


def cpcv_paths(n_folds: int, n_test: int) -> int:
    return math.comb(n_folds, n_test) * n_test // n_folds


def walk_forward(n: int, train: int, test: int, step: int | None = None, anchored: bool = False):
    step = step or test
    out, a = [], 0
    while a + train + test <= n:
        tr = np.arange(0 if anchored else a, a + train)
        out.append((tr, np.arange(a + train, a + train + test)))
        a += step
    return out


def min_backtest_length(n_trials: int, sr_target: float) -> float:
    """The smallest number of years y with expected_max_sr(n_trials, 1 / y) <= sr_target: the expected annual
    Sharpe ratio of the best of n_trials strategies with no skill, each measured over y years, falls to the target."""
    lo, hi = 1e-3, 1e4
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if expected_max_sr(n_trials, 1.0 / mid) > sr_target:
            lo = mid
        else:
            hi = mid
    return hi
