"""Python at scale (One Quant Book 15, chapter 8).

A synthetic history of tick-store events (the version-1 flat records of chapter 4: a signed quantity on every event)
is reduced to one number per event, the exponentially weighted average of signed volume (alpha = 0.01), four ways: a
Python loop over the memory-mapped records, a Python loop over lists, one array expression (a linear filter), and the
same filter streamed through the file in chunks with the state carried between them. All four agree to 1e-9. The
representations of a column of symbols in pandas, and the costs of moving an array to another process (pickled through
a pipe, or placed in shared memory) and of threads under the interpreter lock, are measured by bench_pyscale.py.
"""
from __future__ import annotations

import pathlib
import sys
import threading
import time

import numpy as np
import pandas as pd
import pyarrow as pa

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("pyscale", "tickstore", "tickcap", "feedhandler", "bookbuilder", "pit"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
from firm_pyscale import chunks, ewma_kernel, probe, run  # noqa: E402
from firm_tickstore import EVENT_V1, FlatWriter, flat_open  # noqa: E402

GEN = ROOT / "data/platforms/generated"
ALPHA = 0.01


def history(path: pathlib.Path, n: int, seed: int = 8) -> pathlib.Path:
    """n version-1 events with a random side and quantity, written as a tick-store flat file (once)."""
    if path.exists() and flat_open(path)[1].shape[0] == n:
        return path
    rng = np.random.default_rng(seed)
    w = FlatWriter(path, 1)
    for s in range(0, n, 1_000_000):
        m = min(1_000_000, n - s)
        rec = np.zeros(m, dtype=EVENT_V1)
        rec["seq"] = np.arange(s + 1, s + m + 1)
        rec["side"] = rng.choice([ord("B"), ord("S")], m)
        rec["qty"] = rng.integers(1, 20, m) * 100
        rec["kind"] = ord("E")
        w.append(rec)
    w.close()
    return path


def signed(rec) -> np.ndarray:
    return np.where(rec["side"] == ord("B"), 1.0, -1.0) * rec["qty"]


def loop_records(rec) -> np.ndarray:
    """Pure Python over the memory-mapped records: every field access builds objects."""
    out = np.empty(len(rec))
    y = None
    for i in range(len(rec)):
        x = (1.0 if rec[i]["side"] == 66 else -1.0) * float(rec[i]["qty"])
        y = x if y is None else (1.0 - ALPHA) * y + ALPHA * x
        out[i] = y
    return out


def loop_lists(rec) -> np.ndarray:
    """Pure Python over lists made once from the arrays: the loop pays for the interpreter."""
    sides, qtys = rec["side"].tolist(), rec["qty"].tolist()
    out = [0.0] * len(sides)
    y = None
    for i in range(len(sides)):
        x = (1.0 if sides[i] == 66 else -1.0) * qtys[i]
        y = x if y is None else (1.0 - ALPHA) * y + ALPHA * x
        out[i] = y
    return np.array(out)


def vectorised(rec) -> np.ndarray:
    return ewma_kernel(ALPHA)(signed(rec), None)[0]


def chunked(rec, size: int) -> np.ndarray:
    return run((signed(c) for c in chunks(rec, size)), ewma_kernel(ALPHA))[0]


def agree(n: int = 20_000, path: pathlib.Path | None = None) -> dict:
    p = history(path or GEN / f"pyscale_{n}.flat", n)
    _, rec = flat_open(p)
    ref = vectorised(rec)
    return {k: float(np.max(np.abs(f - ref))) for k, f in (
        ("loop over records", loop_records(rec)), ("loop over lists", loop_lists(rec)),
        ("chunked, 4096", chunked(rec, 4096)))}


def symbol_memory(n: int = 1_000_000, symbols: int = 50, seed: int = 3) -> dict:
    """Bytes of one column of n symbols (as short strings) in three pandas representations."""
    rng = np.random.default_rng(seed)
    names = np.array([f"S{i:03d}" for i in range(symbols)])[rng.integers(0, symbols, n)]
    obj = pd.Series(names.astype(object))
    return {"object": int(obj.memory_usage(deep=True, index=False)),
            "category": int(obj.astype("category").memory_usage(deep=True, index=False)),
            "arrow string": int(pd.Series(pa.array(names.tolist(), pa.string()),
                                          dtype=pd.ArrowDtype(pa.string())).memory_usage(deep=True, index=False)),
            "numpy fixed width": int(names.nbytes)}


def timed(fn, *args, repeat: int = 3):
    best = None
    for _ in range(repeat):
        t = time.perf_counter()
        fn(*args)
        dt = time.perf_counter() - t
        best = dt if best is None else min(best, dt)
    return best


def threads_python(n: int, k: int) -> float:
    """Wall time of k threads each running a pure-Python loop of n iterations: the interpreter lock serialises them."""
    def work():
        s = 0
        for i in range(n):
            s += i
    ts = [threading.Thread(target=work) for _ in range(k)]
    t = time.perf_counter()
    for x in ts:
        x.start()
    for x in ts:
        x.join()
    return time.perf_counter() - t


def threads_numpy(a: np.ndarray, k: int) -> float:
    """Wall time of k threads each sorting a copy of a: numpy releases the lock inside the sort."""
    copies = [a.copy() for _ in range(k)]
    ts = [threading.Thread(target=np.sort, args=(c,)) for c in copies]
    t = time.perf_counter()
    for x in ts:
        x.start()
    for x in ts:
        x.join()
    return time.perf_counter() - t


def whole_day_peak(rec) -> int:
    """Peak bytes to compute the result on the whole array at once (the input is mapped, not counted)."""
    return probe(whole_max, rec)[2]


def chunk_peak(rec, size: int) -> int:
    """Peak bytes of the streamed computation: one chunk's temporaries and the filter's state."""
    return probe(stream_max, rec, size)[2]


def stream_max(rec, size: int) -> float:
    """The largest |EWMA| of the history, streamed: only one chunk and the filter's state
    are ever in memory."""
    k, state, best = ewma_kernel(ALPHA), None, 0.0
    for c in chunks(rec, size):
        y, state = k(signed(c), state)
        best = max(best, float(np.abs(y).max()))
    return best


def whole_max(rec) -> float:
    return float(np.abs(vectorised(rec)).max())
