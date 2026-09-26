"""Chapter 10 of One Quant Book 13: a message loop in a garbage-collected language, with and without allocation.

The dict book keeps each live order as a Python dict (two orders added for one removed, as a book fills during the
morning): the collector runs, and its full collections scan every live order. The pooled book keeps orders in a
pre-allocated NumPy record array indexed by order id, and allocates nothing per message.
"""
import gc
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/gcwatch"))
import firm_gcwatch as gw  # noqa: E402

LatHist = gw.LatHist


def dict_book():
    book = {}

    def step(k):
        book[k] = {"id": k, "px": 1_000_000 + k % 7, "qty": 100, "fills": [k]}
        if k % 2 == 0 and k - 500 in book:
            del book[k - 500]
    return step


def pooled_book(capacity=1 << 18):
    pool = gw.RecordPool(capacity, gw.MESSAGE)
    buf = pool.buf

    def step(k):
        i = k % capacity
        buf["ts"][i] = k
        buf["price"][i] = 1_000_000 + k % 7
        buf["qty"][i] = 100
    return step


def run(step, n, warm=1000):
    """Per-message latency (ns) and the collector's activity over n messages after a warm-up."""
    for k in range(warm):
        step(k)
    ts = [0] * (n + 1)                      # timestamps only: no call and no allocation between two steps
    gc.collect()                            # start every run with empty young generations: counts are reproducible
    clock = time.perf_counter_ns
    with gw.GcWatch() as w:
        ts[0] = clock()
        for j in range(n):
            step(warm + j)
            ts[j + 1] = clock()
    lat = LatHist()
    for j in range(n):
        lat.record(ts[j + 1] - ts[j])
    return lat, w


def garbage_budget(young_bytes, msgs_per_s, session_s, collections=1):
    """Bytes a message may allocate so that the young generation fills at most `collections` times a session."""
    return collections * young_bytes / (msgs_per_s * session_s)
