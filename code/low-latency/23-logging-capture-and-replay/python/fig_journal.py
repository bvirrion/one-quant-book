"""Chapter 23 table data (deterministic): the input journal of two event streams, its size raw and compressed with
zlib at level 6, and the bytes per event. Output journal.csv."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_logging as L  # noqa: E402

OUT = L.ROOT / "figdata/low-latency/23-logging-capture-and-replay"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "journal.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stream", "events", "span_s", "raw_bytes", "zlib_bytes", "ratio", "zlib_bytes_per_event"])
        for name, (recs, span, _) in L.streams().items():
            j = L.journal(recs)
            z = L.compressed(j)
            w.writerow([name, len(recs), f"{span:.3f}", len(j), z, f"{len(j) / z:.2f}", f"{z / len(recs):.2f}"])


if __name__ == "__main__":
    main()
