"""Chapter 7 measured data (not a fig_*.py): ns per message for three dispatchers and for the static and dynamic
pipelines, on one message type and on a random mix. Output: measured_dispatch.csv (design, one_type, mixed)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/07-cpp-for-latency-ii-compile-time/measured_dispatch.csv"


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_dispatch_bench.cpp", includes=[ROOT / "code/firm/pipeline/cpp"])
    lines = u.run(exe, cpus="2").strip().splitlines()
    u.write_measured(OUT, lines[0].split(","), [x.split(",") for x in lines[1:]], flags=" ".join(u.DEFAULT), cpus="2",
                     source="code/low-latency/07-cpp-for-latency-ii-compile-time/cpp/ll_dispatch_bench.cpp")


if __name__ == "__main__":
    main()
