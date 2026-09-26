"""Chapter 20 measured data (not a fig_*.py): distinct outcomes of 100 reruns of the same recorded input, for the firm's
engine and for the small engine of ll_nondet.hpp with each source of nondeterminism switched on (each rerun is a new
process, so that anything seeded at start-up changes); and the firm engine's time per event. Outputs
measured_nondet.csv and measured_engine.csv."""
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(ROOT / "code/low-latency/19-the-order-book-builder/python"))
import firm_ubench as u  # noqa: E402

OUT = ROOT / "figdata/low-latency/20-the-strategy-engine"
FIXTURE = ROOT / "code/firm/bookbuilder/data/events_small.bin"
RUNS = 100


def build(src, includes, extra=()):
    exe = HERE.parent / "cpp/bin" / pathlib.Path(src).stem
    exe.parent.mkdir(exist_ok=True)
    cmd = ["g++", "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", f"-I{HERE.parent / 'cpp'}",
           *(f"-I{ROOT / i}" for i in includes), str(HERE.parent / "cpp" / src), "-o", str(exe), *extra]
    subprocess.run(cmd, check=True, cwd=ROOT)
    return exe


def main():
    nd = build("ll_nondet.cpp", [], ["-lpthread"])
    er = build("ll_engine_run.cpp", ["code/firm/stratengine/cpp", "code/firm/ubench/cpp"])
    rows = []
    firm = {u.run(er, FIXTURE, 1).split()[0] for _ in range(RUNS)}
    rows.append(["firm engine", "firm", RUNS, len(firm)])
    for mode in ("none", "wall_clock", "hash_order", "two_threads", "all"):
        seen = {u.run(nd, FIXTURE, 1, mode).split()[0] for _ in range(RUNS)}
        rows.append([mode.replace("_", " "), mode, RUNS, len(seen)])
    meta = dict(source="code/low-latency/20-the-strategy-engine/cpp/ll_nondet.cpp, ll_engine_run.cpp",
                input="code/firm/bookbuilder/data/events_small.bin (6,000 events)", runs=RUNS)
    u.write_measured(OUT / "measured_nondet.csv", ["label", "key", "runs", "distinct"], rows, **meta)
    import ll_book
    t = []
    with tempfile.TemporaryDirectory() as d:
        for name, ev, tick in (("large", ll_book.large_tick_events(), 100), ("small", ll_book.small_tick_events(), 1)):
            path = pathlib.Path(d) / f"{name}.bin"
            path.write_bytes(ll_book.mk.pack(ev))
            for line in u.run(er, path, tick, "time", cpus=6).strip().splitlines():
                _, q, ns = line.split(",")
                t.append([name, q, ns])
    u.write_measured(OUT / "measured_engine.csv", ["regime", "quantile", "ns"], t, cpus="6",
                     source="code/low-latency/20-the-strategy-engine/cpp/ll_engine_run.cpp",
                     timer="median TSC timer cost subtracted")


if __name__ == "__main__":
    main()
