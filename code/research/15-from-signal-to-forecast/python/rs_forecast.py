"""From signal to forecast (One Quant Book 7, chapter 15).

A planted forecast on the monthly residual returns of firm.synthmkt (seed 1, 698 names listed for ten years): each
month a standard normal score s per name, and a true expected residual return IC0 x vol x s added to the name's
market-adjusted return, vol being the name's residual volatility. Calibration of the score into expected returns (the
scaling rule, bins, isotonic regression, the Mincer-Zarnowitz check); the fundamental law against the information ratio
of the score's portfolio, first with Gaussian residuals, then with the market's own residuals (industries, styles,
volatility clustering), then under a long-only constraint; the IC's noise. NumPy only.
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("forecast", "synthmkt", "combine"):
    sys.path.insert(0, str(ROOT / c))
from firm_combine import ic_series  # noqa: E402
from firm_forecast import (  # noqa: E402
    binned,
    information_ratio,
    isotonic,
    law_ir,
    mincer_zarnowitz,
    qian_hua_ir,
    scale_rule,
    transfer_coefficient,
)
from firm_synthmkt import simulate  # noqa: E402

MONTH, IC0, SEED = 21, 0.05, 15


@functools.lru_cache(maxsize=1)
def data():
    """eps (T, N) monthly residual returns, vol (N,) their standard deviations, s (T, N) scores, r (T, N) realised
    returns with the planted expected return, and the same with Gaussian residuals of the same volatilities."""
    P = simulate()
    full = np.flatnonzero(P.listed.all(axis=0))
    adj = P.ret[:, full] - P.beta[None, full] * P.mkt[:, None]
    T = adj.shape[0] // MONTH
    eps = np.add.reduceat(adj, np.arange(0, T * MONTH, MONTH), axis=0)[:T]
    eps = eps - eps.mean(axis=1, keepdims=True)
    vol = eps.std(axis=0)
    rng = np.random.default_rng(SEED)
    s = rng.standard_normal(eps.shape)
    alpha = IC0 * vol * s
    gauss = vol * rng.standard_normal(eps.shape)
    return eps, vol, s, alpha + eps, alpha + gauss


def calibration():
    """Scaling rule with the IC estimated on the first half, judged on the second: the Mincer-Zarnowitz regression of
    realised returns on the raw score and on the scaled forecast, the calibration by deciles (realised / vol against
    the predicted IC x score), and the isotonic fit of realised / vol on the score."""
    eps, vol, s, r, _ = data()
    h = len(s) // 2
    ic_hat = float(np.mean(ic_series(s[:h], r[:h] / vol)))
    fc = scale_rule(s[h:], ic_hat, vol)
    raw = mincer_zarnowitz(s[h:], r[h:])
    scaled = mincer_zarnowitz(fc, r[h:])
    k, ms, mr = binned(s[h:], r[h:] / vol, 10)
    iso = isotonic(s[h:].ravel(), (r[h:] / vol).ravel())
    grid = np.linspace(-2.5, 2.5, 51)
    xs = s[h:].ravel()
    iso_at = np.array([iso[np.argmin(np.abs(xs - g))] for g in grid])
    return {"ic_hat": ic_hat, "raw": raw, "scaled": scaled, "bins": (ms, mr, ic_hat * ms), "iso": (grid, iso_at),
            "vol_median": float(np.median(vol))}


def portfolio(r, s, vol, te: float | None = None, bench=None):
    """Monthly P&L of the book with active weights proportional to s / vol (the mean-variance weights alpha / vol^2
    for alpha = IC x vol x s). Unconstrained (te None): scaled to unit predicted risk. Long-only (te a monthly
    tracking-error target): an equal-weight benchmark plus the active weights scaled to te, holdings clipped at zero
    and renormalised. Returns the P&L series, the mean transfer coefficient and the share of holdings clipped."""
    N = s.shape[1]
    b = np.full(N, 1.0 / N) if bench is None else np.asarray(bench, float) / np.sum(bench)
    pnl, tcs, clipped = [], [], []
    for t in range(len(s)):
        a = s[t] / vol
        a = a / np.sqrt(np.sum((a * vol) ** 2)) * (1.0 if te is None else te)
        if te is not None:
            clipped.append(float(np.mean(b + a < 0)))
            h = np.maximum(b + a, 0.0)
            a = h / h.sum() - b
        tcs.append(transfer_coefficient(a, IC0 * vol * s[t], vol))
        pnl.append(float(a @ r[t]))
    return np.array(pnl), float(np.mean(tcs)), float(np.mean(clipped)) if clipped else 0.0


def law(te: float = 0.04):
    """The fundamental law against the book's information ratio: Gaussian residuals, the market's residuals, and the
    long-only book; the IC's mean and dispersion, the breadth they imply, and the decomposition of the shortfall."""
    eps, vol, s, r, rg = data()
    T, N = s.shape
    ic_r, ic_g = ic_series(s, r / vol), ic_series(s, rg / vol)
    pnl_g, _, _ = portfolio(rg, s, vol)
    pnl_r, _, _ = portfolio(r, s, vol)
    pnl_l, tc, clip = portfolio(r, s, vol, te)
    mu, sd = float(ic_r.mean()), float(ic_r.std(ddof=1))
    out = {"N": N, "T": T, "law": law_ir(IC0, 12 * N), "ir_gauss": information_ratio(pnl_g),
           "ir_market": information_ratio(pnl_r), "ir_long": information_ratio(pnl_l), "tc": tc, "clipped": clip,
           "te_realised": float(np.std(pnl_l, ddof=1) * math.sqrt(12)), "ic_mean": mu, "ic_sd": sd,
           "ic_sd_gauss": float(ic_g.std(ddof=1)), "qian_hua": qian_hua_ir(mu, sd) * math.sqrt(12),
           "qian_hua_gauss": qian_hua_ir(ic_g.mean(), ic_g.std(ddof=1)) * math.sqrt(12)}
    out["breadth_eff"] = (mu / sd) ** 2 / IC0 ** 2                  # names a month that the IC's noise is worth
    out["steps"] = (out["law"], out["qian_hua"], out["qian_hua"] * tc, out["ir_long"])
    return out


def tracking_error_grid(tes=(0.0025, 0.005, 0.01, 0.02, 0.04)):
    eps, vol, s, r, _ = data()
    out = {}
    for te in tes:
        pnl, tc, clip = portfolio(r, s, vol, te)
        out[te] = {"tc": tc, "ir": information_ratio(pnl), "clipped": clip}
    return out


def concentrated(te: float = 0.01, seed: int = 7):
    """Exercise 7: the long-only book against a benchmark with weights proportional to a lognormal size (the log size
    has a standard deviation of 1.5, so a few names dominate)."""
    eps, vol, s, r, _ = data()
    size = np.exp(np.random.default_rng(seed).normal(0.0, 1.5, s.shape[1]))
    pnl, tc, clip = portfolio(r, s, vol, te, bench=size)
    return {"tc": tc, "ir": information_ratio(pnl), "clipped": clip}
