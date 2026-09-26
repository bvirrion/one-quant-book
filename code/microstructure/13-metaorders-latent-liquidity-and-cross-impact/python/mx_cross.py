"""One Quant Book 10, chapter 13: latent liquidity, fair pricing and cross-impact.

    llob_scan(sizes)            peak impact of a ten-second metaorder on the latent order book (L = 1, D = 1) against
                                its size, and the local exponent between neighbouring sizes
    fair(q)                     the price path of one metaorder: peak, average price paid, and when after the end the
                                price crosses the average paid (fair pricing)
    two_assets(seed, T)         order flows (thousands of shares per interval) of two correlated stocks and their
                                returns (ticks) from a true cross-impact matrix and noise
    cross_study(seed)           the estimated matrix, its symmetric positive projection, the share of each asset's
                                return variance explained by the other's flow; for a two-asset sale and a pair trade,
                                the joint optimum's cost, what an own-impact model estimates for it, the cost of
                                trading the legs one after the other, and the saving when cross-impact decays more
                                slowly than own impact (cached)
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "crossimpact"))
from firm_crossimpact import estimate, explained_by_other, fair_pricing, liquidation, llob, symmetric_psd  # noqa: E402

SIZES = (0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
LLOB = {"L": 1.0, "D": 1.0, "dt": 0.005, "width": 80.0, "dx": 0.1}
LAMBDA = np.array([[1.0, 0.4], [0.4, 0.8]])                   # ticks per thousand shares


@functools.cache
def llob_scan(sizes=SIZES, horizon: float = 10.0) -> dict:
    peaks = [float(llob(q, horizon, **LLOB)[1][-1]) for q in sizes]
    slopes = [float(np.log(peaks[i + 1] / peaks[i]) / np.log(sizes[i + 1] / sizes[i])) for i in range(len(sizes) - 1)]
    return {"sizes": list(sizes), "peaks": peaks, "slopes": slopes}


@functools.cache
def fair(q: float = 10.0, horizon: float = 10.0, after: float = 100.0) -> dict:
    t, p = llob(q, horizon, after=after, **LLOB)
    f = fair_pricing(t, p, horizon)
    post = (t > horizon) & (p <= f["average"])
    f["cross_after"] = float(t[post][0] - horizon) if post.any() else float("nan")
    f["t"], f["p"] = t, p
    return f


def two_assets(seed: int = 1, n: int = 2000, noise: float = 1.0):
    rng = np.random.default_rng(seed)
    q = rng.standard_normal((n, 2)) @ np.array([[1.0, 0.0], [0.6, 0.8]]).T     # flows correlated 0.6
    r = q @ LAMBDA.T + noise * rng.standard_normal((n, 2))
    return r, q


def _cost(q, lam, t, rho: float = 3.0) -> float:
    e = np.exp(-rho * np.abs(t[:, None] - t[None, :]))
    v = np.asarray(q, float).ravel()
    return float(0.5 * v @ np.kron(lam, e) @ v)


def _sequential(x, t, rho: float = 3.0):
    """Each asset's own optimal schedule on half of the horizon, the first asset first."""
    h = len(t) // 2 + 1
    th = t[:h]
    w = np.linalg.solve(np.exp(-rho * np.abs(th[:, None] - th[None, :])), np.ones(h))
    w = w / w.sum()
    q = np.zeros((2, len(t)))
    q[0, :h], q[1, len(t) - h:] = w * x[0], w * x[1]
    return q


@functools.cache
def cross_study(seed: int = 1) -> dict:
    r, q = two_assets(seed)
    est = estimate(r, q)
    t = np.linspace(0.0, 1.0, 21)
    own = np.diag(np.diag(LAMBDA))
    out = {"estimate": est, "psd": symmetric_psd(est), "explained": explained_by_other(r, q),
           "corr_flow": float(np.corrcoef(q.T)[0, 1])}
    for name, x in (("same", np.array([10.0, 10.0])), ("pair", np.array([10.0, -10.0]))):
        qj, cj = liquidation(LAMBDA, 3.0, t, x)
        seq = _sequential(x, t)
        slow_j = liquidation(LAMBDA, 3.0, t, x, rho_cross=0.3)[1]
        slow_n = liquidation(LAMBDA, 3.0, t, x, joint=False, rho_cross=0.3)[1]
        out[name] = {"joint": cj, "own_estimate": _cost(qj, own, t), "sequential": _cost(seq, LAMBDA, t),
                     "saving_vs_sequential": 1 - cj / _cost(seq, LAMBDA, t), "slow_saving": 1 - slow_j / slow_n,
                     "schedule": qj}
    return out
