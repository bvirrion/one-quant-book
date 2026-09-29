"""Columnar formats (One Quant Book 15, chapter 3).

A synthetic month of quotes for fifty symbols (1,000 quotes a symbol a day, 20 trading days, one million rows; Poisson
arrival times, a random walk of the mid on a one-cent grid, spreads of one to three cents, sizes in round lots, four
venues, a condition code that is null on 95% of rows) is written in the open on-disk columnar format (Parquet, through
pyarrow) in three orders -- shuffled, in capture (time) order, and sorted by symbol then time -- and with row groups of
different sizes; three query shapes read it through a file object that counts the bytes pyarrow actually reads. The same
columns are encoded one by one with firm.colfile's four encodings, and the in-memory buffers of the in-memory columnar
format (Arrow) are listed.
"""
from __future__ import annotations

import functools
import io
import pathlib
import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "colfile"))
from firm_colfile import ENCODINGS, encode  # noqa: E402

DAY_NS, OPEN_S, SESSION_S = 86_400 * 10**9, 34_200, 23_400
VENUES = np.array(["XNYS", "XNAS", "ARCX", "BATS"])
ROW_GROUPS = (2_048, 8_192, 32_768, 131_072, 524_288)
QUERIES = {
    "one symbol, one hour": [("symbol", "=", "S007"), ("ts", ">=", 5 * DAY_NS + 36_000 * 10**9),
                             ("ts", "<", 5 * DAY_NS + 39_600 * 10**9)],
    "one symbol, one month": [("symbol", "=", "S007")],
    "all symbols, one hour": [("ts", ">=", 5 * DAY_NS + 36_000 * 10**9), ("ts", "<", 5 * DAY_NS + 39_600 * 10**9)],
}
COLUMNS = ["bid", "ask"]


@functools.lru_cache(maxsize=2)
def quotes(symbols: int = 50, days: int = 20, per: int = 1000, seed: int = 3) -> pa.Table:
    """Quotes in capture order (by time within each day, all symbols interleaved)."""
    rng = np.random.default_rng(seed)
    n = symbols * days * per
    day = np.repeat(np.arange(days), symbols * per)
    sym = np.tile(np.repeat(np.arange(symbols), per), days)
    offs = np.sort(rng.integers(0, SESSION_S * 10**9, size=(days * symbols, per)), axis=1).ravel()
    ts = day.astype(np.int64) * DAY_NS + OPEN_S * 10**9 + offs
    start = rng.integers(20, 200, size=symbols) * 10_000                   # dollars in 1/10,000
    steps = rng.choice([-100, 0, 0, 0, 100], size=(symbols, days * per))
    mid = (start[:, None] + np.cumsum(steps, axis=1)).reshape(symbols, days, per).transpose(1, 0, 2).ravel()
    half = rng.integers(1, 4, size=n) * 50
    cond = np.where(rng.random(n) < 0.05, rng.choice(np.array(["O", "C", "H"]), size=n), None)
    names = np.array([f"S{i:03d}" for i in range(symbols)])
    t = pa.table({
        "date": pa.array(day, pa.int32()), "symbol": names[sym], "ts": ts, "bid": mid - half, "ask": mid + half,
        "bid_size": rng.integers(1, 50, n, dtype=np.int32) * 100,
        "ask_size": rng.integers(1, 50, n, dtype=np.int32) * 100,
        "venue": VENUES[rng.integers(0, 4, n)], "condition": pa.array(cond, pa.string())})
    order = np.lexsort((ts, day))
    return t.take(order)


def layout(t: pa.Table, name: str, seed: int = 11) -> pa.Table:
    if name == "shuffled":
        return t.take(np.random.default_rng(seed).permutation(t.num_rows))
    if name == "time order":
        return t
    if name == "symbol, then time":
        return t.sort_by([("symbol", "ascending"), ("ts", "ascending")])
    raise ValueError(name)


class CountingFile(io.BytesIO):
    """A file object that counts the bytes read from it."""

    def __init__(self, data: bytes):
        super().__init__(data)
        self.nread = 0

    def read(self, n=-1):
        b = super().read(n)
        self.nread += len(b)
        return b

    def readinto(self, b):
        k = super().readinto(b)
        self.nread += k
        return k


def parquet_bytes(t: pa.Table, row_group_size: int) -> bytes:
    buf = io.BytesIO()
    pq.write_table(t, buf, row_group_size=row_group_size, compression="zstd", write_statistics=True)
    return buf.getvalue()


def bytes_read(data: bytes, filters, columns=COLUMNS) -> tuple[int, int]:
    """Bytes pyarrow reads to answer the query, and the rows it returns."""
    f = CountingFile(data)
    r = pq.read_table(f, columns=columns, filters=filters, pre_buffer=False)
    return f.nread, r.num_rows


@functools.lru_cache(maxsize=1)
def study() -> dict:
    t = quotes()
    rows = {}
    for lay in ("shuffled", "time order", "symbol, then time"):
        tl = layout(t, lay)
        for rg in ROW_GROUPS:
            data = parquet_bytes(tl, rg)
            for q, flt in QUERIES.items():
                rows[(lay, rg, q)] = (len(data), *bytes_read(data, flt))
    return rows


def encodings_by_column(t: pa.Table | None = None, sort=False) -> dict:
    """Bytes of each column of one day under each encoding (numpy values; strings as unicode)."""
    t = t if t is not None else quotes()
    day = t.filter(pa.compute.equal(t["date"], 5))
    if sort:
        day = day.sort_by([("symbol", "ascending"), ("ts", "ascending")])
    out = {}
    for c in ("date", "symbol", "ts", "bid", "bid_size", "venue"):
        v = day[c].to_numpy(zero_copy_only=False)
        v = v.astype(str) if v.dtype == object else v
        out[c] = {e: len(encode(v, e)) for e in ENCODINGS if e != "delta" or v.dtype.kind in "iu"}
    return out


def arrow_buffers(t: pa.Table | None = None) -> dict:
    """The physical buffers of three Arrow arrays: an integer column, a nullable string column, a dictionary column."""
    t = t if t is not None else quotes()
    head = t.slice(0, 1000)
    ts = head["ts"].combine_chunks()
    cond = head["condition"].combine_chunks()
    sym = pa.array(head["symbol"].to_numpy(zero_copy_only=False)).dictionary_encode()
    size = lambda b: None if b is None else b.size  # noqa: E731
    return {"ts": [size(b) for b in ts.buffers()], "condition": [size(b) for b in cond.buffers()],
            "condition_nulls": cond.null_count, "symbol_indices": [size(b) for b in sym.indices.buffers()],
            "symbol_dictionary": len(sym.dictionary)}


def colfile_query(path, t: pa.Table | None = None, row_group_size: int = 8_192) -> dict:
    """Exercise 7: the month sorted by symbol then time in firm.colfile, and the one-symbol, one-hour query."""
    from firm_colfile import ColFile, write
    t = layout(t if t is not None else quotes(), "symbol, then time")
    cols = {c: t[c].to_numpy(zero_copy_only=False).astype(str) if c == "symbol" else t[c].to_numpy()
            for c in ("symbol", "ts", "bid", "ask")}
    write(path, cols, row_group_size)
    q = QUERIES["one symbol, one hour"]
    where = [("symbol", "==", q[0][2]), ("ts", ">=", q[1][2]), ("ts", "<", q[2][2])]
    got, stats = ColFile(path).read(["bid", "ask"], where)
    ref = pq.read_table(io.BytesIO(parquet_bytes(t, row_group_size)), columns=COLUMNS, filters=q)
    stats["equal"] = bool((got["bid"] == ref["bid"].to_numpy()).all() and (got["ask"] == ref["ask"].to_numpy()).all())
    stats["rows"] = len(got["bid"])
    return stats
