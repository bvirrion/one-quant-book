"""Chapter 10 measured data (not a fig_*.py): the research pipeline over the month in five engine modes, each in its own
process (wall time and memory high-water mark, minus the imports' baseline); answers checked equal first. Writes
measured_engines.csv (+ .meta). Run on a quiet machine."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import pl_dataframes as P  # noqa: E402

OUT = ROOT / "figdata/platforms/10-dataframes"


def main():
    P.write_month(**P.BIG)
    base = P.measure("baseline")["peak_mb"]
    res = [P.measure(e) for e in P.ENGINES]
    ref = res[0]["answer"]
    assert all(r["answer"] == ref for r in res), "engines disagree"
    rows = [[r["engine"], f"{r['seconds']:.3f}", f"{r['peak_mb'] - base:.1f}"] for r in res]
    u.write_measured(OUT / "measured_engines.csv", ["engine", "seconds", "extra_mb"], rows,
                     source="code/platforms/10-dataframes/python/bench_dataframes.py",
                     timer=f"one run per engine in its own process; memory = VmHWM minus the {base:.0f} MB of a "
                           "process that only imports; POLARS_MAX_THREADS=1, DuckDB threads=1; files in the page cache")


if __name__ == "__main__":
    main()
