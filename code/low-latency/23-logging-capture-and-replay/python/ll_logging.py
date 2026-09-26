"""Chapter 23 helpers: the event streams whose journals the chapter measures, the journal of each, and the storage
arithmetic of the weekend problem.

streams() -> {name: (events as 48-byte records, recorded span in seconds, tick)}
journal(records) -> bytes                    firm.binlog journal, received 5 us after the exchange time stamp
storage_per_day(msgs_per_s, hours, bytes_per_msg, ratio) -> bytes
"""
import pathlib
import struct
import sys
import zlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "code/firm/binlog"))
sys.path.insert(0, str(ROOT / "code/low-latency/19-the-order-book-builder/python"))
import firm_binlog as bl  # noqa: E402

RECORD = 56


def streams():
    import ll_book
    large = ll_book.mk.pack(ll_book.large_tick_events())
    small = (ROOT / "code/firm/bookbuilder/data/events_small.bin").read_bytes()
    out = {}
    for name, raw, tick in (("large tick (the open)", large, 100), ("small tick (synthetic)", small, 1)):
        recs = [raw[i:i + 48] for i in range(0, len(raw), 48)]
        ts = [struct.unpack_from("<Q", r, 12)[0] for r in recs]
        out[name] = (recs, (max(ts) - min(ts)) / 1e9, tick)
    return out


def journal(records):
    return bl.journal_write([(struct.unpack_from("<Q", r, 12)[0] + 5_000, r) for r in records])


def compressed(data, level=6):
    return len(zlib.compress(data, level))


def storage_per_day(msgs_per_s, hours, bytes_per_msg, ratio=1.0):
    return msgs_per_s * hours * 3600 * bytes_per_msg / ratio
