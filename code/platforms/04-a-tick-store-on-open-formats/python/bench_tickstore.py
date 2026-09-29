"""Chapter 4 measured data (not a fig_*.py): compaction time of the week's busiest day, and the time of three query
tasks on the store (a window over the week, the as-of join by three engines, a scan of the day's events from the
memory-mapped flat file and from Parquet). Writes measured_tickstore.csv (+ .meta). Run on a quiet machine."""
import pathlib
import shutil
import sys
import tempfile
import time

import numpy as np
import pyarrow.parquet as pq

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/ubench"))
sys.path.insert(0, str(HERE))
import firm_ubench as u  # noqa: E402
import pl_tickstore as P  # noqa: E402
from firm_tickstore import asof_duckdb, asof_polars, asof_reference, compact, flat_open, ipc_read  # noqa: E402

OUT = ROOT / "figdata/platforms/04-a-tick-store-on-open-formats"
STORE = ROOT / "data/platforms/generated/store_week"


def scan_flat(path):
    return flat_open(path)[1]["qty"].sum()


def best(fn, k=5):
    ts = []
    for _ in range(k):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    return min(ts)


def main():
    if not (STORE / "hist").exists():
        P.build(STORE)
    d = STORE / "intraday" / P.DATES[0]
    _, rec = flat_open(d / "events.flat")
    tables = {"quotes": ipc_read(d / "quotes.arrows"), "trades": ipc_read(d / "trades.arrows"),
              "events": P.events_table(np.asarray(rec))}
    n_events = len(rec)
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        t_compact = best(lambda: compact(tables, tmp / "h", P.DATES[0]), 3)
    finally:
        shutil.rmtree(tmp)
    s = P.store(STORE)
    tr = s.sql("SELECT date, symbol, seq, ts, price, qty FROM trades")
    qu = s.sql("SELECT date, symbol, seq, ts, bid, ask FROM quotes")
    ev_path = STORE / "hist/events" / f"date={P.DATES[0]}"
    rows = [
        ["compaction of the busiest day", n_events, f"{t_compact:.4f}"],
        ["window: SIM2 09:32-09:35; five days", 5, f"{best(lambda: P.window(STORE)):.4f}"],
        ["as-of join; DuckDB", tr.num_rows, f"{best(lambda: asof_duckdb(s)):.4f}"],
        ["as-of join; Polars", tr.num_rows, f"{best(lambda: asof_polars(tr, qu)):.4f}"],
        ["as-of join; reference (Python)", tr.num_rows, f"{best(lambda: asof_reference(tr, qu), 1):.4f}"],
        ["scan of a day; flat file (mmap)", n_events, f"{best(lambda: scan_flat(d / 'events.flat')):.4f}"],
        ["scan of a day; Parquet", n_events, f"{best(lambda: pq.read_table(ev_path, columns=['qty'])['qty']):.4f}"],
    ]
    u.write_measured(OUT / "measured_tickstore.csv", ["task", "rows", "seconds"], rows,
                     source="code/platforms/04-a-tick-store-on-open-formats/python/bench_tickstore.py",
                     timer="time.perf_counter, best of 5 (compaction 3, reference join 1), one thread")


if __name__ == "__main__":
    main()
