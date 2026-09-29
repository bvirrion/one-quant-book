"""firm.tickcap -- tick capture, normalisation, partitioning and storage economics (One Quant Book 15, chapter 2).

Raw capture keeps what arrived on each line exactly as it arrived: records of (receive time u64 | length u32 | packet),
the recorded-file format of Book 10's firm.exchsim. Normalisation arbitrates the redundant lines by sequence number
(first copy wins, duplicates dropped, a gap that neither line fills is recorded and skipped after a timeout) and turns
each message into the firm's 56-byte event record: the receive time followed by Book 13's 48-byte feed-handler event
(firm_feedhandler.normalise), so the store and the trading path share one layout. Partitioning writes a day under
root/date=YYYY-MM-DD/locate=N/; a query that names its partitions reads only them. The storage model turns message
counts, bytes per message and compression ratios into bytes a day and a year, and a cost by storage tier.

API (stable):
    RECORD                                   numpy dtype of the normalised event (56 bytes)
    read_capture(data) -> list[(recv_ns, packet)]
    arbitrate(lines, timeout_ns=500_000) -> (messages, gaps, counters)
        lines: list of [(recv_ns, packet)]; messages: [(recv_ns, seq, bytes)] in sequence order; gaps: [(first, last)]
    normalise(messages) -> np.ndarray[RECORD]
    partition(rec, root, date) -> {locate: path}; read_partition(root, date, locate) -> np.ndarray[RECORD]
    compressed_size(data, method, level) -> int         method: 'zlib' | 'zstd-parquet' | 'delta-zlib'
    delta_encode(rec) -> bytes                          column-wise, deltas on time, sequence and price
    StorageModel(msgs_per_day, bytes_per_msg, ratio, days_per_year=252, copies=1)
        .bytes_per_day(), .bytes_per_year(), .stored_after(years), .cost_per_year(prices, hot_days, warm_days, years)
"""
from __future__ import annotations

import io
import pathlib
import struct
import sys
import zlib
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "feedhandler"))
from firm_feedhandler import EVENT, blocks  # noqa: E402
from firm_feedhandler import normalise as _event  # noqa: E402

RECORD = np.dtype([("recv", "<u8"), ("kind", "u1"), ("side", "u1"), ("locate", "<u2"), ("seq", "<u8"), ("ts", "<u8"),
                   ("ref", "<u8"), ("ref2", "<u8"), ("price", "<u4"), ("qty", "<u8")], align=False)
assert RECORD.itemsize == 8 + EVENT.size == 56
FILE = struct.Struct(">QI")


def read_capture(data: bytes) -> list[tuple[int, bytes]]:
    out, i = [], 0
    while i + FILE.size <= len(data):
        t, n = FILE.unpack_from(data, i)
        out.append((t, bytes(data[i + FILE.size:i + FILE.size + n])))
        i += FILE.size + n
    return out


def arbitrate(lines, timeout_ns: int = 500_000):
    """Merge redundant lines by sequence number. A message is delivered once, at the receive
    time of its first copy; a gap is held open until a later sequence number has waited
    `timeout_ns`, then recorded and skipped."""
    ev = sorted((t, k, p) for k, line in enumerate(lines) for t, p in line)
    nxt, pending, out, gaps = 1, {}, [], []
    cnt = {"packets": 0, "messages": 0, "duplicates": 0, "gap_messages": 0}
    held_since = None
    for t, _k, p in ev:
        cnt["packets"] += 1
        seq, msgs = blocks(p)
        for j, m in enumerate(msgs):
            s = seq + j
            if s < nxt or s in pending:
                cnt["duplicates"] += 1
            else:
                pending[s] = (t, m)
        while nxt in pending:
            tt, m = pending.pop(nxt)
            out.append((tt, nxt, m))
            nxt += 1
        if pending and held_since is None:
            held_since = t
        if pending and t - held_since >= timeout_ns:
            first = min(pending)
            gaps.append((nxt, first - 1))
            cnt["gap_messages"] += first - nxt
            nxt = first
            while nxt in pending:
                tt, m = pending.pop(nxt)
                out.append((tt, nxt, m))
                nxt += 1
            held_since = t if pending else None
        elif not pending:
            held_since = None
    if pending:                                   # end of the capture: close the last gap
        first = min(pending)
        gaps.append((nxt, first - 1))
        cnt["gap_messages"] += first - nxt
        for s in sorted(pending):
            out.append((pending[s][0], s, pending[s][1]))
    cnt["messages"] = len(out)
    return out, gaps, cnt


def normalise(messages) -> np.ndarray:
    rec = np.zeros(len(messages), dtype=RECORD)
    for i, (t, s, m) in enumerate(messages):
        k, side, loc, seq, ts, ref, ref2, price, qty = _event(m, s)
        rec[i] = (t, k, side, loc, seq, ts, ref, ref2, price, qty)
    return rec


def partition(rec: np.ndarray, root, date: str) -> dict[int, pathlib.Path]:
    out = {}
    for loc in np.unique(rec["locate"]):
        d = pathlib.Path(root) / f"date={date}" / f"locate={int(loc)}"
        d.mkdir(parents=True, exist_ok=True)
        path = d / "part.bin"
        rec[rec["locate"] == loc].tofile(path)
        out[int(loc)] = path
    return out


def read_partition(root, date: str, locate: int) -> np.ndarray:
    return np.fromfile(pathlib.Path(root) / f"date={date}" / f"locate={locate}" / "part.bin", dtype=RECORD)


def delta_encode(rec: np.ndarray) -> bytes:
    """Columns one after another; time, sequence, exchange time and price as differences
    from the previous row."""
    cols = []
    for name in RECORD.names:
        delta = name in ("recv", "seq", "ts", "price")
        c = rec[name].astype(np.int64) if delta else rec[name]
        if name in ("recv", "seq", "ts", "price"):
            c = np.diff(c, prepend=c[:1] * 0)
        cols.append(np.ascontiguousarray(c).tobytes())
    return b"".join(cols)


def compressed_size(rec_or_bytes, method: str, level: int = 6) -> int:
    if method == "zlib":
        data = rec_or_bytes if isinstance(rec_or_bytes, bytes) else rec_or_bytes.tobytes()
        return len(zlib.compress(data, level))
    if method == "delta-zlib":
        return len(zlib.compress(delta_encode(rec_or_bytes), level))
    if method == "zstd-parquet":
        import pyarrow as pa
        import pyarrow.parquet as pq
        t = pa.table({n: rec_or_bytes[n] for n in RECORD.names})
        buf = io.BytesIO()
        pq.write_table(t, buf, compression="zstd", compression_level=level)
        return len(buf.getvalue())
    raise ValueError(method)


@dataclass(frozen=True)
class StorageModel:
    msgs_per_day: float
    bytes_per_msg: float
    ratio: float = 1.0                 # compression ratio (raw / compressed)
    days_per_year: int = 252
    copies: int = 1

    def bytes_per_day(self) -> float:
        return self.msgs_per_day * self.bytes_per_msg / self.ratio * self.copies

    def bytes_per_year(self) -> float:
        return self.bytes_per_day() * self.days_per_year

    def stored_after(self, years: float) -> float:
        return self.bytes_per_year() * years

    def cost_per_year(self, prices: dict, hot_days: int, warm_days: int, years: float) -> dict:
        """Steady-state yearly cost of keeping `years` of data: the last hot_days trading days in 'hot', the next
        warm_days in 'warm', the rest in 'cold'; prices in currency per GB-month (GB = 1e9 bytes)."""
        total_days = years * self.days_per_year
        hot = min(hot_days, total_days)
        warm = min(warm_days, total_days - hot)
        cold = total_days - hot - warm
        gb = self.bytes_per_day() / 1e9
        out = {"hot": hot * gb * prices["hot"] * 12, "warm": warm * gb * prices["warm"] * 12,
               "cold": cold * gb * prices["cold"] * 12}
        out["total"] = sum(out.values())
        return out
