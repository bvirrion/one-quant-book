"""firm.wsclient -- WebSocket frames, depth-update decoding, request signing and a connection pool, Python reference
(build of One Quant Book 13, chapter 17). The C++20 twin (`cpp/firm_wsclient.hpp`) decodes the same fixtures to the same
values; the Rust twin (`rust/`) carries the frame codec and the signer.

API (stable):
    encode_frame(payload, opcode=OP_TEXT, fin=True, mask_key=None) -> bytes     RFC 6455, section 5.2
    decode_frame(buf) -> (Frame, used) | (None, 0)                              one frame, unmasked; None if incomplete
    Reassembler().feed(frame) -> list[Message]      data frames joined across fragments, control frames passed through
    DepthUpdate(event_time, symbol, first, last, bids, asks)    prices and quantities as integers of 10**-8
    decode_depth(text) -> DepthUpdate                a depth update in the documented venue shape (e, E, s, U, u, b, a)
    to_book_levels(levels, tick, lot) -> [(ticks, lots)]         for Book 3's firm.wsbook
    Signer(secret).sign(payload) -> hex              HMAC-SHA-256 with the key's pads hashed once (RFC 2104)
    Pool(size, governor)                             persistent connections gated by Book 3's firm.ratelimit
"""
import hashlib
import hmac
import json
import pathlib
import struct
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "ratelimit"))

OP_CONT, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA
SCALE = 10 ** 8                       # prices and quantities as integers of 1e-8


class FrameError(ValueError):
    pass


@dataclass
class Frame:
    fin: bool
    opcode: int
    payload: bytes
    masked: bool = False


def mask(payload, key):
    return bytes(b ^ key[i % 4] for i, b in enumerate(payload))


def encode_frame(payload, opcode=OP_TEXT, fin=True, mask_key=None):
    n = len(payload)
    if opcode >= 0x8 and (n > 125 or not fin):
        raise FrameError("control frames carry at most 125 bytes and are never fragmented")
    head = bytes([(0x80 if fin else 0) | opcode])
    m = 0x80 if mask_key is not None else 0
    if n <= 125:
        head += bytes([m | n])
    elif n <= 0xFFFF:
        head += bytes([m | 126]) + struct.pack(">H", n)
    else:
        head += bytes([m | 127]) + struct.pack(">Q", n)
    if mask_key is None:
        return head + payload
    return head + mask_key + mask(payload, mask_key)


def decode_frame(buf):
    if len(buf) < 2:
        return None, 0
    b0, b1 = buf[0], buf[1]
    if b0 & 0x70:
        raise FrameError("reserved bits set without a negotiated extension")
    fin, opcode, masked, n, i = bool(b0 & 0x80), b0 & 0x0F, bool(b1 & 0x80), b1 & 0x7F, 2
    if n == 126:
        if len(buf) < 4:
            return None, 0
        n, i = struct.unpack_from(">H", buf, 2)[0], 4
        if n < 126:
            raise FrameError("length not minimally encoded")
    elif n == 127:
        if len(buf) < 10:
            return None, 0
        n, i = struct.unpack_from(">Q", buf, 2)[0], 10
        if n <= 0xFFFF or n >> 63:
            raise FrameError("length not minimally encoded")
    if opcode >= 0x8 and (n > 125 or not fin):
        raise FrameError("bad control frame")
    key = b""
    if masked:
        if len(buf) < i + 4:
            return None, 0
        key, i = bytes(buf[i:i + 4]), i + 4
    if len(buf) < i + n:
        return None, 0
    payload = bytes(buf[i:i + n])
    return Frame(fin, opcode, mask(payload, key) if masked else payload, masked), i + n


@dataclass
class Message:
    opcode: int
    payload: bytes


@dataclass
class Reassembler:
    """Joins a fragmented data message (a first frame with its opcode, continuation frames, the last with FIN);
    control frames may arrive between fragments and are delivered at once."""
    opcode: int = -1
    parts: list = field(default_factory=list)

    def feed(self, f):
        if f.opcode >= 0x8:
            return [Message(f.opcode, f.payload)]
        if f.opcode == OP_CONT:
            if self.opcode < 0:
                raise FrameError("continuation without a first fragment")
        else:
            if self.opcode >= 0:
                raise FrameError("new data message inside a fragmented one")
            self.opcode = f.opcode
        self.parts.append(f.payload)
        if not f.fin:
            return []
        m = Message(self.opcode, b"".join(self.parts))
        self.opcode, self.parts = -1, []
        return [m]


# -- depth updates -------------------------------------------------------------------------------------------------

@dataclass
class DepthUpdate:
    event_time: int
    symbol: str
    first: int
    last: int
    bids: list          # [(price, qty)] in units of 1e-8
    asks: list


def fixed(s, scale=SCALE):
    """'0.0024' -> 240000 at 1e-8, exactly (no float)."""
    whole, _, frac = s.partition(".")
    digits = len(str(scale)) - 1
    if len(frac) > digits:
        raise ValueError(f"{s!r} has more than {digits} decimals")
    return int(whole or "0") * scale + int((frac + "0" * digits)[:digits])


def decode_depth(text):
    d = json.loads(text)
    lv = [[(fixed(p), fixed(q)) for p, q in d[k]] for k in ("b", "a")]
    return DepthUpdate(d["E"], d["s"], d["U"], d["u"], lv[0], lv[1])


def to_book_levels(levels, tick, lot):
    """(price, qty) at 1e-8 -> (ticks, lots) for firm.wsbook, given the instrument's tick and lot at 1e-8."""
    return [(p // tick, q // lot) for p, q in levels]


# -- signing -------------------------------------------------------------------------------------------------------

class Signer:
    """HMAC-SHA-256 over a request's payload. The keyed object is built once: hashing K xor ipad and K xor opad is
    done at construction, and each signature copies that state (RFC 2104's precomputation)."""

    def __init__(self, secret):
        self._base = hmac.new(secret.encode() if isinstance(secret, str) else secret, digestmod=hashlib.sha256)

    def sign(self, payload):
        h = self._base.copy()
        h.update(payload.encode() if isinstance(payload, str) else payload)
        return h.hexdigest()


# -- connections ---------------------------------------------------------------------------------------------------

@dataclass
class Pool:
    """Persistent connections to one venue: a request uses an open, idle connection when there is one and opens a
    new one (paying the TCP and TLS handshakes) otherwise; every request passes Book 3's rate-limit governor first."""
    size: int
    governor: object
    open: int = 0
    busy: int = 0
    handshakes: int = 0
    refused: int = 0

    def request(self, now, weight=1, is_order=False):
        """Returns 'reused', 'opened', 'full' (every connection busy: nothing is spent) or 'throttled'."""
        if self.busy >= self.size:
            return "full"
        ok, _ = self.governor.try_send(now, weight, is_order)
        if not ok:
            self.refused += 1
            return "throttled"
        self.busy += 1
        if self.busy <= self.open:
            return "reused"
        self.open += 1
        self.handshakes += 1
        return "opened"

    def done(self):
        self.busy -= 1
