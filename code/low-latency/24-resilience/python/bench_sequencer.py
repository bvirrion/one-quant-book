"""Chapter 24 measured data (not a fig_*.py): the rate at which a replica applies a journal, which sets how long a
backup that is not kept hot takes to catch up. Output measured_apply.csv."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

OUT = ROOT / "figdata/low-latency/24-resilience"
SRC = "code/low-latency/24-resilience/cpp/ll_apply_bench.cpp"


def main():
    exe = u.compile_cpp(ROOT / SRC, includes=[ROOT / "code/firm/sequencer/cpp"])
    rows = [line.split(",")[1:] for line in u.run(exe, cpus=6).splitlines() if line.startswith("apply")]
    u.write_measured(OUT / "measured_apply.csv", ["entries", "seconds", "ns_per_entry"], rows, cpus="6", source=SRC,
                     timer="steady_clock around the whole replay, best of 5")


if __name__ == "__main__":
    main()
