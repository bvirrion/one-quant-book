"""Systematic credit and bond-ETF arbitrage (One Quant Book 9, chapter 19).

Synthetic: firm.syscredit's 300 corporate bonds over eight years (durations 1-12, spreads moved by a market factor,
issuer trends, gaps from fair value and noise; expected excess return rising with the square root of duration), traded
on a quarter of days so their prices are stale; value, momentum and low-risk books and their combination; a bond ETF
whose NAV uses stale prices and whose price, in a planted three-week stress, falls 3% below the bonds' true value;
an authorised participant redeeming at the discount. NumPy.
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
sys.path.insert(0, str(ROOT / "firm" / "syscredit"))
from firm_syscredit import YEAR, SysCreditConfig, ap_arbitrage, factor_book, simulate_bonds  # noqa: E402

FACTORS = ("value", "momentum", "lowrisk")
START = 127


@functools.lru_cache(maxsize=1)
def market():
    cfg = SysCreditConfig()
    sim = simulate_bonds(cfg)
    books = {n: factor_book(sim, cfg, n) for n in FACTORS}
    scaled = [b / b[START:].std() for b in books.values()]
    books["combined"] = np.mean(scaled, axis=0) * np.mean([b[START:].std() for b in books.values()])
    return cfg, sim, books


def factors():
    _, _, books = market()
    out = {n: {"sr": float(b[START:].mean() / b[START:].std() * math.sqrt(YEAR)),
               "vol": float(b[START:].std() * math.sqrt(YEAR))} for n, b in books.items()}
    c = np.corrcoef(np.vstack([books[n][START:] for n in FACTORS]))
    return out | {"corr": {"value-momentum": float(c[0, 1]), "value-lowrisk": float(c[0, 2]),
                           "momentum-lowrisk": float(c[1, 2])}}


def etf():
    cfg, sim, _ = market()
    a, b = sim["stress"]
    ap = ap_arbitrage(sim, cfg)
    d = ap["discount"]
    w = slice(a, b + cfg.stress_back)
    stale_gap = (sim["nav"] / sim["basket"] - 1) * 1e4
    return {"discount_normal": float(d[:a].mean()), "discount_sd_normal": float(d[:a].std()),
            "discount_min": float(d.min()), "min_day": int(d.argmin() - a),
            "stale_at_min": float(stale_gap[d.argmin()]), "price_vs_true_at_min":
            float((sim["price"][d.argmin()] / sim["basket"][d.argmin()] - 1) * 1e4),
            "profit_days": int((ap["profit"][w] > 0).sum()), "profit_sum": float(ap["profit"][w].sum()),
            "profit_max": float(ap["profit"].max()), "profit_outside": int((ap["profit"][:a] > 0).sum()),
            "market_move": float(sim["basket"][b] / sim["basket"][a - 1] - 1)}


def stale_gap(trade_prob=0.25):
    """The stale part of the discount (NAV over true value, bp) at its worst, for a bond trading frequency."""
    cfg = SysCreditConfig(trade_prob=trade_prob)
    sim = simulate_bonds(cfg)
    d = (sim["price"] / sim["nav"] - 1) * 1e4
    i = int(d.argmin())
    return {"discount_min": float(d.min()), "stale": float((sim["nav"][i] / sim["basket"][i] - 1) * 1e4),
            "day": i - sim["stress"][0]}
