"""Chapter 5 measured data (not a fig_*.py): cold and warm (median of 7 interleaved rounds) times of five query shapes
on five engines, answers checked equal first. Writes measured_tsbench.csv (+ .meta). Run on a quiet machine."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import pl_tsbench as P  # noqa: E402

OUT = ROOT / "figdata/platforms/05-time-series-databases-and-the-alternatives"


def main():
    a = P.answers()
    assert all(a["check"].values()), a["check"]
    res = P.run_bench(rounds=7)
    rows = [[r["engine"], r["query"], f"{r['cold'] * 1e3:.3f}", f"{r['median'] * 1e3:.3f}", f"{r['spread'] * 1e3:.3f}"]
            for r in res]
    med = {(r["engine"], r["query"]): r["median"] * 1e3 for r in res}
    wide = [[k, q] + [f"{med[(e, q)]:.3f}" for e in P.ENGINES] for k, q in enumerate(P.QUERIES)]
    u.write_measured(OUT / "measured_tsbench_wide.csv", ["k", "query", *P.ENGINES], wide,
                     source="code/platforms/05-time-series-databases-and-the-alternatives/python/bench_tsbench.py",
                     timer="the median column of measured_tsbench.csv, one column per engine")
    u.write_measured(OUT / "measured_tsbench.csv", ["engine", "query", "cold_ms", "median_ms", "spread_ms"], rows,
                     source="code/platforms/05-time-series-databases-and-the-alternatives/python/bench_tsbench.py",
                     timer="time.perf_counter; cold = first run on a fresh engine instance; warm = median of 7 "
                           "interleaved rounds; one thread; files in the page cache")


if __name__ == "__main__":
    main()
