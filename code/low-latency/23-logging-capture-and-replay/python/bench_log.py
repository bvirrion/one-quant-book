"""Chapter 23 measured data (not a fig_*.py): the cost of one log call on the hot path by method (firm.binlog with a
writer thread, snprintf, fprintf to a buffered file, ostringstream), and the speed of replaying a journal through the
strategy engine against the time it recorded. Outputs measured_logcall.csv and measured_replay.csv."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import ll_logging as L  # noqa: E402

OUT = ROOT / "figdata/low-latency/23-logging-capture-and-replay"
SRC = "code/low-latency/23-logging-capture-and-replay/cpp/ll_logbench.cpp"


def main():
    exe = u.compile_cpp(ROOT / SRC, flags=(*u.DEFAULT, "-pthread"),
                        includes=[ROOT / "code/firm/binlog/cpp", ROOT / "code/firm/stratengine/cpp"])
    rows, dropped = [], 0
    for line in u.run(exe, "calls", cpus="6,8").splitlines():
        f = line.split(",")
        if f[0] == "dropped":
            dropped = int(f[1])
        else:
            rows.append(f[1:])
    u.write_measured(OUT / "measured_logcall.csv", ["method", "quantile", "ns"], rows, cpus="6,8", source=SRC,
                     timer="TSC around each call, median timer cost subtracted", binlog_dropped=dropped,
                     writer="binlog writer thread drains to /dev/null; fprintf fully buffered to /dev/null")
    rows = []
    with tempfile.TemporaryDirectory() as d:
        for name, (recs, span, tick) in L.streams().items():
            if span < 1:                             # a synthetic stream has no real time to compare with
                continue
            path = pathlib.Path(d) / "j.bin"
            path.write_bytes(L.journal(recs))
            best = min(float(u.run(exe, "replay", path, tick, cpus=6).split(",")[2]) for _ in range(5))
            rows.append([name, len(recs), f"{span:.3f}", f"{best:.4f}", f"{span / best:.0f}"])
    u.write_measured(OUT / "measured_replay.csv", ["stream", "events", "span_s", "replay_s", "speedup"], rows,
                     cpus="6", source=SRC, timer="TSC around reading the journal and running the engine, best of 5")


if __name__ == "__main__":
    main()
