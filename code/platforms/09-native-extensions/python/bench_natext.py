"""Chapter 9 measured data (not a fig_*.py): per-call cost of the three routes and time per element of the whole-array
kernels against the size. Writes measured_calls.csv and measured_sweep.csv (+ .meta). Run on a quiet machine."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import pl_natext as P  # noqa: E402

OUT = ROOT / "figdata/platforms/09-native-extensions"
SRC = "code/platforms/09-native-extensions/python/bench_natext.py"


def main():
    P.N.cpp_module()
    P.N.rust_library()
    calls = P.per_call()
    u.write_measured(OUT / "measured_calls.csv", ["route", "ns_per_call"],
                     [[k, f"{v:.1f}"] for k, v in calls.items()], source=SRC,
                     timer="time.perf_counter, best of 3 loops of 1,000,000 calls, the Python loop included")
    rows = P.sweep()
    cols = ["n", "ewma_numpy", "ewma_cpp", "ewma_rust", "ewma_python", "asof_numpy", "asof_cpp", "asof_rust"]
    u.write_measured(OUT / "measured_sweep.csv", cols,
                     [[r["n"]] + [f"{r[c]:.3f}" if r[c] == r[c] else "nan" for c in cols[1:]] for r in rows],
                     source=SRC, timer="time.perf_counter, best of 20 (n <= 10,000) or 5 runs; ns per element")


if __name__ == "__main__":
    main()
