"""firm.gcwatch -- garbage-collector pauses and allocation-free messages for the firm's Python services
(build of One Quant Book 13, chapter 10).

GcWatch installs a gc callback that times every collection (start to stop, nanoseconds) into a firm.lathist histogram
per generation and counts collections; RecordPool is a pre-allocated ring of NumPy records, so that a message loop
writes fields into existing memory instead of creating Python objects; steady_state runs a loop after a warm-up with
the heap frozen and reports the collections it caused.

API (stable):
    GcWatch()   context manager: .pauses[gen] (LatHist of ns), .collections[gen], .total_ns
    RecordPool(n, dtype)   .next() -> index of the next slot (wraps); .buf (the NumPy array)
    steady_state(step, n, warm=1000) -> dict(collections={0: .., 1: .., 2: ..}, pauses=GcWatch)
"""
import gc
import pathlib
import sys
import time

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lathist"))
from firm_lathist import LatHist  # noqa: E402

MESSAGE = np.dtype([("ts", "<i8"), ("price", "<i8"), ("qty", "<u4"), ("side", "u1")])


class GcWatch:
    def __init__(self):
        self.pauses = {g: LatHist() for g in range(3)}
        self.collections = {0: 0, 1: 0, 2: 0}
        self.total_ns = 0
        self._t0 = 0

    def _cb(self, phase, info):
        if phase == "start":
            self._t0 = time.perf_counter_ns()
        else:
            dt = time.perf_counter_ns() - self._t0
            g = info["generation"]
            self.pauses[g].record(dt)
            self.collections[g] += 1
            self.total_ns += dt

    def __enter__(self):
        gc.callbacks.append(self._cb)
        return self

    def __exit__(self, *exc):
        gc.callbacks.remove(self._cb)
        return False


class RecordPool:
    def __init__(self, n, dtype=MESSAGE):
        self.buf = np.zeros(n, dtype=dtype)
        self.n = n
        self.i = -1

    def next(self):
        self.i = (self.i + 1) % self.n
        return self.i


def steady_state(step, n, warm=1000):
    for k in range(warm):
        step(k)
    gc.collect()
    gc.freeze()                       # everything alive now is permanent: collections scan only new objects
    try:
        with GcWatch() as w:
            for k in range(n):
                step(warm + k)
    finally:
        gc.unfreeze()
    return {"collections": dict(w.collections), "pauses": w}
