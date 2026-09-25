"""firm.vixetp -- a volatility index, its futures and exchange-traded products (build of One Quant Book 9, chapter 5).

On firm.synthvol's variance path: a VIX-like index, the 21-day implied vol of the index in points (expected variance
over the next 21 days times 1 + vrp); futures on it expiring every 21 trading days, priced at the index level expected
at expiry (reverting to its mean at the variance's speed) times (1 + premium x years to expiry), so that longs pay a
term premium; a long
index of constant 21-day maturity, rebalanced daily between the first two contracts; exchange-traded products that
deliver a multiple (1, -1, 2) of the index's daily return, with an acceleration clause that ends a product whose
value falls to a fraction of the previous close within a day; and the futures the products must trade at each close
to restore their multiple, A x L (L - 1) x r. NumPy only.

API (stable):
    vix_index(v, cfg)                          (T,) index in vol points
    future(x, mean, cfg, h, premium)           futures price on index level x for expiry h years ahead (vectorised)
    curve_path(v, cfg, premium, every)         dict f1, f2 (T,), days to first expiry, weights, cm (T,) daily return
    etp(r, leverage, accel)                    dict value and alive (T + 1,) of a daily-multiple product, 1 at start
    flow(product, r, leverage)                 (T,) futures notional bought at each close per unit of initial value
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "synthvol"))
from firm_synthvol import YEAR, expected_var  # noqa: E402

TAU = 21 / YEAR


def vix_index(v, cfg):
    return 100 * np.sqrt(expected_var(v, cfg, TAU) * (1 + cfg.vrp))


def future(x, mean, cfg, h, premium: float = 0.5):
    """The index x expected at expiry h years ahead, reverting to its stationary mean at the variance's speed, times
    the term premium."""
    x, h = np.asarray(x, float), np.asarray(h, float)
    return (mean + (x - mean) * np.exp(-cfg.kappa * h)) * (1 + premium * h)


def curve_path(v, cfg, premium: float = 0.5, every: int = 21) -> dict:
    """Contracts expire at days every, 2 x every, ...; at each close the first two live ones and a constant-maturity
    long index held from the close before, whose expiring leg settles at the index level."""
    T = len(v)
    t = np.arange(T)
    x = vix_index(v, cfg)
    m = float(x.mean())                                     # the index's stationary mean, estimated on the path
    d1 = every - t % every                                  # days to the first expiry after today (1..every)
    f1 = future(x, m, cfg, d1 / YEAR, premium)
    f2 = future(x, m, cfg, (d1 + every) / YEAR, premium)
    w1 = d1 / every                                         # weight on the first contract
    cm = np.zeros(T)
    for i in range(1, T):
        a = w1[i - 1]
        if d1[i - 1] == 1:                                  # the first contract expires today at the index
            new1, new2 = x[i], f1[i]
        else:
            new1, new2 = f1[i], f2[i]
        cm[i] = (a * new1 + (1 - a) * new2) / (a * f1[i - 1] + (1 - a) * f2[i - 1]) - 1
    return {"f1": f1, "f2": f2, "d1": d1, "w1": w1, "cm": cm, "vix": x, "mean": m}


def etp(r, leverage: float, accel: float = 0.2) -> dict:
    """Value of a product returning leverage x r each day, 1 at start; ended (frozen, alive False) once a day's value
    is at or below accel of the previous close."""
    val, alive = np.ones(len(r) + 1), np.ones(len(r) + 1, bool)
    for i, x in enumerate(r):
        if not alive[i]:
            val[i + 1], alive[i + 1] = val[i], False
            continue
        val[i + 1] = val[i] * max(1 + leverage * x, 0.0)
        alive[i + 1] = val[i + 1] > accel * val[i]
    return {"value": val, "alive": alive}


def flow(product: dict, r, leverage: float):
    """Futures notional the product must buy at each close (negative: sell) to restore its multiple, on every day it
    starts alive (including the day it ends)."""
    value, alive = product["value"], product["alive"]
    return np.where(alive[:-1], value[:-1] * leverage * (leverage - 1) * np.asarray(r, float), 0.0)
