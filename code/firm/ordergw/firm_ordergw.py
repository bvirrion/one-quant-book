"""firm.ordergw -- the order gateway, Python reference (build of One Quant Book 13, chapter 21).

Between the strategy engine and the venue's order-entry session (Book 10's simulator, PROTOCOL.md section 2): a
table-driven order state machine with pending states, worst-case position accounting that counts every order that
might still fill, a token-bucket throttle, cancel-fill race detection, and reconciliation against the drop copy. The
C++20 and Rust gateways replay the same journal to the same states, positions and counters.

API (stable):
    TABLE {(state, event): state}; STATES; EVENTS; transition(state, event) -> state (KeyError if not allowed)
    TokenBucket(rate_per_s, burst).allow(t_ns) -> bool           integer nano-tokens, like the venue's
    Gateway(rate_per_s, burst, max_long, max_short)
        .new(t, cl, side, qty, price) / .cancel(t, cl) / .replace(t, cl, new_cl, qty, price)
            -> ("send", message tuple) or ("refused", reason)
        .on_report(t, kind, cl, **fields)       kind: A accepted, U replaced, C canceled, E executed, J rejected
        .position, .worst_long(), .worst_short(), .naive_long(), .races, .orders {cl: Order}
    replay(lines, rate_per_s, burst, max_long, check) -> Gateway   re-run a journal (requests must match)
    reconcile(gateway, drop_copy) -> [str]      drop_copy: [(kind, cl, qty)] of E and C reports
    summary(gateway) -> str                     what the C++ and Rust replays must reproduce
    Session(username, password)                 the client side of the venue's SoupBinTCP 4.0 session (PROTOCOL.md 2):
        .login(t) -> frame                      asks for the next sequenced message it has not seen (replay on
                                                reconnect); .send(t, app_bytes) -> frame; .heartbeat(t) -> frame|None
        .on_frame(t, typ, payload) -> app bytes of a sequenced message, else None; .dead(t); .disconnected()
    frames(buf) -> ([(typ, payload)], rest)     split a byte stream into SoupBinTCP frames
"""
import struct
from dataclasses import dataclass

STATES = ("pending_new", "live", "partial", "pending_cancel", "pending_replace", "filled", "cancelled", "rejected")
TERMINAL = ("filled", "cancelled", "rejected")
EVENTS = ("ack", "reject", "fill", "fill_all", "cancel_req", "cancel_ack", "too_late", "replace_req", "replace_ack")

# cancel_ack is any cancellation the venue reports: the answer to ours, or one of its own (a lost connection, a halt,
# a mass cancel, an expiry, self-trade prevention, the remainder of an IOC), which can reach an order in any open state.
TABLE = {
    ("pending_new", "ack"): "live", ("pending_new", "reject"): "rejected",
    ("pending_new", "fill"): "partial", ("pending_new", "fill_all"): "filled",
    ("pending_new", "cancel_req"): "pending_cancel", ("pending_new", "cancel_ack"): "cancelled",
    ("live", "fill"): "partial", ("live", "fill_all"): "filled", ("live", "cancel_req"): "pending_cancel",
    ("live", "replace_req"): "pending_replace", ("live", "cancel_ack"): "cancelled",
    ("partial", "fill"): "partial", ("partial", "fill_all"): "filled", ("partial", "cancel_req"): "pending_cancel",
    ("partial", "replace_req"): "pending_replace", ("partial", "cancel_ack"): "cancelled",
    ("pending_cancel", "fill"): "pending_cancel", ("pending_cancel", "fill_all"): "filled",
    ("pending_cancel", "cancel_ack"): "cancelled", ("pending_cancel", "too_late"): "filled",
    ("pending_cancel", "ack"): "pending_cancel",
    ("pending_replace", "fill"): "pending_replace", ("pending_replace", "fill_all"): "filled",
    ("pending_replace", "replace_ack"): "live", ("pending_replace", "too_late"): "filled",
    ("pending_replace", "cancel_ack"): "cancelled",
    ("filled", "too_late"): "filled", ("cancelled", "too_late"): "cancelled",
}


def transition(state, event):
    return TABLE[(state, event)]


class TokenBucket:
    """rate messages a second, at most burst at once; integer nano-tokens so that every language agrees."""

    def __init__(self, rate_per_s, burst):
        self.rate, self.cap = int(rate_per_s), int(burst) * 1_000_000_000
        self.tokens, self.last = self.cap, None

    def allow(self, t):
        if self.last is not None:
            self.tokens = min(self.cap, self.tokens + self.rate * (t - self.last))
        self.last = t
        if self.tokens < 1_000_000_000:
            return False
        self.tokens -= 1_000_000_000
        return True


@dataclass
class Order:
    cl: int
    side: str
    qty: int
    price: int
    state: str = "pending_new"
    filled: int = 0
    pending_qty: int = 0              # a replace in flight: its new total remaining quantity
    pending_price: int = 0
    new_cl: int = 0

    @property
    def leaves(self):
        return 0 if self.state in TERMINAL else self.qty - self.filled

    def worst_leaves(self):
        """What may still fill: the current leaves, or a replace's new quantity if larger."""
        if self.state == "pending_replace":
            return max(self.qty - self.filled, self.pending_qty)
        return self.leaves


class Gateway:
    def __init__(self, rate_per_s=1000, burst=50, max_long=10**9, max_short=10**9):
        self.bucket = TokenBucket(rate_per_s, burst)
        self.max_long, self.max_short = max_long, max_short
        self.orders = {}
        self.position = 0
        self.races = 0
        self.refused = {"throttle": 0, "exposure": 0, "state": 0}
        self.sent = 0

    # -- exposure -------------------------------------------------------------------------------------------------
    def worst_long(self):
        return self.position + sum(o.worst_leaves() for o in self.orders.values() if o.side == "B")

    def worst_short(self):
        return -self.position + sum(o.worst_leaves() for o in self.orders.values() if o.side == "S")

    def naive_long(self):
        """What a gateway that counts only acknowledged, uncancelled orders believes."""
        return self.position + sum(o.qty - o.filled for o in self.orders.values()
                                   if o.side == "B" and o.state in ("live", "partial"))

    def _refuse(self, why):
        self.refused[why] += 1
        return ("refused", why)

    def _send(self, t, msg):
        if not self.bucket.allow(t):
            return self._refuse("throttle")
        self.sent += 1
        return ("send", msg)

    # -- requests -------------------------------------------------------------------------------------------------
    def new(self, t, cl, side, qty, price):
        wl, ws = self.worst_long(), self.worst_short()
        if (side == "B" and wl + qty > self.max_long) or (side == "S" and ws + qty > self.max_short):
            return self._refuse("exposure")
        r = self._send(t, ("O", cl, side, qty, price))
        if r[0] == "send":
            self.orders[cl] = Order(cl, side, qty, price)
        return r

    def cancel(self, t, cl):
        o = self.orders.get(cl)
        if o is None or o.state not in ("pending_new", "live", "partial"):
            return self._refuse("state")
        r = self._send(t, ("X", cl, 0))
        if r[0] == "send":
            o.state = transition(o.state, "cancel_req")
        return r

    def replace(self, t, cl, new_cl, qty, price):
        o = self.orders.get(cl)
        if o is None or o.state not in ("live", "partial"):
            return self._refuse("state")
        extra = max(0, qty - (o.qty - o.filled))
        if (o.side == "B" and self.worst_long() + extra > self.max_long) or \
                (o.side == "S" and self.worst_short() + extra > self.max_short):
            return self._refuse("exposure")
        r = self._send(t, ("U", cl, new_cl, qty, price))
        if r[0] == "send":
            o.state = transition(o.state, "replace_req")
            o.pending_qty, o.pending_price, o.new_cl = qty, price, new_cl
        return r

    # -- reports --------------------------------------------------------------------------------------------------
    def on_report(self, t, kind, cl, qty=0, price=0, leaves=0, reason="", new_cl=0):
        o = self.orders.get(cl)
        if o is None:
            return
        if kind == "A":
            o.state = transition(o.state, "ack")
        elif kind == "E":
            if o.state in ("pending_cancel", "pending_replace"):
                self.races += 1                              # a fill crossed our cancel or replace on the way
            o.filled += qty
            self.position += qty if o.side == "B" else -qty
            o.state = transition(o.state, "fill_all" if leaves == 0 else "fill")
        elif kind == "C":
            o.state = transition(o.state, "cancel_ack")
        elif kind == "U":                                   # replaced: the order continues under its new identifier
            o.state = transition(o.state, "replace_ack")
            o.qty, o.price, o.filled = o.filled + o.pending_qty, o.pending_price, o.filled
            del self.orders[cl]
            o.cl = o.new_cl or new_cl
            self.orders[o.cl] = o
        elif kind == "J":
            if reason == "L":                               # too late to cancel or replace: it filled first
                o.state = transition(o.state, "too_late")
            else:
                o.state = transition(o.state, "reject")


def reconcile(gw, drop_copy):
    """Compare the gateway's filled quantities and cancellations with the venue's drop copy of E and C reports."""
    filled, cancelled = {}, set()
    for kind, cl, qty in drop_copy:
        if kind == "E":
            filled[cl] = filled.get(cl, 0) + qty
        elif kind == "C":
            cancelled.add(cl)
    breaks = []
    for cl, o in gw.orders.items():
        if o.filled != filled.get(cl, 0):
            breaks.append(f"order {cl}: gateway filled {o.filled}, drop copy {filled.get(cl, 0)}")
        if (o.state == "cancelled") != (cl in cancelled):
            breaks.append(f"order {cl}: gateway {o.state}, drop copy {'cancelled' if cl in cancelled else 'not'}")
    return breaks


def summary(gw):
    states = {}
    for o in gw.orders.values():
        states[o.state] = states.get(o.state, 0) + 1
    st = ",".join(f"{k}:{states[k]}" for k in sorted(states))
    return (f"orders {len(gw.orders)} position {gw.position} races {gw.races} sent {gw.sent} "
            f"refused {gw.refused['throttle']}/{gw.refused['exposure']}/{gw.refused['state']} "
            f"worst {gw.worst_long()}/{gw.worst_short()} states {st}")


def replay(lines, rate_per_s=10_000, burst=100, max_long=10**9, check=None):
    """Re-run a journal through a fresh gateway: requests are made again (their results must match the journal's)
    and reports applied; check(gateway) runs after every line."""
    g = Gateway(rate_per_s, burst, max_long=max_long)
    for line in lines:
        f = line.split()
        t, k = int(f[0]), f[1]
        if k == "Q":
            if f[2] == "N":
                r = g.new(t, int(f[3]), f[4], int(f[5]), int(f[6]))
            elif f[2] == "X":
                r = g.cancel(t, int(f[3]))
            else:
                r = g.replace(t, int(f[3]), int(f[4]), int(f[5]), int(f[6]))
            if r[0] != f[-1]:
                raise AssertionError(f"request replayed as {r[0]}, journal says {f[-1]}: {line}")
        else:
            g.on_report(t, f[2], int(f[3]), qty=int(f[4]), price=int(f[5]), leaves=int(f[6]),
                        reason="" if f[7] == "-" else f[7], new_cl=int(f[8]))
        if check:
            check(g)
    return g


# -- the order-entry session ---------------------------------------------------------------------------------------
def frame(typ, payload=b""):
    return struct.pack(">Hc", len(payload) + 1, typ.encode()) + payload


def frames(buf):
    out = []
    while len(buf) >= 2:
        (n,) = struct.unpack_from(">H", buf)
        if len(buf) < 2 + n:
            break
        out.append((chr(buf[2]), buf[3:2 + n]))
        buf = buf[2 + n:]
    return out, buf


class Session:
    """Client side of a SoupBinTCP 4.0 session. Sequenced messages carry no number on the wire: the client counts
    them, and logging in again asks for the next one it has not seen, so the server's replay fills the gap and nothing
    is applied twice. Heartbeats are sent after a second without sending; a server silent for 15 seconds is dead."""

    def __init__(self, username, password, heartbeat_ns=1_000_000_000, timeout_ns=15_000_000_000):
        self.user, self.password = username, password
        self.heartbeat_ns, self.timeout_ns = heartbeat_ns, timeout_ns
        self.next_seq = 1                  # the next sequenced message expected
        self.logged_in = False
        self.last_sent = self.last_recv = 0
        self.logins = 0

    def login(self, t):
        self.last_sent = self.last_recv = t
        self.logins += 1
        return frame("L", self.user.ljust(6)[:6].encode() + self.password.ljust(10)[:10].encode() + b" " * 10
                     + str(self.next_seq).rjust(20).encode())

    def send(self, t, app):
        self.last_sent = t
        return frame("U", app)

    def heartbeat(self, t):
        if self.logged_in and t - self.last_sent >= self.heartbeat_ns:
            self.last_sent = t
            return frame("R")
        return None

    def dead(self, t):
        return self.logged_in and t - self.last_recv > self.timeout_ns

    def disconnected(self):
        self.logged_in = False

    def on_frame(self, t, typ, payload):
        self.last_recv = t
        if typ == "A":
            first = int(payload[10:30])
            if first != self.next_seq:     # the server starts elsewhere: messages would be lost or applied twice
                raise ValueError(f"login accepted at {first}, expected {self.next_seq}")
            self.logged_in = True
        elif typ == "J":
            raise ConnectionError(f"login rejected: {payload.decode()}")
        elif typ == "S":
            self.next_seq += 1
            return payload
        elif typ == "Z":
            self.logged_in = False
        return None
