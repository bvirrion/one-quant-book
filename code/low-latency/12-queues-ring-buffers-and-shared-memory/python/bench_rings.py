"""Chapter 12 measured data (not a fig_*.py): round trips through SPSC rings (threads, processes over shared memory)
and through a mutex-and-condition-variable queue, and one-way SPSC throughput.
Outputs measured_rtt.csv and measured_throughput.csv."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/12-queues-ring-buffers-and-shared-memory"
SRC = "code/low-latency/12-queues-ring-buffers-and-shared-memory/cpp/ll_rings_bench.cpp"


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_rings_bench.cpp", includes=[ROOT / "code/firm/ring/cpp"])
    lines = u.run(exe, 6, 7, 2, 14).strip().splitlines()
    keys = {("SPSC ring", "neighbours"): "threads", ("SPSC ring", "far"): "other-pair",
            ("SPSC over shared memory", "neighbours"): "processes", ("mutex+condvar queue", "neighbours"): "locked"}
    rows = [[*x.split(","), keys[tuple(x.split(",")[:2])]] for x in lines[1:] if not x.startswith("throughput")]
    tp = [x.split(",")[1] for x in lines if x.startswith("throughput")][0]
    meta = dict(cpus="neighbours 6,7; far 2,14 (from chapter 4's matrix)", round_trips=100000, source=SRC)
    u.write_measured(OUT / "measured_rtt.csv", [*lines[0].split(","), "key"], rows, **meta)
    u.write_measured(OUT / "measured_throughput.csv", ["msgs_per_s"], [[tp]], **meta)


if __name__ == "__main__":
    main()
