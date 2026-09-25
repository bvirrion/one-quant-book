"""firm.markout -- measuring market making and execution (build of One Quant Book 7, chapter 23).

Mark-out curves of fills against a reference price path (mid or microprice), by horizon and by group; the horizon at
which a curve settles; fill statistics; the decomposition of a market maker's P&L into spread capture, adverse
selection up to a horizon, inventory after it and fees, which adds up exactly to the P&L marked at the last
reference price; and the implementation-shortfall decomposition of a parent order into delay, execution and
opportunity costs and fees (Perold), with VWAP slippage, as a transaction cost analysis report. NumPy only.

Prices and P&L are in the units given (ticks in the book's simulations); `side` is +1 for a buy, -1 for a sell, from
the point of view of whoever is measured.

API (stable):
    microprice(bid, bid_qty, ask, ask_qty)       the size-weighted mid (Book 7, chapter 8)
    ref_at(ref_t, ref_px, t)                     the reference price in force at each time (last value at or before)
    markouts(t, side, px, ref_t, ref_px, horizons) (fills, horizons): side * (ref(t + h) - px), per unit
    curve(M, qty, groups)                        {group: (mean, se)} quantity-weighted mean mark-out per horizon
    settle_horizon(mean, horizons, tol)          first horizon from which the curve stays within tol of its last value
    fill_rate(posted, filled)                    filled quantity / posted quantity
    hit_ratio(quotes, trades)                    trades won / quotes given
    mm_decompose(t, side, px, qty, ref_t, ref_px, H, fee, t_end)
                                                 {'spread', 'adverse', 'inventory', 'fees', 'total'}, exact
    shortfall(side, target, decision_px, arrival_px, fills, end_px, fee)
                                                 {'delay', 'execution', 'opportunity', 'fees', 'total', 'filled'}
    vwap_slippage(side, fills, mkt_px, mkt_qty)  average fill price against the market's VWAP, signed as a cost
    tca_report(name, shortfall, vwap_slip, unit) text
"""
from __future__ import annotations

import numpy as np


def microprice(bid, bid_qty, ask, ask_qty):
    bid, ask = np.asarray(bid, float), np.asarray(ask, float)
    bq, aq = np.asarray(bid_qty, float), np.asarray(ask_qty, float)
    return (bid * aq + ask * bq) / (aq + bq)


def ref_at(ref_t, ref_px, t):
    i = np.searchsorted(np.asarray(ref_t), np.asarray(t, float), side="right") - 1
    return np.asarray(ref_px, float)[np.clip(i, 0, len(ref_px) - 1)]


def markouts(t, side, px, ref_t, ref_px, horizons):
    t, side, px = (np.asarray(a, float) for a in (t, side, px))
    return np.column_stack([side * (ref_at(ref_t, ref_px, t + h) - px) for h in horizons])


def curve(M, qty, groups=None):
    M, qty = np.asarray(M, float), np.asarray(qty, float)
    groups = np.zeros(len(qty), int) if groups is None else np.asarray(groups)
    out = {}
    for g in np.unique(groups):
        m, w = M[groups == g], qty[groups == g]
        mean = w @ m / w.sum()
        var = (w[:, None] ** 2 * (m - mean) ** 2).sum(axis=0) / w.sum() ** 2
        out[g.item() if hasattr(g, "item") else g] = (mean, np.sqrt(var))
    return out


def settle_horizon(mean, horizons, tol: float):
    mean = np.asarray(mean, float)
    ok = np.abs(mean - mean[-1]) <= tol
    for i in range(len(ok)):
        if ok[i:].all():
            return horizons[i]
    return horizons[-1]


def fill_rate(posted, filled) -> float:
    return float(np.sum(filled) / np.sum(posted))


def hit_ratio(quotes: int, trades: int) -> float:
    return trades / quotes


def mm_decompose(t, side, px, qty, ref_t, ref_px, H: float, fee: float = 0.0, t_end: float | None = None):
    """For each fill, ref(T) - px = [ref(t) - px] + [ref(min(t + H, T)) - ref(t)] + [ref(T) - ref(min(t + H, T))]:
    spread capture, adverse selection up to H, inventory after H; times side * qty and summed. The total is the P&L
    of the fills with the final position marked at ref(T), minus fees (fee per unit traded)."""
    t, side, px, qty = (np.asarray(a, float) for a in (t, side, px, qty))
    T = float(ref_t[-1]) if t_end is None else t_end
    r0 = ref_at(ref_t, ref_px, t)
    rh = ref_at(ref_t, ref_px, np.minimum(t + H, T))
    rT = float(ref_at(ref_t, ref_px, [T])[0])
    w = side * qty
    out = {"spread": float(w @ (r0 - px)), "adverse": float(w @ (rh - r0)), "inventory": float(w @ (rT - rh)),
           "fees": -fee * float(qty.sum())}
    out["total"] = out["spread"] + out["adverse"] + out["inventory"] + out["fees"]
    return out


def shortfall(side: int, target: float, decision_px: float, arrival_px: float, fills, end_px: float, fee: float = 0.0):
    """Implementation shortfall of a parent order against the paper portfolio traded at the decision price, as a
    cost (positive = worse): delay (decision to arrival, on the filled quantity), execution (fills against arrival),
    opportunity (the unfilled quantity's move from decision to the end), fees. fills: [(price, qty)]."""
    f = np.asarray(fills, float).reshape(-1, 2)
    q = float(f[:, 1].sum())
    cost = {"delay": side * q * (arrival_px - decision_px), "execution": side * float(f[:, 1] @ (f[:, 0] - arrival_px)),
            "opportunity": side * (target - q) * (end_px - decision_px), "fees": fee * q}
    cost["total"] = sum(cost.values())
    cost["filled"] = q
    return cost


def vwap_slippage(side: int, fills, mkt_px, mkt_qty) -> float:
    f = np.asarray(fills, float).reshape(-1, 2)
    avg = float(f[:, 1] @ f[:, 0] / f[:, 1].sum())
    vwap = float(np.asarray(mkt_qty, float) @ np.asarray(mkt_px, float) / np.sum(mkt_qty))
    return side * (avg - vwap)


def tca_report(name: str, sf: dict, vwap_slip: float, unit: str = "ticks") -> str:
    q = sf["filled"]
    lines = [f"TCA {name}: filled {q:g}"]
    for k in ("delay", "execution", "opportunity", "fees", "total"):
        lines.append(f"  {k:<12s} {sf[k]:12.2f} {unit}   {sf[k] / max(q, 1e-12):8.4f} per unit filled")
    lines.append(f"  VWAP slippage {vwap_slip:8.4f} {unit} per unit")
    return "\n".join(lines)
