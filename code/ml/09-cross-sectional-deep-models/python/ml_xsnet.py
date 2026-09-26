"""Cross-sectional deep models (One Quant Book 12, chapter 9).

firm.mlsynth's conditional factor panel: 300 stocks, 240 months, ten ranked characteristics, three factors with premia,
and betas that are functions of the characteristics, half of their cross-sectional variance nonlinear. PCA (static
betas), instrumented PCA (betas linear in the characteristics) and a conditional autoencoder (betas a network of them)
with one, three and five factors, trained on months 0-179 (the autoencoder stopped on months 160-179) and scored on
months 180-239 by total and predictive R-squared; how much of the planted nonlinearity each recovers; and a pooled
network with an entity embedding for industries that carry premia of their own.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("mlsynth", "xsnet"):
    sys.path.insert(0, str(ROOT / c))
from firm_mlsynth import FactorConfig, factor_panel  # noqa: E402
from firm_xsnet import IPCA, CondAE, PCAModel, fit_embed, scores, with_constant  # noqa: E402

FIT, VAL, TRAIN, TEST = np.arange(0, 160), np.arange(160, 180), np.arange(0, 180), np.arange(180, 240)


@functools.lru_cache(maxsize=1)
def data(seed=1):
    d = factor_panel(FactorConfig(seed=seed))
    d["Zc"] = with_constant(d["Z"])
    d["mu_lin"] = d["lin_beta"] @ d["premia"]
    return d


def truth():
    d = data()
    t = TEST
    return scores(np.einsum("tnk,tk->tn", d["beta"][t], d["f"][t]), d["mu"][t], d["r"][t])


def _recovery(mu_hat):
    d = data()
    mu, nl = d["mu"][TEST], (d["mu"] - d["mu_lin"])[TEST]
    return float(np.corrcoef(mu_hat.ravel(), mu.ravel())[0, 1]), float(np.corrcoef(mu_hat.ravel(), nl.ravel())[0, 1])


@functools.lru_cache(maxsize=8)
def pca(K=3):
    d = data()
    m = PCAModel(K).fit(d["r"][TRAIN])
    tot, pred = m.score(d["r"][TEST])
    return tot, pred, _recovery(np.tile(m.B @ m.lam, (len(TEST), 1)))


@functools.lru_cache(maxsize=8)
def ipca(K=3):
    d = data()
    m = IPCA(K).fit(d["Zc"][TRAIN], d["r"][TRAIN])
    tot, pred = m.score(d["Zc"][TEST], d["r"][TEST])
    return tot, pred, _recovery(m.betas(d["Zc"][TEST]) @ m.lam)


@functools.lru_cache(maxsize=16)
def cae(K=3, seed=1):
    d = data()
    m = CondAE(d["Zc"].shape[2], K, seed=seed).fit(d["Zc"][FIT], d["r"][FIT], d["Zc"][VAL], d["r"][VAL])
    tot, pred = m.score(d["Zc"][TEST], d["r"][TEST])
    return tot, pred, _recovery(m.betas(d["Zc"][TEST]) @ m.lam)


@functools.lru_cache(maxsize=2)
def embedding(seed=1, n_ind=30, prem_sd=0.004, emb_init=0.01):
    """Industries with planted monthly premia (sd 0.4%) on top of the panel: pooled networks on the characteristics
    without the industry, with a one-dimensional embedding of it, and the embedding's correlation with the premia."""
    import torch

    d = data()
    rng = np.random.default_rng(seed + 50)
    ind = rng.integers(0, n_ind, d["r"].shape[1])
    prem = prem_sd * rng.standard_normal(n_ind)
    y = d["r"] + prem[ind]
    y = y - y.mean(axis=1, keepdims=True)
    mu = d["mu"] + prem[ind]
    mu = mu - mu.mean(axis=1, keepdims=True)

    def flat(months):
        X = d["Z"][months].reshape(-1, d["Z"].shape[2])
        return np.tile(ind, len(months)), X, y[months].reshape(-1)

    cf, Xf, yf = flat(FIT)
    cv, Xv, yv = flat(VAL)
    ct, Xt, yt = flat(TEST)
    out = {}
    for name, dim in (("no industry", 0), ("embedding", 1)):
        m = fit_embed(cf, Xf, yf, cv, Xv, yv, emb_dim=dim, seed=seed, emb_init=emb_init)
        with torch.no_grad():
            p = m(torch.as_tensor(ct), torch.as_tensor(Xt, dtype=torch.float32)).numpy() * m.y_scale
        out[name] = {"r2": float(1 - np.sum((yt - p) ** 2) / np.sum(yt**2)),
                     "corr_truth": float(np.corrcoef(p, mu[TEST].reshape(-1))[0, 1])}
        if dim:
            e = m.emb.weight.detach().numpy()[:, 0]
            out["embedding_vs_premia"] = float(abs(np.corrcoef(e, prem)[0, 1]))
    return out
