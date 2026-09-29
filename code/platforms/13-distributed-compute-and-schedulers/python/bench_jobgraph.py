"""Chapter 13 measured data (not a fig_*.py): twenty-four small backtests of chapter 11 (level-3 replays of five-minute
firm.tape sessions, seeds 1-24) run through firm.jobgraph's local executor with one worker, in first-in-first-out
order. Writes measured_backtests.csv (+ .meta): the duration of each."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for p in ("code/firm/ubench", "code/firm/jobgraph", "code/firm/btengine",
          "code/platforms/11-backtest-engine-architecture/python"):
    sys.path.insert(0, str(ROOT / p))
import firm_btengine as B  # noqa: E402
import firm_jobgraph as J  # noqa: E402
import firm_ubench as u  # noqa: E402
from pl_btengine import Quoter  # noqa: E402

OUT = ROOT / "figdata/platforms/13-distributed-compute-and-schedulers"


def main():
    data = B.DataAccess(tempfile.mkdtemp())
    names = {s: data.tape(300.0, s) for s in range(1, 25)}           # data first: only the backtests are timed
    tasks = [J.Task(s, 0.0, 0.0) for s in names]
    fns = {s: (lambda n=n: B.Engine(3, Quoter(), data, {"dataset": n, "latency": 20e-6}).run())
           for s, n in names.items()}
    runs = J.LocalExecutor(J.FIFO()).run(tasks, fns)
    rows = [[tid, f"{b - a:.4f}"] for tid, a, b in runs]
    u.write_measured(OUT / "measured_backtests.csv", ["seed", "seconds"], rows,
                     source="code/platforms/13-distributed-compute-and-schedulers/python/bench_jobgraph.py",
                     timer="time.perf_counter around each Engine(3, ...).run() in the local executor, one worker")


if __name__ == "__main__":
    main()
