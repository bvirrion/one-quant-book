"""Signal combination (One Quant Book 7, chapter 14).

Forty planted signals on the monthly returns of firm.synthmkt (seed 1). The target of each month is a name's next
month market-adjusted return, z-scored across the 704 names listed for all ten years, plus a planted expected return
built from eight latent themes, of which only some carry information. Each signal measures one theme (five signals a
theme) with a noise shared by its theme and a noise of its own of varying size, so the signals are correlated in
groups and of unequal quality. The first five years fit the blends, the last five judge them. NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("combine", "synthmkt"):
    sys.path.insert(0, str(ROOT / c))
from firm_combine import (  # noqa: E402
    blend,
    equal,
    ic_matrix,
    ic_series,
    ic_weights,
    lasso,
    max_icir,
    orth_sequential,
    orth_symmetric,
    ridge,
    stack,
    time_folds,
    toward_equal,
    zscore,
)
from firm_synthmkt import simulate  # noqa: E402

MONTH, THEMES, PER = 21, 8, 5
GAMMA = np.array([0.10, 0.08, 0.06, 0.05, 0.03, 0.0, 0.0, 0.0])    # stable world: information per theme
DRIFT_MEAN, DRIFT_SD, DRIFT_PHI = 0.04, 0.04, 0.97                   # drifting world: AR(1) information per theme
SHARED, SEED = 1.0, 14


@functools.lru_cache(maxsize=2)
def data(world: str = "stable"):
    """X (T, N, 40) signals known at each month-end, y (T, N) next month's target, the themes' information by month
    (T, 8), each signal's theme and own-noise size. Stable: fixed information, three themes useless. Drifting: every
    theme informative on average (0.04) but its information wanders as an AR(1) with a half-life of about two years, and
    every signal has the same noise, so equal weights are right on average and any other weights chase noise."""
    P = simulate()
    full = np.flatnonzero(P.listed.all(axis=0))
    adj = P.ret[:, full] - P.beta[None, full] * P.mkt[:, None]
    T = adj.shape[0] // MONTH - 1
    monthly = np.add.reduceat(adj, np.arange(0, (T + 1) * MONTH, MONTH), axis=0)[1:T + 1]
    eps = zscore(monthly[:, :, None])[:, :, 0]
    rng = np.random.default_rng(SEED)
    N = len(full)
    f = rng.standard_normal((T, N, THEMES))
    g = rng.standard_normal((T, N, THEMES))
    if world == "stable":
        gam = np.tile(GAMMA, (T, 1))
    else:
        u = np.empty((T, THEMES))
        u[0] = rng.standard_normal(THEMES)
        for t in range(1, T):
            u[t] = DRIFT_PHI * u[t - 1] + np.sqrt(1 - DRIFT_PHI ** 2) * rng.standard_normal(THEMES)
        gam = DRIFT_MEAN + DRIFT_SD * u
    y = eps + np.einsum("tnj,tj->tn", f, gam)
    if world == "stable":                                                             # quality varies within a theme
        own = np.repeat(np.linspace(1.0, 4.0, PER)[None, :], THEMES, axis=0).ravel()
    else:                                                                             # every signal alike
        own = np.full(THEMES * PER, 2.5)
    theme = np.repeat(np.arange(THEMES), PER)
    X = f[:, :, theme] + SHARED * g[:, :, theme] + own * rng.standard_normal((T, N, THEMES * PER))
    return X, y, gam, theme, own


def split(world: str = "stable"):
    X, y, *_ = data(world)
    h = X.shape[0] // 2
    return X[:h], y[:h], X[h:], y[h:]


def mean_ic(F, y) -> float:
    return float(np.mean(ic_series(F, y)))


def results(world: str = "stable", alphas=(0.0, 0.1, 1.0), shrinks=(0.0, 0.5, 0.9, 1.0),
            lams=(0.0, 0.25, 0.5, 0.75, 1.0)):
    """In-sample and out-of-sample mean IC of each blend fitted on the first five years."""
    Xi, yi, Xo, yo = split(world)
    ic_in = ic_matrix(Xi, yi)
    fit = lambda w: (mean_ic(blend(Xi, w), yi), mean_ic(blend(Xo, w), yo))  # noqa: E731
    out = {"signal_ic_in": ic_in.mean(axis=0), "signal_ic": ic_matrix(Xo, yo).mean(axis=0),
           "equal": (mean_ic(equal(Xi), yi), mean_ic(equal(Xo), yo)), "ic_weighted": fit(ic_weights(ic_in))}
    out["max_icir"] = {s: fit(max_icir(ic_in, s)) for s in shrinks}
    out["ridge"] = {a: fit(ridge(Xi, yi, a)) for a in alphas}
    b = lasso(Xi, yi, 0.002)
    out["lasso"] = (*fit(b), int((b != 0).sum()))
    wr = ridge(Xi, yi, 0.0)
    out["toward_equal"] = {lam: fit(toward_equal(wr, lam)) for lam in lams}
    X, y, gam, theme, own = data(world)
    h = X.shape[0] // 2
    bases = [lambda tr: equal(X), lambda tr: blend(X, ic_weights(ic_matrix(X[tr], y[tr]))),
             lambda tr: blend(X, ridge(X[tr], y[tr], 0.0))]
    ws = stack(bases, y[:h], time_folds(h, 4))
    comp = sum(wk * zscore(p(np.arange(h))) for wk, p in zip(ws, bases, strict=True))
    out["stack"] = (ws, mean_ic(comp[:h], yi), mean_ic(comp[h:], yo))
    oracle = [ic_series(blend(X[t:t + 1], gam[t][theme] / (1.0 + SHARED ** 2 + own ** 2)), y[t:t + 1])[0]
              for t in range(h, X.shape[0])]
    out["oracle"] = float(np.mean(oracle))
    return out


LAMS = tuple(float(x) for x in np.round(np.linspace(0, 1, 11), 1))


def small_universe(world: str, window: int, n_names: int = 100, lams=LAMS, seed=0):
    """A universe of n_names names: blends fitted on the last `window` months of the first half, judged on the
    second half. Out-of-sample IC of equal weights, IC weights, and ridge (no penalty) shrunk toward equal weights by
    each lambda."""
    X, y, *_ = data(world)
    h = X.shape[0] // 2
    names = np.random.default_rng(seed).choice(X.shape[1], n_names, replace=False)
    Xi, yi, Xo, yo = X[h - window:h][:, names], y[h - window:h][:, names], X[h:][:, names], y[h:][:, names]
    wr = ridge(Xi, yi, 0.0)
    return {"equal": mean_ic(equal(Xo), yo), "ic_weighted": mean_ic(blend(Xo, ic_weights(ic_matrix(Xi, yi))), yo),
            "shrunk": {lam: mean_ic(blend(Xo, toward_equal(wr, lam)), yo) for lam in lams}}


def orthogonalised(world: str = "stable"):
    """Out-of-sample IC of equal weights on the raw signals and on the signals orthogonalised within each month,
    sequentially (in the order of the in-sample IC, best first) and symmetrically."""
    Xi, yi, Xo, yo = split(world)
    order = np.argsort(-ic_matrix(Xi, yi).mean(axis=0))
    seq = np.stack([orth_sequential(Xo[t][:, order]) for t in range(len(Xo))])
    sym = np.stack([orth_symmetric(Xo[t]) for t in range(len(Xo))])
    corr = np.mean([np.corrcoef(Xo[0][:, k], sym[0][:, k])[0, 1] for k in range(Xo.shape[2])])
    return {"raw": mean_ic(equal(Xo), yo), "sequential": mean_ic(equal(seq), yo), "symmetric": mean_ic(equal(sym), yo),
            "sym_corr": float(corr)}


def geometry(world: str = "stable", ks=(1, 2, 3, 5, 8, 10, 15, 20, 30, 40), perms: int = 100, seed: int = 1):
    """Out-of-sample IC of the equal-weight blend of K signals taken in random order (mean over permutations), and
    the value K ic / sqrt(K + K (K - 1) c) from the signals' mean IC and mean pairwise correlation."""
    _, _, Xo, yo = split(world)
    ic = ic_matrix(Xo, yo).mean(axis=0)
    C = np.mean([np.corrcoef(Xo[t].T) for t in range(0, len(Xo), 6)], axis=0)
    K = Xo.shape[2]
    cbar = (C.sum() - K) / (K * (K - 1))
    rng = np.random.default_rng(seed)
    orders = [rng.permutation(K) for _ in range(perms)]
    measured = {k: float(np.mean([mean_ic(equal(Xo[:, :, o[:k]]), yo) for o in orders])) for k in ks}
    theory = {k: float(k * ic.mean() / np.sqrt(k + k * (k - 1) * cbar)) for k in ks}
    return measured, theory, float(ic.mean()), float(cbar)
