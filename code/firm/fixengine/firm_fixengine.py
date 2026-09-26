"""firm.fixengine -- FIX tag=value codec and session layer, Python reference (build of One Quant Book 13, chapter 15).

The C++20 engine (`cpp/firm_fixengine.hpp`) reproduces this module's session trace byte for byte on the golden
conversation in `data/`; the Rust crate (`rust/`) carries the codec. Times are integer milliseconds from the start of
a session day, printed in SendingTime (52) as UTC on a fixed date, so that every byte is reproducible.

API (stable):
    checksum(data) -> int                      sum of bytes modulo 256
    encode(msg_type, body, seq, sender, target, now_ms, begin="FIX.4.4", header=()) -> bytes
    decode(buf) -> Message                     validates begin string, body length, field order and checksum
    frame(buf) -> int                          length of the first complete message in buf, 0 if incomplete
    Message.get(tag), .msg_type, .seq, .fields [(tag, bytes)]
    Session(sender, target, heartbeat_s=30): logon(now), send(msg_type, body, now), on_bytes(data, now),
        on_timer(now), logout(now, text), disconnect(); .trace (list of str), .next_out, .next_in, .state
    ADMIN                                      administrative message types (gap-filled, never resent)
"""
from dataclasses import dataclass, field

SOH = b"\x01"
ADMIN = frozenset({b"0", b"1", b"2", b"3", b"4", b"5", b"A"})
DATE = "20260925"


class FixError(ValueError):
    def __init__(self, kind, detail=""):
        super().__init__(f"{kind}: {detail}" if detail else kind)
        self.kind = kind


def _b(v):
    return v if isinstance(v, bytes) else str(v).encode()


def checksum(data):
    return sum(data) % 256


def sending_time(now_ms):
    s, ms = divmod(int(now_ms), 1000)
    h, rem = divmod(s, 3600)
    return f"{DATE}-{h:02d}:{rem // 60:02d}:{rem % 60:02d}.{ms:03d}".encode()


def encode(msg_type, body, seq, sender, target, now_ms, begin="FIX.4.4", header=()):
    """A complete message: 8, 9, 35, 49, 56, 34, 52, extra header fields, the body, 10."""
    fields = [(35, msg_type), (49, sender), (56, target), (34, seq), (52, sending_time(now_ms)), *header, *body]
    b = b"".join(_b(t) + b"=" + _b(v) + SOH for t, v in fields)
    m = b"8=" + _b(begin) + SOH + b"9=" + _b(len(b)) + SOH + b
    return m + b"10=%03d" % checksum(m) + SOH


@dataclass
class Message:
    raw: bytes
    fields: list

    def get(self, tag, default=None):
        for t, v in self.fields:
            if t == tag:
                return v
        return default

    @property
    def msg_type(self):
        return self.get(35)

    @property
    def seq(self):
        return int(self.get(34, b"0"))


def decode(buf):
    buf = bytes(buf)
    if not buf.startswith(b"8=") or not buf.endswith(SOH):
        raise FixError("framing", "must start with 8= and end with SOH")
    parts = buf[:-1].split(SOH)
    fields = []
    for p in parts:
        tag, eq, val = p.partition(b"=")
        if not eq or not tag.isdigit():
            raise FixError("tag", repr(p[:20]))
        fields.append((int(tag), val))
    if len(fields) < 4 or [t for t, _ in fields[:3]] != [8, 9, 35] or fields[-1][0] != 10:
        raise FixError("order", "8, 9, 35 first and 10 last")
    if any(t in (8, 9, 10) for t, _ in fields[3:-1]):      # found by chapter 25's fuzzer: a CheckSum inside the body
        raise FixError("order", "8, 9 and 10 only in their places")
    start = len(parts[0]) + len(parts[1]) + 2          # first byte after "9=...<SOH>"
    end = len(buf) - len(parts[-1]) - 1                # first byte of "10="
    if int(fields[1][1]) != end - start:
        raise FixError("body_length", f"declared {int(fields[1][1])}, counted {end - start}")
    ck = fields[-1][1]
    if len(ck) != 3 or not ck.isdigit() or int(ck) != checksum(buf[:end]):
        raise FixError("checksum", f"declared {ck!r}, computed {checksum(buf[:end]):03d}")
    return Message(buf, fields)


def frame(buf):
    """Length of the first complete message at the start of buf (0 if more bytes are needed)."""
    if len(buf) < 2:
        return 0
    if not buf.startswith(b"8="):
        raise FixError("framing", "stream does not start with 8=")
    a = buf.find(SOH)
    if a < 0 or len(buf) < a + 3:
        return 0
    if buf[a + 1:a + 3] != b"9=":
        raise FixError("framing", "9= must follow 8=")
    b = buf.find(SOH, a + 1)
    if b < 0:
        return 0
    total = b + 1 + int(buf[a + 3:b]) + 7        # body, then "10=nnn<SOH>"
    return total if len(buf) >= total else 0


@dataclass
class Session:
    """The session layer of one FIX connection: sequence numbers, heartbeats, resend and gap fill, logon/logout.

    Every outgoing message is returned as bytes and recorded in `trace` with the time; application messages received
    in sequence are returned to the caller ("delivered") and traced."""
    sender: str
    target: str
    heartbeat_s: int = 30
    begin: str = "FIX.4.4"
    state: str = "disconnected"
    next_out: int = 1
    next_in: int = 1
    store: dict = field(default_factory=dict)        # seq -> (msg_type, body, now_ms) of our messages
    queue: dict = field(default_factory=dict)        # seq -> Message received ahead of a gap
    trace: list = field(default_factory=list)
    last_sent: int = 0
    last_recv: int = 0
    test_id: str = ""
    test_sent: int = 0
    tests: int = 0
    resend_asked: bool = False

    # -- sending ---------------------------------------------------------------------------------------------------
    def _emit(self, msg_type, body, now, seq=None, header=()):
        new = seq is None
        seq = self.next_out if new else seq
        raw = encode(msg_type, body, seq, self.sender, self.target, now, self.begin, header)
        if new:
            self.store[seq] = (_b(msg_type), list(body), now)
            self.next_out += 1
        self.last_sent = now
        self.trace.append(f"{now} out {raw.replace(SOH, b'|').decode()}")
        return raw

    def logon(self, now):
        self.state = "logon_sent"
        self.last_recv = now
        return [self._emit(b"A", [(98, 0), (108, self.heartbeat_s)], now)]

    def send(self, msg_type, body, now):
        if self.state != "active":
            raise FixError("state", f"cannot send application messages while {self.state}")
        return [self._emit(msg_type, body, now)]

    def logout(self, now, text=""):
        self.state = "logout_sent"
        return [self._emit(b"5", [(58, text)] if text else [], now)]

    def disconnect(self, now, why):
        self.state = "disconnected"
        self.trace.append(f"{now} state disconnected ({why})")

    # -- receiving -------------------------------------------------------------------------------------------------
    def on_bytes(self, data, now):
        """Process one complete message; returns (outgoing messages, delivered application messages)."""
        m = decode(data)
        self.last_recv = now
        out, delivered = [], []
        t = m.msg_type
        if t == b"4" and m.get(123, b"N") != b"Y":           # sequence reset, reset mode: ignores the sequence
            self.next_in = int(m.get(36))
            self.trace.append(f"{now} reset next_in={self.next_in}")
            return out, delivered
        if m.seq > self.next_in:
            if t == b"2":                                     # a resend request is answered even during a gap
                out += self._resend(m, now)
            self.queue[m.seq] = m
            if not self.resend_asked:
                self.resend_asked = True
                self.trace.append(f"{now} gap expected={self.next_in} received={m.seq}")
                out.append(self._emit(b"2", [(7, self.next_in), (16, 0)], now))
            return out, delivered
        if m.seq < self.next_in:
            if m.get(43) == b"Y":
                self.trace.append(f"{now} duplicate {m.seq} ignored")
                return out, delivered
            self.trace.append(f"{now} seq {m.seq} too low, expected {self.next_in}")
            out += self.logout(now, f"MsgSeqNum too low, expecting {self.next_in} but received {m.seq}")
            self.disconnect(now, "sequence too low")
            return out, delivered
        self._process(m, now, out, delivered)
        while self.next_in in self.queue:
            q = self.queue.pop(self.next_in)
            if q.msg_type == b"2":
                self.next_in += 1                              # already answered when it arrived
            else:
                self._process(q, now, out, delivered)
        if self.resend_asked and not self.queue:
            self.resend_asked = False
            self.trace.append(f"{now} gap closed next_in={self.next_in}")
        return out, delivered

    def _process(self, m, now, out, delivered):
        t = m.msg_type
        if t == b"4":                                          # gap fill
            self.next_in = int(m.get(36))
            self.trace.append(f"{now} gap fill to {self.next_in}")
            return
        self.next_in += 1
        if t == b"A":
            if self.state == "logon_sent":
                self.state = "active"
                self.trace.append(f"{now} state active")
        elif t == b"0":
            if self.test_id and m.get(112) == self.test_id.encode():
                self.test_id = ""
        elif t == b"1":
            out.append(self._emit(b"0", [(112, m.get(112))], now))
        elif t == b"2":
            out += self._resend(m, now)
        elif t == b"5":
            if self.state != "logout_sent":
                out.append(self._emit(b"5", [], now))
            self.disconnect(now, "logout")
        elif t not in ADMIN:
            delivered.append(m)
            self.trace.append(f"{now} deliver {m.seq} {t.decode()}")

    def _resend(self, m, now):
        """Answer a resend request: application messages again with PossDupFlag and OrigSendingTime; runs of
        administrative messages replaced by one SequenceReset-GapFill each."""
        lo = int(m.get(7))
        hi = int(m.get(16))
        hi = self.next_out - 1 if hi == 0 or hi >= self.next_out else hi
        out, gap_start = [], None
        for seq in range(lo, hi + 1):
            typ, body, sent = self.store.get(seq, (b"0", [], now))
            if typ in ADMIN:
                gap_start = seq if gap_start is None else gap_start
                continue
            if gap_start is not None:
                out.append(self._emit(b"4", [(123, "Y"), (36, seq)], now, seq=gap_start, header=[(43, "Y")]))
                gap_start = None
            out.append(self._emit(typ, body, now, seq=seq, header=[(43, "Y"), (122, sending_time(sent))]))
        if gap_start is not None:
            out.append(self._emit(b"4", [(123, "Y"), (36, hi + 1)], now, seq=gap_start, header=[(43, "Y")]))
        return out

    # -- time ------------------------------------------------------------------------------------------------------
    def on_timer(self, now):
        out = []
        if self.state not in ("active", "logout_sent"):
            return out
        hb = self.heartbeat_s * 1000
        if self.test_id and now - self.test_sent >= hb:
            self.disconnect(now, "no answer to test request")
            return out
        if not self.test_id and now - self.last_recv >= hb + hb // 5:
            self.tests += 1
            self.test_id = f"TEST{self.tests}"
            self.test_sent = now
            out.append(self._emit(b"1", [(112, self.test_id)], now))
        elif now - self.last_sent >= hb:
            out.append(self._emit(b"0", [], now))
        return out


def parse_body(text):
    """'11=ORD1|55=ESZ6' -> [(11, b'ORD1'), (55, b'ESZ6')]"""
    out = []
    for kv in text.split("|"):
        if kv:
            k, _, v = kv.partition("=")
            out.append((int(k), v.encode()))
    return out


def replay(events, sender="FIRM", target="BROKER", heartbeat_s=30):
    """Run a scripted conversation: lines '<ms> logon', '<ms> send <type> <body>', '<ms> in <raw with |>',
    '<ms> timer', '<ms> logout'. Returns the session (its trace is the golden output)."""
    s = Session(sender, target, heartbeat_s)
    for line in events:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        now, verb, *rest = line.split(" ", 2)
        now = int(now)
        if verb == "logon":
            s.logon(now)
        elif verb == "send":
            typ, body = rest[0].split(" ", 1)
            s.send(typ.encode(), parse_body(body), now)
        elif verb == "in":
            s.trace.append(f"{now} in {rest[0]}")
            s.on_bytes(rest[0].encode().replace(b"|", SOH), now)
        elif verb == "timer":
            s.on_timer(now)
        elif verb == "logout":
            s.logout(now)
    return s
