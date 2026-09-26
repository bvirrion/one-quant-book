"""firm.basketarb -- index and basket arbitrage at high frequency (One Quant Book 11, chapter 13).

A one-factor index of n names with capitalisation weights w, betas b and idiosyncratic volatilities s. The future
moves first; each stock's quote follows after its own lag. The arbitrageur buys a partial basket of k names (chosen
and re-weighted to track the index) leg by leg, sells the future, and unwinds once the stocks have caught up.

API (stable):
    covariance(beta, s, sf)                       one-factor covariance matrix
    tracking_var(w, h, cov)                       variance of the basket h against the index w
    partial_basket(w, cov, k)                     greedy choice of k names; weights solve cov_SS h_S = (cov w)_S,
                                                  scaled to the index's beta
    fair_future(S, r, q, T)                       S exp((r - q) T)
    basis_band(S, r, q, T, cost_bp)               (lower, upper) no-arbitrage band around the fair future
    Index(n, seed, ...)                           a synthetic index: weights, betas, idiosyncratic vols, half-spreads
    trade(index, k, jump_bp, leg_us, lag_us, hold_s, seed, n_trades) -> dict
                                                  per-trade capture, costs, tracking noise and net P&L (bp of notional)
    cross_listed(F1, F2, fair_gap)                gap between two listings of one index beyond its fair value, in points
    hedge_ratio(mult1, mult2, fx)                 contracts of listing 2 per contract of listing 1
"""
from __future__ import annotations

import math

import numpy as np

SECONDS_PER_DAY = 23400.0


def covariance(beta, s, sf: float) -> np.ndarray:
    beta, s = np.asarray(beta, float), np.asarray(s, float)
    return np.outer(beta, beta) * sf * sf + np.diag(s * s)


def tracking_var(w, h, cov) -> float:
    d = np.asarray(h, float) - np.asarray(w, float)
    return float(d @ cov @ d)


def partial_basket(w, cov, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Add, one at a time, the name that most reduces the tracking variance with least-squares weights on the chosen
    set; returns (indices, weights on all names)."""
    w = np.asarray(w, float)
    n = len(w)
    target = cov @ w
    chosen: list[int] = []
    best_h = np.zeros(n)
    for _ in range(k):
        best = (math.inf, -1, None)
        for j in range(n):
            if j in chosen:
                continue
            S = chosen + [j]
            hS = np.linalg.solve(cov[np.ix_(S, S)], target[S])
            h = np.zeros(n)
            h[S] = hS
            v = tracking_var(w, h, cov)
            if v < best[0]:
                best = (v, j, h)
        chosen.append(best[1])
        best_h = best[2]
    return np.array(chosen), best_h


def fair_future(S: float, r: float, q: float, T: float) -> float:
    return S * math.exp((r - q) * T)


def basis_band(S: float, r: float, q: float, T: float, cost_bp: float) -> tuple[float, float]:
    f = fair_future(S, r, q, T)
    return f * (1 - cost_bp * 1e-4), f * (1 + cost_bp * 1e-4)


class Index:
    """n names with lognormal capitalisation weights (sigma `conc`), betas 0.6-1.4, idiosyncratic daily volatility
    1-3% and half-spreads that widen for small names: `hs_bp` * (w_max / w)^0.25 basis points."""

    def __init__(self, n: int = 50, seed: int = 0, conc: float = 1.0, sf: float = 0.01, hs_bp: float = 0.5):
        rng = np.random.default_rng(seed)
        cap = np.exp(rng.normal(0.0, conc, n))
        self.w = cap / cap.sum()
        self.beta = rng.uniform(0.6, 1.4, n)
        self.beta = self.beta / float(self.w @ self.beta)          # the index has beta one
        self.s = rng.uniform(0.01, 0.03, n)
        self.sf = sf
        self.hs = hs_bp * (self.w.max() / self.w) ** 0.25
        self.cov = covariance(self.beta, self.s, sf)
        self.n = n


def trade(ix: Index, k: int, jump_bp: float = 3.0, leg_us: float = 20.0, lag_us: float = 400.0, hold_s: float = 10.0,
          fut_hs_bp: float = 0.1, seed: int = 0, n_trades: int = 20000, order: str = "weight") -> dict:
    """The future jumps by `jump_bp`; stock i's quote follows after an exponential lag of mean `lag_us`
    microseconds. The arbitrageur sends its k legs one every `leg_us` microseconds (largest weights first); a leg
    that arrives before its stock's quote has moved buys at the old price and captures beta_i * jump. Costs: the
    half-spread of each leg twice (in and out) and of the future twice. Tracking noise: the basket's idiosyncratic
    difference to the index over `hold_s` seconds. All in basis points of the notional."""
    rng = np.random.default_rng(seed)
    idx, h = partial_basket(ix.w, ix.cov, k)
    hS = h[idx]
    if order == "weight":
        o = np.argsort(-hS)
        idx, hS = idx[o], hS[o]
    arrive = leg_us * np.arange(1, k + 1)
    lags = rng.exponential(lag_us, (n_trades, k))
    early = arrive[None, :] < lags
    capture = (early * (hS * ix.beta[idx])[None, :]).sum(axis=1) * jump_bp
    costs = 2.0 * float(np.sum(hS * ix.hs[idx])) + 2.0 * fut_hs_bp
    te = math.sqrt(tracking_var(ix.w, h, ix.cov) * hold_s / SECONDS_PER_DAY) * 1e4
    noise = rng.standard_normal(n_trades) * te
    pnl = capture - costs + noise
    return {"names": idx, "weights": hS, "capture": float(capture.mean()), "costs": costs, "te": te,
            "mean": float(pnl.mean()), "sd": float(pnl.std()), "sharpe": float(pnl.mean() / pnl.std()),
            "beta_held": float(hS @ ix.beta[idx]), "weight_held": float(hS.sum())}


def cross_listed(F1: float, F2: float, fair_gap: float = 0.0) -> float:
    """Gap between two listings of one index, in index points, beyond the fair gap (quanto, financing, dividends)."""
    return F1 - F2 - fair_gap


def hedge_ratio(mult1: float, mult2: float, fx: float = 1.0) -> float:
    """Contracts of listing 2 per contract of listing 1 for equal exposure: mult1 / (mult2 * fx), with fx the price
    of one unit of listing 2's currency in listing 1's (1.0 for the same currency)."""
    return mult1 / (mult2 * fx)
