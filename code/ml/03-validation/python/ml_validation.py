"""Validation (One Quant Book 12, chapter 3).

A world where nothing is predictable at decision time: firm.mlsynth's panel with a ceiling of zero (300 stocks, 20 years
of months, twenty characteristics that carry nothing), plus quarterly earnings announcements whose surprise moves the
announcing month's return. Every positive out-of-sample R-squared is therefore fake. Five leaks are planted in an
otherwise careful pipeline (gradient-boosted trees, temporal split or purged folds): a period-end join of the surprise,
shuffled folds on overlapping three-month labels, target encoding, a full-sample statistic of the target, and choosing
among configurations by their test score. Each is measured and caught by a detector of firm.cvsplit; flat and nested
hyperparameter searches are compared.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("mlsynth", "cvsplit", "overfit"):
    sys.path.insert(0, str(ROOT / c))
from firm_cvsplit import (  # noqa: E402
    PurgedKFold,
    adversarial_validation,
    canary,
    fold_overlap,
    nested_cv,
    truncation_test,
)
from firm_mlsynth import PanelConfig, panel, r2_oos  # noqa: E402

N, MONTHS, CUT = 200, 240, 160
ANN = 0.02                      # announcement return per unit of surprise


@functools.lru_cache(maxsize=4)
def world(seed=1, ann=ANN):
    P = panel(PanelConfig(n=N, months=MONTHS, seed=seed, ceiling=0.0))
    rng = np.random.default_rng(seed + 100)
    s = rng.standard_normal((MONTHS + 1, N))                           # surprise of the quarter ending at month t
    ends = (np.arange(MONTHS + 1)[:, None] % 3) == (np.arange(N)[None, :] % 3)
    s = np.where(ends, s, np.nan)
    r = P.r.copy()
    # r[t] is the return of month t + 1; the quarter ending at month t is announced (filed) during month t + 1
    r += ann * np.nan_to_num(s[:MONTHS])
    return {"P": P, "X": P.X, "r": r, "s": s, "industry": P.industry}


def _ffill(a):
    out = a.copy()
    for t in range(1, len(out)):
        m = np.isnan(out[t])
        out[t, m] = out[t - 1, m]
    return np.nan_to_num(out)


def surprise_known(s, join="filing"):
    """Row t: the latest surprise as the pipeline sees it at the end of month t. 'filing' uses the quarters filed by
    then (ended the month before or earlier); 'period' joins by the fiscal period's end, so the quarter ending at t
    appears at t although it is filed during t + 1."""
    if join == "period":
        return _ffill(s)
    shifted = np.full_like(s, np.nan)
    shifted[1:] = s[:-1]                                                # filed one month after the period ends
    return _ffill(shifted)


def surprise_feature(s, join="filing"):
    """Two features per stock-month: the latest surprise (by the join rule) and the months since the fiscal quarter
    ended (0, 1, 2), which is known from the calendar."""
    f = surprise_known(s, join)[:-1]
    age = (np.arange(MONTHS)[:, None] - np.arange(N)[None, :] % 3) % 3
    return np.stack([f, age.astype(float)], axis=-1)


def xs(y):
    return y - y.mean(axis=1, keepdims=True)


def gbm(seed=1, **kw):
    import lightgbm as lgb

    p = dict(n_estimators=200, learning_rate=0.03, num_leaves=15, min_child_samples=200, subsample=0.7,
             subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=1, deterministic=True, force_row_wise=True,
             seed=seed)
    p.update(kw)
    return lgb.LGBMRegressor(**p)


def temporal_score(F, r, target=None, model=None):
    """Train on months < CUT (target: cross-sectionally demeaned r), score R-squared against zero on months >= CUT."""
    T = r.shape[0]
    y = xs(r) if target is None else target
    tr, te = np.arange(0, CUT - 1), np.arange(CUT, T)                  # one month purged: r[t] ends at month t + 1
    Xtr, Xte = F[tr].reshape(-1, F.shape[-1]), F[te].reshape(-1, F.shape[-1])
    m = (model or gbm()).fit(Xtr, y[tr].reshape(-1))
    return r2_oos(r[te].reshape(-1), m.predict(Xte))


def with_feature(X, f):
    return np.concatenate([X, f if f.ndim == 3 else f[..., None]], axis=-1)


def announcement_effect(ann, seed=1):
    """The period-end and filing-date pipelines' R-squared for another announcement effect."""
    w = world(seed, ann)
    return tuple(temporal_score(with_feature(w["X"], surprise_feature(w["s"], j)), w["r"])
                 for j in ("period", "filing"))


def target_encoding(r, industry):
    """The industry's mean demeaned return in the same month, computed on all rows: a feature made of the target."""
    y = xs(r)
    te = np.zeros_like(y)
    for k in range(industry.max() + 1):
        m = industry == k
        te[:, m] = y[:, m].mean(axis=1, keepdims=True)
    return te


@functools.lru_cache(maxsize=10)
def _candidates(chunk, seed=1000):
    """100 noise candidate features (months x stocks x 100), float32; ten chunks make the 1,000 candidates."""
    return np.random.default_rng(seed + chunk).standard_normal((MONTHS, N, 100)).astype(np.float32)


def monthly_ic(y, chunks=10):
    """(T, 1000) cross-sectional correlation of every candidate with the target, month by month."""
    T = len(y)
    ym = y - y.mean(axis=1, keepdims=True)
    out = []
    for ch in range(chunks):
        C = _candidates(ch)[:T]
        Cm = C - C.mean(axis=1, keepdims=True)
        out.append((Cm * ym[..., None]).sum(axis=1) / np.sqrt((Cm**2).sum(axis=1) * (ym**2).sum(axis=1)[:, None]))
    return np.concatenate(out, axis=1)


def screened(r, months=None, keep=10, ic=None):
    """Screen the 1,000 noise candidates by their average monthly information coefficient with the demeaned target
    over `months` (default: every month of r) and return the best `keep`, sign-aligned, for every month of r. `ic`
    may pass a precomputed monthly_ic whose first len(r) rows belong to r."""
    T = len(r)
    ic = monthly_ic(xs(r)) if ic is None else ic[:T]
    months = np.arange(T) if months is None else months
    avg = ic[months].mean(axis=0)
    best = np.argsort(-np.abs(avg))[:keep]
    return np.stack([np.sign(avg[j]) * _candidates(j // 100)[:T, :, j % 100] for j in best], axis=-1).astype(float)


def ridge(alpha=1000.0):
    from sklearn.linear_model import Ridge

    return Ridge(alpha=alpha)


@functools.lru_cache(maxsize=2)
def leaks(seed=1):
    """Out-of-sample R-squared of the clean pipeline and of each planted leak (with its clean counterpart)."""
    w = world(seed)
    X, r, s = w["X"], w["r"], w["s"]
    out = {"clean": temporal_score(with_feature(X, surprise_feature(s, "filing")), r)}
    out["period_join"] = temporal_score(with_feature(X, surprise_feature(s, "period")), r)
    out["target_encoding"] = temporal_score(with_feature(X, target_encoding(r, w["industry"])), r)
    out["screening"] = temporal_score(screened(r), r, model=ridge())
    out["screening_clean"] = temporal_score(screened(r, np.arange(0, CUT - 1)), r, model=ridge())
    out["overlap_shuffled"], out["overlap_purged"] = overlap_cv(seed)
    sel = selection(seed)
    out["selection_best"], out["selection_fresh"], out["selection_median"] = (sel["best_on_test"], sel["fresh"],
                                                                                sel["median"])
    return out


def _panel_rows(F, y3, months):
    Xr = F[months].reshape(-1, F.shape[-1])
    yr = y3[months].reshape(-1)
    t0 = np.repeat(months, F.shape[1])
    return Xr, yr, t0


@functools.lru_cache(maxsize=2)
def overlap_cv(seed=1, k=4):
    """Three-month labels sampled monthly (they overlap in two months), predicted from the characteristics by a
    flexible model (deep trees): 4-fold cross-validation with shuffled rows, and purged 4-fold."""
    from sklearn.model_selection import KFold

    w = world(seed)
    y = xs(w["r"])
    y3 = y[:-2] + y[1:-1] + y[2:]
    months = np.arange(0, MONTHS - 2)
    Xr, yr, t0 = _panel_rows(w["X"], y3, months)
    scores = []
    for splitter in (KFold(k, shuffle=True, random_state=0), PurgedKFold(t0, t0 + 2, k, embargo=1)):
        pred = np.zeros(len(yr))
        for a, b in splitter.split(Xr):
            m = gbm(num_leaves=255, min_child_samples=3, n_estimators=60, learning_rate=0.08, subsample=1.0,
                    colsample_bytree=1.0).fit(Xr[a], yr[a])
            pred[b] = m.predict(Xr[b])
        scores.append(r2_oos(yr, pred))
    return tuple(scores)


def overlap_detectors(seed=1, k=5):
    """fold_overlap for the shuffled and purged splits (first fold), and adversarial validation of the first half of
    the months against the second half."""
    from sklearn.model_selection import KFold

    w = world(seed)
    months = np.arange(0, MONTHS - 2)
    t0 = np.repeat(months, N)
    t1 = t0 + 2
    order = np.argsort(t0, kind="stable")
    sh = next(KFold(k, shuffle=True, random_state=0).split(t0))
    # a shuffled fold's "span" is the whole sample: count training labels sharing a month with a test label
    test_months = set(t0[sh[1]])
    shuffled_overlap = int(np.sum(np.isin(t0[sh[0]], list(test_months))))
    pk = next(iter(PurgedKFold(t0[order], t1[order], k, embargo=1).split()))
    purged_overlap = fold_overlap(t0[order], t1[order], pk[0], pk[1])
    half = MONTHS // 2
    auc = adversarial_validation(w["X"][:half].reshape(-1, 20)[::2], w["X"][half:].reshape(-1, 20)[::2])
    return {"shuffled": shuffled_overlap, "purged": purged_overlap, "adversarial_auc": auc}


SEL_CONFIG = dict(num_leaves=16, min_child_samples=50, n_estimators=150, learning_rate=0.05, colsample_bytree=0.5)


@functools.lru_cache(maxsize=2)
def selection(seed=1, n_seeds=30):
    """Thirty runs of one configuration that differ only by their random seed. Choose the run with the best score on
    months 160-199 (the 'test' set used for selection), then score it on months 200-239 (never touched)."""
    w = world(seed)
    X = with_feature(w["X"], surprise_feature(w["s"], "filing"))
    r = w["r"]
    y = xs(r)
    tr, sel, fresh = np.arange(0, 159), np.arange(160, 199), np.arange(200, MONTHS)
    Xtr = X[tr].reshape(-1, X.shape[-1])
    scores, fresh_scores = [], []
    for k in range(n_seeds):
        m = gbm(seed=k + 1, **SEL_CONFIG).fit(Xtr, y[tr].reshape(-1))
        scores.append(r2_oos(r[sel].reshape(-1), m.predict(X[sel].reshape(-1, X.shape[-1]))))
        fresh_scores.append(r2_oos(r[fresh].reshape(-1), m.predict(X[fresh].reshape(-1, X.shape[-1]))))
    b = int(np.argmax(scores))
    return {"scores": np.array(scores), "fresh_scores": np.array(fresh_scores), "best_on_test": float(scores[b]),
            "fresh": float(fresh_scores[b]), "median": float(np.median(scores)),
            "fresh_median": float(np.median(fresh_scores))}


@functools.lru_cache(maxsize=2)
def detectors(seed=1):
    """Which detector flags which leak: the truncation test (features recomputed on the data known at a date), and
    the canary (the pipeline run on noise targets with the real target's structure)."""
    w = world(seed)
    s, r = w["s"], w["r"]
    # knowledge-time layout: row t holds the surprises filed during month t (quarter ended at t - 1)
    filed = np.full_like(s, np.nan)
    filed[1:] = s[:-1]
    checks = range(40, 200, 40)
    ic_full = monthly_ic(xs(r))
    out = {"trunc_period": truncation_test(lambda d: _ffill(np.vstack([d[1:], np.full((1, N), np.nan)])), filed,
                                           checks),
           "trunc_filing": truncation_test(lambda d: _ffill(d), filed, checks),
           "trunc_screening": truncation_test(lambda d: screened(d, ic=ic_full), r, checks)}

    def noise(rng):
        return w["P"].cfg.spec_vol * rng.standard_normal(r.shape)

    out["canary_te"] = canary(lambda y: temporal_score(with_feature(w["X"], target_encoding(y, w["industry"])), y),
                              noise, reps=2)
    out["canary_screening"] = canary(lambda y: temporal_score(screened(y), y, model=ridge()), noise, reps=2)
    out["canary_period"] = canary(lambda y: temporal_score(with_feature(w["X"], surprise_feature(s, "period")), y),
                                  noise, reps=2)
    return out


@functools.lru_cache(maxsize=2)
def nested(seed=1, n_seeds=6):
    """Flat against nested search over six seeds of one configuration (nothing is predictable, so any difference
    between the candidates is noise): the flat search's best mean score over the outer folds against the nested
    estimate."""
    w = world(seed)
    months = np.arange(0, 180, 2)                                      # every other month: labels do not overlap
    Xr = w["X"][months].reshape(-1, 20)
    yr = xs(w["r"])[months].reshape(-1)
    t0 = np.repeat(months, N)

    def inner(tr):
        return PurgedKFold(t0[tr], t0[tr], 3)

    grid = {"seed": list(range(1, n_seeds + 1))}
    res = nested_cv(lambda **c: gbm(**dict(SEL_CONFIG, n_estimators=100), **c), grid, Xr, yr,
                    PurgedKFold(t0, t0, 3), inner, r2_oos)
    return {"flat_best": res["flat_best"], "nested": float(res["outer_scores"].mean()),
            "flat_median": float(np.median(res["flat_scores"])), "chosen": [c["seed"] for c in res["chosen"]]}
