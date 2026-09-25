"""firm.flowmm -- a bank flow desk: client mark-outs, tiered pricing, axe skewing, internalisation (Book 9, ch. 24).

A stream of requests for quote from clients with different information. Each request is a client buying or selling
one unit; whoever fills it, an informed client's trade is followed by a drift of the mid in its direction, so the
mid path is the same whatever the desk quotes (common random numbers across pricing policies). The desk quotes a
half-spread, shifted by an axe skew against its inventory; the client trades with the desk with a probability that
falls as the price it pays rises above its own competing quote (captive clients have wide ones, informed clients
narrow ones). The desk holds its inventory, internalising opposite
flows, and hedges in the market only the part beyond a limit, paying the market's half-spread. The franchise P&L is
decomposed into spread capture, the inventory's marks (where adverse selection shows) and hedging costs. Prices in
basis points. NumPy only.

API (stable):
    FlowConfig(...)                             parameters (seed 179)
    simulate_flow(cfg)                          dict: request times' client, side, the mid path and client types
    run_desk(flow, cfg, half_spread, skew, start, end)
                                                per-request results and the P&L decomposition for a pricing policy;
                                                half_spread is a number or an array by client
    client_markouts(res, flow, cfg, horizon)    each client's mean mark-out per trade filled (bp)
    client_hits(res, flow)                      each client's hit ratio
    price_clients(markouts, hits, quoted, cfg)  half-spreads by client from its mark-out and inferred competition
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FlowConfig:
    requests: int = 200_000
    seed: int = 179
    clients: tuple = (60, 20, 10)       # uninformed, moderately informed, informed
    alpha: tuple = (0.0, 0.8, 2.5)      # drift of the mid after a trade, bp, in the client's direction ...
    decay: int = 10                     # ... spread over this many requests
    vol: float = 0.5                    # other mid noise per request, bp
    compete: tuple = ((1.0, 2.5), (0.8, 1.5), (0.4, 0.8))   # range of each type's competing half-spread, bp
    width: float = 0.25                 # softness of the client's choice, bp
    limit: float = 5.0                  # inventory the desk holds before hedging (units)
    hedge_cost: float = 0.5             # market half-spread per unit hedged, bp


def simulate_flow(cfg: FlowConfig | None = None) -> dict:
    cfg = cfg or FlowConfig()
    rng = np.random.default_rng(cfg.seed)
    types = np.repeat(np.arange(3), cfg.clients)
    n = cfg.requests
    client = rng.integers(0, len(types), n)
    side = rng.choice([-1, 1], n)
    alpha = np.array(cfg.alpha)[types[client]]
    drift = np.zeros(n + cfg.decay)
    for k in range(cfg.decay):
        drift[1 + k:n + 1 + k] += side * alpha / cfg.decay
    dmid = drift[:n] + cfg.vol * rng.standard_normal(n)
    lo, hi = np.array(cfg.compete).T
    compete = rng.uniform(lo[types], hi[types])
    return {"client": client, "side": side, "types": types, "mid": np.concatenate([[0.0], np.cumsum(dmid)]),
            "u": rng.random(n), "compete": compete}


def run_desk(flow: dict, cfg: FlowConfig | None = None, half_spread=1.0, skew: float = 0.0, start: int = 0,
             end: int | None = None) -> dict:
    """Quote each request at mid +/- (half_spread - skew x inventory x side); the client takes it with probability
    1 / (1 + exp((paid - compete) / width)). The desk's inventory moves against the client's side; beyond the limit
    it hedges back to the limit. P&L parts (bp): capture (the half-spread paid), marks (inventory x mid change),
    hedging (cost per unit hedged)."""
    cfg = cfg or FlowConfig()
    end = end or cfg.requests
    client, side, mid, u = flow["client"], flow["side"], flow["mid"], flow["u"]
    hs = np.broadcast_to(np.asarray(half_spread, float), (len(flow["types"]),))
    comp = flow["compete"]
    inv, capture, marks, hedged, hedge_cost, absinv = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    filled = np.zeros(end - start, bool)
    paid_all = np.zeros(end - start)
    for i, t in enumerate(range(start, end)):
        c, s = client[t], side[t]
        paid = hs[c] - skew * inv * s
        if u[t] < 1 / (1 + math.exp((paid - comp[c]) / cfg.width)):
            filled[i], paid_all[i] = True, paid
            capture += paid
            inv -= s
            if abs(inv) > cfg.limit:
                h = abs(inv) - cfg.limit
                hedged += h
                hedge_cost += cfg.hedge_cost * h
                inv = math.copysign(cfg.limit, inv)
        marks += inv * (mid[t + 1] - mid[t])
        absinv += abs(inv)
    volume = filled.sum()
    return {"filled": filled, "paid": paid_all, "start": start, "volume": int(volume), "capture": capture,
            "marks": marks, "hedge_cost": hedge_cost, "net": capture + marks - hedge_cost,
            "internalised": 1 - hedged / volume if volume else 0.0, "abs_inventory": absinv / (end - start)}


def client_markouts(res: dict, flow: dict, cfg: FlowConfig | None = None, horizon: int = 20) -> np.ndarray:
    """Mean mark-out per filled trade by client: the mid's move over `horizon` requests against the desk's side."""
    cfg = cfg or FlowConfig()
    t = res["start"] + np.flatnonzero(res["filled"])
    t = t[t + horizon < len(flow["mid"])]
    m = flow["side"][t] * (flow["mid"][t + horizon] - flow["mid"][t])            # the client's gain = the desk's loss
    k = flow["client"][t]
    out = np.full(len(flow["types"]), np.nan)
    for c in range(len(out)):
        if (k == c).any():
            out[c] = m[k == c].mean()
    return out


def client_hits(res: dict, flow: dict) -> np.ndarray:
    """Each client's hit ratio: the share of its requests the desk filled."""
    k = flow["client"][res["start"]:res["start"] + len(res["filled"])]
    n = np.bincount(k, minlength=len(flow["types"]))
    return np.bincount(k, weights=res["filled"], minlength=len(flow["types"])) / np.maximum(n, 1)


GRID = np.arange(0.5, 5.01, 0.05)


def price_clients(markouts: np.ndarray, hits: np.ndarray, quoted: float, cfg: FlowConfig | None = None,
                  grid=GRID) -> np.ndarray:
    """Half-spread by client that maximises (h - mark-out) x win probability, with the client's competing level
    inferred from its hit ratio at the flat quote: c = quoted + width x logit(hit)."""
    cfg = cfg or FlowConfig()
    m = np.nan_to_num(markouts, nan=float(np.nanmean(markouts)))
    p = np.clip(hits, 0.01, 0.99)
    c = quoted + cfg.width * np.log(p / (1 - p))
    win = 1 / (1 + np.exp((grid[None, :] - c[:, None]) / cfg.width))
    return grid[np.argmax((grid[None, :] - m[:, None]) * win, axis=1)]
