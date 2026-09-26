"""Generative models and synthetic data (One Quant Book 12, chapter 16).

Thirty years of synthetic daily index returns with fat tails, volatility clustering, a leverage effect, six crashes
and a planted momentum effect (firm.genmkt.real_index); the first twenty years train five generators of 32-day windows
(block bootstrap, GARCH-t, VAE, GAN, diffusion), the last ten test. Each generator is judged by a stylised-fact
scorecard, a classifier two-sample test against the training windows, train-on-synthetic test-on-real (TSTR, five
samples of 20,000 windows), train-on-synthetic test-on-synthetic, and nearest-neighbour distances to the training
windows."""
from __future__ import annotations

import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "genmkt"))
from firm_genmkt import (  # noqa: E402
    GAN,
    VAE,
    Diffusion,
    block_bootstrap,
    c2st,
    facts,
    fit_garch,
    garch_windows,
    nn_distance,
    real_index,
    scorecard,
    tstr,
    windows,
)

N_TRAIN, L, STEPS = 5040, 32, 4000
NAMES = ("block bootstrap", "GARCH-t", "VAE", "GAN", "diffusion")


@functools.lru_cache(maxsize=1)
def data():
    d = real_index()
    r = d["r"]
    Wtr, Wte = windows(r[:N_TRAIN], L), windows(r[N_TRAIN:], L)
    return {"r": r, "crashes": d["crashes"], "train": Wtr, "test": Wte, "groups": np.arange(len(Wtr)) // 252}


@functools.lru_cache(maxsize=1)
def generators():
    """name -> sampler(n, seed)."""
    D = data()
    r = D["r"][:N_TRAIN]
    p = fit_garch(r)
    out = {"block bootstrap": lambda n, s: block_bootstrap(r, n, L, 20, s),
           "GARCH-t": lambda n, s: garch_windows(p, n, L, s)}
    for name, M in (("VAE", VAE(L)), ("GAN", GAN(L)), ("diffusion", Diffusion(L))):
        M.fit(D["train"], steps=STEPS, seed=0)
        out[name] = M.sample
    return out


def garch_params():
    return fit_garch(data()["r"][:N_TRAIN])


@functools.lru_cache(maxsize=1)
def judge():
    D = data()
    out = {"real": {"scorecard": scorecard(D["train"]), "facts": facts(D["train"]),
                    "c2st": c2st(D["train"][D["groups"] % 2 == 0], D["train"][D["groups"] % 2 == 1],
                                 D["groups"][D["groups"] % 2 == 0] // 2, D["groups"][D["groups"] % 2 == 1] // 2),
                    "tstr": tstr(D["train"], D["test"]),
                    "nn": float(np.median(nn_distance(D["test"], D["train"])))}}
    ref = np.percentile(nn_distance(D["test"], D["train"]), 5)
    for name, f in generators().items():
        W = f(4000, 1)
        ts = np.array([tstr(f(20000, 10 + s), D["test"]) for s in range(5)])
        G = f(20000, 99)
        nn = nn_distance(W, D["train"])
        out[name] = {"scorecard": scorecard(W), "facts": facts(W), "c2st": c2st(W, D["train"], None, D["groups"]),
                     "tstr": tuple(ts.mean(0)), "tstr sd": tuple(ts.std(0)), "tsts": tstr(G[:10000], G[10000:]),
                     "nn": float(np.median(nn)), "close": float(np.mean(nn < ref))}
    out["real"]["close"] = 0.05
    return out


def abs_acf(W, lags=range(1, 21)):
    a = np.abs(W)
    return [float(np.corrcoef(a[:, :-k].ravel(), a[:, k:].ravel())[0, 1]) for k in lags]


def c2st_random_split():
    """Exercise 5: real even years against real odd years, overlapping windows split at random (not by block)."""
    D = data()
    g = D["groups"]
    return c2st(D["train"][g % 2 == 0], D["train"][g % 2 == 1], None, None)


@functools.lru_cache(maxsize=1)
def gan_steps(steps=(1000, 8000)):
    """Exercise 7: the GAN trained for fewer and more steps: excess kurtosis, two-sample accuracy, TSTS Sharpe ratio."""
    D = data()
    out = {}
    for k in steps:
        M = GAN(L).fit(D["train"], steps=k, seed=0)
        W, G = M.sample(4000, 1), M.sample(20000, 99)
        out[k] = (facts(W)["kurtosis"], c2st(W, D["train"], None, D["groups"]), tstr(G[:10000], G[10000:])[1])
    return out
