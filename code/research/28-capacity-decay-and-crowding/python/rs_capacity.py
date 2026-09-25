"""Capacity, decay and crowding (One Quant Book 7, chapter 28).

Part A: chapter 27's fifty-name book at fund sizes from $10 million to $30 billion, as a fixed rule (costs ignored, the
forecast smoothed over fifty days) and re-optimised at each size (costs inside, smoothed over a day): capacity curves,
the profit-maximising size and the size at which the net Sharpe ratio halves.
Part B: five funds of $2 billion each hold long-short books of 500 stocks (gross four times capital, 100 names a side,
daily volatility 2%, $200 million traded a day in each), made of a common book and their own, with a given overlap.
One fund sells a fraction of its book over three days; square-root impact (eta 0.7), 30% permanent, the rest decaying
with a half-life of one day. The other funds' losses against the fraction sold and the overlap. NumPy only.
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

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "firm" / "capacity"))
sys.path.insert(0, str(HERE.parents[2] / "27-transaction-costs-in-research" / "python"))
from firm_capacity import capacity_curve, overlap, profit_maximising, size_at_fraction  # noqa: E402
from firm_capacity import unwind as simulate_unwind  # noqa: E402
from rs_tcost import run  # noqa: E402

SIZES = (1e7, 3e7, 1e8, 3e8, 1e9, 2e9, 3e9, 5e9, 1e10, 3e10)
N_STOCKS, N_SIDE, FUNDS, CAPITAL, GROSS = 500, 100, 5, 2e9, 4.0
SIGMA, ADV, ETA, PERMANENT, HALF_LIFE, DAYS, HORIZON = 0.02, 2e8, 0.7, 0.3, 1.0, 3, 15
OVERLAPS, FRACTIONS = (0.25, 0.5, 0.75, 1.0), (0.1, 0.25, 0.5, 1.0)


@functools.lru_cache(maxsize=2)
def curve(book: str):
    """'fixed' (costs ignored, 50-day smoothing) or 'optimised' (costs inside, 1-day smoothing)."""
    args = ("naive", 50.0) if book == "fixed" else ("cost-aware", 1.0)
    rows = [run(args[0], a, args[1]) for a in SIZES]
    return capacity_curve(SIZES, [r["ret"] - r["cost"] for r in rows], [r["vol"] for r in rows])


@functools.lru_cache(maxsize=1)
def base_books(seed: int = 28):
    rng = np.random.default_rng(seed)

    def long_short(score):
        w = np.zeros(N_STOCKS)
        o = np.argsort(score)
        w[o[-N_SIDE:]], w[o[:N_SIDE]] = GROSS / 2 / N_SIDE, -GROSS / 2 / N_SIDE
        return w
    common = rng.standard_normal(N_STOCKS)
    own = rng.standard_normal((FUNDS, N_STOCKS))
    return common, own, long_short


def books(theta: float):
    """Each fund ranks stocks on theta * common score + sqrt(1 - theta^2) * its own and holds the top and bottom 100."""
    common, own, long_short = base_books()
    return np.array([long_short(theta * common + math.sqrt(1 - theta * theta) * own[k]) for k in range(FUNDS)])


@functools.lru_cache(maxsize=32)
def unwind(theta: float, fraction: float):
    B = books(theta)
    out = simulate_unwind(B, np.full(FUNDS, CAPITAL), 0, fraction, DAYS, np.full(N_STOCKS, ADV),
                          np.full(N_STOCKS, SIGMA), ETA, PERMANENT, HALF_LIFE, HORIZON)
    others = out["cum"][:, 1:].mean(axis=1)
    ov = float(np.mean([overlap(B[0], B[k]) for k in range(1, FUNDS)]))
    return {"peak": float(others.min()), "day": int(np.argmin(others)) + 1, "end": float(others[-1]),
            "seller": float(out["cum"][-1, 0]), "overlap": ov,
            "path": others, "price": out["price"]}


def summary():
    return {"fixed_max": profit_maximising(curve("fixed")), "fixed_half": size_at_fraction(curve("fixed"), 0.5),
            "opt_max": profit_maximising(curve("optimised")), "opt_half": size_at_fraction(curve("optimised"), 0.5)}
