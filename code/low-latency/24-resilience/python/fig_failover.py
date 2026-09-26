"""Chapter 24 figure data (deterministic: the engine and the scenario are): firm.sequencer's primary killed at every
stage of every order of the scenario (46 orders, 4 stages), recovered by each of three procedures. Outputs
failover.csv (duplicates per procedure and stage) and failover_summary.csv (per procedure: cut points, duplicates,
largest position, recovery time)."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_failover as L  # noqa: E402

OUT = L.ROOT / "figdata/low-latency/24-resilience"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, summary = L.table()
    with open(OUT / "failover.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["procedure", "stage", "stage_index", "points", "duplicates"])
        for (proc, stage), (n, d) in rows.items():
            w.writerow([proc.replace(",", ";"), stage.replace(",", ";"), L.sim.STAGES.index(stage), n, d])
    with open(OUT / "failover_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["procedure", "points", "duplicates", "max_position", "recovery_min_ms", "recovery_max_ms"])
        for proc, n, d, mx, lo, hi in summary:
            w.writerow([proc.replace(",", ";"), n, d, mx, f"{lo / 1e6:.3f}", f"{hi / 1e6:.3f}"])


if __name__ == "__main__":
    main()
