"""Clustering, regimes and anomaly detection (One Quant Book 12, chapter 20).

(1) Clustering firm.synthmkt names (10 industries) on market-residual returns by k-means and hierarchical clustering,
scored by the adjusted Rand index against the planted industries, for window lengths and two industry strengths. (2) A
planted two-state Markov-switching index (calm: mean 5 bp, sd 0.8%; stress: mean -10 bp, sd 2.5%; stays with probability
0.99 and 0.95) over 20 years: Gaussian hidden Markov models fitted on the first ten years, filtered and smoothed on the
last ten, against a volatility threshold, as regime estimates and to scale exposure. (3) Book 9's spoofing
account-days: an isolation forest and an autoencoder against the rule-based detectors, by true-positive rate and
precision at a 1% false-positive rate."""
from __future__ import annotations

import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("regimes", "synthmkt", "surveil"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_regimes import (  # noqa: E402
    GaussianHMM,
    ari,
    autoencoder_scores,
    hier_clusters,
    iforest_scores,
    kmeans_clusters,
    market_residuals,
    regime_series,
    stability,
)
from firm_surveil import spoof_scores, spoofing_days, tpr_at_fpr  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

WINDOWS = (63, 252, 1260)
STRENGTHS = (0.08, 0.15)


@functools.lru_cache(maxsize=2)
def panel(ind_vol):
    P = simulate(MarketConfig(n=200, days=1260, seed=1, ind_vol=ind_vol))
    ok = ~np.isnan(P.ret).any(0)
    return market_residuals(P.ret[:, ok]), P.industry[ok]


@functools.lru_cache(maxsize=1)
def clustering():
    out = {}
    for iv in STRENGTHS:
        E, ind = panel(iv)
        for L in WINDOWS:
            X = E[-L:]
            out[(iv, L)] = (ari(kmeans_clusters(X, 10), ind), ari(hier_clusters(X, 10), ind))
        out[(iv, "stability")] = (stability(E[-252:], 10, "km"), stability(E[-252:], 10, "hier"))
    out["names"] = {iv: panel(iv)[0].shape[1] for iv in STRENGTHS}
    return out


# ---------------------------------------------------------------------------------------------------- regimes
MEANS, SDS, P = (0.0005, -0.001), (0.008, 0.025), [[0.99, 0.01], [0.05, 0.95]]
N, HALF = 5040, 2520


@functools.lru_cache(maxsize=1)
def series():
    return regime_series(N, MEANS, SDS, P, seed=0)


@functools.lru_cache(maxsize=2)
def hmm(k):
    x, _ = series()
    return GaussianHMM(k).fit(x[:HALF], seed=0)


def vol_signal(x, window=20, threshold=0.014):
    """Stress when the trailing 20-day volatility (including today) exceeds 1.4%."""
    v = np.array([x[max(0, t - window + 1):t + 1].std() if t >= 1 else x[:1].std() for t in range(len(x))])
    return v > threshold


def _switches(st):
    return [t for t in range(1, len(st)) if st[t] == 1 and st[t - 1] == 0]


def _delays(est, st):
    """For each switch into stress in the test half: days from the switch to the first day, on or after it, on which
    the estimate says stress (nan if the stress spell ends first)."""
    out = []
    for t0 in _switches(st):
        end = next((t for t in range(t0, len(st)) if st[t] == 0), len(st))
        hit = next((t for t in range(t0, end) if est[t]), None)
        out.append(np.nan if hit is None else hit - t0)
    return out


@functools.lru_cache(maxsize=1)
def regimes():
    """Accuracy of each regime estimate on the test half; delays after the switches into stress; and the mean
    probability of stress on the day before each switch (above the calm level only with hindsight)."""
    x, s = series()
    xt, st = x[HALF:], s[HALF:]
    h = hmm(2)
    pf, ps = h.filter(xt)[:, 1], h.smooth(xt)[:, 1]
    est = {"filtered": pf > 0.5, "smoothed": ps > 0.5, "Viterbi": h.viterbi(xt) == 1,
           "volatility threshold": vol_signal(xt)}
    out = {}
    for k, e in est.items():
        d = np.array(_delays(e, st))
        out[k] = {"accuracy": float(np.mean(e == st)), "median delay": float(np.nanmedian(d)),
                  "mean delay": float(np.nanmean(d)), "missed": int(np.isnan(d).sum()), "switches": len(d)}
    before = [t0 - 1 for t0 in _switches(st)]
    calm = st == 0
    out["P(stress) day before"] = {"filtered": float(pf[before].mean()), "smoothed": float(ps[before].mean()),
                                   "filtered, calm days": float(pf[calm].mean()),
                                   "smoothed, calm days": float(ps[calm].mean())}
    out["stress share"] = float(st.mean())
    return out


@functools.lru_cache(maxsize=1)
def vol_targeting(target=0.01):
    """Exposure target / predicted volatility, the prediction mixing the two regimes' variances with (a) the filtered
    probabilities of yesterday carried forward by the transition matrix, (b) the smoothed probabilities of the same day
    (a backtest with hindsight). Annualised Sharpe ratios on the test half."""
    x, _ = series()
    xt = x[HALF:]
    h = hmm(2)
    pred = np.vstack([h.pi, h.filter(xt)[:-1]]) @ h.P
    sm = h.smooth(xt)
    out = {}
    for k, p in (("filtered, predicted", pred), ("smoothed, same day", sm)):
        r = xt * target / np.sqrt(p @ h.sd**2)
        out[k] = float(r.mean() / r.std() * np.sqrt(252))
    out["buy and hold"] = float(xt.mean() / xt.std() * np.sqrt(252))
    return out


def three_state():
    """A three-state model on the same data: its states' volatilities and the fit's log-likelihoods."""
    h2, h3 = hmm(2), hmm(3)
    return {"sd 3": h3.sd, "loglik 2": h2.loglik, "loglik 3": h3.loglik}


# ---------------------------------------------------------------------------------------------------- anomalies
@functools.lru_cache(maxsize=1)
def anomalies(fpr=0.01):
    """True-positive rate and precision at a 1% false-positive rate: the rule-based detectors of Book 9 and two
    unsupervised scores on the same account-day features."""
    d = spoofing_days()
    X = np.column_stack([np.log1p(d["n_small"]), np.log1p(d["n_large"]), (d["f_small"] + 1) / (d["n_small"] + 2),
                         (d["f_large"] + 1) / (d["n_large"] + 2), d["linked"] / np.maximum(d["c_large"], 1)])
    scores = spoof_scores(d) | {"isolation forest": iforest_scores(X), "autoencoder": autoencoder_scores(X)}
    out = {}
    npos, nneg = int(d["label"].sum()), int((d["label"] == 0).sum())
    for k, sc in scores.items():
        r = tpr_at_fpr(sc, d["label"], fpr)
        tp, fp = r["tpr"] * npos, r["fpr"] * nneg
        out[k] = {"tpr": r["tpr"], "precision": tp / (tp + fp) if tp + fp else 0.0}
    out["counts"] = (npos, nneg)
    return out


def test_loglik():
    """Exercise 7: log-likelihood of the test years under the two- and three-state models fitted on the first ten."""
    x, _ = series()
    xt = x[HALF:]
    return {k: float(np.log(hmm(k)._forward(xt)[1]).sum()) for k in (2, 3)}
