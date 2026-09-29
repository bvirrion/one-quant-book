"""Native extensions (One Quant Book 15, chapter 9).

The per-call cost of crossing from Python into a native function (a one-step EWMA called a million times through
pybind11, through ctypes, and as a Python function), the time per element of four implementations of the whole-array
EWMA and of the as-of lookup against the array size, and the day computed element by element through the boundary
against the whole array in one call. Timings are taken by bench_natext.py; this module holds the measurements.
"""
from __future__ import annotations

import pathlib
import sys
import time

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "natext"))
import firm_natext as N  # noqa: E402

ALPHA = 0.01


def best(fn, *args, repeat: int = 5) -> float:
    b = None
    for _ in range(repeat):
        t = time.perf_counter()
        fn(*args)
        d = time.perf_counter() - t
        b = d if b is None else min(b, d)
    return b


def loop_of_steps(step, x) -> float:
    """The average computed by calling a one-step function once per element from a Python loop."""
    y = x[0]
    for v in x:
        y = step(y, v, ALPHA)
    return y


def per_call(n: int = 1_000_000) -> dict:
    """Nanoseconds per call of the one-step function, loop included, through each route."""
    x = np.random.default_rng(1).standard_normal(n).tolist()
    return {name: best(loop_of_steps, f, x, repeat=3) / n * 1e9
            for name, f in (("python function", N.step_python), ("C++ via pybind11", N.step_cpp),
                            ("Rust via ctypes", N.step_rust))}


def sweep(sizes=(10, 100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000)) -> list[dict]:
    """Nanoseconds per element of the whole-array EWMA and as-of lookup, by implementation and size."""
    rng = np.random.default_rng(2)
    rows = []
    for n in sizes:
        x = rng.standard_normal(n)
        left = np.sort(rng.integers(0, 10**12, n)).astype(np.int64)
        right = np.sort(rng.integers(0, 10**12, n)).astype(np.int64)
        rep = 20 if n <= 10_000 else 5
        row = {"n": n}
        for name, f in (("numpy", N.ewma_numpy), ("cpp", N.ewma_cpp), ("rust", N.ewma_rust)):
            row[f"ewma_{name}"] = best(f, x, ALPHA, repeat=rep) / n * 1e9
        for name, f in (("numpy", N.asof_numpy), ("cpp", N.asof_cpp), ("rust", N.asof_rust)):
            row[f"asof_{name}"] = best(f, left, right, repeat=rep) / n * 1e9
        row["ewma_python"] = best(N.ewma_python, x, ALPHA, repeat=1) / n * 1e9 if n <= 100_000 else float("nan")
        rows.append(row)
    return rows


def break_even(rows, kernel: str, native: str) -> int | None:
    """The smallest measured size at which the native version is faster than numpy (None if never)."""
    for r in rows:
        if r[f"{kernel}_{native}"] < r[f"{kernel}_numpy"]:
            return r["n"]
    return None
