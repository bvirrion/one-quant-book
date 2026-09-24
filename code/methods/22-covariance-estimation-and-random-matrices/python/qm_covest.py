"""Book 4, chapter 22: covariance estimation and random matrices (teaching module).

Two hundred stocks with a known factor covariance (a market factor and five sectors of forty), two years of
daily returns to estimate, one year to hold: the minimum-variance portfolio from each estimator, predicted
against realised risk; the Marchenko-Pastur law; the spike transition.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "covest"))
from firm_covest import (  # noqa: E402
    clip,
    lw_constant_corr,
    lw_identity,
    min_var_weights,
    mp_density,
    mp_edges,
    nonlinear_shrinkage,
    pca_factor,
    portfolio_risk,
    sample_cov,
)

N, T_FIT, T_HOLD = 200, 500, 250
SCALE = 1.1
ANN = math.sqrt(252)


def truth(seed: int = 22) -> np.ndarray:
    rng = np.random.default_rng(seed)
    B = np.column_stack([rng.normal(1, 0.3, N)] + [np.where(np.arange(N) // 40 == k, rng.normal(0.8, 0.2, N), 0.0)
                                                   for k in range(5)])
    f_sd = SCALE * np.array([0.01] + [0.006] * 5)
    spec = SCALE * rng.uniform(0.01, 0.025, N)
    return (B * f_sd**2) @ B.T + np.diag(spec**2)


def estimators(X) -> dict:
    return {"sample": sample_cov(X), "lw_identity": lw_identity(X)[0], "lw_constcorr": lw_constant_corr(X)[0],
            "clipped": clip(X), "nonlinear": nonlinear_shrinkage(X), "pca_factor": pca_factor(X, 6)}


_CACHE: dict = {}


def evaluate(n_rep: int = 50, T: int = T_FIT, seed: int = 100) -> dict:
    """Annualised predicted (in-sample), true and realised (next 250 days) volatility of each minimum-variance
    portfolio, averaged over n_rep histories."""
    key = (n_rep, T, seed)
    if key in _CACHE:
        return _CACHE[key]
    Sigma = truth()
    L = np.linalg.cholesky(Sigma)
    rng = np.random.default_rng(seed)
    acc: dict = {}
    shrink = {"lw_identity": [], "lw_constcorr": []}
    for _ in range(n_rep):
        X = rng.standard_normal((T, N)) @ L.T
        Z = rng.standard_normal((T_HOLD, N)) @ L.T
        shrink["lw_identity"].append(lw_identity(X)[1])
        shrink["lw_constcorr"].append(lw_constant_corr(X)[1])
        for name, S in estimators(X).items():
            w = min_var_weights(S)
            row = (portfolio_risk(w, S) * ANN, portfolio_risk(w, Sigma) * ANN, float(np.std(Z @ w)) * ANN)
            acc.setdefault(name, []).append(row)
    out = {k: {"pred": float(np.mean(v, 0)[0]), "true": float(np.mean(v, 0)[1]), "real": float(np.mean(v, 0)[2]),
               "ratio": float(np.mean([b / a for a, b, _ in v]))} for k, v in acc.items()}
    out["optimum"] = portfolio_risk(min_var_weights(Sigma), Sigma) * ANN
    out["q"] = N / T
    out["intensity"] = {k: float(np.mean(v)) for k, v in shrink.items()}
    _CACHE[key] = out
    return out


def bias_vs_q(Ts=(2000, 1000, 667, 500, 400, 333, 286, 250, 222), n_rep: int = 20, seed: int = 7) -> list:
    """True-to-predicted volatility ratio of the sample minimum-variance portfolio against q = N / T."""
    Sigma = truth()
    L = np.linalg.cholesky(Sigma)
    rng = np.random.default_rng(seed)
    out = []
    for T in Ts:
        r = []
        for _ in range(n_rep):
            X = rng.standard_normal((T, N)) @ L.T
            S = sample_cov(X)
            w = min_var_weights(S)
            r.append(portfolio_risk(w, Sigma) / portfolio_risk(w, S))
        out.append((N / T, float(np.mean(r)), 1 / (1 - N / T)))
    return out


def spectrum(seed: int = 3) -> dict:
    """Eigenvalues of the sample correlation matrix: pure noise (identity truth) and the factor model."""
    rng = np.random.default_rng(seed)
    noise = np.linalg.eigvalsh(np.corrcoef(rng.standard_normal((T_FIT, N)).T))
    Sigma = truth()
    X = rng.standard_normal((T_FIT, N)) @ np.linalg.cholesky(Sigma).T
    fac = np.linalg.eigvalsh(np.corrcoef(X.T))
    sd = np.sqrt(np.diag(Sigma))
    pop = np.linalg.eigvalsh(Sigma / np.outer(sd, sd))
    return {"noise": noise, "factor": fac, "population": pop, "q": N / T_FIT, "edges": mp_edges(N / T_FIT)}


def spike(ells=(1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0, 5.0), n_rep: int = 20, seed: int = 9) -> list:
    """Top sample eigenvalue with one population spike ell (others 1), N = 200, T = 500, against the BBP law."""
    rng = np.random.default_rng(seed)
    q = N / T_FIT
    out = []
    for ell in ells:
        d = np.ones(N)
        d[0] = ell
        tops = [np.linalg.eigvalsh(sample_cov(rng.standard_normal((T_FIT, N)) * np.sqrt(d)))[-1] for _ in range(n_rep)]
        theory = ell * (1 + q / (ell - 1)) if ell > 1 + math.sqrt(q) else (1 + math.sqrt(q)) ** 2
        out.append((ell, float(np.mean(tops)), theory))
    return out


def mp_curve(q: float = N / T_FIT, n: int = 120) -> list:
    lo, hi = mp_edges(q)
    xs = np.linspace(lo * 0.999, hi * 1.001, n)
    return list(zip(xs.tolist(), mp_density(xs, q).tolist(), strict=True))
