"""Chapter 3 measured data (not a fig_*.py; `make figdata` never runs it).

measured_stairs.csv  ns per dependent load against working-set size: random order (4 KiB and huge pages), address order
measured_huge.csv    random chase over 256 MiB, 4 KiB pages against transparent huge pages
measured_false.csv   ns per relaxed increment: one thread; two threads on padded counters; two on one cache line
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/03-memory-hierarchy-and-caches"
SRC = "code/low-latency/03-memory-hierarchy-and-caches/cpp/ll_mem_bench.cpp"


def _table(text):
    lines = text.strip().splitlines()
    return lines[0].split(","), [line.split(",") for line in lines[1:]]


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_mem_bench.cpp", includes=[ROOT / "code/firm/memkit/cpp"])
    flags = " ".join(u.DEFAULT)
    for mode, cpus, args in (("stairs", "2", ()), ("huge", "2", ()), ("false", None, (2, 4))):
        h, rows = _table(u.run(exe, mode, *args, cpus=cpus))
        u.write_measured(OUT / f"measured_{mode}.csv", h, rows, flags=flags, cpus=cpus or "threads pinned to 2 and 4",
                         source=SRC)


if __name__ == "__main__":
    main()
