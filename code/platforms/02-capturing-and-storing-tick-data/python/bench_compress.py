"""Chapter 2 measured data (not a fig_*.py): compression throughput against compression ratio for the chapter's
session, by method and level. Writes measured_compress.csv (+ .meta). Machine-dependent: run on a quiet machine."""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
from pl_tickcap import compressed_size, study  # noqa: E402

OUT = ROOT / "figdata/platforms/02-capturing-and-storing-tick-data"
# label placement in the chart
ANCHOR = {"norm zlib 6": "south east", "raw zlib 6": "north west", "Parquet zstd 9": "south east"}


def main():
    s = study()
    rec = s["rec"]
    raw = (pathlib.Path(ROOT / "data/platforms/generated/day_600s/day_line_A.rec")).read_bytes()
    rows = []
    for label, data, method, level in (("raw zlib 1", raw, "zlib", 1), ("raw zlib 6", raw, "zlib", 6),
                                       ("raw zlib 9", raw, "zlib", 9), ("norm zlib 6", rec, "zlib", 6),
                                       ("Parquet zstd 1", rec, "zstd-parquet", 1),
                                       ("Parquet zstd 9", rec, "zstd-parquet", 9),
                                       ("delta zlib 6", rec, "delta-zlib", 6)):
        n_in = len(data) if isinstance(data, bytes) else data.nbytes
        best = min(_timed(data, method, level) for _ in range(5))
        size = compressed_size(data, method, level)
        rows.append([label, f"{n_in / size:.3f}", f"{n_in / best / 1e6:.1f}", ANCHOR.get(label, "south west")])
    u.write_measured(OUT / "measured_compress.csv", ["method", "ratio", "mb_per_s", "anchor"], rows,
                     source="code/platforms/02-capturing-and-storing-tick-data/python/bench_compress.py",
                     timer="time.perf_counter, best of 5, one thread")


def _timed(data, method, level):
    t = time.perf_counter()
    compressed_size(data, method, level)
    return time.perf_counter() - t


if __name__ == "__main__":
    main()
