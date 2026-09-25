"""firm.simlive -- reconciling simulated and live trading (build of One Quant Book 7, chapter 19).

Fills are arrays of records (t, side, price, qty). The matcher pairs each live fill with a simulated fill of the same
side and price within a time tolerance (greedy, in time order); the parity test reports the share of lots matched on
each side; the waterfall turns a sequence of P&L estimates, each one assumption closer to live, into the steps between
them; calibration picks, on a grid, the simulator parameter whose output is closest to the live one; the
implementation shortfall splits an order's cost against its decision price (Perold). NumPy only.

API (stable):
    FILL                                         dtype (t, side, price, qty)
    as_fills(rows)                               array of FILL from (t, side, price, qty) tuples
    match_fills(live, sim, tol)                  (pairs [(i_live, j_sim, qty)], live lots unmatched, sim lots unmatched)
    parity(live, sim, tol)                       (share of live quantity matched, share of simulated quantity matched)
    fill_pnl(fills, mark)                        per fill: side * qty * (mark - price), summing to the marked P&L
    waterfall(steps)                             [(name, value, change from the previous step)]
    calibrate(grid, metric, target)              (best parameter, its metric): argmin |metric(p) - target|
    implementation_shortfall(side, qty, decision_px, fills, end_px, fee_per_unit)
                                                 {'execution', 'opportunity', 'fees', 'total'} in price x quantity
"""
from __future__ import annotations

import numpy as np

FILL = np.dtype([("t", "f8"), ("side", "i1"), ("price", "f8"), ("qty", "f8")])


def as_fills(rows) -> np.ndarray:
    return np.array([tuple(r) for r in rows], dtype=FILL)


def match_fills(live, sim, tol: float = 1.0):
    """Greedy matching in time order: each live fill takes the earliest unmatched simulated quantity of the same side
    and price within `tol` seconds; partial quantities match partially."""
    live, sim = np.asarray(live, dtype=FILL), np.asarray(sim, dtype=FILL)
    left = sim["qty"].astype(float).copy()
    pairs, live_left = [], 0.0
    for i in np.argsort(live["t"], kind="stable"):
        need = float(live["qty"][i])
        cand = np.flatnonzero((sim["side"] == live["side"][i]) & (sim["price"] == live["price"][i])
                              & (np.abs(sim["t"] - live["t"][i]) <= tol) & (left > 0))
        for j in cand[np.argsort(sim["t"][cand], kind="stable")]:
            q = min(need, left[j])
            if q <= 0:
                continue
            pairs.append((int(i), int(j), q))
            left[j] -= q
            need -= q
            if need <= 0:
                break
        live_left += need
    return pairs, live_left, float(left.sum())


def parity(live, sim, tol: float = 1.0) -> tuple[float, float]:
    pairs, _, _ = match_fills(live, sim, tol)
    m = sum(q for *_, q in pairs)
    lv, sm = float(np.sum(np.asarray(live, dtype=FILL)["qty"])), float(np.sum(np.asarray(sim, dtype=FILL)["qty"]))
    return (m / lv if lv else 1.0), (m / sm if sm else 1.0)


def fill_pnl(fills, mark: float) -> np.ndarray:
    f = np.asarray(fills, dtype=FILL)
    return f["side"] * f["qty"] * (mark - f["price"])


def waterfall(steps) -> list[tuple[str, float, float]]:
    out, prev = [], None
    for name, v in steps:
        out.append((name, float(v), float(v - prev) if prev is not None else 0.0))
        prev = v
    return out


def calibrate(grid, metric, target: float):
    vals = [(p, float(metric(p))) for p in grid]
    return min(vals, key=lambda pv: abs(pv[1] - target))


def implementation_shortfall(side: int, qty: float, decision_px: float, fills, end_px: float,
                             fee_per_unit: float = 0.0) -> dict:
    """Paper portfolio: all of qty at decision_px. Execution cost: what the filled quantity paid beyond the decision
    price; opportunity cost: the unfilled quantity's missed move to end_px; fees on the filled quantity."""
    f = np.asarray(fills, dtype=FILL)
    filled = float(f["qty"].sum())
    execution = float(side * np.sum(f["qty"] * (f["price"] - decision_px)))
    opportunity = float(side * (qty - filled) * (end_px - decision_px))
    fees = fee_per_unit * filled
    return {"execution": execution, "opportunity": opportunity, "fees": fees,
            "total": execution + opportunity + fees}
