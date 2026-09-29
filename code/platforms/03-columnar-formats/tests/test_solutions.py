"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 3 (text and solutions)."""
import io
import pathlib
import sys

import pyarrow.parquet as pq
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "colfile"))
from firm_colfile import encode
from pl_colfmt import (
    QUERIES,
    arrow_buffers,
    bytes_read,
    colfile_query,
    encodings_by_column,
    layout,
    parquet_bytes,
    quotes,
    study,
)


def pct(v, d=2):
    return round(100 * v[1] / v[0], d)


def test_small_runs(tmp_path):
    t = quotes(symbols=5, days=2, per=200)
    assert t.num_rows == 2000
    srt, tim = layout(t, "symbol, then time"), layout(t, "time order")
    q = [("symbol", "=", "S001")]
    a, na = bytes_read(parquet_bytes(srt, 256), q)
    b, nb = bytes_read(parquet_bytes(tim, 256), q)
    assert na == nb == 400 and a < b
    st = colfile_query(tmp_path / "s.ocf", t, 256)
    assert st["equal"] and st["row_groups_read"] < st["row_groups"]


def test_buffers_and_encodings():
    b = arrow_buffers()
    assert b["ts"] == [None, 8000] and b["condition"] == [125, 4004, 49] and b["condition_nulls"] == 951
    assert b["symbol_indices"] == [None, 4000] and b["symbol_dictionary"] == 50
    e, es = encodings_by_column(), encodings_by_column(sort=True)
    assert e["date"] == {"plain": 200000, "dict": 13, "rle": 15, "delta": 449}
    assert e["symbol"] == {"plain": 400008, "dict": 37917, "rle": 404432} and es["symbol"]["rle"] == 480
    assert e["ts"] == {"plain": 400000, "dict": 500009, "rle": 406259, "delta": 201085}
    assert e["bid"] == {"plain": 400000, "dict": 99097, "rle": 410505, "delta": 137947}
    assert e["bid_size"] == {"plain": 200000, "dict": 37705, "rle": 208072, "delta": 87948}
    assert e["venue"] == {"plain": 400008, "dict": 12549, "rle": 318436}
    assert round(8 * e["ts"]["delta"] / 50000, 1) == 32.2 and round(8 * es["ts"]["delta"] / 50000, 1) == 44.9
    # exercise 3: 2-bit indices + 9-byte header + 40-byte dictionary
    assert 50000 * 2 // 8 + 9 + 40 == 12549
    # exercise 2 and 1
    assert 1000 // 8 + 1001 * 4 + 49 == 4178 and (5 * 8 * 10**6, 8 * 10**6) == (40_000_000, 8_000_000)
    assert encode is not None


@pytest.mark.reference
def test_layouts():
    s = study()
    one_h, month, xs = QUERIES
    # hook and named result (8,192-row groups)
    assert s[("shuffled", 8192, one_h)][:2] == (19510913, 17020715)
    assert s[("time order", 8192, one_h)][1] == 389606 and s[("symbol, then time", 8192, one_h)][1] == 357863
    assert (pct(s[("shuffled", 8192, one_h)], 1), pct(s[("time order", 8192, one_h)]),
            pct(s[("symbol, then time", 8192, one_h)])) == (87.2, 2.65, 2.79)
    # table at 32,768 rows
    tab = [[pct(s[(lay, 32768, q)], 3) for lay in ("shuffled", "time order", "symbol, then time")] for q in QUERIES]
    assert [[round(x, 1) if x > 10 else round(x, 2) for x in r] for r in tab] == [
        [86.0, 3.3, 3.3], [34.1, 28.2, 1.07], [81.7, 3.13, 86.1]]
    assert all(s[(lay, rg, one_h)][2] == 153 for lay in ("shuffled", "time order") for rg in (8192, 32768))
    # row-group curve
    mb = {rg: round(s[("time order", rg, one_h)][1] / 1e6, 2) for rg in (2048, 8192, 524288)}
    assert mb == {2048: 0.64, 8192: 0.39, 524288: 6.00}
    assert round(s[("symbol, then time", 2048, one_h)][1] / 1e6, 2) == 0.57
    assert round(s[("symbol, then time", 524288, one_h)][1] / 1e6, 1) == 5.5
    footer = {rg: pq.ParquetFile(io.BytesIO(parquet_bytes(layout(quotes(), "time order"), rg))).metadata
              for rg in (2048, 8192)}
    assert (footer[2048].num_row_groups, round(footer[2048].serialized_size / 1e3),
            round(footer[8192].serialized_size / 1e3)) == (489, 444, 115)
    assert round(footer[2048].serialized_size / footer[8192].serialized_size, 1) == 3.9


@pytest.mark.reference
def test_exercise_7(tmp_path):
    st = colfile_query(tmp_path / "m.ocf")
    assert (st["row_groups"], st["row_groups_read"], st["rows"], st["equal"]) == (123, 2, 153, True)
