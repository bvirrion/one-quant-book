"""Chapter 22 measured data (not a fig_*.py): the cost of one pre-trade check of firm.riskgate (twelve checks) on
the fixture's orders, accepted and refused, and on a stream where every order passes. Output measured_check.csv."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

OUT = ROOT / "figdata/low-latency/22-pre-trade-risk-and-kill-switches"
SRC = "code/low-latency/22-pre-trade-risk-and-kill-switches/cpp/ll_risk_bench.cpp"


def main():
    exe = u.compile_cpp(ROOT / SRC, includes=[ROOT / "code/firm/riskgate/cpp"])
    rows = [line.split(",")[1:] for line in u.run(exe, cpus=6).splitlines()]
    u.write_measured(OUT / "measured_check.csv", ["case", "quantile", "ns", "n"], rows, cpus="6", source=SRC,
                     timer="TSC around each check, median timer cost subtracted",
                     input="code/firm/riskgate/data/events.txt (4,874 orders, 4 timed passes)")


if __name__ == "__main__":
    main()
