"""One Quant Book 16, chapter 26: a year of a desk's decision journal, and five opinions against one (synthetic).

400 events a year, each with a true probability drawn from a Beta(2, 2). Five forecasters see the log-odds of the
truth with their own noise (standard deviation 0.8) and their own overconfidence (they stretch their log-odds by a
factor between 1.0 and 1.6). Independent forecasts are aggregated three ways; a discussion before forecasting makes
the forecasters' errors correlated at rho, and the desk records one consensus forecast (their mean).
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/decisionlog"))
import firm_decisionlog as dl  # noqa: E402

N, K, NOISE = 400, 5, 0.8
STRETCH = np.array([1.0, 1.15, 1.3, 1.45, 1.6])


def year(seed=26, rho=0.0, n=N):
    rng = np.random.default_rng(seed)
    q = rng.beta(2.0, 2.0, n)
    y = (rng.random(n) < q).astype(int)
    common = rng.standard_normal(n)
    own = rng.standard_normal((K, n))
    err = NOISE * (np.sqrt(rho) * common + np.sqrt(1 - rho) * own)
    P = dl.expit(STRETCH[:, None] * (dl.logit(q)[None, :] + err))
    return q, y, P


def scores(seed=26, a=1.5):
    q, y, P = year(seed)
    out = {f"forecaster {k + 1}": dl.brier(P[k], y) for k in range(K)}
    out["truth"] = dl.brier(q, y)
    out["mean"] = dl.brier(dl.aggregate(P, "mean"), y)
    out["log-odds"] = dl.brier(dl.aggregate(P, "logodds"), y)
    out["extremised"] = dl.brier(dl.aggregate(P, "extremised", a), y)
    return out


def five_or_one(rhos=(0.0, 0.25, 0.5, 0.75, 1.0), seeds=range(26, 46)):
    """Mean Brier score over twenty simulated years: five independent forecasts (log-odds mean) against one consensus
    forecast after a discussion that correlates the errors at rho."""
    indep = np.mean([dl.brier(dl.aggregate(year(s)[2], "logodds"), year(s)[1]) for s in seeds])
    out = {}
    for rho in rhos:
        out[rho] = float(np.mean([dl.brier(dl.aggregate(year(s, rho)[2], "logodds"), year(s, rho)[1]) for s in seeds]))
    return float(indep), out


def journal(seed=26, k=1):
    """Forecaster k bets at even odds on every event it gives more than 55 per cent (either way): positive expected
    value by its own forecast. The journal records the decision, the probability and the outcome."""
    q, y, P = year(seed)
    out = []
    for i, p in enumerate(P[k]):
        if p > 0.55:
            out.append(dl.Entry(f"back event {i}", f"forecaster {k + 1}", float(p), int(y[i]), 2 * p - 1))
        elif p < 0.45:
            out.append(dl.Entry(f"oppose event {i}", f"forecaster {k + 1}", float(1 - p), int(1 - y[i]), 1 - 2 * p))
    return out
