"""Index and basket arbitrage (One Quant Book 11, chapter 13).

A synthetic index of fifty names (firm.basketarb.Index, seed 1): the future jumps 3 basis points; each stock's quote
follows after an exponential lag of 400 microseconds on average; the arbitrageur buys a partial basket of k names,
one leg every 20 microseconds (or 2), sells the future and holds ten seconds. Net edge per trade and its ratio to its
standard deviation, by basket size.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "basketarb"))
import firm_basketarb as fb  # noqa: E402

KS = (1, 2, 3, 5, 8, 10, 15, 20, 30, 40, 50)


@functools.cache
def index() -> fb.Index:
    return fb.Index(seed=1)


@functools.cache
def sweep(leg_us: float = 20.0, lag_us: float = 400.0) -> dict:
    return {k: fb.trade(index(), k, leg_us=leg_us, lag_us=lag_us) for k in KS}


def best(leg_us: float = 20.0, lag_us: float = 400.0) -> dict:
    s = sweep(leg_us, lag_us)
    return {"mean": max(s, key=lambda k: s[k]["mean"]), "sharpe": max(s, key=lambda k: s[k]["sharpe"])}


def concentration() -> dict:
    ix = index()
    w = np.sort(ix.w)[::-1]
    return {"top5": float(w[:5].sum()), "top10": float(w[:10].sum()), "hs_min": float(ix.hs.min()),
            "hs_max": float(ix.hs.max())}


def dividend_shift_bp(dq: float = 0.002, T: float = 0.25) -> float:
    """Change in the fair future (basis points) when the dividend yield forecast is off by dq over T years."""
    return 1e4 * (np.exp(dq * T) - 1.0)
