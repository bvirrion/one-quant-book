"""firm.wholesale -- retail wholesaling: segmented flow, price improvement, internalisation (One Quant Book 11, ch. 23).

A day of marketable orders in one stock arrives at a wholesaler, which fills them against the national best bid
and offer improved by a share of the half-spread, pays the broker for the flow, keeps the position and hedges on an
exchange whatever exceeds its inventory limit. Retail orders are small and carry little short-term information but
come in waves (herding); institutional orders are larger and informed. Amounts in cents per share unless stated.

API (stable):
    Flow(kind, n, seed, ...)                     orders: time (s), side (+1 buy), size (shares), the mid's move over
                                                 the next minute in the order's direction (information), half-spread
    wholesale(flow, pi_share, pfof, limit, hedge_fee, sigma_day, seed)
                                                 per share traded: capture (half-spread less improvement), mark-out
                                                 (information lost), payment for flow, hedging cost, inventory P&L and
                                                 its standard deviation; net; share of volume hedged
    rule605(flow, pi_share)                      the retail order's statistics: quoted and effective spread, the
                                                 E/Q ratio, price improvement per share and the share improved
"""
from __future__ import annotations

import math

import numpy as np


class Flow:
    """kind 'retail': Poisson arrivals (rate a second), lognormal sizes (median 50 shares), sides from a herding
    sentiment (AR(1) with persistence `herd`), information `info` cents a share in the order's direction over the
    next minute. kind 'institutional': median 2,000 shares, information `info` (larger), no herding."""

    def __init__(self, kind: str = "retail", n: int = 20000, seed: int = 0, rate: float = 1.0, herd: float = 0.995,
                 info: float | None = None, half_spread: float = 1.0, spread_jitter: float = 0.5):
        rng = np.random.default_rng(seed)
        self.kind, self.n = kind, n
        self.t = np.cumsum(rng.exponential(1.0 / rate, n))
        if kind == "retail":
            self.size = np.maximum(1, np.round(rng.lognormal(math.log(50.0), 1.0, n)))
            s = np.empty(n)
            x = 0.0
            z = rng.standard_normal(n)
            for i in range(n):
                x = herd * x + math.sqrt(1.0 - herd * herd) * z[i]
                s[i] = x
            p_buy = 0.5 + 0.3 * np.tanh(s)
            self.side = np.where(rng.random(n) < p_buy, 1.0, -1.0)
            info = 0.1 if info is None else info
        else:
            self.size = np.maximum(100, np.round(rng.lognormal(math.log(2000.0), 0.8, n)))
            self.side = np.where(rng.random(n) < 0.5, 1.0, -1.0)
            info = 1.5 if info is None else info
        self.info = info + rng.standard_normal(n) * 0.0
        self.half = half_spread + spread_jitter * rng.random(n)


def wholesale(flow: Flow, pi_share: float = 0.3, pfof: float = 0.1, limit: float = 10000.0, hedge_fee: float = 0.3,
              sigma_day: float = 100.0, seed: int = 1, day_s: float = 23400.0) -> dict:
    """The wholesaler sells at the offer less pi_share x half-spread (buys at the bid plus it); its inventory takes the
    opposite of each order; beyond +-limit shares it hedges the excess on an exchange at the half-spread plus
    hedge_fee. The mid moves by the orders' information plus noise of sigma_day cents a share over a day."""
    rng = np.random.default_rng(seed)
    n = flow.n
    vol = flow.size.sum()
    capture = float(np.sum(flow.size * flow.half * (1.0 - pi_share)))
    markout = float(np.sum(flow.size * flow.info))                     # information the wholesaler gives up
    pay = pfof * vol
    q, hedge_cost, hedged, inv_pnl = 0.0, 0.0, 0.0, 0.0
    dt = np.diff(np.concatenate([[0.0], flow.t]))
    noise = rng.standard_normal(n) * sigma_day * np.sqrt(dt / day_s)
    for i in range(n):
        inv_pnl += q * noise[i]
        q -= flow.side[i] * flow.size[i]
        if abs(q) > limit:
            x = abs(q) - limit
            hedge_cost += x * (flow.half[i] + hedge_fee)
            hedged += x
            q = math.copysign(limit, q)
    net = capture - markout - pay - hedge_cost + inv_pnl
    return {"volume": float(vol), "capture": capture / vol, "markout": markout / vol, "pfof": pay / vol,
            "hedge": hedge_cost / vol, "inventory": inv_pnl / vol, "net": net / vol, "hedged_share": hedged / vol,
            "net_ex_inventory": (capture - markout - pay - hedge_cost) / vol}


def rule605(flow: Flow, pi_share: float = 0.3) -> dict:
    """Quoted spread 2h, effective spread 2 x (h - improvement), E/Q, improvement a share, share of orders improved."""
    h = flow.half
    eff = 2.0 * h * (1.0 - pi_share)
    w = flow.size / flow.size.sum()
    return {"quoted": float(w @ (2 * h)), "effective": float(w @ eff), "eq": float((w @ eff) / (w @ (2 * h))),
            "improvement": float(w @ (h * pi_share)), "improved_share": 1.0 if pi_share > 0 else 0.0}
