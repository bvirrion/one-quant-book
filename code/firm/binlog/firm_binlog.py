"""firm.binlog -- binary logs with deferred formatting, and input journals: Python reference encoder and the decoder
(build of One Quant Book 13, chapter 23). Formats in cpp/firm_binlog.hpp; the C++20 and Rust loggers write the same
bytes for the same statements (data/sample.blog), and this module formats them offline.

API (stable):
    site_id(fmt, types) -> int                 16-bit identifier (FNV-1a over the format, a zero byte, the type codes)
    Writer(); .log(ts, fmt, types, *args); .bytes() -> bytes      reference encoder (file header + records)
    read(data) -> (sites {id: (fmt, types)}, records [(ts, id, args)])
    text(sites, records) -> [str]              "ts formatted-message", one per record
    first_difference(a, b) -> index or None    first record at which two decoded logs differ (bisecting a replay)
    journal_write(records) -> bytes; journal_read(data) -> [(recv_ts, event48)]
"""
import struct

MAGIC, JMAGIC = b"FBINLOG1", b"FJOURNL1"
SIZES = {"i": 8, "u": 8, "d": 8, "c": 1}


def site_id(fmt, types):
    h = 2166136261
    for b in fmt.encode() + b"\0" + types.encode():
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0xFFFF


def _encode(types, args):
    out = b""
    for c, a in zip(types, args, strict=True):
        if c == "i":
            out += struct.pack("<q", a)
        elif c == "u":
            out += struct.pack("<Q", a)
        elif c == "d":
            out += struct.pack("<d", a)
        elif c == "c":
            out += a.encode() if isinstance(a, str) else bytes([a])
        else:
            s = a.encode()[:16]
            out += bytes([len(s)]) + s
    return out


class Writer:
    def __init__(self):
        self.sites, self.recs = {}, b""

    def log(self, ts, fmt, types, *args):
        i = site_id(fmt, types)
        if self.sites.setdefault(i, (fmt, types)) != (fmt, types):
            raise ValueError(f"two statements hash to {i}: {fmt!r}")
        payload = _encode(types, args)
        self.recs += struct.pack("<HHIQ", i, len(payload), 0, ts) + payload

    def header(self):
        h = MAGIC + struct.pack("<I", len(self.sites))
        for i in sorted(self.sites):
            fmt, types = self.sites[i]
            h += struct.pack("<HB", i, len(types)) + types.encode() + struct.pack("<H", len(fmt)) + fmt.encode()
        return h

    def bytes(self):
        return self.header() + self.recs


def read(data):
    if data[:8] != MAGIC:
        raise ValueError("not a binlog file")
    (n,) = struct.unpack_from("<I", data, 8)
    p, sites = 12, {}
    for _ in range(n):
        i, nt = struct.unpack_from("<HB", data, p)
        types = data[p + 3:p + 3 + nt].decode()
        p += 3 + nt
        (nf,) = struct.unpack_from("<H", data, p)
        sites[i] = (data[p + 2:p + 2 + nf].decode(), types)
        p += 2 + nf
    recs = []
    while p + 16 <= len(data):
        i, n, _, ts = struct.unpack_from("<HHIQ", data, p)
        q, args = p + 16, []
        for c in sites[i][1]:
            if c in "iud":
                args.append(struct.unpack_from({"i": "<q", "u": "<Q", "d": "<d"}[c], data, q)[0])
                q += 8
            elif c == "c":
                args.append(chr(data[q]))
                q += 1
            else:
                k = data[q]
                args.append(data[q + 1:q + 1 + k].decode())
                q += 1 + k
        if q != p + 16 + n:
            raise ValueError(f"record at {p}: payload of {n} bytes, types consume {q - p - 16}")
        recs.append((ts, i, tuple(args)))
        p = q
    return sites, recs


def text(sites, records):
    return [f"{ts} {sites[i][0].format(*args)}" for ts, i, args in records]


def first_difference(a, b):
    for k, (x, y) in enumerate(zip(a, b, strict=False)):   # the shorter length decides below
        if x != y:
            return k
    return None if len(a) == len(b) else min(len(a), len(b))


def journal_write(records):
    return JMAGIC + struct.pack("<I", 56) + b"".join(struct.pack("<Q", t) + ev for t, ev in records)


def journal_read(data):
    if data[:8] != JMAGIC:
        raise ValueError("not a journal")
    (size,) = struct.unpack_from("<I", data, 8)
    return [(struct.unpack_from("<Q", data, p)[0], data[p + 8:p + size]) for p in range(12, len(data) - size + 1, size)]
