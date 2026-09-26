"""Chapter 19 measured data (not a fig_*.py): time per event of three book builders (tree map, sorted vector, ladder)
on a large-tick stream (the simulator's minute, chapter 18) and a small-tick one (synthetic), and the ladder's cost by
width on a small-tick day whose price moves thirty percent. Outputs measured_update.csv and measured_width.csv."""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_book as L  # noqa: E402

sys.path.insert(0, str(L.ROOT / "code/firm/ubench"))
import firm_ubench as u  # noqa: E402

OUT = L.ROOT / "figdata/low-latency/19-the-order-book-builder"
SRC = "code/low-latency/19-the-order-book-builder/cpp/ll_books_bench.cpp"
WIDTHS = (256, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304)


def main():
    exe = u.compile_cpp(HERE.parent / "cpp/ll_books_bench.cpp")
    rows, wrows = [], []
    with tempfile.TemporaryDirectory() as d:
        files = {"large": (L.large_tick_events(), 100), "small": (L.small_tick_events(), 1),
                 "small30": (L.small_tick_events(move=0.3), 1)}
        for k, (ev, _tick) in files.items():
            (pathlib.Path(d) / f"{k}.bin").write_bytes(L.mk.pack(ev))
        for k in ("large", "small"):
            out = u.run(exe, pathlib.Path(d) / f"{k}.bin", files[k][1], cpus=6).strip().splitlines()
            rows += [[k, *x.split(",")] for x in out[1:4]]
        for w in WIDTHS:
            out = u.run(exe, pathlib.Path(d) / "small30.bin", 1, w, cpus=6).strip().splitlines()
            lad = next(x.split(",") for x in out if x.startswith("ladder"))
            rec = next(x.split(",")[1] for x in out if x.startswith("recentrings"))
            tot = next(x.split(",")[1] for x in out if x.startswith("total_ms"))
            wrows.append([w, rec, tot, *lad[1:]])
        n = {k: len(v[0]) for k, v in files.items()}
    meta = dict(cpus="6", source=SRC, events=str(n), timer="median TSC timer cost subtracted per event")
    u.write_measured(OUT / "measured_update.csv", ["regime", "structure", "q50", "q90", "q99", "q999"], rows, **meta)
    u.write_measured(OUT / "measured_update_keyed.csv", ["key", "q50", "q99"],
                     [[f"{r[0]}-{r[1]}", r[2], r[4]] for r in rows], **meta)
    u.write_measured(OUT / "measured_width.csv", ["width", "recentrings", "total_ms", "q50", "q90", "q99", "q999"],
                     wrows, **meta)


if __name__ == "__main__":
    main()
