"""Flow market making at a bank (One Quant Book 9, chapter 24).

Synthetic: firm.flowmm's 200,000 requests for quote from 90 clients (60 uninformed, 20 moderately informed, 10
informed), each with its own competing quote. The first half is quoted flat at 1.2 bp; each client's mark-out and hit
ratio are estimated from it; the second half compares flat quotes with prices by client, with and without an axe skew,
and decomposes the franchise P&L. Prices in basis points. NumPy.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "flowmm"))
from firm_flowmm import FlowConfig, client_hits, client_markouts, price_clients, run_desk, simulate_flow  # noqa: E402

FLAT = 1.2
HORIZON = 20
TYPES = ("uninformed", "moderate", "informed")


@functools.lru_cache(maxsize=1)
def market():
    cfg = FlowConfig()
    flow = simulate_flow(cfg)
    half = cfg.requests // 2
    hist = run_desk(flow, cfg, FLAT, 0.0, 0, half)
    m, h = client_markouts(hist, flow, cfg, HORIZON), client_hits(hist, flow)
    return cfg, flow, half, m, h, price_clients(m, h, FLAT, cfg)


@functools.cache
def policy(kind: str, level: float) -> dict:
    """The second half under a flat half-spread (kind 'flat', level = the half-spread) or client prices with an axe skew
    (kind 'priced', level = the skew, bp per unit of inventory)."""
    cfg, flow, half, _, _, hs = market()
    return run_desk(flow, cfg, level, 0.0, half) if kind == "flat" else run_desk(flow, cfg, hs, level, half)


def by_type(res: dict) -> dict:
    """Per client type: trades, capture per trade, mark-out per trade (horizon 20), net per trade."""
    _, flow, _, _, _, _ = market()
    t = res["start"] + np.flatnonzero(res["filled"])
    ty = flow["types"][flow["client"][t]]
    paid = res["paid"][res["filled"]]
    ok = t + HORIZON < len(flow["mid"])
    later = flow["mid"][np.minimum(t + HORIZON, len(flow["mid"]) - 1)]
    mo = np.where(ok, flow["side"][t] * (later - flow["mid"][t]), 0)
    out = {}
    for k, name in enumerate(TYPES):
        sel = ty == k
        n = int(sel.sum())
        out[name] = {"trades": n, "capture": float(paid[sel].mean()) if n else 0.0,
                     "markout": float(mo[sel & ok].mean()) if n else 0.0,
                     "net": float(paid[sel].mean() - mo[sel & ok].mean()) if n else 0.0}
    return out


def estimates() -> dict:
    """How well the history identifies clients: mean estimated mark-out and price by true type, and the correlation of
    estimated with inferred competing quotes."""
    cfg, flow, _, m, h, hs = market()
    c_hat = FLAT + cfg.width * np.log(np.clip(h, 0.01, 0.99) / (1 - np.clip(h, 0.01, 0.99)))
    return {name: {"markout": float(np.nanmean(m[flow["types"] == k])), "price": float(hs[flow["types"] == k].mean()),
                   "hit": float(h[flow["types"] == k].mean())} for k, name in enumerate(TYPES)} | {
        "compete_corr": float(np.corrcoef(c_hat, flow["compete"])[0, 1])}


def summary(res: dict) -> dict:
    return {k: res[k] for k in ("volume", "capture", "marks", "hedge_cost", "net", "internalised", "abs_inventory")}


def markout_curve(horizons=range(0, 41, 2)) -> dict:
    """Mean mark-out by client type against the horizon, trades filled in the flat history."""
    cfg, flow, half, _, _, _ = market()
    hist = run_desk(flow, cfg, FLAT, 0.0, 0, half)
    t = np.flatnonzero(hist["filled"])
    ty = flow["types"][flow["client"][t]]
    return {h: [float((flow["side"][t[ty == k]] * (flow["mid"][t[ty == k] + h] - flow["mid"][t[ty == k]])).mean())
                for k in range(3)] for h in horizons}
