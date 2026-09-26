"""Chapter 10 measured data (not a fig_*.py): per-message latency of the dict book and the pooled book over 200,000
messages, with the collector's pauses. Output: measured_gc.csv."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402
import ll_gc  # noqa: E402

OUT = ROOT / "figdata/low-latency/10-managed-and-functional-languages-on-the-desk/measured_gc.csv"
N = 200_000


def main():
    rows = []
    for name, make in (("dict book", ll_gc.dict_book), ("pooled book", ll_gc.pooled_book)):
        lat, w = ll_gc.run(make(), N)
        gcmax = max((h.max for h in w.pauses.values()), default=0)
        rows.append([name, *(lat.quantile(p) for p in (0.5, 0.99, 0.999, 1.0)), *(w.collections[g] for g in range(3)),
                     gcmax])
    u.write_measured(OUT, ["design", "p50", "p99", "p999", "max", "gen0", "gen1", "gen2", "gc_max_ns"], rows,
                     interpreter=sys.version.split()[0], messages=N,
                     source="code/low-latency/10-managed-and-functional-languages-on-the-desk/python/ll_gc.py")


if __name__ == "__main__":
    main()
