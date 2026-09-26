"""Targets, labels and sample weights (One Quant Book 12, chapter 2).

Twenty synthetic assets, ten years of daily returns with GARCH volatility and a planted persistent drift
(firm.mlsynth.series). An event every day for every asset; ten-day fixed-horizon labels and triple-barrier labels with
barriers at one ten-day volatility; the primary trade is long when the noisy drift reading is positive and short
otherwise. What the fixed-horizon label says about that trade; how much the labels overlap; bagged trees trained with
plain bootstrap samples, with samples as small as the average uniqueness, and with uniqueness weights; the sequential
bootstrap's effect on the uniqueness of a sample; and meta-labelling the primary trade with gradient-boosted trees.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("mlsynth", "labeling"):
    sys.path.insert(0, str(ROOT / c))
from firm_labeling import (  # noqa: E402
    average_uniqueness,
    concurrency,
    fixed_horizon,
    meta_labels,
    sequential_bootstrap,
    triple_barrier,
    vol_widths,
)
from firm_mlsynth import SeriesConfig, series  # noqa: E402

H, WARM, SPLIT = 10, 60, 0.6


@functools.lru_cache(maxsize=4)
def events(seed=1, k=1.0):
    """Per asset: event days, fixed-horizon and triple-barrier outcomes of the primary trade, features, uniqueness."""
    s = series(SeriesConfig(seed=seed))
    r, sig, F = s["r"], s["sigma"], s["F"]
    T, A = r.shape
    t0 = np.arange(WARM, T - H - 1)
    rows = []
    for a in range(A):
        side = np.where(F[t0, a, 0] > 0, 1, -1)
        fh = fixed_horizon(r[:, a], t0, H)
        w = vol_widths(sig[:, a], t0 + 1, H, k)                        # sigma of day t0 + 1 is known at t0's close
        tb = triple_barrier(r[:, a], t0, w, w, H, side=side)
        rows.append(dict(asset=np.full(len(t0), a), t0=t0, side=side, fh_t1=fh["t1"], fh_ret=fh["ret"],
                         fh_label=fh["label"], tb_t1=tb["t1"], tb_ret=tb["ret"], tb_label=tb["label"], hit=tb["hit"],
                         width=w, X=F[t0, a, :], fh_u=average_uniqueness(t0, fh["t1"], T),
                         tb_u=average_uniqueness(t0, tb["t1"], T)))
    out = {k2: np.concatenate([row[k2] for row in rows]) for k2 in rows[0]}
    out["T"] = T
    return out


def label_stats(seed=1, k=1.0):
    e = events(seed, k)
    trade_fh = e["side"] * e["fh_ret"]
    stopped = e["hit"] == "down"
    return {"n": len(e["t0"]), "fh_conc": float(concurrency(e["t0"][e["asset"] == 0], e["fh_t1"][e["asset"] == 0],
                                                              e["T"])[WARM + H:-H].mean()),
            "fh_u": float(e["fh_u"].mean()), "tb_u": float(e["tb_u"].mean()),
            "fh_eff": float(e["fh_u"].sum()), "tb_eff": float(e["tb_u"].sum()),
            "stopped": float(stopped.mean()), "stopped_then_up": float((trade_fh[stopped] > 0).mean()),
            "profit_hit": float((e["hit"] == "up").mean()), "time_hit": float((e["hit"] == "time").mean()),
            "disagree": float((np.sign(trade_fh) != e["tb_label"]).mean()),
            "tb_len": float((e["tb_t1"] - e["t0"]).mean()),
            "t_naive": _t(e["side"] * e["tb_ret"] / e["width"], len(e["t0"])),
            "t_adjusted": _t(e["side"] * e["tb_ret"] / e["width"], e["tb_u"].sum())}


def _t(x, n):
    return float(x.mean() / x.std() * np.sqrt(n))


def _split(e):
    cut = e["t0"].min() + int(SPLIT * (e["t0"].max() - e["t0"].min()))
    train = e["t0"] + H < cut                                          # purged: train labels end before the cut
    test = e["t0"] > cut
    return train, test


def _bag(X, y, w, mode, seed, n_trees=30, u_mean=None):
    from sklearn.tree import DecisionTreeClassifier

    rng = np.random.default_rng(seed)
    n = len(y)
    trees = []
    for _ in range(n_trees):
        size = n if mode == "plain" else int(round(u_mean * n))
        idx = rng.integers(0, n, size)
        t = DecisionTreeClassifier(min_samples_leaf=50 if mode == "plain" else max(5, int(50 * u_mean)),
                                   max_features=0.6, random_state=int(rng.integers(1 << 30)))
        t.fit(X[idx], y[idx], sample_weight=None if w is None else w[idx])
        trees.append(t)
    return trees


def _proba(trees, X):
    return np.mean([t.predict_proba(X)[:, 1] for t in trees], axis=0)


@functools.lru_cache(maxsize=16)
def bagging(seed=1, mode="plain", model_seed=0):
    """Out-of-sample AUC of bagged trees predicting the fixed-horizon label's sign from the features: plain bootstrap
    ("plain"), samples of size average uniqueness x n ("small"), or small samples weighted by uniqueness
    ("weighted")."""
    from sklearn.metrics import roc_auc_score

    e = events(seed)
    train, test = _split(e)
    X, y = e["X"][train], (e["fh_ret"][train] > 0).astype(int)
    u = e["fh_u"][train]
    trees = _bag(X, y, u / u.mean() if mode == "weighted" else None, mode, model_seed, u_mean=float(u.mean()))
    p = _proba(trees, e["X"][test])
    return float(roc_auc_score((e["fh_ret"][test] > 0).astype(int), p))


def bagging_table(seeds=(1, 2, 3)):
    rows = {m: np.array([bagging(s, m) for s in seeds]) for m in ("plain", "small", "weighted")}
    return rows


@functools.lru_cache(maxsize=2)
def bootstrap_uniqueness(n_labels=400, draws=40, reps=50, seed=5):
    """Average uniqueness of a sample drawn by the plain bootstrap and by the sequential bootstrap, on the first
    n_labels ten-day labels of one asset."""
    e = events(1)
    t0, t1 = e["t0"][:n_labels], e["fh_t1"][:n_labels]
    n = int(t1.max()) + 2
    rng = np.random.default_rng(seed)

    def uniq(idx):
        return float(average_uniqueness(t0[idx], t1[idx], n).mean())

    plain = [uniq(rng.integers(0, n_labels, draws)) for _ in range(reps)]
    seq = [uniq(sequential_bootstrap(t0, t1, n, draws, rng)) for _ in range(reps)]
    return float(np.mean(plain)), float(np.mean(seq))


@functools.lru_cache(maxsize=8)
def meta(seed=1, threshold=0.52):
    """Meta-label the primary trade: gradient-boosted trees estimate the probability that it hits its profit barrier
    first or ends positive; trade only above the threshold. Per-trade results out of sample, in units of the barrier
    width (one ten-day volatility)."""
    import lightgbm as lgb

    e = events(seed)
    train, test = _split(e)
    y = meta_labels(e["side"], e["tb_ret"])
    Z = np.column_stack([e["X"], e["side"] * e["X"][:, 0]])
    m = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.03, num_leaves=8, min_child_samples=400,
                           subsample=0.5, subsample_freq=1, verbose=-1, n_jobs=1, deterministic=True,
                           force_row_wise=True, seed=1)
    m.fit(Z[train], y[train], sample_weight=e["tb_u"][train] / e["tb_u"][train].mean())
    p = m.predict_proba(Z[test])[:, 1]
    pnl = (e["side"] * e["tb_ret"] / e["width"])[test]
    take = p > threshold
    u = e["tb_u"][test]

    def stats(mask):
        x = pnl[mask]
        neff = u[mask].sum()                                            # overlap-adjusted number of trades
        return {"share": float(mask.mean()), "hit": float((x > 0).mean()), "mean": float(x.mean()),
                "t": float(x.mean() / x.std() * np.sqrt(neff))}

    return {"primary": stats(np.ones(len(pnl), bool)), "meta": stats(take), "p_mean": float(p.mean())}
