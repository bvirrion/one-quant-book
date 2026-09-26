"""Deep hedging and machine learning in pricing (One Quant Book 12, chapter 19).

(1) Selling a one-month at-the-money call under Heston paths (Book 5's firm.heston: v0 = vbar = 0.04, kappa 2, eta
0.5, rho -0.7), hedged daily with the underlying at proportional costs of 0 to 20 basis points: no-transaction band
networks trained on 20,000 paths to minimise the entropic risk (and, once, expected shortfall), against Black-Scholes
delta and the Whalley-Wilmott band on 20,000 other paths. (2) A surrogate of the Heston call price in (spot, initial
variance) learned from single-path Monte Carlo samples, with and without differential labels. (3) A calibration network
from a grid of fifteen call prices to the five Heston parameters, against Book 5's Levenberg-Marquardt calibrator."""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402
import torch  # noqa: E402

_FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for _c in ("deephedge", "heston"):
    sys.path.insert(0, str(_FIRM / _c))
import firm_heston as fh  # noqa: E402
from firm_deephedge import (  # noqa: E402
    band,
    bs_policy,
    entropic,
    expected_shortfall,
    fit_calibrator,
    fit_surrogate,
    hedge_pnl,
    heston_paths,
    no_hedge,
    surrogate_values,
    train_hedge,
    ww_policy,
)

MODEL = fh.Heston(0.04, 2.0, 0.04, 0.5, -0.7)
S0, K, T, N = 100.0, 100.0, 1 / 12, 21
COSTS = (0.0, 0.0005, 0.001, 0.002)
TRAIN = {"steps": 1000, "batch": 2048, "lr": 5e-3}


@functools.lru_cache(maxsize=1)
def paths():
    S = heston_paths(MODEL, S0, T, N, 40000, seed=0)
    return S[:20000], S[20000:]


def atm_vol():
    return float(fh.implied_vols(MODEL, S0, np.array([K]), T)[0])


def price():
    return float(fh.call_prices(MODEL, S0, np.array([K]), T)[0])


def vega_point():
    """Black-Scholes vega of the call for one volatility point."""
    return S0 * math.sqrt(T) * math.exp(-0.5 * (0.5 * atm_vol() * math.sqrt(T)) ** 2) / math.sqrt(2 * math.pi) / 100


@functools.lru_cache(maxsize=8)
def hedger(cost, risk="entropic"):
    tr, _ = paths()
    return train_hedge(tr, K, T, cost, risk, seed=0, **TRAIN)


def _stats(X):
    X = torch.as_tensor(X)
    return {"entropic": float(entropic(X)), "ES": float(expected_shortfall(X)), "mean cost": float(-X.mean()),
            "sd": float(X.std())}


@functools.lru_cache(maxsize=1)
def hedging():
    """For each cost: risk statistics on the test paths of each policy, and the band at mid-life at the money."""
    _, te = paths()
    iv = atm_vol()
    out = {}
    for c in COSTS:
        pols = {"deep hedge": hedger(c), "Black-Scholes delta": bs_policy(iv, K, T),
                "Whalley-Wilmott": ww_policy(iv, K, T, c, 1.0), "no hedge": no_hedge}
        with torch.no_grad():
            row = {k: _stats(hedge_pnl(p, te, K, T, c)) for k, p in pols.items()}
        row["band deep"] = band(hedger(c), 0.5, S0, K)
        row["band WW"] = band(ww_policy(iv, K, T, c, 1.0), 0.5, S0, K)
        out[c] = row
    return out


@functools.lru_cache(maxsize=1)
def shortfall_hedge(cost=0.001):
    """A band network trained on expected shortfall (95%) instead of the entropic risk, at 10 basis points."""
    _, te = paths()
    es, en = hedger(cost, "es"), hedger(cost)                          # train outside no_grad
    with torch.no_grad():
        return {"ES-trained": _stats(hedge_pnl(es, te, K, T, cost)),
                "entropic-trained": _stats(hedge_pnl(en, te, K, T, cost)), "band ES": band(es, 0.5, S0, K)}


def turnover(cost=0.0005):
    """Mean cost paid per path by the Black-Scholes delta hedge, and by the deep hedge (cost x traded notional)."""
    _, te = paths()
    iv = atm_vol()
    net = hedger(cost)
    with torch.no_grad():
        a = hedge_pnl(bs_policy(iv, K, T), te, K, T, cost) - hedge_pnl(bs_policy(iv, K, T), te, K, T, 0.0)
        b = hedge_pnl(net, te, K, T, cost) - hedge_pnl(net, te, K, T, 0.0)
    return float(-a.mean()), float(-b.mean())


# ---------------------------------------------------------------------------------------------------- surrogates
TAU = 0.25


def heston_terminal(s0, v0, seed, steps=50):
    """One Heston path per sample, with its own spot and initial variance; full-truncation Euler."""
    rng = np.random.default_rng(seed)
    dt = TAU / steps
    x, v = np.log(s0), v0.copy()
    c = math.sqrt(1 - MODEL.rho**2)
    for _ in range(steps):
        z1, z2 = rng.standard_normal(len(s0)), rng.standard_normal(len(s0))
        vp = np.maximum(v, 0.0)
        x = x - 0.5 * vp * dt + np.sqrt(vp * dt) * z1
        v = v + MODEL.kappa * (MODEL.vbar - vp) * dt + MODEL.eta * np.sqrt(vp * dt) * (MODEL.rho * z1 + c * z2)
    return np.exp(x)


def true_price(s0, v0):
    return np.array([fh.call_prices(fh.Heston(v, MODEL.kappa, MODEL.vbar, MODEL.eta, MODEL.rho), s, np.array([K]),
                                    TAU)[0] for s, v in zip(s0, v0, strict=True)])


@functools.lru_cache(maxsize=1)
def test_grid():
    rng = np.random.default_rng(99)
    s0, v0 = rng.uniform(80, 120, 400), rng.uniform(0.02, 0.08, 400)
    p = true_price(s0, v0)
    h = 0.01
    d = (true_price(s0 + h, v0) - true_price(s0 - h, v0)) / (2 * h)
    return s0, v0, p, d


def _features(s0, v0):
    return np.column_stack([(s0 - 100) / 20, (v0 - 0.05) / 0.03])


@functools.lru_cache(maxsize=1)
def surrogates(sizes=(256, 1024, 4096)):
    """Test RMSE of price and of delta for networks trained on single-path payoffs, with and without the pathwise
    delta labels dPayoff/dS0 = 1{S_T > K} S_T / S0 (the network's input is the scaled spot, hence the factor 20)."""
    s0t, v0t, pt, dt_ = test_grid()
    out = {}
    for n in sizes:
        rng = np.random.default_rng(n)
        s0, v0 = rng.uniform(70, 130, n), rng.uniform(0.01, 0.09, n)
        sT = heston_terminal(s0, v0, seed=n)
        y = np.maximum(sT - K, 0.0)
        dy = (sT > K) * sT / s0 * 20.0
        for diff in (False, True):
            net = fit_surrogate(_features(s0, v0), y, dy, differential=diff, seed=0)
            p, d = surrogate_values(net, _features(s0t, v0t))
            out[(n, diff)] = (float(np.sqrt(np.mean((p - pt) ** 2))), float(np.sqrt(np.mean((d / 20.0 - dt_) ** 2))))
    return out


# ---------------------------------------------------------------------------------------------------- calibration
MONEY, MATS = np.array([0.85, 0.925, 1.0, 1.075, 1.15]), np.array([1 / 12, 0.25, 1.0])
LO, HI = np.array([0.01, 0.5, 0.01, 0.1, -0.9]), np.array([0.09, 4.0, 0.09, 1.0, 0.0])


def surface(p):
    m = fh.Heston(*p)
    return np.concatenate([fh.call_prices(m, 1.0, MONEY, t) for t in MATS])


@functools.lru_cache(maxsize=1)
def calibration(n_train=4000, n_test=200):
    """Train the inverse map on random parameters; report the test error of each parameter and the price error of the
    surface re-priced with the predicted parameters."""
    rng = np.random.default_rng(5)
    P = LO + (HI - LO) * rng.random((n_train + n_test, 5))
    V = np.array([surface(p) for p in P])
    pred = fit_calibrator(V[:n_train] * 100, P[:n_train], seed=0)
    Ph = pred(V[n_train:] * 100)
    Ph = np.clip(Ph, LO, HI)
    Vh = np.array([surface(p) for p in Ph])
    names = ("v0", "kappa", "vbar", "eta", "rho")
    err = {k: float(np.sqrt(np.mean((Ph[:, i] - P[n_train:, i]) ** 2)) / (HI[i] - LO[i])) for i, k in enumerate(names)}
    rmse = float(1e4 * np.sqrt(np.mean((Vh - V[n_train:]) ** 2)))
    return {"parameter rmse / range": err, "price rmse (bp of spot)": rmse, "test": (P[n_train:], Ph, V[n_train:])}


def lm_check(k=5):
    """Book 5's Levenberg-Marquardt calibrator on the first k test surfaces (implied vols), started from the network's
    answer and from a fixed guess: final implied-vol RMSE (vol points)."""
    Ptrue, Ph, _ = calibration()["test"]
    out = []
    for i in range(k):
        quotes = [(t, MONEY, fh.implied_vols(fh.Heston(*Ptrue[i]), 1.0, MONEY, t)) for t in MATS]
        net_vols = np.concatenate([fh.implied_vols(fh.Heston(*Ph[i]), 1.0, MONEY, t) for t in MATS])
        true_vols = np.concatenate([q[2] for q in quotes])
        _, r1 = fh.calibrate(quotes, 1.0, fh.Heston(*Ph[i]))
        _, r2 = fh.calibrate(quotes, 1.0, fh.Heston(0.04, 1.5, 0.04, 0.5, -0.5))
        out.append((float(100 * np.sqrt(np.mean((net_vols - true_vols) ** 2))), 100 * r1, 100 * r2))
    return out
