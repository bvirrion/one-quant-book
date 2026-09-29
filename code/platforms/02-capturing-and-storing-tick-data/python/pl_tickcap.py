"""Capturing and storing tick data (One Quant Book 15, chapter 2).

A busy simulated session from Book 10's firm.exchsim (make_recorded_day: two instruments, lines A and B with loss,
bursts, duplicates, jitter and a five-second outage on line B) is captured raw, arbitrated and normalised by
firm.tickcap, compressed several ways, partitioned by instrument, and scaled with the storage model to a cited
full-feed message count. The chapter's session is ten minutes (about 0.26 million messages, 16 MB a line), generated
once into data/platforms/generated/ (git-ignored); the fast tests use 72 seconds in a temporary directory.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("tickcap", "feedhandler", "exchsim"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
import make_recorded_day  # noqa: E402
from firm_tickcap import (  # noqa: E402
    RECORD,
    StorageModel,
    arbitrate,
    compressed_size,
    normalise,
    partition,
    read_capture,
)

HOURS = 0.1667                                   # ten minutes of the busy open
GEN = ROOT / "data/platforms/generated"

# Cited inputs (ledger F1-F2): OPRA's projected capacity for July 2026 and a cloud object store's list prices.
OPRA_MSGS_PER_DAY = 311e9                        # total messages per day, capacity projection effective 7/2026
PRICES = {"hot": 0.023, "warm": 0.0125, "cold": 0.00099}      # USD per GB-month: standard, infrequent, deep archive
RETENTION_YEARS = 5                              # order records kept five years (RTS 6, article 28)


def day(hours: float = HOURS, out: pathlib.Path | None = None) -> pathlib.Path:
    out = out or GEN / f"day_{round(hours * 3600)}s"
    if not (out / "day_summary.json").exists():
        make_recorded_day.run(hours, 2, out=out)
    return out


def capture(d: pathlib.Path):
    a, b = (d / "day_line_A.rec").read_bytes(), (d / "day_line_B.rec").read_bytes()
    return a, b


@functools.lru_cache(maxsize=4)
def study(hours: float = HOURS, out: str | None = None) -> dict:
    d = day(hours, pathlib.Path(out) if out else None)
    a, b = capture(d)
    msgs, gaps, cnt = arbitrate([read_capture(a), read_capture(b)])
    rec = normalise(msgs)
    n = len(rec)
    kinds, counts = np.unique(rec["kind"], return_counts=True)
    layouts = {
        "raw capture": len(a),
        "raw, zlib 6": compressed_size(a, "zlib", 6),
        "normalised": rec.nbytes,
        "normalised, zlib 6": compressed_size(rec, "zlib", 6),
        "Parquet, zstd 3": compressed_size(rec, "zstd-parquet", 3),
        "delta columns, zlib 6": compressed_size(rec, "delta-zlib", 6),
    }
    parts = {}
    for loc in np.unique(rec["locate"]):
        parts[int(loc)] = int((rec["locate"] == loc).sum()) * RECORD.itemsize
    return {"messages": n, "bytes_A": len(a), "bytes_B": len(b), "gaps": gaps, "counters": cnt,
            "kinds": {chr(k): int(c) for k, c in zip(kinds, counts, strict=True)},
            "layouts": layouts, "per_msg": {k: v / n for k, v in layouts.items()},
            "ratio": {k: layouts["raw capture" if k.startswith("raw") else "normalised"] / v
                      for k, v in layouts.items()},
            "partitions": parts, "rec": rec}


def write_partitions(rec, root, date="2026-09-28"):
    return partition(rec, root, date)


def economics(per_msg: dict, msgs_per_day: float = OPRA_MSGS_PER_DAY) -> dict:
    """Bytes a day and a year, and five years kept, for full capture at the cited message count."""
    rows = {}
    for name, b, copies in (("raw capture, both lines", per_msg["raw capture"], 2),
                            ("raw capture, one line", per_msg["raw capture"], 1),
                            ("normalised", per_msg["normalised"], 1),
                            ("delta columns, zlib 6", per_msg["delta columns, zlib 6"], 1)):
        m = StorageModel(msgs_per_day, b, 1.0, copies=copies)
        rows[name] = {"TB_day": m.bytes_per_day() / 1e12, "PB_year": m.bytes_per_year() / 1e15,
                      "PB_5y": m.stored_after(RETENTION_YEARS) / 1e15,
                      "cost": m.cost_per_year(PRICES, hot_days=21, warm_days=231, years=RETENTION_YEARS)}
    return rows
