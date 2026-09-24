"""From a raw order-by-order feed to research tables, and what goes wrong on the way (Chapter 28)."""
import pathlib
import statistics
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/feed"))
from firm_feed import Book, decode

SAMPLE = pathlib.Path(__file__).resolve().parents[3] / "firm/feed/data/sample.itch"


def replay(limit: int | None = None):
    """Best bid and offer after every message, and the tape, from the sample file."""
    book, l1 = Book(), []
    for i, m in enumerate(decode(SAMPLE.read_bytes())):
        if limit is not None and i >= limit:
            break
        book.apply(m)
        bb, bq, ba, aq = book.best(7)
        l1.append((m.ts, bb, bq, ba, aq))
    return book, l1


def receive_times(exchange_ns: np.ndarray, base_latency_ns: float, jitter_ns: float, seed: int) -> np.ndarray:
    """What a receiver's clock stamps: exchange time plus a latency that varies message by message."""
    rng = np.random.default_rng(seed)
    return exchange_ns + base_latency_ns + rng.exponential(jitter_ns, len(exchange_ns))


def inversions(exchange_ns: np.ndarray, receive_ns: np.ndarray) -> int:
    """Adjacent pairs that a sort by receive time would put in the wrong order."""
    order = np.argsort(receive_ns, kind="stable")
    return int(np.sum(np.diff(exchange_ns[order]) < 0))


TRADES = [  # (sequence, time, price, shares, condition), one stock, one morning; conditions are this book's labels
    (1, "09:30:00", 100.02, 12_000, "open"), (2, "09:30:04", 100.05, 300, ""), (3, "09:30:09", 100.04, 50, "odd"),
    (4, "09:30:15", 100.07, 500, ""), (5, "09:30:21", 100.06, 200, ""), (6, "09:30:30", 10.01, 400, ""),
    (7, "09:30:31", 100.08, 400, ""), (8, "09:30:40", 100.10, 1_000, ""), (9, "09:30:52", 100.09, 300, "cancelled"),
    (10, "09:31:03", 100.11, 600, ""), (11, "09:31:10", 99.80, 5_000, "late"), (12, "09:31:18", 100.12, 200, ""),
    (13, "09:31:25", 100.13, 700, ""), (14, "09:31:40", 100.12, 100, ""), (15, "09:31:55", 100.15, 900, ""),
]


def vwap(rows) -> float:
    return sum(p * q for _, _, p, q, _ in rows) / sum(q for _, _, _, q, _ in rows)


def clean(rows, band: float = 0.10):
    """Drop cancelled prints, and prints further than `band` from the median price of regular trades."""
    regular = [r for r in rows if r[4] != "cancelled"]
    med = statistics.median(p for _, _, p, _, _ in regular)
    kept = [r for r in regular if abs(r[2] / med - 1.0) <= band]
    return kept, [r for r in rows if r not in kept]
