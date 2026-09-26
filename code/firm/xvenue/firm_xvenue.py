"""firm.xvenue -- lead-lag and price discovery across instruments and venues (One Quant Book 11, chapter 8).

Two prices of one thing (a future and its fund, one stock on two venues, a coin on two exchanges) share a common
efficient price; one usually moves first. This module measures who leads and trades it:

* lead estimation on asynchronous ticks with Book 7's Hayashi-Yoshida lead-lag estimator (firm.leadlag);
* price-discovery shares from a vector error-correction model on a regular grid, with the cointegrating vector fixed
  at (1, -1): d p_t = alpha (p1 - p2)_{t-1} + sum_i Gamma_i d p_{t-i} + e_t. The component share of market j is its
  weight in the common trend, gamma = alpha_perp / sum(alpha_perp), alpha_perp = (alpha_2, -alpha_1); the
  information share is the share of the common trend's innovation variance due to market j, whose bounds come from
  the two orderings of the Cholesky factor of Cov(e) (Book 10 ch. 8 defines both shares);
* the edge of trading the lead: when the leader's mid has moved by at least `move` ticks over the last `window`
  seconds and the follower's has not followed, a taker acting `latency` seconds later crosses the follower's spread
  and is marked at the follower's mid H seconds after that; without impact (one lot).

API (stable):
    sample(t, x, grid)                                   the last value at or before each grid time
    lead(t1, x1, t2, x2, lags)                           (estimated lead of series 1 over 2 in seconds, ccf)
    shares(p1, p2, lags)                                 {'alpha', 'component', 'is_low', 'is_high', 'is_mid'} for
                                                         market 1 (market 2's are the complements)
    lead_edge(lead_t, lead_mid, fol_t, fol_bid, fol_ask, latency, move, window, H, fee)
                                                         {'trades', 'edge' (ticks per share, after half-spread and fee)}
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "leadlag"))
import firm_leadlag  # noqa: E402


def sample(t, x, grid) -> np.ndarray:
    t, x = np.asarray(t, float), np.asarray(x, float)
    i = np.clip(np.searchsorted(t, np.asarray(grid, float), side="right") - 1, 0, len(x) - 1)
    return x[i]


def lead(t1, x1, t2, x2, lags) -> tuple[float, np.ndarray]:
    ccf = firm_leadlag.hy_ccf(t1, x1, t2, x2, lags)
    return firm_leadlag.lead_estimate(lags, ccf), ccf


def shares(p1, p2, lags: int = 5) -> dict:
    p = np.column_stack([np.asarray(p1, float), np.asarray(p2, float)])
    dp = np.diff(p, axis=0)
    z = (p[:-1, 0] - p[:-1, 1])
    rows = range(lags, len(dp))
    X = [np.r_[z[k], [dp[k - i, j] for i in range(1, lags + 1) for j in range(2)], 1.0] for k in rows]
    X = np.array(X)
    Y = dp[lags:]
    B, *_ = np.linalg.lstsq(X, Y, rcond=None)
    alpha = B[0]
    E = Y - X @ B
    omega = np.cov(E.T)
    a_perp = np.array([alpha[1], -alpha[0]])
    gamma = a_perp / a_perp.sum()
    out = {"alpha": alpha, "component": float(gamma[0])}
    iss = []
    for order in ((0, 1), (1, 0)):
        Om = omega[np.ix_(order, order)]
        F = np.linalg.cholesky(Om)
        g = gamma[list(order)]
        contrib = (g @ F) ** 2
        tot = contrib.sum()
        iss.append(float(contrib[order.index(0)] / tot))
    out["is_low"], out["is_high"] = min(iss), max(iss)
    out["is_mid"] = 0.5 * (out["is_low"] + out["is_high"])
    return out


def lead_edge(lead_t, lead_mid, fol_t, fol_bid, fol_ask, latency: float, move: float = 1.0, window: float = 1.0,
              H: float = 5.0, fee: float = 0.0) -> dict:
    lead_t, lead_mid = np.asarray(lead_t, float), np.asarray(lead_mid, float)
    fol_t = np.asarray(fol_t, float)
    fol_mid = 0.5 * (np.asarray(fol_bid, float) + np.asarray(fol_ask, float))
    change = np.flatnonzero(np.diff(lead_mid) != 0) + 1
    edges, last = [], -np.inf
    for i in change:
        t = lead_t[i]
        if t - last < window:
            continue
        d_lead = lead_mid[i] - sample(lead_t, lead_mid, [t - window])[0]
        d_fol = sample(fol_t, fol_mid, [t])[0] - sample(fol_t, fol_mid, [t - window])[0]
        gap = d_lead - d_fol
        if abs(gap) < move:
            continue
        s = 1.0 if gap > 0 else -1.0
        te = t + latency
        if te + H > fol_t[-1]:
            break
        px = sample(fol_t, fol_ask if s > 0 else fol_bid, [te])[0]
        later = sample(fol_t, fol_mid, [te + H])[0]
        edges.append(s * (later - px) - fee)
        last = t
    e = np.array(edges)
    return {"trades": int(len(e)), "edge": float(e.mean()) if len(e) else 0.0,
            "se": float(e.std(ddof=1) / np.sqrt(len(e))) if len(e) > 1 else 0.0}
