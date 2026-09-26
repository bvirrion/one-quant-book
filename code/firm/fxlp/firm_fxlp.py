"""firm.fxlp -- principal electronic FX liquidity provision (One Quant Book 11, chapter 21).

Built on Book 2's firm.lastlook (the last-look check and its transaction-cost analysis). Prices in basis points of
the rate unless stated; time in milliseconds.

API (stable):
    fair_price(mids, noise_bp, ages_ms, sigma)       inverse-variance average of venue mids, each with its noise and
                                                     the variance accumulated since its last update (sigma^2 * age)
    venue_errors(n, seed, noise_bp, lags_ms, sigma)  RMS error of the primary venue's mid and of the consolidated fair
                                                     price against the true rate
    stream(tiers, hold, threshold, policy, sigma, n, seed)
                                                     per tier and in total: fill ratio, reject rates, mark-out and
                                                     capture per request with firm.lastlook
    internalise(h, seed, trades, size, sigma_day, half_bp, hedge_bp, lam, skew)
                                                     a day of client trades: a share h hedged at once on the primary
                                                     venue, the rest internalised and worked off by skewing the stream;
                                                     spread, hedge cost, inventory risk, objective
    best_hedge_share(grid, **kw)                     the hedge share maximising the objective
    synthetic_cross(a_bid, a_ask, b_bid, b_ask, invert_b)
                                                     the cross A x B (or A / B) from two legs' bids and offers
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lastlook"))
import firm_lastlook as ll  # noqa: E402


def fair_price(mids, noise_bp, ages_ms, sigma: float) -> tuple[float, np.ndarray]:
    mids, noise_bp, ages_ms = (np.asarray(x, float) for x in (mids, noise_bp, ages_ms))
    var = noise_bp ** 2 + sigma ** 2 * ages_ms
    w = (1.0 / var) / np.sum(1.0 / var)
    return float(w @ mids), w


def venue_errors(n: int = 20000, seed: int = 0, noise_bp=(0.3, 0.6, 0.8), lags_ms=(1.0, 3.0, 5.0),
                 sigma: float = 0.05) -> dict:
    """Each venue shows the true rate as it was a random (exponential) time ago, with its own noise; the primary is
    venue 0. The true rate's move since each venue's last update is Brownian with sigma bp per sqrt(ms)."""
    rng = np.random.default_rng(seed)
    noise_bp, lags_ms = np.asarray(noise_bp, float), np.asarray(lags_ms, float)
    ages = rng.exponential(lags_ms, (n, len(lags_ms)))
    moves = rng.standard_normal((n, len(lags_ms))) * sigma * np.sqrt(ages)
    mids = -moves + rng.standard_normal((n, len(lags_ms))) * noise_bp          # true rate at 0
    var = noise_bp ** 2 + sigma ** 2 * ages
    w = (1.0 / var) / np.sum(1.0 / var, axis=1, keepdims=True)
    fair = np.sum(w * mids, axis=1)
    return {"primary": float(np.sqrt(np.mean(mids[:, 0] ** 2))), "consolidated": float(np.sqrt(np.mean(fair ** 2))),
            "best_single": float(min(np.sqrt(np.mean(mids ** 2, axis=0))))}


def stream(tiers: dict, hold: float = 5.0, threshold: float = 0.1, policy: str = "asymmetric", sigma: float = 0.05,
           n: int = 20000, seed: int = 1) -> dict:
    """tiers: name -> (half-spread bp, share of requests, informed share, informed edge bp). Capture per request is
    the fill ratio times the mark-out (bp)."""
    out, tot_req, tot_cap, tot_fill = {}, 0.0, 0.0, 0.0
    for i, (name, (half, share, inf, edge)) in enumerate(tiers.items()):
        reqs = ll.simulate(n, sigma, hold, threshold, policy, inf, edge, seed=seed + i)
        t = ll.tca(reqs, half)
        cap = t["fill_ratio"] * t["markout"]
        out[name] = {**t, "capture": cap, "reject": 1.0 - t["fill_ratio"]}
        tot_req += share
        tot_cap += share * cap
        tot_fill += share * t["fill_ratio"]
    out["all"] = {"capture": tot_cap / tot_req, "reject": 1.0 - tot_fill / tot_req}
    return out


def internalise(h: float, seed: int = 0, trades: int = 20000, size: float = 1.0, sigma_day: float = 60.0,
                half_bp: float = 0.4, hedge_bp: float = 0.25, lam: float = 0.002, skew: float = 0.01) -> dict:
    """A day of `trades` client trades of `size` (millions), evenly spread. A share h of each trade is hedged at once
    on the primary venue at hedge_bp; the rest joins the inventory. The provider skews its stream so that a client is
    more likely to take the side that reduces the inventory: probability 1/2 + skew x inventory (millions), clipped.
    The rate moves by sigma_day bp over the day. Amounts in bp x millions (hundreds of dollars): spread earned, hedge
    cost, standard deviation of the inventory P&L, and the objective spread - hedge - lam x variance."""
    rng = np.random.default_rng(seed)
    u = rng.random(trades)
    inv = np.empty(trades)
    q = 0.0
    for i in range(trades):
        p_reduce = min(max(0.5 + skew * abs(q), 0.0), 0.95)
        reduce = u[i] < p_reduce
        direction = -math.copysign(1.0, q) if q != 0 else (1.0 if u[i] < 0.5 else -1.0)
        client = direction if reduce else -direction            # our inventory change
        q += client * size * (1.0 - h)
        inv[i] = q
    dP = rng.standard_normal(trades) * sigma_day / math.sqrt(trades)
    spread = trades * size * half_bp
    hedge = trades * size * h * hedge_bp
    var = float(np.sum(inv[:-1] ** 2) * sigma_day ** 2 / trades)          # expected variance of the inventory P&L
    return {"spread": spread, "hedge": hedge, "risk_sd": math.sqrt(var), "realised_inv": float(inv[:-1] @ dP[1:]),
            "objective": spread - hedge - lam * var, "end_inventory": float(inv[-1]),
            "mean_abs_inventory": float(np.mean(np.abs(inv)))}


def best_hedge_share(grid=None, **kw) -> tuple[float, dict]:
    grid = np.linspace(0.0, 1.0, 21) if grid is None else grid
    res = {float(h): internalise(float(h), **kw) for h in grid}
    best = max(res, key=lambda k: res[k]["objective"])
    return best, res


def synthetic_cross(a_bid: float, a_ask: float, b_bid: float, b_ask: float,
                    invert_b: bool = False) -> tuple[float, float]:
    """A x B: bid = a_bid * b_bid, ask = a_ask * b_ask; A / B (invert_b): bid = a_bid / b_ask, ask = a_ask / b_bid."""
    if invert_b:
        return a_bid / b_ask, a_ask / b_bid
    return a_bid * b_bid, a_ask * b_ask
