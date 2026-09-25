"""Delta-one and dividend trading (One Quant Book 9, chapter 26).

Synthetic: firm.deltaone's ten years of a futures-implied financing spread (mean 20 bp over the overnight rate,
quarter-end premium 25 bp) and a year of minute mispricings around fair value; index arbitrage with execution lags;
quarterly financing trades entered at the roll or in the quarter-end window; the dividend exposure of a five-year
autocallable from Book 5's pricer; and a dividend futures market whose prices sit 4% per year of maturity below
expected dividends, with recession years that cut dividends by 30%. NumPy.
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
sys.path.insert(0, str(ROOT / "firm" / "deltaone"))
from firm_deltaone import (  # noqa: E402
    DeltaOneConfig,
    dividend_market,
    financing_trade,
    index_arb,
    issuer_dividend_exposure,
    simulate_financing,
)

LAGS = (0, 1, 2, 5)


@functools.lru_cache(maxsize=1)
def market():
    cfg = DeltaOneConfig()
    return cfg, simulate_financing(cfg)


def arbitrage() -> dict:
    """Index arbitrage over a year of minutes, by execution lag: trades, mean bp per trade, total, share winning."""
    cfg, sim = market()
    out = {}
    for lag in LAGS:
        p = index_arb(sim, cfg, lag)["pnl"]
        out[lag] = {"trades": len(p), "mean": float(p.mean()), "total": float(p.sum()), "win": float((p > 0).mean())}
    return out | {"band": 2 * (cfg.basket_cost + cfg.futures_cost)}


def financing() -> dict:
    """Financing trades entered at the quarterly roll (day 0) or in the quarter-end window (day 55): share of quarters
    taken, mean locked spread and P&L a year (bp of notional)."""
    cfg, sim = market()
    out = {}
    for off in (0, 55):
        f = financing_trade(sim, cfg, off)
        out[off] = {"taken": float(f["taken"].mean()), "locked": float(f["locked"].mean()),
                    "annual": float(f["pnl"].sum() / (cfg.days / 252))}
    return out | {"mean_spread": float(sim["spread"].mean()), "hurdle": cfg.own_funding + cfg.capital_charge}


@functools.lru_cache(maxsize=1)
def exposure() -> dict:
    return issuer_dividend_exposure(n_paths=20_000)


@functools.lru_cache(maxsize=1)
def dividends() -> dict:
    """By maturity: expected dividends, futures price, mean annualised holding return, its sd, 5% quantile, chance of
    a loss; and the correlation of the one-year trade with the index in the same year."""
    cfg = DeltaOneConfig()
    d = dividend_market(cfg)
    a = d["annual"]
    return {"expected": d["expected"].tolist(), "futures": d["futures"].tolist(), "mean": a.mean(axis=0).tolist(),
            "sd": a.std(axis=0).tolist(), "q05": np.quantile(a, 0.05, axis=0).tolist(),
            "loss": (d["return"] < 0).mean(axis=0).tolist(),
            "corr": float(np.corrcoef(d["return"][:, 0], d["equity"][:, 0])[0, 1]),
            "recession_return": float(d["return"][d["recession"][:, 0], 0].mean())}
