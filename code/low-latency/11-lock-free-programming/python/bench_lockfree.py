"""Chapter 11 measured data (not a fig_*.py): measured_counters.csv (four counters, 1-4 threads), measured_aba.csv
(the untagged stack), measured_litmus.csv (store-buffer outcomes by memory ordering, a million trials each).
At most four threads (user ruling for the batch)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/11-lock-free-programming"
SRC = "code/low-latency/11-lock-free-programming/cpp/ll_lockfree_bench.cpp"


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_lockfree_bench.cpp", includes=[ROOT / "code/firm/memkit/cpp"])
    lines = u.run(exe, "counters").strip().splitlines()
    rows = [x.split(",") for x in lines[1:]]
    designs = ["mutex", "CAS loop", "fetch_add", "per-thread"]
    by = {(d, int(t)): v for d, t, v in rows}
    header = ["threads", *[d.replace(" ", "_").replace("-", "_") for d in designs]]
    u.write_measured(OUT / "measured_counters.csv", header, [[t, *[by[(d, t)] for d in designs]] for t in (1, 2, 3, 4)],
                     cpus="unpinned (1-4 threads)", source=SRC)
    lines = u.run(exe, "aba").strip().splitlines()
    u.write_measured(OUT / "measured_aba.csv", lines[0].split(","), [x.split(",") for x in lines[1:]],
                     cpus="unpinned (2 threads)", source=SRC)
    lines = u.run(exe, "litmus").strip().splitlines()
    u.write_measured(OUT / "measured_litmus.csv", lines[0].split(","), [x.split(",") for x in lines[1:]],
                     cpus="unpinned (2 threads)", source=SRC)


if __name__ == "__main__":
    main()
