"""Chapter 5 deterministic chart: latency by percentile for the closed-loop, corrected and open-loop testers."""
import csv
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ll_measure as m  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/low-latency/05-measuring-latency"
PS = (0.5, 0.75, 0.9, 0.95, 0.98, 0.99, 0.993, 0.995, 0.998, 0.999, 0.9995, 0.9999)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q, _ = m.spectrum(ps=PS)
    with open(OUT / "spectrum.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["p", "nines", "closed_ms", "corrected_ms", "open_ms"])
        for i, p in enumerate(PS):
            w.writerow([p, f"{-math.log10(1 - p):.4f}", f"{q['closed loop'][i] / 1000:.4f}",
                        f"{q['corrected'][i] / 1000:.4f}", f"{q['open loop'][i] / 1000:.4f}"])


if __name__ == "__main__":
    main()
