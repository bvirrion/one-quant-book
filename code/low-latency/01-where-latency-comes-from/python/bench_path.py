"""Chapter 1 measured data: per-stage latency of the toy path (decode, book, decide, encode) on this machine.

Not a fig_*.py: `make figdata` never runs it. Output: figdata/low-latency/01-where-latency-comes-from/measured_path.csv
(+ .meta). Pinned to one CPU with taskset.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/01-where-latency-comes-from/measured_path.csv"
FLAGS = (*u.DEFAULT,)
CPU = "2"


def main(passes=200):
    exe = u.compile_cpp(HERE / "cpp/ll_path_bench.cpp", flags=FLAGS)
    lines = u.run(exe, passes, cpus=CPU).strip().splitlines()
    header = lines[0].split(",")
    rows = [line.split(",") for line in lines[1:] if not line.startswith("overhead")]
    ovh = [line.split(",")[1] for line in lines if line.startswith("overhead")][0]
    u.write_measured(OUT, header, rows, flags=" ".join(FLAGS), cpus=CPU, passes=passes,
                     timer_overhead_ns=ovh, source="code/low-latency/01-where-latency-comes-from/cpp/ll_path_bench.cpp")


if __name__ == "__main__":
    main()
