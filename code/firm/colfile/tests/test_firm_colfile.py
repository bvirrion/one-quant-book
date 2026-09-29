"""Acceptance tests of firm.colfile (One Quant Book 15, chapter 3)."""
import io
import pathlib
import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_colfile import ENCODINGS, ColFile, best_encoding, bitpack, bitunpack, decode, encode, write


def data(n=20_000, seed=5):
    rng = np.random.default_rng(seed)
    sym = np.sort(rng.choice(np.array(["AAA", "BB", "CCCC", "D"]), n))
    ts = np.cumsum(rng.integers(1, 1000, n)).astype(np.int64)
    return {"symbol": sym, "ts": ts, "price": rng.integers(990, 1010, n).astype(np.int64) * 100,
            "size": rng.integers(1, 9, n).astype(np.int32), "flag": np.repeat(np.arange(4), n // 4).astype(np.uint8)}


@pytest.mark.parametrize("width", [0, 1, 3, 17, 40, 64])
def test_bitpack_round_trip(width):
    v = np.random.default_rng(width).integers(0, 2**63, 70_001, dtype=np.uint64)
    v = v & np.uint64((1 << width) - 1) if width < 64 else v
    assert (bitunpack(bitpack(v, width), width, len(v)) == v).all()
    assert len(bitpack(v, width)) == (len(v) * width + 7) // 8


def test_every_encoding_round_trips_every_column():
    for name, v in data().items():
        for e in ENCODINGS:
            if e == "delta" and v.dtype.kind not in "iu":
                with pytest.raises(ValueError):
                    encode(v, e)
                continue
            assert (decode(encode(v, e), e, v.dtype, len(v)) == v).all(), (name, e)


def test_best_encoding_picks_the_obvious_one():
    assert best_encoding(np.repeat(np.arange(3), 10_000))[0] == "rle"
    assert best_encoding(np.arange(0, 3 * 10**5, 3, dtype=np.int64))[0] == "delta"
    assert best_encoding(np.random.default_rng(1).choice(np.array(["x", "y", "z"]), 10_000))[0] == "dict"


def test_file_answers_like_pyarrow_and_prunes(tmp_path):
    d = data()
    path = tmp_path / "t.ocf"
    write(path, d, row_group_size=1000)
    cf = ColFile(path)
    where = [("symbol", "==", "CCCC"), ("ts", ">=", int(d["ts"][9000])), ("ts", "<", int(d["ts"][9500]))]
    got, st = cf.read(["ts", "price"], where)
    buf = io.BytesIO()
    pq.write_table(pa.table(d), buf)
    ref = pq.read_table(io.BytesIO(buf.getvalue()), columns=["ts", "price"],
                        filters=[("symbol", "=", "CCCC"), ("ts", ">=", int(d["ts"][9000])), ("ts", "<", int(d["ts"][9500]))])
    assert (got["ts"] == ref["ts"].to_numpy()).all() and (got["price"] == ref["price"].to_numpy()).all()
    assert st["row_groups"] == 20 and st["row_groups_read"] == 1
    assert st["bytes_read"] - cf.footer_bytes < (st["file_bytes"] - cf.footer_bytes) / 10
    everything, st2 = cf.read()
    assert all((everything[c] == d[c]).all() for c in d) and st2["row_groups_read"] == 20


def test_projection_reads_only_the_named_columns(tmp_path):
    d = data()
    path = tmp_path / "t.ocf"
    footer = write(path, d, row_group_size=5000, encodings={"ts": "delta"})
    assert {rg["chunks"]["ts"]["encoding"] for rg in footer["row_groups"]} == {"delta"}
    _, st = ColFile(path).read(["size"])
    sizes = sum(rg["chunks"]["size"]["length"] for rg in footer["row_groups"])
    assert st["bytes_read"] == sizes + ColFile(path).footer_bytes
