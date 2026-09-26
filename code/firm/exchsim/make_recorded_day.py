"""Regenerate a deterministic recorded trading day (not committed), streaming to disk.

    nice -n 19 .venv/bin/python code/firm/exchsim/make_recorded_day.py [--hours 1.0] [--instruments 2] [--out DIR]

Each instrument is driven by its own Book 7 firm_tape session (kept as compact numpy arrays); their orders are merged
in time order and fed one by one to the engine; every record's feed messages are packetised (MoldUDP64) and written
at once to the line files with each line's impairments (independent loss, Gilbert-Elliott bursts, duplicates,
jitter, an outage on line B), so only the tapes' numpy arrays grow with the day. The defaults (one busy hour, two
instruments: about 0.8 million feed messages, about 140 MB, 34 s and 350 MB of memory on the author's laptop)
are for Book 13's benchmarks; run them once, late, under nice. The test runs a 72-second day.

Writes to data/generated/ (git-ignored): day_line_A.rec, day_line_B.rec (recorded files: send_ns u64 | length
u32 | MoldUDP64 packet), day_snapshots.rec (the snapshot channel every 30 s), day_journal.bin (the engine journal:
any engine replays it to the same feed), day_config.json and day_summary.json (counts and SHA-256 of each file).
Same arguments, same bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
from firm_exchsim import OPEN_NS, SEC, ExchangeConfig, InstrumentSpec, rng_uniform, stream_key  # noqa: E402
from firm_exchsim_codec import NT, encode, file_record, journal_record, mold_packet  # noqa: E402
from firm_exchsim_engine import Engine  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402

IN, CTL = NT["in"], NT["ctl"]
LOSS, BURST, DUP, JITTER_NS, LINE_NS = 0.0005, (0.0002, 0.2, 0.8), 0.0002, 2_000, (0, 1_500)


def tape_orders(tape, locate: int, session: int, tick: int, start_ns: int):
    """Yield (t_ns, locate, session, In message) for one tape, lazily: adds, cancels, and one market order per trade."""
    m = tape.msgs
    ex = m["kind"] == b"E"
    trade_ids, first = np.unique(m["trade"][ex], return_index=True)
    sizes = np.zeros(len(trade_ids), dtype=np.int64)
    np.add.at(sizes, np.searchsorted(trade_ids, m["trade"][ex]), m["qty"][ex])
    first_pos = set(np.flatnonzero(ex)[first].tolist())
    size_of = dict(zip(trade_ids.tolist(), sizes.tolist(), strict=True))
    for i in range(len(m)):
        row = m[i]
        t = start_ns + round(float(row["t"]) * SEC)
        k = row["kind"]
        if k == b"A":
            yield t, locate, session, IN["O"](int(row["oid"]), locate, "B" if row["side"] == 1 else "S",
                                             int(row["qty"]), int(row["price"]) * tick, "D", "Y", "N", 0, 0, 0, "N", 0)
        elif k == b"X":
            yield t, locate, session, IN["X"](int(row["oid"]), 0)
        elif i in first_pos:
            tid = int(row["trade"])
            yield t, locate, session, IN["O"](10**12 + tid, locate, "B" if row["agg"] == 1 else "S", size_of[tid], 0,
                                             "I", "Y", "N", 0, 0, 0, "N", 0)


class Line:
    """One feed line written straight to disk with its impairments (FIFO: jitter never reorders)."""

    def __init__(self, path: pathlib.Path, key: int, index: int, outage=None):
        self.f = open(path, "wb")
        self.key, self.index, self.outage = key, index, outage
        self.good, self.n, self.last, self.written = True, 0, 0, 0
        self.h = hashlib.sha256()

    def send(self, t: int, pkt: bytes) -> None:
        n, key = self.n, self.key
        self.n += 1
        if self.outage and self.outage[0] <= t < self.outage[1]:
            return
        u = rng_uniform(key, 4 * n)
        self.good = (u >= BURST[0]) if self.good else (u < BURST[1])
        if not self.good and rng_uniform(key, 4 * n + 1) < BURST[2]:
            return
        if rng_uniform(key, 4 * n + 2) < LOSS:
            return
        arr = t + LINE_NS[self.index] + int(-JITTER_NS * math.log(max(rng_uniform(key, 4 * n + 3), 1e-300)))
        arr = max(arr, self.last)
        self.last = arr
        copies = 2 if rng_uniform(key ^ 0xD0, n) < DUP else 1
        for c in range(copies):
            rec = file_record(arr + c, pkt)
            self.f.write(rec)
            self.h.update(rec)
            self.written += 1

    def close(self) -> str:
        self.f.close()
        return self.h.hexdigest()


def packets(session: str, first: int, enc: list[bytes], cap: int = 1380):
    chunk, size, seq = [], 0, first
    for e in enc:
        if chunk and size + 2 + len(e) > cap:
            yield mold_packet(session, seq, chunk)
            seq += len(chunk)
            chunk, size = [], 0
        chunk.append(e)
        size += 2 + len(e)
    if chunk:
        yield mold_packet(session, seq, chunk)


def run(hours: float = 1.0, n_inst: int = 2, seed: int = 2026, out: pathlib.Path | None = None) -> dict:
    out = out or HERE / "data" / "generated"
    out.mkdir(parents=True, exist_ok=True)
    (out / ".gitignore").write_text("*\n")
    close = OPEN_NS + int(hours * 3600 * SEC)
    inst = tuple(InstrumentSpec(f"SIM{k}", k, tick=100, lot=100, start_price=1_000_000 * (1 + k % 3))
                 for k in range(1, n_inst + 1))
    cfg = ExchangeConfig(venue="SIMX", instruments=inst, seed=seed)
    ecfg = cfg.engine_config()
    (out / "day_config.json").write_text(json.dumps(ecfg, indent=1) + "\n")
    eng = Engine(ecfg)
    session = cfg.mold_session
    lines = [Line(out / "day_line_A.rec", stream_key(seed, 0, 0xFEED, 0), 0),
             Line(out / "day_line_B.rec", stream_key(seed, 0, 0xFEED, 1), 1,
                  (OPEN_NS + int(0.3 * hours * 3600 * SEC), OPEN_NS + int(0.3 * hours * 3600 * SEC) + 5 * SEC))]
    snap_f, jour_f = open(out / "day_snapshots.rec", "wb"), open(out / "day_journal.bin", "wb")
    h_snap, h_jour = hashlib.sha256(), hashlib.sha256()
    feed_seq, snap_seq, n_feed, n_rec = 0, 1, 0, 0

    def process(t: int, sid: int, msg) -> None:
        nonlocal feed_seq, n_feed, n_rec
        rec = journal_record(t, sid, encode("ctl" if sid == 0 else "in", msg))
        jour_f.write(rec)
        h_jour.update(rec)
        n_rec += 1
        feed, _ = eng.process(t, sid, msg)
        eng.trades.clear()                       # keep memory flat: the truth is not needed here
        if feed:
            enc = [encode("feed", x) for x in feed]
            for pkt in packets(session, feed_seq + 1, enc):
                for ln in lines:
                    ln.send(eng.ts, pkt)
            feed_seq += len(enc)
            n_feed += len(enc)

    for m in (CTL["S"]("O"), CTL["S"]("S"), CTL["S"]("Q")):
        process(OPEN_NS - SEC, 0, m)
    for k in range(1, n_inst + 1):
        process(OPEN_NS - SEC, 0, CTL["L"](k, 100 + k, "N"))
    process(OPEN_NS, 0, CTL["P"](0, "T", "OPEN"))
    tapes = [simulate(TapeConfig(seconds=hours * 3600.0, seed=seed + 17 * k, u_shape=1.5, lo_rate=2.8, noise_mu=0.7,
                                 start=10_000 * (1 + k % 3))) for k in range(1, n_inst + 1)]
    streams = [tape_orders(tp, k, k, 100, OPEN_NS) for k, tp in enumerate(tapes, start=1)]
    next_snap = OPEN_NS + 30 * SEC
    for t, _, sid, msg in heapq.merge(*streams, key=lambda r: (r[0], r[1])):
        while t >= next_snap:
            for loc in range(1, n_inst + 1):
                enc = [encode("feed", x) for x in eng.snapshot(loc, feed_seq, next_snap)]
                for pkt in packets((cfg.venue[:9] + "S").ljust(10), snap_seq, enc):
                    rec = file_record(next_snap, pkt)
                    snap_f.write(rec)
                    h_snap.update(rec)
                snap_seq += len(enc)
            next_snap += 30 * SEC
        process(t, sid, msg)
    del tapes
    process(close, 0, CTL["P"](0, "C", "CLOS"))
    process(close + 1, 0, CTL["E"](0, "D"))
    process(close + 2, 0, CTL["S"]("C"))
    snap_f.close()
    jour_f.close()
    summary = {"feed_messages": n_feed, "journal_records": n_rec,
               "packets_A": lines[0].written, "packets_B": lines[1].written,
               "sha256": {"day_line_A.rec": lines[0].close(), "day_line_B.rec": lines[1].close(),
                          "day_snapshots.rec": h_snap.hexdigest(), "day_journal.bin": h_jour.hexdigest()}}
    (out / "day_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=1.0)
    ap.add_argument("--instruments", type=int, default=2)
    ap.add_argument("--out", default=str(HERE / "data" / "generated"))
    a = ap.parse_args(argv)
    s = run(a.hours, a.instruments, out=pathlib.Path(a.out))
    print(json.dumps(s, indent=1))
    return s


if __name__ == "__main__":
    main()
