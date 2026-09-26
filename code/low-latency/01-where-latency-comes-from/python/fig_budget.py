"""Chapter 1 deterministic charts: end-to-end tail with independent and common stalls; race win probability."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ll_budget as b  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/low-latency/01-where-latency-comes-from"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "ccdf.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x_us", "ccdf"])
        for x, c in b.ccdf_rows():
            w.writerow([f"{x / 1000:.3f}", f"{max(c, 1e-6):.6f}"])
    c = b.composition()
    with open(OUT / "marks.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sum_p99", "p99", "sum_union", "top"])
        w.writerow([f"{c['sum_p99'] / 1000:.3f}", f"{c['p99'] / 1000:.3f}", f"{c['sum_union'] / 1000:.3f}", "1"])
    with open(OUT / "race.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["median_us", "with_stalls", "no_stalls"])
        for m, p, q in b.race_curve():
            w.writerow([m / 1000, f"{p:.4f}", f"{q:.4f}"])


if __name__ == "__main__":
    main()
