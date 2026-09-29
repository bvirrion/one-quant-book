"""Book 18, chapter 24: the Python coding answers."""
from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np


def read_fills(path):
    """Yield (symbol, qty, price) from a CSV of fills one line at a time: constant memory."""
    with open(path, encoding="ascii") as f:
        next(f)  # header
        for line in f:
            sym, qty, px = line.rstrip("\n").split(",")
            yield sym, int(qty), float(px)


def large_fills(rows, min_notional):
    return (r for r in rows if abs(r[1]) * r[2] >= min_notional)


def notional_by_symbol(rows):
    out = {}
    for sym, qty, px in rows:
        out[sym] = out.get(sym, 0.0) + qty * px
    return out


@contextmanager
def temporary_limit(limits, key, value):
    """Change a risk limit for a block and restore it even if the block raises."""
    old = limits[key]
    limits[key] = value
    try:
        yield limits
    finally:
        limits[key] = old


def rolling_mean_loop(x, k):
    return [sum(x[i - k + 1 : i + 1]) / k for i in range(k - 1, len(x))]


def rolling_mean_vec(x, k):
    """Rolling mean by cumulative sums: O(n), no Python loop."""
    c = np.cumsum(np.concatenate([[0.0], np.asarray(x, dtype=float)]))
    return (c[k:] - c[:-k]) / k


@dataclass(frozen=True)
class OrderKey:
    """A value type usable as a dict key: equality and hash from the fields, immutable."""

    venue: str
    client_order_id: int
