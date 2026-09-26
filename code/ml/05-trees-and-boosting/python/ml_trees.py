"""Trees and boosting (One Quant Book 12, chapter 5).

The forty-characteristic panel with factor risk of chapter 4, smaller (300 stocks, 240 months): single trees of three
depths, a random forest and its out-of-bag score, and gradient-boosted trees; early stopping on a purged validation
block; a random search of 20 configurations whose winner is re-scored on fresh seeds; and, on firm.tape sessions,
boosted trees with and without monotonic constraints on order-book features whose sign microstructure fixes.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("mlsynth", "mlbase", "gbdt", "tape", "intraml"):
    sys.path.insert(0, str(ROOT / c))
from firm_gbdt import DEFAULTS, fit_early_stop, make, plateau_select  # noqa: E402
from firm_mlbase import fit, predict  # noqa: E402
from firm_mlsynth import PanelConfig, ceiling, panel, r2_oos  # noqa: E402

N, T = 300, 240
TRAIN, TEST = np.arange(0, 160), np.arange(160, 240)
FIT, VAL = np.arange(0, 119), np.arange(120, 160)                      # one month purged between them


@functools.lru_cache(maxsize=2)
def data(seed=1):
    return panel(PanelConfig(n=N, months=T, k=40, seed=seed, style_vol=0.02))


def _xy(P, months):
    X = P.X[months].reshape(-1, P.X.shape[2])
    y = (P.r[months] - P.r[months].mean(axis=1, keepdims=True)).reshape(-1)
    return X, y


def _score(model, P, months=TEST):
    return r2_oos(P.r[months], predict(model, P.X, months))


@functools.lru_cache(maxsize=2)
def family(seed=1):
    """Test R-squared (against zero) of single trees, a random forest (with its out-of-bag score) and boosted trees."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.tree import DecisionTreeRegressor

    P = data(seed)
    out = {"ceiling": ceiling(P, TEST)}
    for d in (2, 5, 10):
        out[f"tree_{d}"] = _score(fit(DecisionTreeRegressor(max_depth=d, min_samples_leaf=100, random_state=0),
                                      P.X, P.r, TRAIN), P)
    rf = fit(RandomForestRegressor(n_estimators=40, min_samples_leaf=300, max_features=0.3, oob_score=True,
                                   random_state=0, n_jobs=1), P.X, P.r, TRAIN)
    out["forest"] = _score(rf, P)
    _, y = _xy(P, TRAIN)
    out["forest_oob"] = 1 - np.sum((y - rf.oob_prediction_) ** 2) / np.sum(y**2)
    out["forest_train"] = 1 - np.sum((y - rf.predict(_xy(P, TRAIN)[0])) ** 2) / np.sum(y**2)
    out["boosting"] = _score(fit(make(), P.X, P.r, TRAIN), P)
    return out


@functools.lru_cache(maxsize=2)
def early(seed=1):
    """Early stopping at two learning rates: best number of trees on the validation block, test R-squared there, and
    test R-squared had the fit run to 600 trees."""
    P = data(seed)
    X, y = _xy(P, FIT)
    Xv, yv = _xy(P, VAL)
    out = {}
    for lr in (0.1, 0.01):
        m, best, curve = fit_early_stop({"learning_rate": lr}, X, y, Xv, yv, max_trees=600, patience=600)
        full = make({"learning_rate": lr, "n_estimators": 600}).fit(X, y)
        out[lr] = {"best": best, "curve": curve, "test_best": _score(m, P), "test_full": _score(full, P)}
    return out


def _configs(n, rng):
    return [dict(num_leaves=int(rng.choice([4, 8, 16, 32, 64])),
                 learning_rate=float(rng.choice([0.01, 0.02, 0.05, 0.1])),
                 min_child_samples=int(rng.choice([20, 50, 200, 500, 1000])),
                 n_estimators=int(rng.choice([100, 200, 300])),
                 subsample=float(rng.choice([0.5, 0.7, 1.0])), colsample_bytree=float(rng.choice([0.3, 0.6, 1.0])),
                 reg_lambda=float(rng.choice([0.0, 1.0, 10.0]))) for _ in range(n)]


def _complexity(c):
    return c["num_leaves"] * c["n_estimators"] * c["learning_rate"] / max(c["min_child_samples"], 1) ** 0.5


@functools.lru_cache(maxsize=2)
def tuning(seed=1, n_configs=20, n_seeds=4):
    """Random search on the validation block; the winner and the defaults re-scored with four model seeds, and all on
    the test months."""
    P = data(seed)
    X, y = _xy(P, FIT)
    cfgs = _configs(n_configs, np.random.default_rng(seed + 7))

    def val(c, s=1):
        return _score(make(c, seed=s).fit(X, y), P, VAL)

    scores = np.array([val(c) for c in cfgs])
    b = int(np.argmax(scores))
    best_seeds = np.array([val(cfgs[b], s) for s in range(1, n_seeds + 1)])
    def_seeds = np.array([val({}, s) for s in range(1, n_seeds + 1)])
    sd = float(def_seeds.std(ddof=1))
    plateau = plateau_select(scores, sd, [_complexity(c) for c in cfgs])
    test = {name: _score(make(c).fit(X, y), P) for name, c in (("best", cfgs[b]), ("defaults", {}),
                                                                 ("plateau", cfgs[plateau]))}
    return {"scores": scores, "best": b, "best_config": cfgs[b], "best_seeds": best_seeds, "default_seeds": def_seeds,
            "seed_sd": sd, "within": float(np.mean(np.abs(scores - def_seeds.mean()) <= 2 * sd)),
            "plateau": plateau, "plateau_config": cfgs[plateau], "test": test, "configs": cfgs}


# ------------------------------------------------------------------------------------------------ monotone constraints
POSITIVE = {"imbalance": 1, "ofi_1": 1, "ofi_5": 1, "ofi_30": 1, "flow_5": 1, "flow_30": 1, "micro": 1}


@functools.lru_cache(maxsize=1)
def tape_data(sessions=16, seconds=600, horizon=5):
    from firm_intraml import NAMES, features, targets
    from firm_tape import TapeConfig, simulate

    Xs, ys = [], []
    for s in range(sessions):
        tape = simulate(TapeConfig(seconds=seconds, news_at=None, seed=100 + s))
        times, X, _, _ = features(tape, step=1.0)
        y = targets(tape, times, (horizon,))[horizon]
        ok = ~np.isnan(y)
        Xs.append(X[ok][::horizon])                                    # non-overlapping 5-second labels
        ys.append(y[ok][::horizon])
    return Xs, ys, list(NAMES)


@functools.lru_cache(maxsize=2)
def monotone(n_train=8, ofi5_sign=1):
    """Boosted trees on the first n_train sessions, tested on the rest, with and without monotonic constraints; and the
    share of test rows where raising the order-flow imbalance lowers the unconstrained prediction."""
    Xs, ys, names = tape_data()
    X, y = np.vstack(Xs[:n_train]), np.concatenate(ys[:n_train])
    Xt, yt = np.vstack(Xs[n_train:]), np.concatenate(ys[n_train:])
    params = dict(num_leaves=31, min_child_samples=20, n_estimators=300, learning_rate=0.05)
    free = make(params).fit(X, y)
    mono = make(params, monotone=dict(POSITIVE, ofi_5=ofi5_sign), names=names).fit(X, y)
    j = names.index("ofi_5")
    up = Xt.copy()
    up[:, j] += Xt[:, j].std() * 0.5
    viol = float(np.mean(free.predict(up) < free.predict(Xt) - 1e-12))
    viol_mono = float(np.mean(mono.predict(up) < mono.predict(Xt) - 1e-12))

    def r2(p):
        return 1 - np.sum((yt - p) ** 2) / np.sum((yt - yt.mean()) ** 2)

    return {"free": r2(free.predict(Xt)), "mono": r2(mono.predict(Xt)), "viol": viol, "viol_mono": viol_mono,
            "n_train": len(y), "n_test": len(yt)}


def partial_dependence(feature="ofi_5", n_train=8, grid=21):
    """Average prediction as the feature sweeps its 2nd to 98th percentile, other features at their observed values."""
    Xs, ys, names = tape_data()
    X, y = np.vstack(Xs[:n_train]), np.concatenate(ys[:n_train])
    params = dict(num_leaves=31, min_child_samples=20, n_estimators=300, learning_rate=0.05)
    free = make(params).fit(X, y)
    mono = make(params, monotone=POSITIVE, names=names).fit(X, y)
    j = names.index(feature)
    xs = np.linspace(*np.quantile(X[:, j], [0.02, 0.98]), grid)
    out = []
    for v in xs:
        Z = X.copy()
        Z[:, j] = v
        out.append((v, float(free.predict(Z).mean()), float(mono.predict(Z).mean())))
    return out


def defaults():
    return dict(DEFAULTS)
