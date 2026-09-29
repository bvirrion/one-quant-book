"""firm.eventlog -- a partitioned log in process, consumer groups, delivery modes, outbox, dead letters (B15 ch. 24).

The log is the Kafka design at toy scale and without a server: topics split into partitions, a message's partition
chosen by a stable hash of its key (so one key's messages stay in order), each partition an append-only sequence of
messages addressed by offset, written in segments to disk when a directory is given, and trimmed by retention.
Producers may attach a (producer id, sequence) pair, and a partition ignores a pair it has already stored, so a resend
does not duplicate. Consumer groups share a topic's partitions among their members and keep one committed offset per
partition. The consumer helpers implement the three ways of combining processing with committing, the outbox the
standard way of publishing an event together with a database change (sqlite3, standard library), and a dead-letter
topic takes messages a handler keeps failing on.

API (stable):
    Log(directory=None, segment=1000): .create(topic, partitions) ; .append(topic, key, value, pid=None, seq=None)
        -> (partition, offset) ; .read(topic, partition, offset, n) -> [(offset, key, value)] ; .end(topic, p)
        .retain(topic, keep) ; .commit(group, topic, p, offset) ; .committed(group, topic, p) -> int
    assign(partitions, members) -> {member: [partitions]}          round-robin, deterministic
    run_batch(log, group, topic, p, n, apply, mode, crash=None, store=None) -> int (messages read)
        modes: 'at-most-once' (commit, then process), 'at-least-once' (process, then commit),
        'atomic' (state and offset in one sqlite transaction: store = AtomicStore)
    AtomicStore(path).apply(fill) ; .offset(topic, p) ; .positions()
    Outbox(path): .write(trade, event) in one transaction ; .relay(log, topic, crash=None) -> published
    process_with_dlq(log, topic, p, offset, handler, retries=3) -> (next offset, sent to dead letters)
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import zlib


class Crash(Exception):
    """Raised by a crash schedule to stop a consumer or relay at a chosen point."""


class Log:
    def __init__(self, directory: str | pathlib.Path | None = None, segment: int = 1000):
        self.dir = pathlib.Path(directory) if directory else None
        self.segment = segment
        self.parts: dict = {}          # topic -> [[(offset, key, value)]]
        self.base: dict = {}           # (topic, p) -> offset of the first retained message
        self.seen: dict = {}           # (topic, p) -> {(pid, seq)}
        self.offsets: dict = {}        # (group, topic, p) -> committed offset

    def create(self, topic: str, partitions: int) -> None:
        self.parts[topic] = [[] for _ in range(partitions)]
        for p in range(partitions):
            self.base[(topic, p)], self.seen[(topic, p)] = 0, set()

    def partition(self, topic: str, key: str) -> int:
        return zlib.crc32(key.encode()) % len(self.parts[topic])

    def append(self, topic, key, value, pid=None, seq=None) -> tuple[int, int]:
        """Append to the key's partition; a (pid, seq) already stored is ignored."""
        p = self.partition(topic, key)
        if pid is not None:
            if (pid, seq) in self.seen[(topic, p)]:
                return p, -1                           # duplicate send: ignored
            self.seen[(topic, p)].add((pid, seq))
        off = self.end(topic, p)
        self.parts[topic][p].append((off, key, value))
        if self.dir is not None:
            self._write(topic, p, off, key, value)
        return p, off

    def _write(self, topic, p, off, key, value) -> None:
        seg = self.dir / topic / f"{p:03d}" / f"{off - off % self.segment:012d}.log"
        seg.parent.mkdir(parents=True, exist_ok=True)
        with open(seg, "a") as f:
            f.write(json.dumps([off, key, value]) + "\n")

    def end(self, topic: str, p: int) -> int:
        return self.base[(topic, p)] + len(self.parts[topic][p])

    def read(self, topic: str, p: int, offset: int, n: int) -> list:
        i = max(0, offset - self.base[(topic, p)])
        return self.parts[topic][p][i:i + n]

    def retain(self, topic: str, keep: int) -> None:
        """Keep the last `keep` messages of every partition, dropping whole segments on disk."""
        for p, msgs in enumerate(self.parts[topic]):
            drop = max(0, len(msgs) - keep)
            self.base[(topic, p)] += drop
            self.parts[topic][p] = msgs[drop:]
            if self.dir is not None:
                for seg in sorted((self.dir / topic / f"{p:03d}").glob("*.log")):
                    if int(seg.stem) + self.segment <= self.base[(topic, p)]:
                        seg.unlink()

    def commit(self, group: str, topic: str, p: int, offset: int) -> None:
        self.offsets[(group, topic, p)] = offset

    def committed(self, group: str, topic: str, p: int) -> int:
        return self.offsets.get((group, topic, p), 0)


def assign(partitions: list, members: list) -> dict:
    out = {m: [] for m in sorted(members)}
    for i, p in enumerate(sorted(partitions)):
        out[sorted(members)[i % len(members)]].append(p)
    return out


# ------------------------------------------------------------ delivery modes
def run_batch(log, group, topic, p, n, apply, mode, crash=None, store=None) -> int:
    """Read up to n messages from the committed offset and process them under `mode`;
    crash(stage, i) may raise Crash to simulate the process dying at that point."""
    crash = crash or (lambda stage, i: None)
    start = store.offset(topic, p) if mode == "atomic" else log.committed(group, topic, p)
    batch = log.read(topic, p, start, n)
    if not batch:
        return 0
    nxt = batch[-1][0] + 1
    if mode == "at-most-once":
        log.commit(group, topic, p, nxt)             # commit first: a crash loses the rest
    if mode == "atomic":
        store.begin()
    for i, (_off, _key, value) in enumerate(batch):
        crash("process", i)
        apply(value)
    crash("before-commit", len(batch))
    if mode == "at-least-once":
        log.commit(group, topic, p, nxt)             # commit after: a crash repeats it
    if mode == "atomic":
        store.commit(topic, p, nxt)                  # state and offset in one transaction
    return len(batch)


class AtomicStore:
    """Positions and consumed offsets in one SQLite database, changed in one transaction."""

    def __init__(self, path: str):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")      # a process crash never splits a transaction;
        self.db.execute("PRAGMA synchronous=NORMAL")    # an OS crash may lose the last ones, whole
        self.db.execute("CREATE TABLE IF NOT EXISTS pos (k TEXT PRIMARY KEY, q INTEGER)")
        self.db.execute("CREATE TABLE IF NOT EXISTS off (t TEXT, p INTEGER, o INTEGER, PRIMARY KEY (t, p))")

    def begin(self) -> None:
        self.db.execute("BEGIN")

    def apply(self, fill: dict) -> None:
        self.db.execute("INSERT INTO pos VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET q = q + excluded.q",
                        (fill["account"] + "/" + fill["symbol"], fill["qty"]))

    def commit(self, topic: str, p: int, offset: int) -> None:
        self.db.execute("INSERT OR REPLACE INTO off VALUES (?, ?, ?)", (topic, p, offset))
        self.db.execute("COMMIT")

    def rollback(self) -> None:
        if self.db.in_transaction:
            self.db.execute("ROLLBACK")

    def offset(self, topic: str, p: int) -> int:
        r = self.db.execute("SELECT o FROM off WHERE t = ? AND p = ?", (topic, p)).fetchone()
        return r[0] if r else 0

    def positions(self) -> dict:
        return dict(self.db.execute("SELECT k, q FROM pos"))


# ------------------------------------------------------------ transactional outbox
class Outbox:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS trades (id TEXT PRIMARY KEY, body TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS outbox (n INTEGER PRIMARY KEY, key TEXT, body TEXT, sent INT)")

    def write(self, trade: dict, event: dict) -> None:
        """The trade and the event that announces it, committed together or not at all."""
        self.db.execute("BEGIN")
        self.db.execute("INSERT INTO trades VALUES (?, ?)",
                        (trade["id"], json.dumps(trade)))
        self.db.execute("INSERT INTO outbox (key, body, sent) VALUES (?, ?, 0)",
                        (event["key"], json.dumps(event)))
        self.db.execute("COMMIT")

    def relay(self, log: Log, topic: str, crash=None) -> int:
        """Publish unsent events in order, with the outbox number as idempotence key, then
        mark each sent; a crash in between resends it later, and the log ignores it."""
        n = 0
        rows = self.db.execute("SELECT n, key, body FROM outbox WHERE sent = 0 "
                               "ORDER BY n").fetchall()
        for num, key, body in rows:
            log.append(topic, key, json.loads(body), pid="outbox", seq=num)
            if crash:
                crash("published", num)
            self.db.execute("UPDATE outbox SET sent = 1 WHERE n = ?", (num,))
            n += 1
        return n


# ------------------------------------------------------------ dead letters
def process_with_dlq(log: Log, topic: str, p: int, offset: int, handler, retries: int = 3):
    """Process one message; after `retries` failures, send it to '<topic>.dlq' and move on."""
    msgs = log.read(topic, p, offset, 1)
    if not msgs:
        return offset, False
    off, key, value = msgs[0]
    for _ in range(retries):
        try:
            handler(value)
            return off + 1, False
        except Exception:                               # noqa: BLE001 - any handler failure
            continue
    dlq = topic + ".dlq"
    if dlq not in log.parts:
        log.create(dlq, 1)
    log.append(dlq, key, {"offset": off, "partition": p, "value": value})
    return off + 1, True
