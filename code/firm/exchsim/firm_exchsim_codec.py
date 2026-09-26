"""firm.exchsim codec -- every byte of the simulator's protocols, from one table (One Quant Book 10, chapter 26).

Three protocols, big-endian throughout, prices in 1/10,000 currency unit:
  * the market-data feed: ITCH-style messages framed by a u16 length inside MoldUDP64 packets
    (session alpha10 | sequence number of the first message u64 | message count u16);
  * order entry: OUCH-style application messages inside SoupBinTCP 4.0 frames (u16 length | u8 type);
  * the engine journal: the control messages a venue operator sends (phases, auctions, bands, logins), and the
    journal record (t_ns u64 | session u16 | length u16 | message) that every engine replays byte for byte.
The A/E/X/D/P feed messages keep Book 1's firm_feed layouts byte for byte; U, C, Q, I, S, H have ITCH 5.0's
lengths; R, G, W are this simulator's own. `MESSAGES` is the single source: schema.json is generated from it
(`schema()`), and Book 13 generates its client codecs from schema.json.

Messages in Python are namedtuples whose class names are PROTOCOL_TYPE (Feed_A, In_O, Out_E, Ctl_P ...), whose
fields are the table's fields without the leading type byte; single characters are one-character str, alpha
fields str (right-trimmed), integers int.

API (stable):
    MESSAGES                               {protocol: {type: [(field, kind), ...]}}; kinds u8 u16 u32 u64 i64 u48
                                           char alphaN numN (ASCII, SoupBinTCP style)
    NT[protocol][type]                     the namedtuple class
    encode(protocol, msg) -> bytes         msg a namedtuple of that protocol (its class says the type)
    decode(protocol, data) -> namedtuple   one message without framing
    frame(msgs) / unframe(data)            u16-length framing of a list of encoded messages
    mold_packet(session, seq, payloads) -> bytes ; mold_parse(packet) -> (session, seq, count, [payload bytes])
    soup_frame(type, payload) -> bytes ; soup_parse(data) -> [(type, payload)] (whole frames only), rest
    journal_record(t_ns, session, payload) / journal_parse(data) -> [(t_ns, session, payload)]
    file_record(send_ns, packet) / file_parse(data) -> [(send_ns, packet)]     recorded-file format
    crc32(data)                            zlib.crc32, the W message's book checksum
    schema() -> dict                       the machine-readable description written to schema.json
"""
from __future__ import annotations

import struct
import zlib
from collections import namedtuple

_TS = [("locate", "u16"), ("tracking", "u16"), ("ts", "u48")]

MESSAGES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "feed": {
        "A": _TS + [("ref", "u64"), ("side", "char"), ("shares", "u32"), ("stock", "alpha8"), ("price", "u32")],
        "E": _TS + [("ref", "u64"), ("shares", "u32"), ("match", "u64")],
        "X": _TS + [("ref", "u64"), ("shares", "u32")],
        "D": _TS + [("ref", "u64")],
        "P": _TS + [("ref", "u64"), ("side", "char"), ("shares", "u32"), ("stock", "alpha8"), ("price", "u32"),
                    ("match", "u64")],
        "U": _TS + [("ref", "u64"), ("new_ref", "u64"), ("shares", "u32"), ("price", "u32")],
        "C": _TS + [("ref", "u64"), ("shares", "u32"), ("match", "u64"), ("printable", "char"), ("price", "u32")],
        "Q": _TS + [("shares", "u64"), ("stock", "alpha8"), ("price", "u32"), ("match", "u64"),
                    ("cross_type", "char")],
        "I": _TS + [("paired", "u64"), ("imbalance", "u64"), ("direction", "char"), ("stock", "alpha8"),
                    ("far", "u32"), ("near", "u32"), ("ref_price", "u32"), ("cross_type", "char"),
                    ("variation", "char")],
        "S": _TS + [("event", "char")],
        "H": _TS + [("stock", "alpha8"), ("state", "char"), ("reserved", "char"), ("reason", "alpha4")],
        "R": _TS + [("stock", "alpha8"), ("tick", "u32"), ("lot", "u32"), ("matching", "char")],
        "G": _TS + [("seq", "u64"), ("orders", "u32")],
        "W": _TS + [("seq", "u64"), ("crc", "u32")],
    },
    "in": {
        "O": [("cl_ord_id", "u64"), ("locate", "u16"), ("side", "char"), ("qty", "u32"), ("price", "u32"),
              ("tif", "char"), ("display", "char"), ("post_only", "char"), ("display_qty", "u32"),
              ("min_qty", "u32"), ("stp_group", "u16"), ("stp_mode", "char"), ("stop_price", "u32")],
        "U": [("cl_ord_id", "u64"), ("new_cl_ord_id", "u64"), ("qty", "u32"), ("price", "u32")],
        "X": [("cl_ord_id", "u64"), ("leave_qty", "u32")],
        "M": [("locate", "u16"), ("side", "char")],
        "Q": [("quote_id", "u64"), ("locate", "u16"), ("bid_price", "u32"), ("bid_qty", "u32"),
              ("ask_price", "u32"), ("ask_qty", "u32")],
    },
    "out": {
        "S": [("ts", "u64"), ("event", "char")],
        "A": [("ts", "u64"), ("cl_ord_id", "u64"), ("ref", "u64"), ("locate", "u16"), ("side", "char"),
              ("qty", "u32"), ("price", "u32"), ("tif", "char"), ("display", "char"), ("state", "char")],
        "U": [("ts", "u64"), ("cl_ord_id", "u64"), ("new_cl_ord_id", "u64"), ("ref", "u64"), ("qty", "u32"),
              ("price", "u32"), ("priority", "char")],
        "C": [("ts", "u64"), ("cl_ord_id", "u64"), ("decrement", "u32"), ("reason", "char")],
        "E": [("ts", "u64"), ("cl_ord_id", "u64"), ("qty", "u32"), ("price", "u32"), ("match", "u64"),
              ("liquidity", "char"), ("fee", "i64"), ("leaves", "u32")],
        "J": [("ts", "u64"), ("cl_ord_id", "u64"), ("reason", "char")],
    },
    "ctl": {
        "L": [("session", "u16"), ("firm", "u32"), ("cod", "char")],
        "D": [("session", "u16")],
        "P": [("locate", "u16"), ("phase", "char"), ("reason", "alpha4")],
        "X": [("locate", "u16"), ("cross_type", "char")],
        "I": [("locate", "u16"), ("cross_type", "char")],
        "R": [("locate", "u16"), ("ref_price", "u32"), ("band_lo", "u32"), ("band_hi", "u32")],
        "E": [("locate", "u16"), ("tif", "char")],
        "F": [("locate", "u16"), ("freeze", "char")],
        "S": [("event", "char")],
        "N": [("locate", "u16"), ("bid", "u32"), ("ask", "u32")],
    },
    "soup_client": {
        "L": [("username", "alpha6"), ("password", "alpha10"), ("session", "alpha10"), ("seq", "num20")],
        "U": [("payload", "rest")],
        "R": [],
        "O": [],
    },
    "soup_server": {
        "A": [("session", "alpha10"), ("seq", "num20")],
        "J": [("reason", "char")],
        "S": [("payload", "rest")],
        "H": [],
        "Z": [],
        "+": [("text", "rest")],
    },
}

ENUMS = {
    "feed.side": {"B": "buy", "S": "sell"},
    "feed.printable": {"Y": "printable", "N": "not printable (cross executions)"},
    "feed.cross_type": {"O": "opening", "C": "closing", "H": "halt or pause reopening", "B": "batch"},
    "feed.direction": {"B": "buy imbalance", "S": "sell imbalance", "N": "no imbalance", "O": "no cross possible"},
    "feed.event": {"O": "start of messages", "S": "start of system hours", "Q": "start of market hours",
                   "M": "end of market hours", "E": "end of system hours", "C": "end of messages"},
    "feed.state": {"T": "trading", "H": "halted", "P": "paused (reopening call)", "Q": "quotation only (call)",
                   "C": "closed"},
    "feed.matching": {"F": "price-time (FIFO)", "P": "pro rata", "C": "configurable (top, FIFO share, pro rata)"},
    "in.side": {"B": "buy", "S": "sell"},
    "in.tif": {"D": "day", "I": "immediate or cancel", "F": "fill or kill", "G": "good till cancelled",
               "O": "at the open (opening auction only)", "C": "at the close (closing auction only)"},
    "in.display": {"Y": "visible", "N": "hidden", "M": "midpoint peg (hidden)", "P": "primary peg (visible)"},
    "in.post_only": {"Y": "reject if it would take liquidity", "N": "no"},
    "in.stp_mode": {"N": "none", "O": "cancel oldest (resting)", "W": "cancel newest (incoming)",
                    "B": "cancel both", "D": "decrement both"},
    "in.M.side": {"B": "bids", "S": "offers", "*": "both"},
    "out.state": {"L": "live", "S": "stop order waiting for its trigger"},
    "out.priority": {"Y": "kept (size decrease at the same price)", "N": "lost (new reference)"},
    "out.reason.C": {"U": "user", "I": "IOC/FOK remainder or market remainder", "S": "self-trade prevention",
                     "D": "disconnect (cancel on disconnect)", "H": "halt", "M": "mass cancel", "E": "expired"},
    "out.reason.J": {"T": "throttle", "X": "price not on the tick grid", "Q": "bad quantity", "H": "halted or closed",
                     "S": "unknown instrument", "D": "duplicate cl_ord_id", "O": "post-only would cross",
                     "B": "outside the price band", "L": "too late to cancel or unknown order",
                     "C": "after the closing-order cut-off"},
    "out.liquidity": {"A": "added (maker)", "R": "removed (taker)", "C": "auction cross"},
    "ctl.phase": {"C": "closed", "O": "opening call", "T": "continuous trading", "K": "closing call",
                  "H": "halted", "U": "paused (reopening call)", "B": "batch call (frequent batch auction)"},
    "ctl.E.tif": {"D": "expire day, at-open and at-close orders", "A": "expire everything"},
    "soup_server.reason": {"A": "not authorized", "S": "session not available"},
}

_WIDTH = {"u8": 1, "char": 1, "u16": 2, "u32": 4, "u64": 8, "i64": 8, "u48": 6}
_FMT = {"u8": "B", "char": "c", "u16": "H", "u32": "I", "u64": "Q", "i64": "q", "u48": "HI"}


def _width(kind: str) -> int:
    if kind in _WIDTH:
        return _WIDTH[kind]
    if kind.startswith("alpha"):
        return int(kind[5:])
    if kind.startswith("num"):
        return int(kind[3:])
    raise ValueError(kind)


def _cls(proto: str, t: str):
    name = f"{proto.capitalize()}_{'plus' if t == '+' else t}"
    return namedtuple(name, [f for f, _ in MESSAGES[proto][t]])


NT = {p: {t: _cls(p, t) for t in m} for p, m in MESSAGES.items()}
_TYPE_OF = {NT[p][t]: t for p in NT for t in NT[p]}


class _Layout:
    def __init__(self, t: str, fields):
        self.t = t
        self.rest = bool(fields) and fields[-1][1] == "rest"
        fixed = fields[:-1] if self.rest else fields
        self.kinds = [k for _, k in fixed]
        fmt = ">c" + "".join(_FMT[k] if k in _FMT else f"{_width(k)}s" for k in self.kinds)
        self.st = struct.Struct(fmt)
        self.size = self.st.size

    def pack(self, msg) -> bytes:
        vals = [self.t.encode()]
        for k, v in zip(self.kinds, msg, strict=False):
            if k == "char":
                vals.append(v.encode())
            elif k == "u48":
                vals += [v >> 32, v & 0xFFFFFFFF]
            elif k.startswith("alpha"):
                vals.append(v.encode().ljust(_width(k))[:_width(k)])
            elif k.startswith("num"):
                vals.append(str(v).rjust(_width(k)).encode())
            else:
                vals.append(v)
        out = self.st.pack(*vals)
        return out + msg[-1] if self.rest else out

    def unpack(self, data: bytes):
        raw = self.st.unpack_from(data)
        vals, i = [], 1
        for k in self.kinds:
            v = raw[i]
            if k == "char":
                vals.append(v.decode())
            elif k == "u48":
                vals.append((v << 32) | raw[i + 1])
                i += 1
            elif k.startswith("alpha"):
                vals.append(v.decode().rstrip())
            elif k.startswith("num"):
                vals.append(int(v.decode().strip() or 0))
            else:
                vals.append(v)
            i += 1
        if self.rest:
            vals.append(bytes(data[self.size:]))
        elif len(data) != self.size:
            raise ValueError(f"message {self.t!r}: {len(data)} bytes, expected {self.size}")
        return vals


_LAYOUT = {p: {t: _Layout(t, f) for t, f in m.items()} for p, m in MESSAGES.items()}
LENGTH = {p: {t: lay.size for t, lay in m.items() if not lay.rest} for p, m in _LAYOUT.items()}


def encode(proto: str, msg) -> bytes:
    return _LAYOUT[proto][_TYPE_OF[type(msg)]].pack(msg)


def decode(proto: str, data: bytes):
    t = chr(data[0])
    lay = _LAYOUT[proto].get(t)
    if lay is None:
        raise ValueError(f"unknown {proto} message type {t!r}")
    return NT[proto][t](*lay.unpack(data))


def frame(payloads) -> bytes:
    return b"".join(struct.pack(">H", len(p)) + p for p in payloads)


def unframe(data: bytes) -> list[bytes]:
    out, i = [], 0
    while i < len(data):
        (n,) = struct.unpack_from(">H", data, i)
        if i + 2 + n > len(data):
            raise ValueError("truncated frame")
        out.append(bytes(data[i + 2:i + 2 + n]))
        i += 2 + n
    return out


MOLD_HEADER = struct.Struct(">10sQH")
HEARTBEAT, END_OF_SESSION = 0, 0xFFFF


def mold_packet(session: str, seq: int, payloads) -> bytes:
    return MOLD_HEADER.pack(session.encode().ljust(10)[:10], seq, len(payloads)) + frame(payloads)


def mold_end(session: str, seq: int) -> bytes:
    return MOLD_HEADER.pack(session.encode().ljust(10)[:10], seq, END_OF_SESSION)


def mold_parse(packet: bytes):
    s, seq, count = MOLD_HEADER.unpack_from(packet)
    msgs = [] if count in (HEARTBEAT, END_OF_SESSION) else unframe(packet[MOLD_HEADER.size:])
    if count not in (HEARTBEAT, END_OF_SESSION) and len(msgs) != count:
        raise ValueError(f"packet announces {count} messages, carries {len(msgs)}")
    return s.decode().rstrip(), seq, count, msgs


def soup_frame(t: str, payload: bytes = b"") -> bytes:
    return struct.pack(">Hc", len(payload) + 1, t.encode()) + payload


def soup_parse(data: bytes):
    """Split a byte stream into whole SoupBinTCP frames; return ([(type, payload)], unconsumed bytes)."""
    out, i = [], 0
    while i + 2 <= len(data):
        (n,) = struct.unpack_from(">H", data, i)
        if i + 2 + n > len(data):
            break
        out.append((chr(data[i + 2]), bytes(data[i + 3:i + 2 + n])))
        i += 2 + n
    return out, bytes(data[i:])


def soup_encode(side: str, msg) -> bytes:
    """A whole SoupBinTCP frame for a soup_client / soup_server namedtuple."""
    body = encode(side, msg)
    return struct.pack(">H", len(body)) + body


JOURNAL = struct.Struct(">QHH")


def journal_record(t_ns: int, session: int, payload: bytes) -> bytes:
    return JOURNAL.pack(t_ns, session, len(payload)) + payload


def journal_parse(data: bytes):
    out, i = [], 0
    while i < len(data):
        t, s, n = JOURNAL.unpack_from(data, i)
        out.append((t, s, bytes(data[i + JOURNAL.size:i + JOURNAL.size + n])))
        i += JOURNAL.size + n
    return out


FILE = struct.Struct(">QI")


def file_record(send_ns: int, packet: bytes) -> bytes:
    return FILE.pack(send_ns, len(packet)) + packet


def file_parse(data: bytes):
    out, i = [], 0
    while i < len(data):
        t, n = FILE.unpack_from(data, i)
        out.append((t, bytes(data[i + FILE.size:i + FILE.size + n])))
        i += FILE.size + n
    return out


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def schema() -> dict:
    """Every message of every protocol with its fields' types, widths and offsets (the type byte at offset 0)."""
    out = {"version": 1, "byte_order": "big-endian",
           "price_unit": "1/10,000 currency unit", "time_unit": "nanoseconds since midnight",
           "framing": {"feed": "MoldUDP64 packet: session alpha10 | seq u64 | count u16 | (u16 length | message)*;"
                               " count 0 = heartbeat, 0xFFFF = end of session",
                       "in/out": "inside SoupBinTCP 4.0 frames (u16 length | u8 type): U unsequenced (client), S"
                                 " sequenced (server)",
                       "ctl": "engine journal record: t_ns u64 | session u16 | length u16 | message; session 0"
                              " carries control messages",
                       "recorded_file": "records of send_ns u64 | length u32 | MoldUDP64 packet"},
           "protocols": {}, "enums": ENUMS}
    for p, m in MESSAGES.items():
        msgs = {}
        for t, fields in m.items():
            off, fl = 1, [{"name": "type", "type": "char", "offset": 0, "length": 1, "value": t}]
            for f, k in fields:
                if k == "rest":
                    fl.append({"name": f, "type": "bytes", "offset": off, "length": None})
                    continue
                w = _width(k)
                fl.append({"name": f, "type": k, "offset": off, "length": w})
                off += w
            msgs[t] = {"length": None if fields and fields[-1][1] == "rest" else off, "fields": fl}
        out["protocols"][p] = msgs
    return out
