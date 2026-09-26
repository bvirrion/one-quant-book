"""Chapter 25 measured data (not a fig_*.py): the pools of runs the performance gate is studied on. First 20 runs of A
set the planted regression at 5% of their median 99th percentile; then 400 interleaved pairs (A B B A ...) of the gate
benchmark, A the engine as it is and B with a busy wait of that many nanoseconds after each event; each run gives its
median and 99th percentile. Output measured_gate_runs.csv."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(ROOT / "code/firm/perfgate"))
import firm_perfgate as pg  # noqa: E402
import firm_ubench as u  # noqa: E402

OUT = ROOT / "figdata/low-latency/25-testing-and-deploying-low-latency-systems"
SRC = "code/low-latency/25-testing-and-deploying-low-latency-systems/cpp/ll_gate_bench.cpp"
PAIRS, RISE = 400, 0.05


def main():
    exe = u.compile_cpp(ROOT / SRC, includes=[ROOT / "code/firm/stratengine/cpp"])
    base = sorted(float(u.run(exe, 0, cpus=6).split()[1]) for _ in range(20))
    extra = round(RISE * (base[9] + base[10]) / 2, 1)
    rows = []
    for i, v in enumerate(pg.interleave(PAIRS)):
        p50, p99 = u.run(exe, extra if v == "B" else 0, cpus=6).split()
        rows.append([i, v, p50, p99])
    u.write_measured(OUT / "measured_gate_runs.csv", ["run", "variant", "p50_ns", "p99_ns"], rows, cpus="6",
                     source=SRC, pairs=PAIRS, planted_wait_ns=extra,
                     run="3 replays of events_small (18,000 timed events), TSC per event, timer cost subtracted")


if __name__ == "__main__":
    main()
