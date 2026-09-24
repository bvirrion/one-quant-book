"""Convertibles and the credit-equity link (Book 5, Chapter 21): a five-year convertible on a share at 30 with a
conversion price of 40, under a constant hazard and under an equity-to-credit hazard lambda(S) = lambda0
(S / 30)^(-1.2); its bond floor, delta, gamma and credit sensitivity; and the delta-hedged position's P&L when the
share falls 20% and the spread widens 300 bp."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/convertible"))
from firm_convertible import Convertible, greeks, power_hazard, price_grid, value_at  # noqa: E402

R, Q, VOL, S0, LAM0, P, REC = 0.03, 0.01, 0.30, 30.0, 0.05, 1.2, 0.4
CB = Convertible()
STRAIGHT = Convertible(ratio=1e-9, call_trigger=1e12)


@functools.cache
def grid(lam0: float = LAM0, p: float = P, vol: float = VOL, ratio_zero: bool = False):
    cb = STRAIGHT if ratio_zero else CB
    return price_grid(cb, R, Q, vol, power_hazard(lam0, S0, p))


def spread(lam: float) -> float:
    return lam * (1 - REC)


def profile(p: float = P, spots=None) -> dict:
    spots = np.linspace(10.0, 90.0, 81) if spots is None else spots
    g = grid(LAM0, p)
    floor = grid(LAM0, p, ratio_zero=True)
    return {"s": spots, "cb": np.array([value_at(x, g) for x in spots]),
            "floor": np.array([value_at(x, floor) for x in spots]), "conv": CB.ratio * spots,
            "delta": np.array([greeks(x, g, 0.03)["delta"] for x in spots]),
            "gamma": np.array([greeks(x, g, 0.03)["gamma"] for x in spots])}


def table(spots=(20.0, 30.0, 40.0, 60.0, 80.0)) -> dict:
    out = {}
    for name, p in (("constant", 0.0), ("e2c", P)):
        g, fl = grid(LAM0, p), grid(LAM0, p, ratio_zero=True)
        out[name] = [{"s": s, **greeks(s, g, 0.03), "floor": value_at(s, fl), "conv": CB.ratio * s,
                      "premium": value_at(s, g) / (CB.ratio * s) - 1} for s in spots]
    return out


def credit_sensitivity(s: float = S0, p: float = P, bump_bp: float = 10.0) -> dict:
    """Value change for +1 bp of credit spread at today's share price (lambda0 bumped by bump / (1 - R)), per bond,
    and the same for the straight bond."""
    dl = bump_bp / 1e4 / (1 - REC)
    base, up = value_at(s, grid(LAM0, p)), value_at(s, grid(LAM0 + dl, p))
    fb, fu = value_at(s, grid(LAM0, p, ratio_zero=True)), value_at(s, grid(LAM0 + dl, p, ratio_zero=True))
    return {"cs01": (up - base) / bump_bp, "floor_cs01": (fu - fb) / bump_bp}


def rpv01(lam: float, t: float = 5.0) -> float:
    """Risky annuity per unit of spread (continuous premium) for a CDS of maturity t."""
    return (1 - math.exp(-(R + lam) * t)) / (R + lam)


def stress(share_move: float = -0.20, widen_bp: float = 300.0, p: float = P) -> dict:
    """Delta-hedged long convertible (and, second, also hedged with CDS protection sized to its credit sensitivity):
    the share moves by share_move and the credit spread at the new share price ends widen_bp above today's."""
    s1 = S0 * (1 + share_move)
    g0 = grid(LAM0, p)
    v0 = value_at(S0, g0)
    d0 = greeks(S0, g0)["delta"]
    lam_target = (spread(LAM0) + widen_bp / 1e4) / (1 - REC)            # hazard at the new share price
    lam0_new = lam_target / (s1 / S0) ** (-p) if p else lam_target
    v1 = value_at(s1, grid(round(lam0_new, 8), p))
    hedged = v1 - v0 - d0 * (s1 - S0)
    cs01 = credit_sensitivity(S0, p)["cs01"]
    notional = -cs01 / (rpv01(LAM0) * 1e-4)                             # CDS protection per bond, in currency
    cds_pnl = notional * (widen_bp / 1e4) * rpv01(lam_target)
    return {"s1": s1, "v0": v0, "v1": v1, "delta": d0, "unhedged": v1 - v0, "hedged": hedged,
            "cds_notional": notional, "cds_pnl": cds_pnl, "with_cds": hedged + cds_pnl, "lam_target": lam_target}


NO_CALL = Convertible(call_trigger=1e12)


@functools.cache
def grid_no_call(p: float = P):
    return price_grid(NO_CALL, R, Q, VOL, power_hazard(LAM0, S0, p))


def call_effect(spots=(40.0, 52.0, 60.0, 80.0)) -> list[tuple[float, float, float]]:
    """Value with and without the issuer's soft call (from year 2, at 100, if the share is at or above 52)."""
    g, n = grid(), grid_no_call()
    return [(s, value_at(s, g), value_at(s, n)) for s in spots]


def stress_grid(moves=(-0.3, -0.2, -0.1, 0.0, 0.1, 0.2), widens=(0.0, 150.0, 300.0)) -> dict:
    return {w: [stress(m, w)["hedged"] for m in moves] for w in widens}
