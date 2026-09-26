"""Chapter 6 measured data (not a fig_*.py; `make figdata` never runs it).

measured_churn.csv   ns per destroy+create of a 64-byte order, 10,000 live, by allocator (p50, p99, p99.9, max)
measured_faults.csv  ns per page for the first write to each 4 KiB page of 64 MiB, fresh against pre-faulted
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/06-cpp-for-latency-i-memory"
SRC = "code/low-latency/06-cpp-for-latency-i-memory/cpp/ll_alloc_bench.cpp"


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_alloc_bench.cpp", includes=[ROOT / "code/firm/arena/cpp"])
    for mode in ("churn", "faults"):
        lines = u.run(exe, mode, cpus="2").strip().splitlines()
        u.write_measured(OUT / f"measured_{mode}.csv", lines[0].split(","), [x.split(",") for x in lines[1:]],
                         flags=" ".join(u.DEFAULT), cpus="2", source=SRC)


if __name__ == "__main__":
    main()
