"""firm.decisionlog -- a decision journal and the scoring of the forecasts in it: the Brier score and Murphy's
decomposition, calibration, forecast aggregation (linear, log-odds, extremised) and an outcome-bias check (build of
One Quant Book 16, chapter 26).

Murphy (1973): with forecasts grouped into bins k of size n_k, mean forecast f_k and observed frequency o_k, and the
overall frequency o, the Brier score is approximately reliability - resolution + uncertainty, where
reliability = sum n_k (f_k - o_k)^2 / N, resolution = sum n_k (o_k - o)^2 / N and uncertainty = o (1 - o); the
identity is exact when every forecast in a bin equals the bin's mean.

API (stable):
    Entry(decision, forecaster, prob, outcome, ev, date) ; brier(p, y) ; murphy(p, y, bins) -> dict
    calibration(p, y, bins) -> (mean forecast, observed frequency, count) per bin
    aggregate(P, how, a) ; logit ; expit ; outcome_bias(entries) -> dict
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Entry:
    decision: str
    forecaster: str
    prob: float
    outcome: int
    ev: float = 0.0          # expected value at decision time, by the decision maker's own model
    date: str = ""


def brier(p, y):
    p, y = np.asarray(p, float), np.asarray(y, float)
    return float(np.mean((p - y) ** 2))


def _bins(p, bins):
    return np.clip((np.asarray(p, float) * bins).astype(int), 0, bins - 1)


def calibration(p, y, bins=10):
    p, y = np.asarray(p, float), np.asarray(y, float)
    b = _bins(p, bins)
    out = []
    for k in range(bins):
        m = b == k
        if m.any():
            out.append((float(p[m].mean()), float(y[m].mean()), int(m.sum())))
    return out


def murphy(p, y, bins=10):
    p, y = np.asarray(p, float), np.asarray(y, float)
    n, o = len(p), float(y.mean())
    rel = res = 0.0
    for f, ok, nk in calibration(p, y, bins):
        rel += nk * (f - ok) ** 2 / n
        res += nk * (ok - o) ** 2 / n
    return {"brier": brier(p, y), "reliability": rel, "resolution": res, "uncertainty": o * (1 - o)}


def logit(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def expit(x):
    return 1 / (1 + np.exp(-np.asarray(x, float)))


def aggregate(P, how="mean", a=1.0):
    """P: forecasters x events. 'mean' of probabilities; 'logodds' mean of log-odds; 'extremised' mean log-odds
    times a."""
    P = np.asarray(P, float)
    if how == "mean":
        return P.mean(axis=0)
    z = logit(P).mean(axis=0)
    return expit(z * (a if how == "extremised" else 1.0))


def outcome_bias(entries):
    """Among decisions with positive expected value, the share that lost; a reviewer who judges by outcome calls all
    of those bad decisions, a reviewer who judges by process calls none of them bad."""
    good = [e for e in entries if e.ev > 0]
    lost = [e for e in good if e.outcome == 0]
    share = len(lost) / len(good) if good else 0.0
    return {"positive_ev": len(good), "lost": len(lost), "share_misjudged_by_outcome": share}
