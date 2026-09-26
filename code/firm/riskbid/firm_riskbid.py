"""firm.riskbid -- pricing a principal bid for a basket: liquidation cost, the risk carried, competition and the
winner's curse, blind against disclosed; a transition with internal crossing (build of One Quant Book 10, chapter 22).

Notionals in currency; costs in basis points of the basket's gross notional unless said otherwise.

API (stable):
    liquidation(notional, adv, sigma, spread_bp, cap, y)   per name: days to trade at no more than `cap` of daily
                                                   volume (at least one day) and cost in bp of the name's notional,
                                                   half-spread + y sigma sqrt(min(Q / ADV, cap)); {'days', 'cost_bp',
                                                   'total_bp'}
    risk_sd(notional, cov, days, hedge=None)       standard deviation (currency) of the basket's P&L while it is sold
                                                   down in straight lines over each name's days: sum_ij w_i w_j C_ij
                                                   I(d_i, d_j), I(a, b) = a/2 - a^2/(6b) for a <= b; hedge = a factor
                                                   loading vector (e.g. betas) and its daily variance, removed as if
                                                   hedged at once with a future
    profile(notional, adv, sector, edges)          the basket's liquidity profile: its notional by days-of-volume
                                                   bucket and by sector (shares of gross)
    curse(sigma_est, competitors)                  the winner's-curse shading: sigma_est E[max of n + 1 normals]
    auction(true_cost, sigma_est, bidders, shade, margin, trials, seed)   the winner's average profit (bp) when every
                                                   bidder bids estimate + shade + margin
    transition(old, new, cross_share)              notional to trade: selling the old and buying the new, netting the
                                                   names they share, and crossing a share of the rest internally
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rfq"))
from firm_rfq import expected_max_normal  # noqa: E402


def liquidation(notional, adv, sigma, spread_bp, cap: float = 0.2, y: float = 0.7) -> dict:
    q = np.abs(np.asarray(notional, float))
    part = q / np.asarray(adv, float)
    days = np.maximum(1.0, part / cap)
    cost = 0.5 * np.asarray(spread_bp, float) + y * np.asarray(sigma, float) * np.sqrt(np.minimum(part, cap))
    return {"days": days, "cost_bp": cost, "total_bp": float(q @ cost / q.sum())}


def _overlap(d):
    a = np.minimum.outer(d, d)
    b = np.maximum.outer(d, d)
    return a / 2 - a**2 / (6 * b)


def risk_sd(notional, cov, days, hedge=None) -> float:
    w = np.asarray(notional, float)
    c = np.asarray(cov, float)
    if hedge is not None:
        load, var = hedge
        load = np.asarray(load, float)
        c = c - var * np.outer(load, load)       # the factor sold at once with a future
    var = w @ (c * _overlap(np.asarray(days, float))) @ w
    return float(np.sqrt(max(var, 0.0)))


def profile(notional, adv, sector, edges=(0.05, 0.2, 1.0)) -> dict:
    q = np.abs(np.asarray(notional, float))
    dv = q / np.asarray(adv, float)
    b = np.searchsorted(np.asarray(edges), dv)
    sec = np.asarray(sector)
    return {"buckets": np.bincount(b, weights=q, minlength=len(edges) + 1) / q.sum(),
            "sectors": {int(s): float(q[sec == s].sum() / q.sum()) for s in np.unique(sec)}}


def curse(sigma_est: float, competitors: int) -> float:
    return sigma_est * expected_max_normal(competitors + 1)


def auction(true_cost: float, sigma_est: float, bidders: int, shade: float,
            margin: float = 0.0, trials: int = 100_000, seed: int = 1) -> float:
    """Each bidder estimates the cost with an independent error; the lowest bid wins;
    the winner's profit is its bid minus the true cost."""
    rng = np.random.default_rng(seed)
    est = true_cost + sigma_est * rng.standard_normal((trials, bidders))
    win = est.min(axis=1) + shade + margin
    return float(np.mean(win - true_cost))


def transition(old: dict, new: dict, cross_share: float = 0.0) -> dict:
    """old, new: {name: notional}. Returns notional sold and bought: without netting, netted, netted and crossed."""
    names = set(old) | set(new)
    full = sum(old.values()) + sum(new.values())
    sells = sum(max(old.get(k, 0.0) - new.get(k, 0.0), 0.0) for k in names)
    buys = sum(max(new.get(k, 0.0) - old.get(k, 0.0), 0.0) for k in names)
    crossed = cross_share * min(sells, buys) * 2
    return {"full": full, "netted": sells + buys, "crossed": sells + buys - crossed}
