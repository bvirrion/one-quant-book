"""Feed normaliser (build of Book 1, Chapter 28): an order-by-order binary feed into a book and a tape.

The wire format is a teaching subset in the style of Nasdaq TotalView-ITCH 5.0: big-endian
integers, prices with four implied decimals, 48-bit nanosecond timestamps since midnight, and
the same field order for the five message types used here. Each message is framed by a 2-byte
big-endian length. It is NOT the production protocol: no stock directory, no MPID, no crosses.

  A  add order       type, locate(2), tracking(2), ts(6), ref(8), side(1), shares(4), stock(8), price(4)  = 36
  E  order executed  type, locate, tracking, ts, ref(8), shares(4), match(8)                              = 31
  X  order cancel    type, locate, tracking, ts, ref(8), shares(4)                                        = 23
  D  order delete    type, locate, tracking, ts, ref(8)                                                   = 19
  P  trade (hidden)  type, locate, tracking, ts, ref(8), side(1), shares(4), stock(8), price(4), match(8) = 44
"""
import struct
from dataclasses import dataclass, field

LENGTHS = {b"A": 36, b"E": 31, b"X": 23, b"D": 19, b"P": 44}


@dataclass(frozen=True)
class Msg:
    kind: str
    locate: int
    tracking: int
    ts: int                          # nanoseconds since midnight
    ref: int
    side: str = ""
    shares: int = 0
    stock: str = ""
    price: int = 0                   # in 1/10,000 of a dollar
    match: int = 0


def _ts(ns: int) -> bytes:
    return ns.to_bytes(6, "big")


def encode(m: Msg) -> bytes:
    head = m.kind.encode() + struct.pack(">HH", m.locate, m.tracking) + _ts(m.ts) + struct.pack(">Q", m.ref)
    if m.kind == "A":
        stock = f"{m.stock:<8}".encode()
        body = head + m.side.encode() + struct.pack(">I", m.shares) + stock + struct.pack(">I", m.price)
    elif m.kind == "E":
        body = head + struct.pack(">IQ", m.shares, m.match)
    elif m.kind == "X":
        body = head + struct.pack(">I", m.shares)
    elif m.kind == "D":
        body = head
    elif m.kind == "P":
        body = (head + m.side.encode() + struct.pack(">I", m.shares) + f"{m.stock:<8}".encode()
                + struct.pack(">IQ", m.price, m.match))
    else:
        raise ValueError(f"unknown message type {m.kind!r}")
    assert len(body) == LENGTHS[m.kind.encode()]
    return struct.pack(">H", len(body)) + body


def decode(buf: bytes):
    """Yield messages from a framed buffer. Raises on a truncated frame or a length that does not
    match the message type: a decoder that guesses is worse than one that stops."""
    i = 0
    while i < len(buf):
        if i + 2 > len(buf):
            raise ValueError("truncated length prefix")
        (n,) = struct.unpack_from(">H", buf, i)
        body = buf[i + 2:i + 2 + n]
        if len(body) != n:
            raise ValueError("truncated message")
        kind = body[:1]
        if LENGTHS.get(kind) != n:
            raise ValueError(f"type {kind!r} with length {n}")
        locate, tracking = struct.unpack_from(">HH", body, 1)
        ts = int.from_bytes(body[5:11], "big")
        (ref,) = struct.unpack_from(">Q", body, 11)
        k = kind.decode()
        if k == "A":
            side = chr(body[19])
            (shares,) = struct.unpack_from(">I", body, 20)
            stock = body[24:32].decode().rstrip()
            (price,) = struct.unpack_from(">I", body, 32)
            yield Msg(k, locate, tracking, ts, ref, side, shares, stock, price)
        elif k == "E":
            shares, match = struct.unpack_from(">IQ", body, 19)
            yield Msg(k, locate, tracking, ts, ref, shares=shares, match=match)
        elif k == "X":
            (shares,) = struct.unpack_from(">I", body, 19)
            yield Msg(k, locate, tracking, ts, ref, shares=shares)
        elif k == "D":
            yield Msg(k, locate, tracking, ts, ref)
        else:
            side = chr(body[19])
            (shares,) = struct.unpack_from(">I", body, 20)
            stock = body[24:32].decode().rstrip()
            price, match = struct.unpack_from(">IQ", body, 32)
            yield Msg(k, locate, tracking, ts, ref, side, shares, stock, price, match)
        i += 2 + n


@dataclass
class Order:
    side: str
    shares: int
    price: int
    locate: int


@dataclass(frozen=True)
class Trade:
    ts: int
    locate: int
    price: int
    shares: int
    match: int
    aggressor: str                   # 'B' or 'S': the side that took liquidity; '' if unknown (hidden)


@dataclass
class Book:
    """All instruments of one feed. Level 3 in, levels 2 and 1 and a tape out."""
    orders: dict[int, Order] = field(default_factory=dict)
    levels: dict[tuple[int, str], dict[int, int]] = field(default_factory=dict)   # (locate, side) -> price -> shares
    trades: list[Trade] = field(default_factory=list)
    last_ts: int = 0
    errors: list[str] = field(default_factory=list)

    def _level(self, locate: int, side: str) -> dict[int, int]:
        return self.levels.setdefault((locate, side), {})

    def _reduce(self, ref: int, shares: int) -> Order | None:
        o = self.orders.get(ref)
        if o is None:
            self.errors.append(f"unknown order {ref}")
            return None
        if shares > o.shares:
            self.errors.append(f"order {ref}: {shares} > {o.shares} resting")
            shares = o.shares
        lv = self._level(o.locate, o.side)
        lv[o.price] -= shares
        if lv[o.price] == 0:
            del lv[o.price]
        o.shares -= shares
        if o.shares == 0:
            del self.orders[ref]
        return o

    def apply(self, m: Msg) -> None:
        if m.ts < self.last_ts:
            self.errors.append(f"timestamp went backwards at ref {m.ref}")
        self.last_ts = max(self.last_ts, m.ts)
        if m.kind == "A":
            if m.ref in self.orders:
                self.errors.append(f"duplicate order {m.ref}")
                return
            self.orders[m.ref] = Order(m.side, m.shares, m.price, m.locate)
            lv = self._level(m.locate, m.side)
            lv[m.price] = lv.get(m.price, 0) + m.shares
        elif m.kind == "E":
            before = self.orders.get(m.ref)
            price, side = (before.price, before.side) if before else (0, "")
            if self._reduce(m.ref, m.shares) is not None:
                self.trades.append(Trade(m.ts, m.locate, price, m.shares, m.match, "S" if side == "B" else "B"))
        elif m.kind == "X":
            self._reduce(m.ref, m.shares)
        elif m.kind == "D":
            o = self.orders.get(m.ref)
            self._reduce(m.ref, o.shares if o else 0)
        elif m.kind == "P":
            self.trades.append(Trade(m.ts, m.locate, m.price, m.shares, m.match, ""))

    def best(self, locate: int) -> tuple[int | None, int, int | None, int]:
        bids, asks = self.levels.get((locate, "B"), {}), self.levels.get((locate, "S"), {})
        bb = max(bids) if bids else None
        ba = min(asks) if asks else None
        return bb, bids.get(bb, 0) if bb is not None else 0, ba, asks.get(ba, 0) if ba is not None else 0

    def depth(self, locate: int, side: str, n: int) -> list[tuple[int, int]]:
        lv = self.levels.get((locate, side), {})
        prices = sorted(lv, reverse=(side == "B"))[:n]
        return [(p, lv[p]) for p in prices]


def summary(book: Book, locate: int) -> tuple[int | None, int, int | None, int, int, int, int]:
    """What the C++ and Rust decoders must reproduce: best bid and size, best ask and size,
    number of trades, shares traded, number of live orders."""
    bb, bq, ba, aq = book.best(locate)
    trades = [t for t in book.trades if t.locate == locate]
    live = sum(1 for o in book.orders.values() if o.locate == locate)
    return bb, bq, ba, aq, len(trades), sum(t.shares for t in trades), live
