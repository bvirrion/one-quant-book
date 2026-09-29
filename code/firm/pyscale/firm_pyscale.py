"""firm.pyscale -- chunked pipelines and a time-and-memory probe (build of One Quant Book 15, chapter 8).

A chunked pipeline reads its input as a sequence of slices (a memory-mapped flat file of the tick store, a list of
Parquet partitions), runs a kernel on each slice, and carries between slices the little state the kernel needs to
continue exactly where it stopped (the tail of a rolling window, the last value of a recursive filter). Its peak memory
is set by the chunk size, not by the size of the history. The probe runs a function and reports its wall time and the
peak of memory allocated through Python's tracemalloc (numpy reports its buffers there too).

API (stable):
    chunks(array, size) -> iterator of slices (views, no copy)
    run(source, kernel, state=None) -> (outputs concatenated, final state)
        kernel(chunk, state) -> (output array, new state)
    ewma_kernel(alpha)          recursive exponential average across chunks (state: last value)
    rolling_sum_kernel(window)  rolling sum of the last `window` values across chunks (state: the previous tail)
    probe(fn, *args) -> (result, seconds, peak_bytes)
"""
from __future__ import annotations

import time
import tracemalloc

import numpy as np
from scipy.signal import lfilter


def chunks(a, size: int):
    for s in range(0, len(a), size):
        yield a[s:s + size]


def run(source, kernel, state=None):
    outs = []
    for c in source:
        out, state = kernel(c, state)
        outs.append(out)
    return (np.concatenate(outs) if outs else np.zeros(0)), state


def ewma_kernel(alpha: float):
    """y_t = (1 - alpha) y_{t-1} + alpha x_t, the recursion done by a linear filter over the
    whole chunk; the state is the last y, the filter's start for the next chunk."""
    b, a = [alpha], [1.0, -(1.0 - alpha)]

    def k(x, last):
        x = np.asarray(x, dtype=float)
        if last is None:
            last = x[0]
        y, _ = lfilter(b, a, x, zi=[(1.0 - alpha) * last])
        return y, float(y[-1])
    return k


def rolling_sum_kernel(window: int):
    """Sum of the last `window` values (fewer at the very start), carried across chunks by keeping the previous
    window - 1 values."""
    def k(x, tail):
        x = np.asarray(x, dtype=float)
        tail = np.zeros(0) if tail is None else tail
        full = np.concatenate([tail, x])
        c = np.concatenate([[0.0], np.cumsum(full)])
        idx = np.arange(len(tail), len(full)) + 1
        out = c[idx] - c[np.maximum(idx - window, 0)]
        return out, full[-(window - 1):] if window > 1 else np.zeros(0)
    return k


def probe(fn, *args, **kwargs):
    """Result, wall seconds, and peak bytes allocated (tracemalloc) while fn ran."""
    tracemalloc.start()
    tracemalloc.reset_peak()
    t = time.perf_counter()
    try:
        out = fn(*args, **kwargs)
        dt = time.perf_counter() - t
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return out, dt, peak
