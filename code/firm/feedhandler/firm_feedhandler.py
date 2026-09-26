"""firm.feedhandler -- the market-data feed handler, Python reference (build of One Quant Book 13, chapter 18).

Reads the simulator's two redundant MoldUDP64 lines (Book 10's firm.exchsim, PROTOCOL.md), arbitrates them by sequence
number, detects gaps, waits a short time for the other line, then asks a retransmission server, and falls back to the
snapshot channel when the server cannot help; normalises every message into the firm's event record and publishes it;
keeps a stale-book flag and counters. The C++20 and Rust twins produce the same events (compared by a 64-bit hash) and
the same staleness intervals on the shared fixtures.

Time is the recorded arrival time of each packet (nanoseconds since midnight): the handler is a pure function of its
inputs, so a recorded day replays exactly. One instrument per feed (the simulator's default venue).

API (stable):
    Handler(retx, gap_timeout_ns=500_000, rtt_ns=200_000)      retx: RetxServer or None
    Handler.run(events) -> Handler          events: merged (t, source, packet), source 'A', 'B' or 'S' (snapshot)
    .events [Event], .hash, .stale [(start, end)], .counters {name: n}
    RetxServer(clean_packets, window, max_count=1000)          emulates the simulator's retransmission service
    merge(lineA, lineB, snapshot) -> events                    from recorded files
    EVENT = struct '<BBHQQQQIQ' (kind, side, locate, seq, ts, ref, ref2, price, qty), fnv1a(bytes) -> int
"""
import heapq
import struct
from dataclasses import dataclass, field

EVENT = struct.Struct("<BBHQQQQIQ")          # 48 bytes
FNV_OFFSET, FNV_PRIME, MASK = 0xCBF29CE484222325, 0x100000001B3, (1 << 64) - 1


def fnv1a(data, h=FNV_OFFSET):
    for b in data:
        h = ((h ^ b) * FNV_PRIME) & MASK
    return h


def recorded(b):
    """Records of a recorded file: (send_ns, packet)."""
    out, i = [], 0
    while i + 12 <= len(b):
        t, n = struct.unpack_from(">QI", b, i)
        out.append((t, bytes(b[i + 12:i + 12 + n])))
        i += 12 + n
    return out


def blocks(p):
    """(first sequence number, [messages]) of a MoldUDP64 packet; heartbeats and end of session carry none."""
    seq, count = struct.unpack_from(">QH", p, 10)
    if count in (0, 0xFFFF):
        return seq, []
    msgs, i = [], 20
    for _ in range(count):
        n = struct.unpack_from(">H", p, i)[0]
        msgs.append(p[i + 2:i + 2 + n])
        i += 2 + n
    return seq, msgs


def be(m, o, n):
    return int.from_bytes(m[o:o + n], "big")


def normalise(m, seq):
    """The firm's event record of one feed message: (kind, side, locate, seq, ts, ref, ref2, price, qty)."""
    k = m[0]
    loc, ts = be(m, 1, 2), be(m, 5, 6)
    ref = ref2 = price = qty = side = 0
    if k == ord("A"):
        ref, side, qty, price = be(m, 11, 8), m[19], be(m, 20, 4), be(m, 32, 4)
    elif k == ord("E"):
        ref, qty, ref2 = be(m, 11, 8), be(m, 19, 4), be(m, 23, 8)
    elif k == ord("X"):
        ref, qty = be(m, 11, 8), be(m, 19, 4)
    elif k == ord("D"):
        ref = be(m, 11, 8)
    elif k == ord("P"):
        side, qty, price, ref2 = m[19], be(m, 20, 4), be(m, 32, 4), be(m, 36, 8)
    elif k == ord("U"):
        ref, ref2, qty, price = be(m, 11, 8), be(m, 19, 8), be(m, 27, 4), be(m, 31, 4)
    elif k == ord("C"):
        ref, qty, ref2, price = be(m, 11, 8), be(m, 19, 4), be(m, 23, 8), be(m, 32, 4)
    elif k == ord("Q"):
        qty, price, ref2 = be(m, 11, 8), be(m, 27, 4), be(m, 31, 8)
    elif k in (ord("G"), ord("W")):
        ref2 = be(m, 11, 8)
    return (k, side, loc, seq, ts, ref, ref2, price, qty)


@dataclass
class RetxServer:
    """The retransmission service as the simulator offers it (PROTOCOL.md): messages seq .. seq+count-1, at most
    max_count per request, from the last `window` messages published before the request."""
    clean: list                      # (t, packet) of the lossless stream
    window: int
    max_count: int = 1000

    def request(self, t, seq, count):
        published = 0
        for pt, p in self.clean:
            if pt > t:
                break
            s, msgs = blocks(p)
            published = max(published, s + len(msgs) - 1)
        if seq <= published - self.window or count <= 0:
            return None
        count = min(count, self.max_count)
        return [p for pt, p in self.clean if pt <= t and blocks(p)[0] < seq + count
                and blocks(p)[0] + len(blocks(p)[1]) > seq]


@dataclass
class Handler:
    retx: object = None
    gap_timeout_ns: int = 500_000
    rtt_ns: int = 200_000
    next: int = 1
    mode: str = "live"               # live | await_line | await_retx | await_snapshot
    pending: dict = field(default_factory=dict)       # seq -> message received beyond a gap
    events: list = field(default_factory=list)
    stale: list = field(default_factory=list)
    counters: dict = field(default_factory=lambda: {k: 0 for k in (
        "packets", "messages", "duplicates", "gaps", "filled_by_line", "retransmissions", "snapshots")})
    hash: int = FNV_OFFSET
    _since: int = 0
    _deadline: int = 0
    _snap: list = field(default_factory=list)
    _queue: list = field(default_factory=list)

    def _publish(self, ev):
        self.events.append(ev)
        self.hash = fnv1a(EVENT.pack(*ev), self.hash)

    def _deliver(self, m, seq):
        self._publish(normalise(m, seq))
        self.counters["messages"] += 1

    def _drain(self, t):
        while self.next in self.pending:
            self._deliver(self.pending.pop(self.next), self.next)
            self.next += 1
        if self.mode != "live" and not self.pending:
            if self.mode == "await_line":
                self.counters["filled_by_line"] += 1
            self.stale.append((self._since, t))
            self.mode = "live"

    def _incremental(self, t, p):
        seq, msgs = blocks(p)
        self.counters["packets"] += 1
        if msgs and seq + len(msgs) <= self.next:
            self.counters["duplicates"] += 1
            return
        for k, m in enumerate(msgs):
            s = seq + k
            if s < self.next:
                continue
            if s == self.next and self.mode == "live":
                self._deliver(m, s)
                self.next += 1
            else:
                self.pending.setdefault(s, m)
        if self.pending and self.mode == "live":
            self.mode, self._since, self._deadline = "await_line", t, t + self.gap_timeout_ns
            self.counters["gaps"] += 1
        self._drain(t)

    def _timeout(self, t):
        first_held = min(self.pending)
        reply = self.retx.request(t, self.next, first_held - self.next) if self.retx else None
        self.counters["retransmissions" if reply is not None else "snapshots"] += 1
        if reply is None:
            self.mode = "await_snapshot"
            return
        self.mode = "await_retx"
        n = len(self.events)
        for k, p in enumerate(reply):
            heapq.heappush(self._queue, (t + self.rtt_ns, 2, n, k, "R", p))
        # after the answer: if the gap is still open (the server caps a request), ask for the rest at once
        heapq.heappush(self._queue, (t + self.rtt_ns, 2, n, len(reply), "D", b""))

    def _snapshot(self, t, p):
        if self.mode != "await_snapshot":
            return
        for m in blocks(p)[1]:
            if m[0] == ord("G"):
                self._snap = [m]
            elif self._snap:
                self._snap.append(m)
                if m[0] == ord("W"):
                    self._apply_snapshot(t)

    def _apply_snapshot(self, t):
        upto = be(self._snap[0], 11, 8)
        if upto + 1 < self.next:               # older than what the book already holds: wait for the next cycle
            self._snap = []
            return
        for m in self._snap:
            self._publish(normalise(m, upto))
        self._snap = []
        self.next = upto + 1
        for s in [s for s in self.pending if s <= upto]:
            del self.pending[s]
        self._drain(t)
        if self.pending and self.mode != "live":             # a hole after the snapshot: detect it again
            self.mode, self._deadline = "await_line", t + self.gap_timeout_ns

    def run(self, events):
        for n, (t, src, p) in enumerate(events):
            heapq.heappush(self._queue, (t, 0 if src in "AB" else 1, n, 0, src, p))
        while self._queue:
            t, _, _, _, src, p = heapq.heappop(self._queue)
            if self.mode == "await_line" and t >= self._deadline:
                self._timeout(self._deadline)
            if src == "S":
                self._snapshot(t, p)
            elif src == "D":
                if self.mode == "await_retx" and self.pending:
                    self._timeout(t)
            else:
                self._incremental(t, p)
        return self


def merge(line_a, line_b, snapshot=b""):
    ev = [(t, "A", p) for t, p in recorded(line_a)] + [(t, "B", p) for t, p in recorded(line_b)]
    ev += [(t, "S", p) for t, p in recorded(snapshot)]
    return sorted(ev, key=lambda e: (e[0], "ABS".index(e[1])))


def book(events):
    """Level-3 book (ref -> [side, price, qty]) after applying normalised events; a snapshot begin clears it."""
    orders = {}
    for k, side, _loc, _seq, _ts, ref, ref2, price, qty in events:
        c = chr(k)
        if c == "G":
            orders.clear()
        elif c == "A":
            orders[ref] = [side, price, qty]
        elif c in "EXC" and ref in orders:
            orders[ref][2] -= qty
            if orders[ref][2] <= 0:
                del orders[ref]
        elif c == "D":
            orders.pop(ref, None)
        elif c == "U" and ref in orders:
            s = orders.pop(ref)[0]
            orders[ref2] = [s, price, qty]
    return orders
