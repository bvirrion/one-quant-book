"""Chapter 19 measured data (not a fig_*.py): the autocallable script priced by the per-path interpreter and by the
compiled (array) version at several path counts, best of three, one thread. Writes measured_speed.csv (+ .meta)."""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import pl_payoffdsl as P  # noqa: E402

OUT = ROOT / "figdata/platforms/19-pricing-library-architecture"


def best(fn, reps=3):
    b = float("inf")
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        b = min(b, time.perf_counter() - t)
    return b


def main():
    md, script = P.market(), P.products()["autocallable"][0]
    rows = []
    for n in (1_000, 3_000, 10_000, 30_000):
        ti = best(lambda n=n: P.D.ScriptEngine(n_paths=n, mode="interpreted").price(script, P.FP.BlackScholes(), md))
        tc = best(lambda n=n: P.D.ScriptEngine(n_paths=n, mode="compiled").price(script, P.FP.BlackScholes(), md))
        rows.append([n, f"{ti:.5f}", f"{tc:.5f}", f"{ti / tc:.1f}"])
    u.write_measured(OUT / "measured_speed.csv", ["paths", "interpreted_s", "compiled_s", "speedup"], rows,
                     source="code/platforms/19-pricing-library-architecture/python/bench_payoffdsl.py",
                     timer="best of 3, time.perf_counter, path generation included in both")


if __name__ == "__main__":
    main()
