"""Credit relative value (One Quant Book 9, chapter 18).

Synthetic: firm.creditrv's forty issuers over ten years, CDS near 120 bp, bond spreads equal to CDS plus a market
funding premium of 15 bp that a planted crisis in year 5 lifts to 150 bp over a quarter and brings back over a year;
the negative-basis book (every bond held against CDS protection, 10% haircut) for traders funding at 0, 30 and 60 bp,
held from day 0 or entered at the trough; the index-against-members and curve trades on their planted noises. NumPy.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "creditrv"))
from firm_creditrv import (  # noqa: E402
    YEAR,
    CreditConfig,
    curve_trade,
    index_arbitrage,
    negative_basis,
    simulate_credit,
)


@functools.lru_cache(maxsize=1)
def market():
    cfg = CreditConfig()
    return cfg, simulate_credit(cfg)


def basis_stats():
    cfg, s = market()
    b = s["basis"].mean(axis=1)
    a = cfg.stress_start
    return {"normal": float(b[:a].mean()), "trough": float(b.min()), "trough_day": int(b.argmin()),
            "trough_year": float(b.argmin() / YEAR), "cds_mean": float(s["cds"].mean())}


def basis_book(own_funding: float = 30.0):
    """Returns on capital: annual before the crisis, the loss from the crisis start to the book's low, the recovery
    after the low, and ten years."""
    cfg, s = market()
    x = negative_basis(s, cfg, own_funding)["on_capital"]
    a = cfg.stress_start
    cum = np.cumsum(x[a:])
    low = int(np.argmin(cum))
    return {"before": float(x[:a].mean() * YEAR), "to_low": float(cum[low]), "low_day": a + low,
            "recovery": float(cum[-1] - cum[low]), "ten_years": float(x.sum()),
            "sr_before": float(x[:a].mean() / x[:a].std() * math.sqrt(YEAR))}


def at_the_trough(own_funding: float = 30.0, hold: int = YEAR):
    """Enter the negative-basis book at the basis's low and hold for a year: return on capital, carry and marks."""
    cfg, s = market()
    nb = negative_basis(s, cfg, own_funding)
    t0 = basis_stats()["trough_day"]
    w = slice(t0, t0 + hold)
    return {"total": float(nb["on_capital"][w].sum()), "carry": float(nb["carry"][w].sum() / cfg.haircut),
            "marks": float(nb["marks"][w].sum() / cfg.haircut)}


def rv_trades():
    cfg, s = market()
    out = {}
    for name, x in (("index", index_arbitrage(s, cfg)), ("curve", curve_trade(s, cfg))):
        out[name] = {"bp": float(x.mean() * YEAR), "sr": float(x.mean() / x.std() * math.sqrt(YEAR)),
                     "active": float((x != 0).mean())}
    return out


def stop_out(own_funding: float = 0.0, limit: float = -0.5):
    """Exercise 7: sell the book when its cumulative return on capital reaches `limit`; the result locked in, the day,
    and what holding to the end earned instead."""
    cfg, s = market()
    x = negative_basis(s, cfg, own_funding)["on_capital"]
    cum = np.cumsum(x)
    hit = np.nonzero(cum <= limit)[0]
    day = int(hit[0]) if len(hit) else len(x) - 1
    return {"locked": float(cum[day]), "day": day, "year": day / YEAR, "held": float(cum[-1])}
