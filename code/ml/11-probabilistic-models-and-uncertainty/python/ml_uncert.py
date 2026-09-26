"""Probabilistic models and uncertainty (One Quant Book 12, chapter 11).

Twenty synthetic assets, ten years of daily returns with GARCH volatility, Student-t shocks and a planted drift
(firm.mlsynth.series), with a volatility regime from day 2,100 on (every shock 1.6 times larger). The target is the next
day's return; the features are the drift reading, 5- and 20-day returns, the volatility ratio and an EWMA volatility.
Training days 60-1511, calibration days 1512-1763, test days 1764-2518. Quantile gradient boosting, a Gaussian network
(five seeds, an ensemble) and a two-component mixture density network, scored by the pinball loss, the CRPS and interval
coverage before and after the regime change; split and adaptive conformal intervals; and positions sized by the mean
forecast against the mean over the predicted variance.
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("mlsynth", "uncert", "gbdt"):
    sys.path.insert(0, str(ROOT / c))
from firm_gbdt import make  # noqa: E402
from firm_mlsynth import SeriesConfig, series  # noqa: E402
from firm_uncert import (  # noqa: E402
    MDN,
    GaussNet,
    adaptive_conformal,
    coverage,
    crps_quantiles,
    ensemble_split,
    fit_nll,
    mdn_quantile,
    pinball,
    predict_gauss,
    predict_mdn,
    split_conformal,
)

BREAK = 2100
TRAIN, CAL, TEST = np.arange(60, 1512), np.arange(1512, 1764), np.arange(1764, 2519)
ALPHAS = tuple(round(0.05 * k, 2) for k in range(1, 20))


@functools.lru_cache(maxsize=5)
def data(seed=1, days=2520, brk=BREAK):
    s = series(SeriesConfig(seed=seed, days=days, vol_break=brk, vol_mult=1.6 if brk else 1.0))
    r = s["r"]
    T, A = r.shape
    ew = np.zeros((T, A))
    v = np.full(A, r[:20].var(axis=0))
    for t in range(T):                                                   # EWMA variance, known at the close of t
        v = 0.94 * v + 0.06 * r[t] ** 2
        ew[t] = v
    F = np.concatenate([s["F"][:, :, :4], np.log(np.sqrt(ew))[:, :, None]], axis=-1)
    y = np.full((T, A), np.nan)
    y[:-1] = r[1:]
    sig_next = np.full((T, A), np.nan)
    sig_next[:-1] = s["sigma"][1:]
    return {"F": F, "y": y, "mu": s["drift"], "sig": sig_next, "day": np.arange(T)}


def _xy(days):
    d = data()
    return d["F"][days].reshape(-1, 5), d["y"][days].reshape(-1)


def _day(days):
    return np.repeat(days, data()["F"].shape[1])


@functools.lru_cache(maxsize=1)
def quantile_gbm():
    X, y = _xy(TRAIN)
    Xt, _ = _xy(TEST)
    Xc, _ = _xy(CAL)
    params = dict(num_leaves=8, n_estimators=200, learning_rate=0.03, min_child_samples=300)
    out = {}
    for a in ALPHAS:
        m = make(dict(params, objective="quantile", alpha=a)).fit(X, y)
        out[a] = (m.predict(Xc), m.predict(Xt))
    mean = make(params).fit(X, y)
    return {"cal": np.stack([out[a][0] for a in ALPHAS], 1), "test": np.stack([out[a][1] for a in ALPHAS], 1),
            "mean_cal": mean.predict(Xc), "mean_test": mean.predict(Xt)}


@functools.lru_cache(maxsize=8)
def gauss(seed):
    X, y = _xy(TRAIN)
    Xv, yv = _xy(CAL)
    net = fit_nll(GaussNet(5), _std(X), y, _std(Xv), yv, seed=seed)
    return predict_gauss(net, _std(Xv)), predict_gauss(net, _std(_xy(TEST)[0]))


@functools.lru_cache(maxsize=1)
def mdn(seed=1):
    X, y = _xy(TRAIN)
    Xv, yv = _xy(CAL)
    net = fit_nll(MDN(5, K=2), _std(X), y, _std(Xv), yv, seed=seed)
    return predict_mdn(net, _std(_xy(TEST)[0]))


@functools.lru_cache(maxsize=1)
def _moments():
    X, _ = _xy(TRAIN)
    return X.mean(axis=0), X.std(axis=0)


def _std(X):
    m, s = _moments()
    return ((X - m) / s).astype(np.float32)


def ensemble(n=5):
    cal = [gauss(s)[0] for s in range(1, n + 1)]
    test = [gauss(s)[1] for s in range(1, n + 1)]
    return (ensemble_split([c[0] for c in cal], [c[1] for c in cal]),
            ensemble_split([t[0] for t in test], [t[1] for t in test]))


def _gauss_q(mu, var):
    from scipy.stats import norm

    return mu[:, None] + np.sqrt(var)[:, None] * norm.ppf(np.asarray(ALPHAS))[None, :]


@functools.lru_cache(maxsize=1)
def scores():
    """Pinball (5% and 95%), CRPS and 90% coverage on the test days before and after the break."""
    _, y = _xy(TEST)
    day = _day(TEST)
    d = data()
    truth_mu, truth_sig = d["mu"][TEST].reshape(-1), d["sig"][TEST].reshape(-1)
    (_, _, _), (em, ea, ee) = ensemble()
    w, m, s = mdn()
    mdn_q = np.stack([mdn_quantile(w, m, s, a) for a in ALPHAS], 1)
    models = {"boosted quantiles": quantile_gbm()["test"], "Gaussian network": _gauss_q(*_single()),
              "ensemble of 5": _gauss_q(em, ea + ee), "mixture density": mdn_q,
              "truth (Gaussian)": _gauss_q(truth_mu, truth_sig**2)}
    out = {}
    i5, i95 = ALPHAS.index(0.05), ALPHAS.index(0.95)
    for name, Q in models.items():
        row = {}
        for tag, mask in (("before", day < BREAK), ("after", day >= BREAK)):
            row[tag] = {"crps": crps_quantiles(y[mask], Q[mask], ALPHAS),
                        "pin05": pinball(y[mask], Q[mask, i5], 0.05), "pin95": pinball(y[mask], Q[mask, i95], 0.95),
                        "cov90": coverage(y[mask], Q[mask, i5], Q[mask, i95])}
        out[name] = row
    out["epistemic_share"] = float(np.mean(ee) / np.mean(ea + ee))
    return out


def _single():
    (_, _), (mu, sig) = gauss(1)
    return mu, sig**2


@functools.lru_cache(maxsize=1)
def conformal(alpha=0.1, gamma=0.005):
    """Intervals around the boosted mean forecast: split conformal on the calibration year with raw and with
    volatility-normalised scores, and adaptive conformal (normalised scores) run through the test days."""
    qg = quantile_gbm()
    _, yc = _xy(CAL)
    _, y = _xy(TEST)
    day = _day(TEST)
    (cm, ca, ce), (tm, ta, te) = ensemble()
    sc, st = np.sqrt(ca + ce), np.sqrt(ta + te)
    raw_c, raw_t = np.abs(yc - qg["mean_cal"]), np.abs(y - qg["mean_test"])
    nrm_c, nrm_t = raw_c / sc, raw_t / st
    q_raw, q_nrm = split_conformal(raw_c, alpha), split_conformal(nrm_c, alpha)
    th, err = adaptive_conformal(nrm_t, alpha, gamma, window=5000, start=nrm_c)
    out = {}
    for tag, mask in (("before", day < BREAK), ("after", day >= BREAK)):
        out[tag] = {"raw": float(np.mean(raw_t[mask] <= q_raw)), "normalised": float(np.mean(nrm_t[mask] <= q_nrm)),
                    "adaptive": float(1 - err[mask].mean())}
    out["last_quarter_after"] = float(1 - err[day >= BREAK + 300].mean())
    out["q_raw"], out["q_nrm"] = q_raw, q_nrm
    out["band"] = {"mean": qg["mean_test"], "sigma": st, "adaptive_threshold": th, "y": y, "day": day}
    return out


def _net_variance(d):
    """A Gaussian network trained on days 60-1511 of a series; its predicted variance for every later day."""
    F, y = d["F"], d["y"]
    X, Y = F[60:1512].reshape(-1, 5), y[60:1512].reshape(-1)
    m, sd = X.mean(axis=0), X.std(axis=0)
    net = fit_nll(GaussNet(5), ((X - m) / sd).astype(np.float32), Y,
                  ((F[1512:1764].reshape(-1, 5) - m) / sd).astype(np.float32), y[1512:1764].reshape(-1), seed=1)
    Z = ((F[1764:-1].reshape(-1, 5) - m) / sd).astype(np.float32)
    return predict_gauss(net, Z)[1].reshape(-1, F.shape[1]) ** 2


@functools.lru_cache(maxsize=1)
def sizing(seeds=(1, 2, 3, 4), days=5040):
    """Daily portfolios of twenty assets from the drift reading (the one feature with a planted link to the mean):
    weights proportional to the reading, and to the reading over three variance forecasts (EWMA, a Gaussian network
    trained on the first six years, the truth); and the true mean alone and over the true variance. Weights are not
    renormalised day by day, so a rule holds less when risk is high (a Sharpe ratio does not depend on a constant
    scale). Twenty-year series, four seeds, scored from day 1764 on; annualised Sharpe ratios per seed."""
    out = {}
    for sd in seeds:
        d = data(sd, days, None)
        T = slice(1764, days - 1)
        y, rd = d["y"][T], d["F"][T, :, 0]
        tv, ew = d["sig"][T] ** 2, np.exp(2 * d["F"][T, :, 4])
        rules = {"reading": rd, "reading / EWMA variance": rd / ew, "reading / network variance": rd / _net_variance(d),
                 "reading / true variance": rd / tv, "true mean": d["mu"][T],
                 "true mean / true variance": d["mu"][T] / tv}
        for name, w in rules.items():
            p = (w * y).sum(axis=1)
            out.setdefault(name, []).append(float(p.mean() / p.std() * math.sqrt(252)))
    return {k: np.array(v) for k, v in out.items()}
