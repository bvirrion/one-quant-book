"""Futures market making (One Quant Book 11, chapter 15).

The over-quoting game in a pro-rata book (firm.futmm): aggressors of lognormal size (median 200 lots), makers who earn
one tick a lot and pay 0.01 per squared lot of inventory; the symmetric equilibrium size against the number of makers,
and the fills a very large aggressor gives. Then a strip of four quarterly futures whose calendar-spread books follow
the outrights late: implied-price arbitrages by the spread books' lag.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "futmm"))
import firm_futmm as ff  # noqa: E402

fm = ff.fm
H, GAMMA = 1.0, 0.01
NS = (1, 2, 3, 5, 8, 10, 12, 15, 20)
GRID = np.unique(np.round(np.geomspace(10, 5000, 120)))
LAGS = (0, 1, 3, 5, 10, 20, 30)


@functools.cache
def X() -> np.ndarray:
    return ff.aggressors(20000, 0)


@functools.cache
def game() -> dict:
    x = X()
    q = ff.fifo_size(x, H, GAMMA, GRID)
    big = float(np.quantile(x, 0.999))
    out = {"fifo": q, "p999": big, "median": float(np.median(x)), "mean": float(x.mean())}
    rows = {}
    for n in NS:
        s = q if n == 1 else ff.equilibrium(n, x, H, GAMMA, GRID)
        rows[n] = {"size": s, "factor": s / q, "u_eq": ff.utility(s, (n - 1) * s, x, H, GAMMA),
                   "u_fifo": ff.utility(q, (n - 1) * q, x, H, GAMMA), "big_fill": min(big, n * s) / n,
                   "depth_over_mean": n * s / float(x.mean())}
    out["rows"] = rows
    return out


@functools.cache
def implied() -> dict:
    return {lag: ff.scan(ff.Strip(lag=lag, steps=5000)) for lag in LAGS}


def allocation_example() -> dict:
    """Firm.match on one level: 1,000 lots resting as 100 (top order), 400, 300 and 200; an aggressor of 250."""
    book = [fm.Resting("A", 100, top=True), fm.Resting("B", 400), fm.Resting("C", 300), fm.Resting("D", 200)]
    return {"fifo": fm.fifo(book, 250), "pro_rata": fm.pro_rata(book, 250),
            "top_then_pro_rata": fm.configurable(book, 250, top_pct=100)}


def riskier(gamma: float = 0.02, n: int = 10) -> dict:
    """Exercise 7: the time-priority size and the equilibrium with a larger inventory penalty."""
    q = ff.fifo_size(X(), H, gamma, GRID)
    s = ff.equilibrium(n, X(), H, gamma, GRID)
    return {"fifo": q, "size": s, "factor": s / q}
