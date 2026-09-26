"""Chapter 16 figure data (deterministic: the simulator is seeded): 60 seconds of the lossy A and B lines, the gaps on
each and on the arbitrated stream. Outputs gaps_events_A.csv, gaps_events_B.csv, gaps_events_arb.csv and
gaps_summary.csv."""
import csv
import heapq
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_lines as L  # noqa: E402

ROOT = HERE.parents[3]
OUT = ROOT / "figdata/low-latency/16-protocols-ii-binary-exchange-protocols"
SECONDS = 60


def arb_events(a, b):
    merged = heapq.merge(((t, 0, p) for t, p in a), ((t, 1, p) for t, p in b), key=lambda x: (x[0], x[1]))
    nxt, out = 1, []
    for t, _, p in merged:
        seq, count = L.header(p)
        count = 0 if count == 0xFFFF else count
        if count and seq + count <= nxt:
            continue
        if seq > nxt:
            out.append(((t - L.OPEN) / L.SEC, seq - nxt))
        nxt = max(nxt, seq + count)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        L.record(SECONDS, d)
        a, b = L.packets(pathlib.Path(d) / "lineA.bin"), L.packets(pathlib.Path(d) / "lineB.bin")
    for name, ev in (("A", L.gap_events(a)), ("B", L.gap_events(b)), ("arb", arb_events(a, b))):
        with open(OUT / f"gaps_events_{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t_s", "missing", "y"])
            y = {"A": 3, "B": 2, "arb": 1}[name]
            w.writerows([[f"{t:.4f}", m, y] for t, m in ev])
    with open(OUT / "gaps_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stream", "packets", "messages", "gaps", "missing", "duplicates"])
        w.writerow(["A", *L.line_gaps(a), 0])
        w.writerow(["B", *L.line_gaps(b), 0])
        w.writerow(["arbitrated", *L.arbitrate(a, b)])


if __name__ == "__main__":
    main()
