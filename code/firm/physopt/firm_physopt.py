"""firm.physopt -- storage, transport and cargo options and the hedging programmes that monetise them (Book 9, ch. 22).

Built on Book 6's `firm_energymodel` (two-factor forward curves, Kirk's approximation, the storage `Facility` and
least-squares Monte Carlo). A storage lease is monetised by forward hedges: the intrinsic programme locks today's
best plan and holds its hedges; the rolling-intrinsic programme re-optimises the plan on each month's forward curve and
trades the difference in hedges, paying a cost per unit of forward traded. P&L is realised path by path (physical
cash at spot plus the hedges' marks, zero rates), so the extra value of rolling is measured as a distribution, not
only as a mean. The spread-option view pairs the intrinsic plan's injections with its withdrawals and values each pair
as a calendar-spread option. Transport capacity from hub A to hub B is a strip of spread options on B - A struck at
the variable cost; a cargo that can go to either of two markets is an option on the better netback. NumPy only.

API (stable):
    plans(fac, prices, inv)                      optimal schedules (rows, n) on rows of forward prices, from inventory
    hedge_programme(fac, model, F0, T, ...)      per-path P&L of the intrinsic and rolling-intrinsic programmes
    spread_option_pairs(fac, F0, T, model)       FIFO injection-withdrawal pairs of the intrinsic plan, valued by Kirk
    transport(FA, FB, T, cost, sA, sB, rho)      intrinsic and spread-option value of a strip of monthly capacity
    diversion(F1, F2, K, T, s1, s2, rho)         value of a cargo that may go to market 1 or to market 2 at extra cost K
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "energymodel"))
from firm_energymodel import Facility, TwoFactor, intrinsic, kirk  # noqa: E402,F401


def plans(fac: Facility, prices: np.ndarray, inv: np.ndarray) -> np.ndarray:
    """Best schedule (units injected, negative for withdrawn, per period) on each row of forward prices, starting from
    each row's inventory; zero rates."""
    rows, n = prices.shape
    cap = fac.capacity
    V = np.full((rows, cap + 1), -np.inf)
    V[:, fac.end if fac.end >= 0 else slice(None)] = 0.0
    policy = []
    for m in range(n - 1, -1, -1):
        W, A = np.full_like(V, -np.inf), np.zeros((rows, cap + 1), int)
        for i in range(cap + 1):
            for a in fac.actions(i):
                v = fac.cash(a, prices[:, m]) + V[:, i + a]
                better = v > W[:, i]
                W[:, i], A[:, i] = np.where(better, v, W[:, i]), np.where(better, a, A[:, i])
        V = W
        policy.append(A)
    policy.reverse()
    out, i = np.zeros((rows, n), int), inv.astype(int).copy()
    for m in range(n):
        out[:, m] = policy[m][np.arange(rows), i]
        i = i + out[:, m]
    return out


def _cash(fac: Facility, a: np.ndarray, price: np.ndarray) -> np.ndarray:
    return np.where(a > 0, -a * price - fac.cost_in * a, -a * price + fac.cost_out * a)


def hedge_programme(fac: Facility, model: TwoFactor, F0: list[float], T: list[float], paths: int = 2000,
                    seed: int = 5, cost: float = 0.0, roll: bool = True, gate: bool = False) -> dict:
    """Lock the intrinsic plan with forwards (long what will be injected, short what will be withdrawn); with `roll`,
    re-optimise at each month on the simulated curve and trade the change in hedges at `cost` per unit; with `gate`,
    only where the new plan's value on the curve beats the old plan's by more than that cost. Returns the intrinsic
    value and, per path, the realised P&L and the units of forward traded."""
    chi, xi = model.simulate(T, paths, seed)
    n, rows = len(T), chi.shape[0]
    first = plans(fac, np.array([F0], float), np.array([fac.start]))[0]
    value0 = float(sum(_cash(fac, np.array(first), np.array(F0, float))))
    h = np.tile(first.astype(float), (rows, 1))                        # forward position per delivery month
    prev = np.tile(np.array(F0, float), (rows, 1))
    inv = np.full(rows, fac.start)
    pnl, traded = np.full(rows, -cost * np.abs(first).sum()), np.full(rows, float(np.abs(first).sum()))
    for m in range(n):
        curve = np.column_stack([model.forward(F0[k], T[m], T[k], chi[:, m], xi[:, m]) for k in range(m, n)])
        pnl += (h[:, m:] * (curve - prev[:, m:])).sum(axis=1)             # marks of the hedges
        prev[:, m:] = curve
        if roll:
            new = plans(fac, curve, inv).astype(float)
            dh = np.abs(new - h[:, m:]).sum(axis=1)
            if gate:
                gain = (_cash(fac, new, curve) - _cash(fac, h[:, m:], curve)).sum(axis=1)
                keep = gain <= cost * dh
                new[keep], dh[keep] = h[keep, m:], 0.0
            pnl -= cost * dh
            traded += dh
            h[:, m:] = new
        a = h[:, m].astype(int)
        pnl += _cash(fac, a, curve[:, 0])                  # physical at spot; the month's hedge settles at its mark
        inv = inv + a
    return {"intrinsic": value0, "pnl": pnl, "traded": traded}


def spread_option_pairs(fac: Facility, F0: list[float], T: list[float], model: TwoFactor) -> list[dict]:
    """Match the intrinsic plan's injected units with its withdrawn units first in, first out; value each pair (inject
    in month i, withdraw in month j) as an option on F_j - F_i struck at the two operating costs, expiring at the
    injection, with the model's implied vols and correlation."""
    plan = plans(fac, np.array([F0], float), np.array([fac.start]))[0]
    queue, out = [], []
    for m, a in enumerate(plan):
        queue += [m] * max(a, 0)
        for _ in range(max(-a, 0)):
            i = queue.pop(0)
            te = max(T[i] - 1 / 24, 1 / 365)
            s1, s2 = model.implied_vol(te, T[m]), model.implied_vol(te, T[i])
            rho = model.cov(te, T[m], T[i]) / math.sqrt(model.var(te, T[m]) * model.var(te, T[i]))
            k = fac.cost_in + fac.cost_out
            out.append({"inject": i, "withdraw": m, "intrinsic": F0[m] - F0[i] - k,
                        "option": kirk(F0[m], F0[i], k, te, s1, s2, rho)})
    return out


def transport(FA: list[float], FB: list[float], T: list[float], cost: float, sA: float, sB: float,
              rho: float) -> dict:
    """One unit a month of capacity from A to B: used when B - A exceeds the variable cost."""
    intr = [max(b - a - cost, 0.0) for a, b in zip(FA, FB, strict=True)]
    opt = [kirk(b, a, cost, t, sB, sA, rho) for a, b, t in zip(FA, FB, T, strict=True)]
    return {"intrinsic": sum(intr), "option": sum(opt), "by_month": list(zip(intr, opt, strict=True))}


def diversion(F1: float, F2: float, K: float, T: float, s1: float, s2: float, rho: float) -> dict:
    """A cargo committed to market 1 that may instead go to market 2 at an extra cost K: worth F1 plus a spread option
    on F2 - F1 struck at K."""
    return {"committed": F1, "switch": kirk(F2, F1, K, T, s2, s1, rho), "intrinsic_switch": max(F2 - F1 - K, 0.0)}
