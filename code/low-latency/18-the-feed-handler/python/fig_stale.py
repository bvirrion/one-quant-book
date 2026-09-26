"""Chapter 18 figure data (deterministic: the simulator and the handler are): one minute from the open with an
eightfold burst and impaired lines; the handler run with the retransmission server and without it (snapshot
recovery). Outputs rate.csv (messages per 100 ms), stale_retx.csv and stale_snapshot.csv (staleness intervals), and
summary.csv (counters of both runs)."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ll_feed as L  # noqa: E402

OUT = L.ROOT / "figdata/low-latency/18-the-feed-handler"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    a, b, clean, snap = L.minute()
    rate = L.rate_per_100ms(clean)
    with open(OUT / "rate.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "messages"])
        w.writerows([[f"{k / 10:.1f}", rate.get(k, 0)] for k in range(0, 600)])
    ev = L.fh.merge(a, b, snap)
    runs = {"retx": L.fh.Handler(retx=L.fh.RetxServer(L.fh.recorded(clean), window=100_000)).run(ev),
            "snapshot": L.fh.Handler().run(ev)}
    with open(OUT / "summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        keys = list(runs["retx"].counters)
        w.writerow(["run", "events", "stale_intervals", "stale_ms", "worst_ms", *keys])
        for name, h in runs.items():
            iv = [e - s for s, e in h.stale]
            w.writerow([name, len(h.events), len(iv), f"{sum(iv) / 1e6:.3f}", f"{max(iv) / 1e6:.3f}",
                        *(h.counters[k] for k in keys)])
    # the figure's bottom panel: the gaps the other line could not fill, as bars from start to end (nan breaks the line)
    with open(OUT / "stale_bars.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "retx", "snapshot"])
        for s, e in runs["retx"].stale:
            if e - s > 600_000:
                w.writerows([[f"{(s - L.OPEN) / 1e9:.4f}", 2, "nan"], [f"{(e - L.OPEN) / 1e9:.4f}", 2, "nan"],
                             ["nan", "nan", "nan"]])
        for s, e in runs["snapshot"].stale:
            if e - s > 100_000_000:
                w.writerows([[f"{(s - L.OPEN) / 1e9:.4f}", "nan", 1], [f"{(e - L.OPEN) / 1e9:.4f}", "nan", 1],
                             ["nan", "nan", "nan"]])
    for name, h in runs.items():
        with open(OUT / f"stale_{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["start_s", "end_s", "ms", "y"])
            y = 2 if name == "retx" else 1
            w.writerows([[f"{(s - L.OPEN) / 1e9:.4f}", f"{(e - L.OPEN) / 1e9:.4f}", f"{(e - s) / 1e6:.3f}", y]
                         for s, e in h.stale])


if __name__ == "__main__":
    main()
