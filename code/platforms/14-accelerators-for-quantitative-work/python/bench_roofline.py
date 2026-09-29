"""Chapter 14 measured data (not a fig_*.py): one core's roof (peak by a 2000 x 2000 double matrix product on one BLAS
thread, the best of all its runs; bandwidth by the C++20 triad) and four reference kernels timed on it (best of
five). Writes measured_roof.csv and measured_kernels.csv (+ .meta). Run with OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1
on a quiet machine."""
import pathlib
import sys
import time

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(ROOT / "code/firm/roofline"))
import firm_roofline as R  # noqa: E402
import firm_ubench as u  # noqa: E402

OUT = ROOT / "figdata/platforms/14-accelerators-for-quantitative-work"
SRC = "code/platforms/14-accelerators-for-quantitative-work/python/bench_roofline.py"


def best(fn, reps=5):
    b = float("inf")
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        b = min(b, time.perf_counter() - t)
    return b


def main():
    assert R.one_thread(), "set OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1"
    peak, bw = R.measure_peak(), R.measure_bandwidth()
    rng = np.random.default_rng(14)
    n = 2 ** 23
    S, Z = np.ones(n), rng.standard_normal(n)
    P, A = 500_000, 20
    B, w = rng.lognormal(0, 0.2, (P, A)), np.full(A, 1 / A)
    V = rng.standard_normal((2000, 50, 200))
    M1, M2 = rng.standard_normal((2000, 2000)), rng.standard_normal((2000, 2000))
    cases = [(R.k_path(n), lambda: R.path_step(S, Z, 0.0, 0.01)),
             (R.k_basket(P, A), lambda: R.basket_payoff(B, w, 1.0)),
             (R.k_exposure(2000, 50, 200), lambda: R.exposure_profile(V)),
             (R.k_matmul(2000), lambda: R.matmul(M1, M2))]
    rows = []
    for k, fn in cases:
        t = best(fn)
        rows.append([k.name, f"{k.flops:.4e}", f"{k.bytes:.4e}", f"{k.intensity:.4f}", f"{t:.6f}",
                     f"{k.flops / t / 1e9:.3f}"])
    peak = max(peak, 2.0 * 2000 ** 3 / min(float(r[4]) for r in rows if r[0] == "matrix product"))
    u.write_measured(OUT / "measured_roof.csv", ["quantity", "value"], [["peak_flops", f"{peak:.4e}"],
                     ["bandwidth", f"{bw:.4e}"]], source=SRC,
                     timer="peak: best matrix-product rate (3 + 5 runs); bandwidth: best of 10 triads; one thread")
    u.write_measured(OUT / "measured_kernels.csv", ["kernel", "flops", "bytes", "intensity", "seconds", "gflops"],
                     rows, source=SRC, timer="best of 5, one thread, time.perf_counter")


if __name__ == "__main__":
    main()
