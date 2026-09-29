"""Acceptance tests of firm.tickstore (One Quant Book 15, chapter 4)."""
import pathlib
import sys

import numpy as np
import pyarrow as pa
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tickstore import (
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

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


def ev(rows):
    """rows of (kind, side, locate, seq, ts, ref, price, qty)."""
    rec = np.zeros(len(rows), dtype=EVENT_V1)
    for i, (k, s, loc, seq, ts, ref, price, qty) in enumerate(rows):
        rec[i] = (ts + 5, ord(k), ord(s) if s else 0, loc, seq, ts, ref, 0, price, qty)
    return rec


BOOK = ev([("A", "B", 1, 1, 100, 11, 9900, 100), ("A", "S", 1, 2, 100, 12, 10100, 100),
           ("A", "B", 1, 3, 200, 13, 9950, 200), ("E", None, 1, 4, 300, 13, 0, 200),       # bid 9950 taken
           ("A", "S", 1, 5, 300, 14, 10050, 50), ("E", None, 1, 6, 400, 14, 0, 50)])       # ask 10050 taken


def test_flat_files_both_versions(tmp_path):
    for version, dt in ((1, EVENT_V1), (2, EVENT_V2)):
        w = FlatWriter(tmp_path / f"v{version}.flat", version)
        w.append(upgrade(BOOK, version) if version == 2 else BOOK)
        w.append(upgrade(BOOK[:2], version) if version == 2 else BOOK[:2])
        w.close()
        v, rec = flat_open(tmp_path / f"v{version}.flat")
        assert v == version and rec.dtype == dt and len(rec) == 8 and isinstance(rec, np.memmap)
        assert (rec["seq"][:6] == BOOK["seq"]).all() and (rec[:6]["qty"] == BOOK["qty"]).all()
        head = (tmp_path / f"v{version}.flat").stat().st_size - 8 * dt.itemsize
        assert head % 64 == 0
    assert EVENT_V1.itemsize == 56 and EVENT_V2.itemsize == 64
    assert (upgrade(BOOK, 2)["venue"] == 0).all()
    (tmp_path / "bad.flat").write_bytes(b"XXXX" + bytes(60))
    with pytest.raises(ValueError):
        flat_open(tmp_path / "bad.flat")


def test_python_reader_matches_the_fixture_the_twins_check():
    for line in (DATA / "fixture_expected.txt").read_text().splitlines():
        name, loc, c, q, s = line.split()
        _, rec = flat_open(DATA / name)
        m = rec["locate"] == int(loc)
        assert (int(m.sum()), int(rec["qty"][m & (rec["kind"] == ord("E"))].sum()), int(rec["seq"][m].max())) == \
            (int(c), int(q), int(s))


def test_quotes_and_trades_from_events():
    q, t = quotes_trades(BOOK, {1: "X"})
    assert q["seq"].to_pylist() == [2, 3, 4, 5, 6]
    assert q["bid"].to_pylist() == [9900, 9950, 9900, 9900, 9900]
    assert q["ask"].to_pylist() == [10100, 10100, 10100, 10050, 10100]
    assert t["price"].to_pylist() == [9950, 10050] and t["seq"].to_pylist() == [4, 6]


def test_ipc_round_trip(tmp_path):
    q, _ = quotes_trades(BOOK, {1: "X"})
    w = IpcWriter(tmp_path / "q.arrows", q.schema)
    w.append(q.slice(0, 2))
    w.append(q.slice(2))
    w.close()
    assert ipc_read(tmp_path / "q.arrows").equals(q)


def test_store_unions_history_and_today_and_evolves(tmp_path):
    q, t = quotes_trades(BOOK, {1: "X"})
    compact({"quotes": q, "trades": t}, tmp_path / "hist", "2026-09-21")
    q2 = q.append_column("venue", pa.array(["V"] * q.num_rows))
    compact({"quotes": q2, "trades": t}, tmp_path / "hist", "2026-09-22")
    s = Store(tmp_path / "hist", {"quotes": q2, "trades": t}, "2026-09-23")
    r = s.sql("SELECT date, count(*) n, count(venue) v FROM quotes GROUP BY date ORDER BY date").to_pylist()
    assert [(x["n"], x["v"]) for x in r] == [(5, 0), (5, 5), (5, 5)]
    duck = asof_duckdb(s)
    tr = s.sql("SELECT date, symbol, seq, ts, price, qty FROM trades")
    qu = s.sql("SELECT date, symbol, seq, ts, bid, ask FROM quotes")
    for other in (asof_polars(tr, qu), asof_reference(tr, qu)):
        assert all(duck[c].to_pylist() == other[c].to_pylist() for c in duck.column_names)
    # the quote prevailing before each trade: before seq 4 the bid was 9950, before seq 6 the ask was 10050
    assert duck["bid"].to_pylist()[:2] == [9950, 9900] and duck["ask"].to_pylist()[:2] == [10100, 10050]
    # a join on the timestamp picks a quote the trade itself produced (same ts)
    by_ts = asof_duckdb(s, "ts")
    assert by_ts["bid"].to_pylist()[0] == 9900 and by_ts["ask"].to_pylist()[1] == 10100


def test_schema_evolution_rules():
    v1 = {"a": "u8", "b": "u4"}
    assert check_evolution(v1, {"a": "u8", "b": "u4", "c": "u2"}) == []
    assert check_evolution(v1, {"a": "u8"}) == ["field b removed or renamed"]
    assert check_evolution(v1, {"a": "i8", "b": "u4"}) == ["field a retyped u8 -> i8"]
    assert check_evolution(v1, {"b": "u4", "a": "u8"}) == ["old fields reordered"]
    assert check_evolution(v1, {"a": "u8", "c": "u2", "b": "u4"}) == ["field c inserted before existing fields"]
