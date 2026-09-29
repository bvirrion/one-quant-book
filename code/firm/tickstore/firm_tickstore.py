"""firm.tickstore -- a tick store on open formats (build of One Quant Book 15, chapter 4).

Intraday, the store appends: the normalised events of firm.tickcap go to a flat file of fixed-width records behind a
versioned header (readable in place through a memory map, from Python, C++20 or Rust), and the derived quotes and
trades go to Arrow IPC streams, one record batch per flush. At the close, compaction sorts each table by symbol and
time and writes it as Parquet under <root>/<table>/date=YYYY-MM-DD/symbol=S/, one file per partition. A query layer puts
DuckDB over both stores, so that one SQL name covers the historical Parquet partitions and the current day's intraday
data. As-of joins of trades to the prevailing quote are provided three ways (DuckDB, Polars, and Book 7's firm.pit as
the reference), and a schema registry states the evolution rules: fields are added with defaults, never removed,
renamed or retyped.

API (stable):
    EVENT_V1 (= firm_tickcap.RECORD, 56 bytes), EVENT_V2 (adds venue u2 and flags u2; 64 bytes), SCHEMAS = {1:, 2:}
    FlatWriter(path, version=2).append(rec) / .close();  flat_open(path) -> (version, np.memmap)
    upgrade(rec, version) -> rec in that version (new fields at their defaults)
    IpcWriter(path, schema).append(table) / .close();  ipc_read(path) -> pa.Table
    quotes_trades(events, symbols) -> (quotes, trades)          top of book after each change; executions with price
    compact(tables, root, date, row_group_size=65536) -> {table: {'rows', 'files', 'bytes'}}
    Store(root, intraday=None).sql(q) -> pa.Table                views: <table> = historical UNION ALL BY NAME intraday
    asof_duckdb(store, key='seq'), asof_polars(trades, quotes, key='seq'), asof_reference(trades, quotes) -> pa.Table
        each trade with the quote of its symbol prevailing before it (the last quote of an earlier sequence number;
        bid, ask; null if none); key='ts' joins on the timestamp instead, at or before, to show the tie problem
    check_evolution(old: dict, new: dict) -> list[str]           field -> type; problems if not add-only
"""
from __future__ import annotations

import json
import pathlib
import struct
import sys

import duckdb
import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq

_FIRM = pathlib.Path(__file__).resolve().parents[1]
for _c in ("tickcap", "feedhandler", "bookbuilder", "pit"):
    sys.path.insert(0, str(_FIRM / _c))
from firm_bookbuilder import Book  # noqa: E402
from firm_pit import asof_join  # noqa: E402
from firm_tickcap import RECORD  # noqa: E402

EVENT_V1 = RECORD
EVENT_V2 = np.dtype(RECORD.descr + [("venue", "<u2"), ("flags", "<u2"), ("pad", "<u4")])
SCHEMAS = {1: EVENT_V1, 2: EVENT_V2}
DEFAULTS = {"venue": 0, "flags": 0, "pad": 0}
MAGIC, HEAD = b"OQTS", struct.Struct("<4sHHI")         # magic, version, record size, schema length
ALIGN = 64


# ------------------------------------------------------------------------------------------- flat files
class FlatWriter:
    """Append-only fixed-width records behind a header padded to 64 bytes."""

    def __init__(self, path, version: int = 2):
        self.dtype = SCHEMAS[version]
        schema = json.dumps(self.dtype.descr).encode()
        head = HEAD.pack(MAGIC, version, self.dtype.itemsize, len(schema)) + schema
        self.f = open(path, "wb")
        self.f.write(head + b"\0" * (-len(head) % ALIGN))
        self.n = 0

    def append(self, rec: np.ndarray) -> None:
        self.f.write(np.ascontiguousarray(rec, dtype=self.dtype).tobytes())
        self.n += len(rec)

    def close(self) -> None:
        self.f.close()


def flat_open(path):
    """(version, records) with the records memory-mapped read-only: nothing is read until
    it is touched."""
    with open(path, "rb") as f:
        magic, version, size, slen = HEAD.unpack(f.read(HEAD.size))
    if magic != MAGIC or SCHEMAS[version].itemsize != size:
        raise ValueError(f"{path}: not a tick-store flat file of a known version")
    start = HEAD.size + slen
    start += -start % ALIGN
    return version, np.memmap(path, dtype=SCHEMAS[version], mode="r", offset=start)


def upgrade(rec: np.ndarray, version: int) -> np.ndarray:
    out = np.zeros(len(rec), dtype=SCHEMAS[version])
    for name in out.dtype.names:
        out[name] = rec[name] if name in rec.dtype.names else DEFAULTS[name]
    return out


# ------------------------------------------------------------------------------------------- Arrow IPC
class IpcWriter:
    def __init__(self, path, schema: pa.Schema):
        self.sink = pa.OSFile(str(path), "wb")
        self.w = ipc.new_stream(self.sink, schema)

    def append(self, t: pa.Table) -> None:
        self.w.write_table(t)

    def close(self) -> None:
        self.w.close()
        self.sink.close()


def ipc_read(path) -> pa.Table:
    with pa.OSFile(str(path), "rb") as f:
        return ipc.open_stream(f).read_all()


# ------------------------------------------------------------------------------------------- derived tables
QUOTE = pa.schema([("seq", pa.int64()), ("ts", pa.int64()), ("recv", pa.int64()), ("symbol", pa.string()),
                   ("bid", pa.int64()), ("bid_qty", pa.int64()), ("ask", pa.int64()), ("ask_qty", pa.int64())])
TRADE = pa.schema([("seq", pa.int64()), ("ts", pa.int64()), ("recv", pa.int64()), ("symbol", pa.string()),
                   ("price", pa.int64()), ("qty", pa.int64()), ("match", pa.int64())])


def quotes_trades(events: np.ndarray, symbols: dict[int, str]) -> tuple[pa.Table, pa.Table]:
    """Top of book after each event that changes it (one book per instrument, Book 13's builder), and every
    execution with the price of the resting order it executed against. Prices in 1/10,000. Each row carries the feed
    sequence number of the event that produced it: an execution and the quote change it causes share one."""
    books: dict[int, Book] = {}
    last: dict[int, tuple] = {}
    q, t = [], []
    for e in events:
        loc = int(e["locate"])
        if loc not in symbols:
            continue
        b = books.setdefault(loc, Book())
        k = int(e["kind"])
        if k in (ord("E"), ord("C")):
            o = b.orders.get(int(e["ref"]))
            price = int(e["price"]) if k == ord("C") else (o[1] if o else 0)
            t.append((int(e["seq"]), int(e["ts"]), int(e["recv"]), symbols[loc], price, int(e["qty"]), int(e["ref2"])))
        b.apply((k, int(e["side"]), loc, int(e["seq"]), int(e["ts"]), int(e["ref"]), int(e["ref2"]),
                 int(e["price"]), int(e["qty"])))
        top = b.best()
        if top is not None and top[0] is not None and top[2] is not None and top != last.get(loc):
            last[loc] = top
            q.append((int(e["seq"]), int(e["ts"]), int(e["recv"]), symbols[loc], top[0], top[1], top[2], top[3]))
    cols = lambda rows, schema: {f.name: [r[i] for r in rows] for i, f in enumerate(schema)}  # noqa: E731
    return pa.table(cols(q, QUOTE), schema=QUOTE), pa.table(cols(t, TRADE), schema=TRADE)


# ------------------------------------------------------------------------------------------- compaction
def compact(tables: dict, root, date: str, row_group_size: int = 65_536) -> dict:
    out = {}
    for name, t in tables.items():
        t = t.sort_by([("symbol", "ascending"), ("ts", "ascending")])
        files, size = 0, 0
        for sym in sorted(set(t["symbol"].to_pylist())):
            part = t.filter(pa.compute.equal(t["symbol"], sym)).drop_columns(["symbol"])
            d = pathlib.Path(root) / name / f"date={date}" / f"symbol={sym}"
            d.mkdir(parents=True, exist_ok=True)
            pq.write_table(part, d / "part.parquet", row_group_size=row_group_size,
                           compression="zstd")
            files += 1
            size += (d / "part.parquet").stat().st_size
        out[name] = {"rows": t.num_rows, "files": files, "bytes": size}
    return out


# ------------------------------------------------------------------------------------------- query layer
class Store:
    """DuckDB over the historical Parquet partitions and the day's intraday tables."""

    def __init__(self, root, intraday: dict | None = None, date: str | None = None):
        self.root = pathlib.Path(root)
        self.con = duckdb.connect()
        for name in ("quotes", "trades"):
            hist = self.root / name
            parts = []
            if hist.exists() and any(hist.glob("date=*/symbol=*/*.parquet")):
                files = f"{hist}/date=*/symbol=*/*.parquet"
                parts.append(f"SELECT * FROM read_parquet('{files}', "
                             "hive_partitioning = true, union_by_name = true)")
            if intraday and name in intraday:
                t = intraday[name]
                self.con.register(f"{name}_intraday", t)
                parts.append(f"SELECT *, DATE '{date}' AS date FROM {name}_intraday")
            if parts:
                union = " UNION ALL BY NAME ".join(parts)
                self.con.execute(f"CREATE VIEW {name} AS {union}")

    def sql(self, q: str) -> pa.Table:
        return self.con.execute(q).to_arrow_table()


ASOF_SQL = """
SELECT t.date, t.symbol, t.seq, t.ts, t.price, t.qty, q.bid, q.ask
FROM trades t ASOF LEFT JOIN quotes q
  ON t.date = q.date AND t.symbol = q.symbol AND t.{key} {op} q.{key}
ORDER BY t.date, t.symbol, t.seq"""
COLS = ["date", "symbol", "seq", "ts", "price", "qty", "bid", "ask"]


def asof_duckdb(store: Store, key: str = "seq") -> pa.Table:
    """The quote prevailing before each trade: the last quote of an earlier sequence number
    (key='seq'), or, to show the tie problem, the last quote at or before the trade's
    timestamp (key='ts')."""
    return store.sql(ASOF_SQL.format(key=key, op=">" if key == "seq" else ">="))


def asof_polars(trades: pa.Table, quotes: pa.Table, key: str = "seq") -> pa.Table:
    """Both tables must carry date and symbol."""
    tr = pl.from_arrow(trades).sort([key])
    qu = pl.from_arrow(quotes).sort([key]).select(["date", "symbol", key, "bid", "ask"])
    j = tr.join_asof(qu, on=key, by=["date", "symbol"], strategy="backward", allow_exact_matches=key != "seq",
                     check_sortedness=False)
    return j.sort(["date", "symbol", "seq"]).select(COLS).to_arrow()


def asof_reference(trades: pa.Table, quotes: pa.Table) -> pa.Table:
    """Book 7's firm.pit.asof_join (strict: the quote known before the trade), one (date, symbol) group at a time."""
    tk, qk = trades.to_pydict(), quotes.to_pydict()
    rows = []
    for g in sorted(set(zip(tk["date"], tk["symbol"], strict=True))):
        ti = [i for i, k in enumerate(zip(tk["date"], tk["symbol"], strict=True)) if k == g]
        qi = sorted((i for i, k in enumerate(zip(qk["date"], qk["symbol"], strict=True)) if k == g),
                    key=lambda i: qk["seq"][i])
        qs = np.array([qk["seq"][i] for i in qi], dtype=float)
        idx = asof_join([tk["seq"][i] for i in ti], qs, np.arange(len(qi), dtype=float), strict=True) \
            if qi else np.full(len(ti), np.nan)
        for i, j in zip(ti, idx, strict=True):
            b, a = (None, None) if np.isnan(j) else (qk["bid"][qi[int(j)]], qk["ask"][qi[int(j)]])
            rows.append((tk["date"][i], tk["symbol"][i], tk["seq"][i], tk["ts"][i], tk["price"][i], tk["qty"][i], b, a))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    return pa.table({n: [r[k] for r in rows] for k, n in enumerate(COLS)})


# ------------------------------------------------------------------------------------------- schema registry
def check_evolution(old: dict, new: dict) -> list[str]:
    """Add-only evolution: every old field kept with its type; new fields are appended."""
    out = [f"field {f} removed or renamed" for f in old if f not in new]
    out += [f"field {f} retyped {old[f]} -> {new[f]}" for f in old if f in new and new[f] != old[f]]
    if [f for f in new if f in old] != [f for f in old if f in new]:
        out.append("old fields reordered")
    keys = list(new)
    out += [f"field {f} inserted before existing fields" for f in keys if f not in old
            and any(g in old for g in keys[keys.index(f) + 1:])]
    return out
