"""firm.colfile -- a minimal columnar file format, written from scratch (build of One Quant Book 15, chapter 3).

The file is a sequence of row groups; each row group holds one chunk per column; each chunk is encoded with one of four
encodings and carries its row count and its minimum and maximum; a JSON footer at the end lists every chunk's offset,
length, encoding and statistics, followed by the footer's length and a magic number, so a reader seeks to the end, reads
the footer, and then reads only the chunks it needs. It is the design of the open columnar formats (chapter 3), small
enough to read in an afternoon, and tested against pyarrow on the same data.

Encodings (numpy only):
    plain       the values' bytes (fixed width); strings as u32 offsets + UTF-8 bytes
    dict        sorted distinct values (plain) + bit-packed indices
    rle         run values (plain) + bit-packed run lengths
    delta       first value + per block of 1024 deltas: the block's minimum delta, then each delta's excess over it,
                bit-packed at the block's own width
                (integers only)

API (stable):
    ENCODINGS = ('plain', 'dict', 'rle', 'delta')
    bitpack(values, width) -> bytes; bitunpack(data, width, n) -> np.ndarray[uint64]
    encode(values, encoding) -> bytes; decode(data, encoding, dtype, n) -> np.ndarray
    best_encoding(values) -> (encoding, size)          the smallest of those that apply
    write(path, columns: dict[str, np.ndarray], row_group_size, encodings=None) -> footer dict
        encodings: {column: encoding} or None (choose the smallest per chunk)
    ColFile(path).read(columns=None, where=()) -> (dict[str, np.ndarray], stats)
        where: [(column, op, value)] with op in '==', '<', '<=', '>', '>=' (a conjunction)
        stats: {'row_groups', 'row_groups_read', 'bytes_read', 'file_bytes'}
"""
from __future__ import annotations

import json
import pathlib
import struct

import numpy as np

MAGIC = b"OQCF"
ENCODINGS = ("plain", "dict", "rle", "delta")
BLOCK = 1024
OPS = {"==": np.equal, "<": np.less, "<=": np.less_equal, ">": np.greater, ">=": np.greater_equal}


# ----------------------------------------------------------------------------------------------- bit packing
STEP = 1 << 16                     # values per pass: 2**16 * width bits is a whole number of bytes


def bitpack(values: np.ndarray, width: int) -> bytes:
    """Each value's low `width` bits, least significant first, values one after another."""
    if width == 0 or len(values) == 0:
        return b""
    v, out, shifts = np.asarray(values, dtype=np.uint64), [], np.arange(width, dtype=np.uint64)
    for b in range(0, len(v), STEP):
        bits = ((v[b:b + STEP, None] >> shifts) & np.uint64(1)).astype(np.uint8)
        out.append(np.packbits(bits.ravel(), bitorder="little").tobytes())
    return b"".join(out)


def bitunpack(data: bytes, width: int, n: int) -> np.ndarray:
    if width == 0 or n == 0:
        return np.zeros(n, dtype=np.uint64)
    raw, out, shifts = np.frombuffer(data, dtype=np.uint8), [], np.arange(width, dtype=np.uint64)
    for b in range(0, n, STEP):
        m = min(STEP, n - b)
        chunk = raw[b * width // 8:(b * width + m * width + 7) // 8]
        bits = np.unpackbits(chunk, bitorder="little")[: m * width].reshape(m, width).astype(np.uint64)
        out.append((bits << shifts).sum(axis=1, dtype=np.uint64))
    return np.concatenate(out)


def _width(x: np.ndarray) -> int:
    return int(x.max()).bit_length() if len(x) else 0


# ----------------------------------------------------------------------------------------------- plain values
def _plain(values: np.ndarray) -> bytes:
    if values.dtype.kind in "US":
        raw = [str(x).encode() for x in values]
        off = np.cumsum([0] + [len(b) for b in raw]).astype(np.uint32)
        return struct.pack("<I", len(off)) + off.tobytes() + b"".join(raw)
    return np.ascontiguousarray(values).tobytes()


def _unplain(data: bytes, dtype, n: int) -> tuple[np.ndarray, int]:
    """Values and the number of bytes consumed."""
    dtype = np.dtype(dtype)
    if dtype.kind in "US":
        (k,) = struct.unpack_from("<I", data, 0)
        off = np.frombuffer(data, dtype=np.uint32, count=k, offset=4)
        base = 4 + 4 * k
        vals = [data[base + off[i]:base + off[i + 1]].decode() for i in range(k - 1)]
        return np.array(vals, dtype=dtype), base + int(off[-1])
    size = n * dtype.itemsize
    return np.frombuffer(data[:size], dtype=dtype).copy(), size


# ----------------------------------------------------------------------------------------------- encodings
def encode(values: np.ndarray, encoding: str) -> bytes:
    n = len(values)
    if encoding == "plain":
        return _plain(values)
    if encoding == "dict":
        uniq, idx = np.unique(values, return_inverse=True)
        w = _width(idx)
        head = _plain(uniq)
        return struct.pack("<IIB", len(uniq), len(head), w) + head + bitpack(idx, w)
    if encoding == "rle":
        change = np.r_[True, values[1:] != values[:-1]] if n else np.zeros(0, dtype=bool)
        starts = np.flatnonzero(change)
        runs = np.diff(np.r_[starts, n]).astype(np.uint64)
        head = _plain(values[starts])
        w = _width(runs)
        return struct.pack("<IIB", len(starts), len(head), w) + head + bitpack(runs, w)
    if encoding == "delta":
        if values.dtype.kind not in "iu":
            raise ValueError("delta encoding needs integers")
        v = values.astype(np.int64)
        d = np.diff(v) if n > 1 else np.zeros(0, dtype=np.int64)
        out = [struct.pack("<q", int(v[0]) if n else 0)]
        for b in range(0, len(d), BLOCK):     # per block: its minimum delta, then the excess
            blk = d[b:b + BLOCK]
            lo = int(blk.min())
            x = (blk - lo).astype(np.uint64)
            w = _width(x)
            out.append(struct.pack("<qB", lo, w) + bitpack(x, w))
        return b"".join(out)
    raise ValueError(encoding)


def decode(data: bytes, encoding: str, dtype, n: int) -> np.ndarray:
    dtype = np.dtype(dtype)
    if encoding == "plain":
        return _unplain(data, dtype, n)[0]
    if encoding in ("dict", "rle"):
        k, hl, w = struct.unpack_from("<IIB", data, 0)
        uniq, _ = _unplain(data[9:9 + hl], dtype, k)
        packed = bitunpack(data[9 + hl:], w, n if encoding == "dict" else k)
        if encoding == "dict":
            return uniq[packed.astype(np.int64)]
        return np.repeat(uniq, packed.astype(np.int64))
    if encoding == "delta":
        (first,) = struct.unpack_from("<q", data, 0)
        pos, deltas = 8, []
        left = n - 1
        while left > 0:
            lo, w = struct.unpack_from("<qB", data, pos)
            m = min(BLOCK, left)
            nbytes = (m * w + 7) // 8
            deltas.append(lo + bitunpack(data[pos + 9:pos + 9 + nbytes], w, m).astype(np.int64))
            pos += 9 + nbytes
            left -= m
        d = np.concatenate(deltas) if deltas else np.zeros(0, dtype=np.int64)
        return (first + np.r_[0, np.cumsum(d)]).astype(dtype) if n else np.zeros(0, dtype=dtype)
    raise ValueError(encoding)


def best_encoding(values: np.ndarray) -> tuple[str, int]:
    cands = [e for e in ENCODINGS if e != "delta" or values.dtype.kind in "iu"]
    sizes = {e: len(encode(values, e)) for e in cands}
    e = min(sizes, key=lambda k: (sizes[k], ENCODINGS.index(k)))
    return e, sizes[e]


# ----------------------------------------------------------------------------------------------- file
def _stat(x):
    return x.item() if hasattr(x, "item") else str(x)


def write(path, columns: dict, row_group_size: int, encodings: dict | None = None) -> dict:
    names = list(columns)
    n = len(columns[names[0]])
    footer = {"n": n, "schema": {c: np.asarray(columns[c]).dtype.str for c in names}, "row_groups": []}
    with open(path, "wb") as f:
        f.write(MAGIC)
        for start in range(0, n, row_group_size):
            rg = {"rows": min(row_group_size, n - start), "chunks": {}}
            for c in names:
                v = np.asarray(columns[c])[start:start + row_group_size]
                enc = (encodings or {}).get(c) or best_encoding(v)[0]
                data = encode(v, enc)
                rg["chunks"][c] = {"offset": f.tell(), "length": len(data), "encoding": enc,
                                   "min": _stat(v[np.argmin(v)]), "max": _stat(v[np.argmax(v)])}
                f.write(data)
            footer["row_groups"].append(rg)
        blob = json.dumps(footer).encode()
        f.write(blob + struct.pack("<I", len(blob)) + MAGIC)
    return footer


class ColFile:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        size = self.path.stat().st_size
        with open(self.path, "rb") as f:
            f.seek(size - 8)
            (flen,) = struct.unpack("<I", f.read(4))
            if f.read(4) != MAGIC:
                raise ValueError("not a colfile")
            f.seek(size - 8 - flen)
            self.footer = json.loads(f.read(flen))
        self.file_bytes, self.footer_bytes = size, flen + 8

    def _may_match(self, rg, where) -> bool:
        """Zone-map pruning: False only if a condition can hold for no row of the group."""
        for col, op, val in where:
            lo, hi = rg["chunks"][col]["min"], rg["chunks"][col]["max"]
            if (op == "==" and not lo <= val <= hi) \
                    or (op in ("<", "<=") and not OPS[op](lo, val)) \
                    or (op in (">", ">=") and not OPS[op](hi, val)):
                return False
        return True

    def read(self, columns=None, where=()):
        columns = list(columns or self.footer["schema"])
        need = list(dict.fromkeys(columns + [c for c, _, _ in where]))
        out = {c: [] for c in columns}
        stats = {"row_groups": len(self.footer["row_groups"]), "row_groups_read": 0,
                 "bytes_read": self.footer_bytes, "file_bytes": self.file_bytes}
        with open(self.path, "rb") as f:
            for rg in self.footer["row_groups"]:
                if not self._may_match(rg, where):
                    continue
                stats["row_groups_read"] += 1
                vals = {}
                for c in need:
                    ch = rg["chunks"][c]
                    f.seek(ch["offset"])
                    data = f.read(ch["length"])
                    stats["bytes_read"] += ch["length"]
                    kind = self.footer["schema"][c]
                    vals[c] = decode(data, ch["encoding"], kind, rg["rows"])
                mask = np.ones(rg["rows"], dtype=bool)
                for col, op, val in where:
                    mask &= OPS[op](vals[col], val)
                for c in columns:
                    out[c].append(vals[c][mask])
        dt = self.footer["schema"]
        cols = {c: np.concatenate(out[c]) if out[c] else np.zeros(0, dtype=dt[c])
                for c in columns}
        return cols, stats
