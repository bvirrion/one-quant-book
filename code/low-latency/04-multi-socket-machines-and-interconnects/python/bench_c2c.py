"""Chapter 4 measured data (not a fig_*.py): one-way core-to-core latency for every pair of virtual CPUs.

measured_c2c.csv: a,b,ns (every ordered pair; the diagonal is 0), best of three runs of 20,000 round trips.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figdata/low-latency/04-multi-socket-machines-and-interconnects/measured_c2c.csv"


def main():
    exe = u.compile_cpp(HERE / "cpp/ll_c2c_bench.cpp", includes=[ROOT / "code/firm/memkit/cpp"])
    lines = u.run(exe, 20000).strip().splitlines()
    u.write_measured(OUT, lines[0].split(","), [line.split(",") for line in lines[1:]], flags=" ".join(u.DEFAULT),
                     cpus="each pair in turn", round_trips=20000,
                     source="code/low-latency/04-multi-socket-machines-and-interconnects/cpp/ll_c2c_bench.cpp")


if __name__ == "__main__":
    main()
