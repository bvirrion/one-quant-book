"""Chapter 8 measured data (not a fig_*.py): nanoseconds per event of four implementations, time and peak memory of the
streamed computation against the chunk size, moving an array to another process (pickled through a pipe, or in shared
memory), and threads under the interpreter lock. Writes measured_*.csv (+ .meta). Run on a quiet machine."""
import multiprocessing as mp
import pathlib
import sys
import time
from multiprocessing import shared_memory

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import pl_pyscale as P  # noqa: E402

OUT = ROOT / "figdata/platforms/08-python-at-scale"
SRC = "code/platforms/08-python-at-scale/python/bench_pyscale.py"
N_BIG, N_LOOP = 2_000_000, 200_000


def _child_pickle(conn):
    a = conn.recv()
    conn.send(float(a.sum()))


def _child_shm(name, n, conn):
    shm = shared_memory.SharedMemory(name=name)
    a = np.ndarray((n,), dtype=np.float64, buffer=shm.buf)
    conn.send(float(a.sum()))
    del a
    shm.close()


def transfer(n: int = 8_000_000):
    """Seconds to get an n-float array (64 MB) summed by a child process: pickled through a pipe, or shared."""
    a = np.random.default_rng(1).standard_normal(n)
    ctx = mp.get_context("fork")
    out = {}
    parent, child = ctx.Pipe()
    p = ctx.Process(target=_child_pickle, args=(child,))
    p.start()
    t = time.perf_counter()
    parent.send(a)
    parent.recv()
    out["pickled through a pipe"] = time.perf_counter() - t
    p.join()
    shm = shared_memory.SharedMemory(create=True, size=a.nbytes)
    try:
        t = time.perf_counter()
        b = np.ndarray(a.shape, dtype=a.dtype, buffer=shm.buf)
        b[:] = a
        parent, child = ctx.Pipe()
        p = ctx.Process(target=_child_shm, args=(shm.name, n, child))
        p.start()
        parent.recv()
        out["shared memory"] = time.perf_counter() - t
        p.join()
        del b
    finally:
        shm.close()
        shm.unlink()
    return out


def main():
    big = P.history(P.GEN / f"pyscale_{N_BIG}.flat", N_BIG)
    small = P.history(P.GEN / f"pyscale_{N_LOOP}.flat", N_LOOP)
    _, rb = P.flat_open(big)
    _, rs = P.flat_open(small)
    rows = [["loop over records", f"{P.timed(P.loop_records, rs, repeat=1) / N_LOOP * 1e9:.1f}"],
            ["loop over lists", f"{P.timed(P.loop_lists, rs) / N_LOOP * 1e9:.1f}"],
            ["array expression", f"{P.timed(P.vectorised, rb) / N_BIG * 1e9:.2f}"],
            ["chunked; 65 536", f"{P.timed(P.chunked, rb, 65_536) / N_BIG * 1e9:.2f}"]]
    u.write_measured(OUT / "measured_methods.csv", ["method", "ns_per_event"], rows, source=SRC,
                     timer="time.perf_counter, best of 3 (records loop: 1 run); loops on 200,000 events, arrays on "
                           "2,000,000")
    rows = []
    for size in (1_000, 10_000, 100_000, 1_000_000):
        rows.append([size, f"{P.timed(P.stream_max, rb, size):.4f}", f"{P.chunk_peak(rb, size) / 1e6:.2f}"])
    rows.append([N_BIG, f"{P.timed(P.whole_max, rb):.4f}", f"{P.whole_day_peak(rb) / 1e6:.2f}"])
    u.write_measured(OUT / "measured_chunks.csv", ["chunk", "seconds", "peak_mb"], rows, source=SRC,
                     timer="time.perf_counter best of 3; peak = tracemalloc peak while computing (the input is "
                           "memory-mapped and not counted); last row: the whole array at once")
    tr = transfer()
    py1, py2 = P.threads_python(5_000_000, 1), P.threads_python(5_000_000, 2)
    a = np.random.default_rng(2).standard_normal(8_000_000)
    np1, np2 = P.threads_numpy(a, 1), P.threads_numpy(a, 2)
    rows = [[k, f"{v:.4f}"] for k, v in tr.items()]
    rows += [["python loop; 1 thread", f"{py1:.4f}"], ["python loop; 2 threads", f"{py2:.4f}"],
             ["numpy sort; 1 thread", f"{np1:.4f}"], ["numpy sort; 2 threads", f"{np2:.4f}"]]
    u.write_measured(OUT / "measured_parallel.csv", ["task", "seconds"], rows, source=SRC,
                     timer="time.perf_counter, one run each; 64 MB array; two threads or two processes at most")


if __name__ == "__main__":
    main()
