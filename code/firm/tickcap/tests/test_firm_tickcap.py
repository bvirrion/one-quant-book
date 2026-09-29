"""Acceptance tests of firm.tickcap (One Quant Book 15, chapter 2)."""
import pathlib
import sys
import zlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "feedhandler"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "exchsim"))
import firm_feedhandler as fh
import make_recorded_day
from firm_exchsim_codec import file_record, mold_packet
from firm_tickcap import (
    RECORD,
    StorageModel,
    arbitrate,
    compressed_size,
    delta_encode,
    normalise,
    partition,
    read_capture,
    read_partition,
)


def msg(seq):
    """A valid 'D' (delete) feed message: type, locate, tracking, 6-byte ts, 8-byte ref."""
    return b"D" + (1).to_bytes(2, "big") + b"\0\0" + (1000 + seq).to_bytes(6, "big") + seq.to_bytes(8, "big")


def pkt(seq):
    return mold_packet("SIMX", seq, [msg(seq)])


def test_record_layout_is_receive_time_plus_feed_event():
    assert RECORD.itemsize == 56 == 8 + fh.EVENT.size


def test_capture_round_trip():
    data = b"".join(file_record(10 * s, pkt(s)) for s in range(1, 6))
    got = read_capture(data)
    assert [t for t, _ in got] == [10, 20, 30, 40, 50] and got[2][1] == pkt(3)


def test_arbitration_first_copy_wins_and_gaps_are_recorded():
    a = [(100, pkt(1)), (300, pkt(3)), (400, pkt(4)), (2_000_000, pkt(7))]      # 2 lost on A
    b = [(150, pkt(1)), (250, pkt(2)), (350, pkt(3)), (2_000_100, pkt(7))]      # 5, 6 lost on both
    msgs, gaps, cnt = arbitrate([a, b], timeout_ns=500_000)
    assert [(t, s) for t, s, _ in msgs] == [(100, 1), (250, 2), (300, 3), (400, 4), (2_000_000, 7)]
    assert gaps == [(5, 6)] and cnt["gap_messages"] == 2 and cnt["duplicates"] == 3


def test_same_events_as_the_feed_handler_on_a_recorded_session(tmp_path):
    make_recorded_day.run(0.005, 2, out=tmp_path)
    A, B = (tmp_path / "day_line_A.rec").read_bytes(), (tmp_path / "day_line_B.rec").read_bytes()
    msgs, gaps, _ = arbitrate([read_capture(A), read_capture(B)])
    rec = normalise(msgs)
    h = fh.Handler(retx=None).run(fh.merge(A, B))
    upto = gaps[0][0] - 1 if gaps else len(rec)
    assert upto > 1000
    ev = [tuple(int(x) for x in r) for r in rec[["kind", "side", "locate", "seq", "ts", "ref", "ref2", "price", "qty"]]]
    assert ev[:upto] == [tuple(e) for e in h.events[:upto]]
    assert (np.diff(rec["seq"].astype(np.int64)) > 0).all()


def test_partition_round_trip(tmp_path):
    rec = np.zeros(10, dtype=RECORD)
    rec["locate"] = [1, 2] * 5
    rec["seq"] = np.arange(10)
    paths = partition(rec, tmp_path, "2026-09-28")
    assert set(paths) == {1, 2} and paths[1].stat().st_size == 5 * 56
    assert (read_partition(tmp_path, "2026-09-28", 2)["seq"] == [1, 3, 5, 7, 9]).all()


def test_compression_methods_and_delta_is_invertible():
    rec = np.zeros(1000, dtype=RECORD)
    rec["recv"] = 10**9 + np.arange(1000) * 1000
    rec["seq"] = np.arange(1, 1001)
    rec["price"] = 1_000_000 + (np.arange(1000) % 7) * 100
    for m in ("zlib", "delta-zlib", "zstd-parquet"):
        assert 0 < compressed_size(rec, m) < rec.nbytes
    assert compressed_size(rec, "delta-zlib") < compressed_size(rec, "zlib")
    raw = zlib.decompress(zlib.compress(delta_encode(rec)))
    col = np.frombuffer(raw[:8000], dtype=np.int64)
    assert (np.cumsum(col) == rec["recv"].astype(np.int64)).all()


def test_storage_model_arithmetic():
    m = StorageModel(1e9, 50, ratio=5.0, days_per_year=250, copies=2)
    assert m.bytes_per_day() == 2e10 and m.bytes_per_year() == 5e12 and m.stored_after(2) == 1e13
    c = m.cost_per_year({"hot": 1.0, "warm": 0.5, "cold": 0.1}, hot_days=10, warm_days=90, years=1)
    assert c["hot"] == 10 * 20 * 12 and c["warm"] == 90 * 20 * 0.5 * 12 and c["cold"] == 150 * 20 * 0.1 * 12
