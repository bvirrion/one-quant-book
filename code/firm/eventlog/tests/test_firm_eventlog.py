"""Acceptance tests of firm.eventlog (One Quant Book 15, chapter 24)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_eventlog as L  # noqa: E402


def test_partitions_offsets_segments_retention(tmp_path):
    log = L.Log(tmp_path, segment=10)
    log.create("t", 3)
    offs = [log.append("t", "k1", i) for i in range(25)]
    p = offs[0][0]
    assert all(q == p for q, _ in offs) and [o for _, o in offs] == list(range(25))   # one key, one partition, in order
    assert [v for _, _, v in log.read("t", p, 20, 10)] == [20, 21, 22, 23, 24]
    assert len(list((tmp_path / "t" / f"{p:03d}").glob("*.log"))) == 3
    log.retain("t", 8)
    assert log.read("t", p, 0, 2)[0][0] == 17 and log.end("t", p) == 25
    assert len(list((tmp_path / "t" / f"{p:03d}").glob("*.log"))) == 2               # segment 0-9 dropped


def test_idempotent_producer_and_groups():
    log = L.Log()
    log.create("t", 2)
    assert log.append("t", "a", 1, pid="P", seq=7)[1] == 0
    assert log.append("t", "a", 1, pid="P", seq=7)[1] == -1                          # resend ignored
    assert L.assign([0, 1, 2, 3, 4, 5, 6, 7], ["c", "a", "b"]) == {"a": [0, 3, 6], "b": [1, 4, 7], "c": [2, 5]}
    log.commit("g", "t", 0, 5)
    assert (log.committed("g", "t", 0), log.committed("h", "t", 0)) == (5, 0)


def _run(mode, crash_at, tmp_path):
    log = L.Log()
    log.create("f", 1)
    for i in range(10):
        log.append("f", "acc", {"id": i, "account": "A", "symbol": "S", "qty": 1})
    seen, store = [], (L.AtomicStore(str(tmp_path / "s.db")) if mode == "atomic" else None)

    def apply(f):
        seen.append(f["id"]) if store is None else store.apply(f)

    def crash(stage, i):
        if (stage, i) == crash_at:
            raise L.Crash(stage)
    with pytest.raises(L.Crash):
        L.run_batch(log, "g", "f", 0, 10, apply, mode, crash, store)
    if store is not None:
        store.rollback()
    L.run_batch(log, "g", "f", 0, 10, apply, mode, None, store)                   # restart
    return seen if store is None else store.positions()


@pytest.mark.parametrize("mode,crash_at,expect", [
    ("at-most-once", ("process", 4), [0, 1, 2, 3]),                        # the rest of the batch is lost
    ("at-least-once", ("before-commit", 10), list(range(10)) * 2),         # the whole batch again
    ("atomic", ("before-commit", 10), {"A/S": 10})])                       # exactly once
def test_delivery_modes(tmp_path, mode, crash_at, expect):
    assert _run(mode, crash_at, tmp_path) == expect


def test_outbox_relay_resend_is_deduplicated(tmp_path):
    log, box = L.Log(), L.Outbox(str(tmp_path / "o.db"))
    log.create("trades", 1)
    box.write({"id": "T1"}, {"key": "T1"})

    def crash(stage, num):
        raise L.Crash(stage)
    with pytest.raises(L.Crash):
        box.relay(log, "trades", crash)
    assert box.relay(log, "trades") == 1 and log.end("trades", 0) == 1       # resent, stored once


def test_dead_letters():
    log = L.Log()
    log.create("f", 1)
    for v in (1, "bad", 3):
        log.append("f", "k", v)
    out, off = [], 0

    def handler(v):
        out.append(v + 0)
    for _ in range(3):
        off, dead = L.process_with_dlq(log, "f", 0, off, handler)
    assert out == [1, 3] and log.read("f.dlq", 0, 0, 1)[0][2]["offset"] == 1
