"""Volatility-book P&L: delta-hedged options by full revaluation, Greek-based explain against it under sticky-strike or
sticky-delta marking, and the roll-down of a term structure (build of Book 5, Chapter 25).

Rates and dividends are zero; time is in years with trading days of 1/252. A surface gives each option its own
implied volatility; the explain uses every option's Greeks at its own volatility.
"""
import math
import pathlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import bs, greeks  # noqa: E402

DT = 1.0 / 252.0


@dataclass(frozen=True)
class Option:
    strike: float
    expiry: float          # in years from the book's time origin
    right: str             # "C" or "P"
    qty: float = 1.0


@dataclass(frozen=True)
class SkewSurface:
    """Implied volatility atm(T) + skew ln(K / X) / sqrt(T): X is the fixed reference spot under sticky strike, the
    current spot under sticky delta (sticky moneyness)."""
    atm: Callable[[float], float]
    skew: float = 0.0
    ref: float | None = None           # None: sticky delta

    def vol(self, strike: float, tau: float, spot: float) -> float:
        x = self.ref if self.ref is not None else spot
        return max(self.atm(tau) + self.skew * math.log(strike / x) / math.sqrt(tau), 1e-4)

    def shifted(self, d_atm: float) -> "SkewSurface":
        return SkewSurface(lambda tau, f=self.atm: f(tau) + d_atm, self.skew, self.ref)


def value(book: Sequence[Option], spot: float, t: float, surf: SkewSurface) -> float:
    total = 0.0
    for o in book:
        tau = o.expiry - t
        if tau <= 1e-12:
            total += o.qty * max((spot - o.strike) if o.right == "C" else (o.strike - spot), 0.0)
        else:
            total += o.qty * bs(spot, o.strike, tau, 0.0, 0.0, surf.vol(o.strike, tau, spot), o.right)
    return total


def book_greeks(book: Sequence[Option], spot: float, t: float, surf: SkewSurface) -> dict[str, float]:
    """Sum of qty x analytic Greeks, each option at its own implied volatility (theta per year)."""
    out = dict.fromkeys(("delta", "gamma", "vega", "theta", "vanna", "volga"), 0.0)
    for o in book:
        tau = o.expiry - t
        if tau <= 1e-12:
            continue
        g = greeks(spot, o.strike, tau, 0.0, 0.0, surf.vol(o.strike, tau, spot), o.right)
        for k in out:
            out[k] += o.qty * g[k]
    return out


def explain(book: Sequence[Option], s0: float, s1: float, t0: float, t1: float, surf0: SkewSurface,
            surf1: SkewSurface, hedge: float = 0.0) -> dict[str, float]:
    """One period's P&L of the book plus `hedge` shares: full revaluation against the Greek explain. Each option's
    volatility change is the change of its own mark (surface and spot both move)."""
    ds, dt = s1 - s0, t1 - t0
    parts = dict.fromkeys(("delta", "gamma", "theta", "vega", "vanna", "volga"), 0.0)
    for o in book:
        tau0, tau1 = o.expiry - t0, o.expiry - t1
        if tau0 <= 1e-12:
            continue
        v0 = surf0.vol(o.strike, tau0, s0)
        dv = (surf1.vol(o.strike, tau1, s1) if tau1 > 1e-12 else v0) - v0
        g = greeks(s0, o.strike, tau0, 0.0, 0.0, v0, o.right)
        parts["delta"] += o.qty * g["delta"] * ds
        parts["gamma"] += o.qty * 0.5 * g["gamma"] * ds * ds
        parts["theta"] += o.qty * g["theta"] * dt
        parts["vega"] += o.qty * g["vega"] * dv
        parts["vanna"] += o.qty * g["vanna"] * ds * dv
        parts["volga"] += o.qty * 0.5 * g["volga"] * dv * dv
    parts["delta"] += hedge * ds
    total = value(book, s1, t1, surf1) - value(book, s0, t0, surf0) + hedge * ds
    parts["total"] = total
    parts["unexplained"] = total - sum(parts[k] for k in ("delta", "gamma", "theta", "vega", "vanna", "volga"))
    return parts


def hedged_pnl(path: Sequence[float], book: Sequence[Option], surfaces: Sequence[SkewSurface], t0: float = 0.0,
               dt: float = DT) -> dict[str, np.ndarray]:
    """Daily delta-hedged P&L of a book along a spot path (one surface per date), with the explain of each day."""
    rows = []
    for i in range(len(path) - 1):
        t = t0 + i * dt
        hedge = -book_greeks(book, path[i], t, surfaces[i])["delta"]
        rows.append(explain(book, path[i], path[i + 1], t, t + dt, surfaces[i], surfaces[i + 1], hedge))
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}


def gamma_scalp(returns: Sequence[float], strike: float = 100.0, days: int = 21, vol: float = 0.18,
                s0: float = 100.0) -> dict:
    """A long straddle bought at implied `vol`, marked and delta-hedged daily at that volatility along the
    given daily log returns: P&L by full revaluation and the cash-gamma sum 1/2 Gamma S^2 (r^2 - vol^2 dt)."""
    path = s0 * np.exp(np.concatenate([[0.0], np.cumsum(returns)]))
    book = [Option(strike, days * DT, "C"), Option(strike, days * DT, "P")]
    flat = SkewSurface(lambda tau: vol)
    res = hedged_pnl(path, book, [flat] * len(path))
    cash_gamma = np.array([0.5 * book_greeks(book, path[i], i * DT, flat)["gamma"] * path[i] ** 2
                           for i in range(len(returns))])
    approx = cash_gamma * (np.asarray(returns) ** 2 - vol * vol * DT)
    return {"path": path, "daily": res["total"], "approx": approx, "cash_gamma": cash_gamma,
            "premium": value(book, s0, 0.0, flat),
            "realised": math.sqrt(float(np.sum(np.asarray(returns) ** 2)) / (len(returns) * DT))}


def roll_down(atm: Callable[[float], float], tau: float, horizon: float) -> float:
    """Change of an option's implied volatility when its expiry shortens by `horizon` along an unchanged term
    structure: atm(tau - horizon) - atm(tau)."""
    return atm(tau - horizon) - atm(tau)
