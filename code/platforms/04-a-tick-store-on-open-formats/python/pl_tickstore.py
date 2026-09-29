"""A tick store on open formats (One Quant Book 15, chapter 4).

Five simulated trading days (the chapter 2 session with five seeds: ten busy minutes, two instruments, both feed lines)
go through the whole store: each day is captured and normalised (firm.tickcap), its events appended to a flat file and
its quotes and trades to Arrow IPC streams as the session runs; the first four days are compacted into date- and
symbol-partitioned Parquet sorted by time; the fifth stays intraday, as the current day. The quotes gained a field (the
venue) from the fourth day: the store's schema evolved mid-week. One query layer (DuckDB) answers over both stores,
and the as-of join of every trade to its prevailing quote is computed by DuckDB, by Polars and by Book 7's reference
join, which must agree row for row.
"""
from __future__ import annotations

import pathlib
import shutil
import sys

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("tickstore", "tickcap", "feedhandler", "bookbuilder", "pit", "exchsim"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
import make_recorded_day  # noqa: E402
from firm_tickcap import arbitrate, normalise, read_capture  # noqa: E402
from firm_tickstore import (  # noqa: E402
    COLS,
    EVENT_V1,
    EVENT_V2,
    FlatWriter,
    IpcWriter,
    Store,
    asof_duckdb,
    asof_polars,
    asof_reference,
    check_evolution,
    compact,
    flat_open,
    ipc_read,
    quotes_trades,
    upgrade,
)

DATES = ("2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25")
SYMBOLS = {1: "SIM1", 2: "SIM2"}
V2_FROM = 3                                       # the fourth day onwards carries the venue field
GEN = ROOT / "data/platforms/generated"
BATCH = 20_000                                    # events per intraday flush


def day_events(k: int, hours: float = 0.1667, gen: pathlib.Path = GEN) -> np.ndarray:
    out = gen / f"week_{round(hours * 3600)}s_day{k}"
    if not (out / "day_summary.json").exists():
        make_recorded_day.run(hours, 2, seed=2026 + 101 * k, out=out)
    a, b = (out / "day_line_A.rec").read_bytes(), (out / "day_line_B.rec").read_bytes()
    msgs, _gaps, _cnt = arbitrate([read_capture(a), read_capture(b)])
    return normalise(msgs)


def capture_day(k: int, ev: np.ndarray, root: pathlib.Path) -> dict:
    """The intraday store of day k, written as the session runs: events flushed to a flat file, quotes and trades
    to Arrow IPC streams, one flush every BATCH events."""
    version = 2 if k >= V2_FROM else 1
    d = root / "intraday" / DATES[k]
    d.mkdir(parents=True, exist_ok=True)
    fw = FlatWriter(d / "events.flat", version)
    q_all, t_all = quotes_trades(ev, SYMBOLS)
    if version == 2:
        q_all = q_all.append_column("venue", pa.array(["SIMX"] * q_all.num_rows))
    qw, tw = IpcWriter(d / "quotes.arrows", q_all.schema), IpcWriter(d / "trades.arrows", t_all.schema)
    for s in range(0, len(ev), BATCH):
        chunk = ev[s:s + BATCH]
        fw.append(upgrade(chunk, version) if version == 2 else chunk)
        lo, hi = int(chunk["seq"][0]), int(chunk["seq"][-1])
        qw.append(q_all.filter(pc.and_(pc.greater_equal(q_all["seq"], lo), pc.less_equal(q_all["seq"], hi))))
        tw.append(t_all.filter(pc.and_(pc.greater_equal(t_all["seq"], lo), pc.less_equal(t_all["seq"], hi))))
    for w in (fw, qw, tw):
        w.close()
    return {"events": len(ev), "quotes": q_all.num_rows, "trades": t_all.num_rows, "version": version,
            "flat_bytes": (d / "events.flat").stat().st_size, "ipc_bytes": (d / "quotes.arrows").stat().st_size
            + (d / "trades.arrows").stat().st_size}


def events_table(rec: np.ndarray) -> pa.Table:
    t = pa.table({n: rec[n] for n in rec.dtype.names if n != "pad"})
    return t.append_column("symbol", pa.array([SYMBOLS.get(int(x), "SYS") for x in rec["locate"]]))


def build(root: pathlib.Path, days: int = 5, hours: float = 0.1667, gen: pathlib.Path = GEN) -> dict:
    """Capture every day intraday, then compact all but the last."""
    if root.exists():
        shutil.rmtree(root)
    info = {}
    for k in range(days):
        ev = day_events(k, hours, gen)
        info[k] = capture_day(k, ev, root)
        if k < days - 1:
            d = root / "intraday" / DATES[k]
            _, rec = flat_open(d / "events.flat")
            info[k]["compacted"] = compact({"quotes": ipc_read(d / "quotes.arrows"),
                                            "trades": ipc_read(d / "trades.arrows"),
                                            "events": events_table(np.asarray(rec))}, root / "hist", DATES[k])
    return info


def today(root: pathlib.Path, days: int = 5) -> dict[str, pa.Table]:
    d = root / "intraday" / DATES[days - 1]
    return {"quotes": ipc_read(d / "quotes.arrows"), "trades": ipc_read(d / "trades.arrows")}


def store(root: pathlib.Path, days: int = 5) -> Store:
    return Store(root / "hist", today(root, days), DATES[days - 1])


def asof_all(root: pathlib.Path, days: int = 5) -> dict:
    s = store(root, days)
    duck = asof_duckdb(s)
    trades = s.sql("SELECT date, symbol, seq, ts, price, qty FROM trades")
    quotes = s.sql("SELECT date, symbol, seq, ts, bid, ask FROM quotes")
    pol, ref = asof_polars(trades, quotes), asof_reference(trades, quotes)
    by_ts = asof_duckdb(s, "ts")
    same = lambda a, b: all(a[c].to_pylist() == b[c].to_pylist() for c in COLS)  # noqa: E731
    differ = sum(x != y for x, y in zip(duck["bid"].to_pylist(), by_ts["bid"].to_pylist(), strict=True)) + sum(
        x != y for x, y in zip(duck["ask"].to_pylist(), by_ts["ask"].to_pylist(), strict=True))
    moved = sum((b1 != b2) or (a1 != a2) for b1, b2, a1, a2 in zip(
        duck["bid"].to_pylist(), by_ts["bid"].to_pylist(), duck["ask"].to_pylist(), by_ts["ask"].to_pylist(),
        strict=True))
    return {"trades": duck.num_rows, "duck_polars": same(duck, pol), "duck_reference": same(duck, ref),
            "with_quote": duck.num_rows - duck["bid"].null_count, "ts_join_differs": moved, "fields": differ,
            "duck": duck}


def window(root: pathlib.Path, days: int = 5) -> pa.Table:
    """SIM2's quotes from 09:32 to 09:35 on every day of the week, from whichever store holds the day."""
    s = store(root, days)
    lo, hi = (9 * 3600 + 32 * 60) * 10**9, (9 * 3600 + 35 * 60) * 10**9
    return s.sql(f"SELECT date, count(*) AS n, count(venue) AS with_venue FROM quotes WHERE symbol = 'SIM2' "
                 f"AND ts >= {lo} AND ts < {hi} GROUP BY date ORDER BY date")


def flat_summary(path) -> dict:
    """What the C++ and Rust readers compute: per instrument, the record count, the executed quantity and the last
    sequence number."""
    _, rec = flat_open(path)
    out = {}
    for loc in np.unique(rec["locate"]):
        m = rec["locate"] == loc
        ex = m & (rec["kind"] == ord("E"))
        out[int(loc)] = (int(m.sum()), int(rec["qty"][ex].sum()), int(rec["seq"][m].max()))
    return out


def evolution() -> dict:
    v1 = {n: str(EVENT_V1[n]) for n in EVENT_V1.names}
    v2 = {n: str(EVENT_V2[n]) for n in EVENT_V2.names}
    bad = dict(v1)
    bad["price"] = "int64"
    return {"v1_to_v2": check_evolution(v1, v2), "retype": check_evolution(v1, bad),
            "drop": check_evolution(v2, v1)}
