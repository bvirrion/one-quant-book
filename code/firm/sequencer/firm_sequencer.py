"""firm.sequencer -- a sequencer, a journal with fencing epochs, and replicas of a deterministic trading state machine
(build of One Quant Book 13, chapter 24), Python reference.

Every input of the trading process (market events, and the order gateway's reports) goes through one sequencer, which
numbers it and appends it to a journal; every replica applies the journal in sequence order and computes the same state
and the same outputs. Only the primary sends its outputs to the venue. On failover the backup raises the journal's epoch
(so that a primary that is not quite dead can no longer append: fencing), reconnects the order-entry session, replays
the reports it missed, reconciles, and resends the outputs that no report acknowledges. Client order identifiers are
derived from the output's key (the input's sequence number and the output's index), so every replica knows every order
by the same identifier. A resend that reuses it is idempotent: the venue rejects a copy of an order it already has. A
resend under a fresh identifier (the habit of gateways that never reuse one) is a second order when the first had
reached the venue. The resend is itself journaled (kind "A", an alias), so that the replicas agree on it. The C++20 and
Rust replicas replay the fixture's journal to the same states (data/expected.txt).

API (stable):
    Journal(); .append(epoch, kind, *fields) -> seq (ValueError if fenced); .fence(epoch); .entries; .epoch
    Replica(); .apply(entry) -> [(cl, side, qty, price)]; .unacknowledged() -> [(key, cl)]
        .position, .open {cl: Order}, .hash, .applied, .reports_seen;  cl_for(key) -> cl
    entry format: (epoch, seq, kind, fields): kind "M" (price,), "E" (cl, qty, leaves), "C" (cl,), "J" (cl, reason),
        "Q" (cl,) accepted (counted: the session's reports are numbered),
        "A" (key seq, key index, new cl): the order of that key resent under a new identifier
    to_line(entry) / from_line(line)            the journal's text form (data/journal.txt)
"""
from dataclasses import dataclass

LIMIT, SIZE, AGGRESS = 1_000, 100, 300          # position limit per side, order size, price offset of the order
MAX_OPEN = 3


class Journal:
    def __init__(self):
        self.entries, self.epoch = [], 1

    def append(self, epoch, kind, *fields):
        if epoch < self.epoch:
            raise ValueError(f"fenced: epoch {epoch} < {self.epoch}")
        seq = len(self.entries) + 1
        self.entries.append((epoch, seq, kind, tuple(fields)))
        return seq

    def fence(self, epoch):
        if epoch <= self.epoch:
            raise ValueError("a new epoch must be larger")
        self.epoch = epoch


@dataclass
class Order:
    key: tuple                                    # (input seq, output index): the output's identity
    side: str
    qty: int
    price: int
    filled: int = 0


def cl_for(key):
    """The client order identifier of an output, derived from its key: the same in every replica."""
    return key[0] * 16 + key[1]


class Replica:
    """The trading state machine: on each price change it trades SIZE against the move (buys when the price falls,
    sells when it rises) with a marketable immediate-or-cancel order, while the worst-case position on that side stays
    within LIMIT and fewer than MAX_OPEN orders are open. Integer arithmetic only."""

    def __init__(self):
        self.position, self.last_price = 0, 0
        self.open = {}                            # cl -> Order
        self.abandoned = {}                       # cl -> Order: identifiers given up at a resend
        self.applied = 0
        self.reports_seen = 0
        self.hash = 0xCBF29CE484222325

    def _mix(self, *vals):
        for v in vals:
            for b in int(v).to_bytes(8, "little", signed=True):
                self.hash = ((self.hash ^ b) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF

    def open_qty(self, side):
        return sum(o.qty - o.filled for o in self.open.values() if o.side == side)

    def apply(self, entry):
        _, seq, kind, f = entry
        if seq != self.applied + 1:
            raise ValueError(f"gap: expected {self.applied + 1}, got {seq}")
        self.applied = seq
        out = []
        if kind == "M":
            (p,) = f
            if self.last_price and p != self.last_price and len(self.open) < MAX_OPEN:
                side = "B" if p < self.last_price else "S"
                room = LIMIT - (self.position if side == "B" else -self.position) - self.open_qty(side)
                if room >= SIZE:
                    key = (seq, 0)
                    cl = cl_for(key)
                    price = p + AGGRESS if side == "B" else p - AGGRESS
                    self.open[cl] = Order(key, side, SIZE, price)
                    out.append((cl, side, SIZE, price))
                    self._mix(seq, 0, ord(side), SIZE, price)
            self.last_price = p
        elif kind == "A":                         # resent under a new identifier: the old one is given up for lost
            key, new = (f[0], f[1]), f[2]
            old = next(c for c, o in self.open.items() if o.key == key)
            o = self.open.pop(old)
            self.abandoned[old] = o               # if it did reach the venue, its reports still count
            self.open[new] = Order(key, o.side, o.qty, o.price)
            self._mix(seq, new)
        else:
            self.reports_seen += 1
            cl = f[0]
            o = self.open.get(cl)
            if o is None and cl in self.abandoned:
                o = self.abandoned[cl]
                if kind == "E":
                    self.position += f[1] if o.side == "B" else -f[1]
                if kind in "EC" and (kind == "C" or f[2] == 0):
                    del self.abandoned[cl]
                o = None
            if kind == "E" and o is not None:
                o.filled += f[1]
                self.position += f[1] if o.side == "B" else -f[1]
                if f[2] == 0:
                    del self.open[cl]
            elif kind == "C" and o is not None:
                del self.open[cl]
            elif kind == "J" and o is not None and f[1] != "D":   # a duplicate: the venue has the original
                del self.open[cl]
        self._mix(seq, self.position, len(self.open))
        return out

    def unacknowledged(self):
        """Open orders that no report has mentioned yet: sent or not, the replica cannot tell."""
        return sorted((o.key, cl) for cl, o in self.open.items() if o.filled == 0)


def to_line(entry):
    epoch, seq, kind, f = entry
    return " ".join(map(str, (epoch, seq, kind, *f)))


def from_line(line):
    p = line.split()
    epoch, seq, kind = int(p[0]), int(p[1]), p[2]
    rest = p[3:]
    if kind == "J":
        f = (int(rest[0]), rest[1])
    else:
        f = tuple(int(x) for x in rest)
    return epoch, seq, kind, f
