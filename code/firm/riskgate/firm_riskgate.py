"""firm.riskgate -- the pre-trade risk gate, Python reference (build of One Quant Book 13, chapter 22).

Every order the strategy engine sends passes the gate before the order gateway (chapter 21). The gate checks it
against a hierarchy of limits (firm, desk, strategy, instrument) and answers in one step: accept, or refuse with the
first failed check. The C++20 and Rust gates replay the same event stream to the same decisions (data/expected.txt).
Policy -- which limits, at which levels, with which values -- is One Quant Book 11's (firm.riskctl, chapter 27); this
component is the nanosecond implementation, and `from_riskctl` reads the section riskctl exports for it.

Checks, in this order (a refusal reports the first; the audit record keeps them all as a bit mask):
    K kill       the strategy, its desk or the firm is killed
    S stale      the limits snapshot is older than its max_age (fail closed: no fresh limits, no orders)
    R reference  no reference price, or one older than ref_max_age (fail closed)
    C collar     price outside reference +- collar_bp (buy above, sell below)
    Q quantity   qty > max_qty
    N notional   qty * price > max_notional
    L long       worst-case long position (position + every open buy, in flight included) + qty > max_long
    H short      the same for sells and max_short
    O open       open orders of the strategy >= max_open
    G gross      gross notional of the desk or the firm (executed + open) + qty * price > max_gross
    T throttle   the strategy's token bucket (rate, burst) is empty
    D duplicate  same instrument, side, qty and price as one of the strategy's last 16 orders within dup_ns

API (stable):
    Limits.from_dict(d) / from_riskctl(d)           the schema below; integer prices (1e-4) and quantities
    Gate(limits, t)                                  .check(t, strat, instr, side, qty, price, cl) -> (code, mask)
        .set_limits(t, limits)  whole snapshot, between events;  .heartbeat(t)  the limits are still current
        .set_reference(t, instr, price);  .on_fill(cl, qty);  .on_done(cl)  (cancelled, rejected or filled)
        .kill(t, level, name, action) -> [cl to cancel] (+ [(instr, side, qty, price)] to flatten);  .unkill
        .audit: [(t, cl, code, mask)]
    replay(lines) -> Gate                            the event stream of data/events.txt
    CODES, BIT {code: bit}

Schema: {"version", "max_age_ns", "ref_max_age_ns", "dup_ns",
         "firm": {"max_gross"}, "desks": {name: {"max_gross"}},
         "strategies": {name: {"desk", "rate", "burst", "max_open"}},
         "instruments": {locate: {"collar_bp", "max_qty", "max_notional", "max_long", "max_short"}}}
"""
from dataclasses import dataclass, field

CODES = "KSRCQNLHOGTD"
BIT = {c: 1 << i for i, c in enumerate(CODES)}
ONE = 1_000_000_000                                   # a token, in nano-tokens
DUP_SLOTS = 16


@dataclass
class Limits:
    version: int
    max_age_ns: int
    ref_max_age_ns: int
    dup_ns: int
    firm_gross: int
    desks: dict
    strategies: dict
    instruments: dict

    @classmethod
    def from_dict(cls, d):
        return cls(int(d["version"]), int(d["max_age_ns"]), int(d["ref_max_age_ns"]), int(d.get("dup_ns", 0)),
                   int(d["firm"]["max_gross"]), {k: dict(v) for k, v in d["desks"].items()},
                   {k: dict(v) for k, v in d["strategies"].items()},
                   {int(k): dict(v) for k, v in d["instruments"].items()})


def from_riskctl(d):
    """Adapter from Book 11's firm.riskctl: its export() writes {"riskctl": policy, "riskgate": this schema}, and the
    gate reads the "riskgate" section (a dict already in this schema is accepted as it is)."""
    return Limits.from_dict(d.get("riskgate", d))


@dataclass
class Order:
    strat: str
    instr: int
    side: str
    qty: int
    price: int
    filled: int = 0


@dataclass
class StratState:
    tokens: int = 0
    last: int = -1
    open: int = 0
    recent: list = field(default_factory=list)       # (t, instr, side, qty, price), newest last, at most DUP_SLOTS


class Gate:
    def __init__(self, limits, t=0):
        self.orders = {}
        self.pos = {}                                  # instr -> signed position
        self.open_buy, self.open_sell = {}, {}         # instr -> open quantity (worst case: everything may fill)
        self.gross = {}                                # desk -> executed + open notional; key None: the firm
        self.ref = {}                                  # instr -> (price, t)
        self.strat = {}
        self.killed = set()                            # ("firm", ""), ("desk", name), ("strategy", name)
        self.audit = []
        self.set_limits(t, limits)

    # -- limits -----------------------------------------------------------------------------------------------
    def set_limits(self, t, limits):
        self.lim, self.lim_t = limits, t
        for s, v in limits.strategies.items():
            st = self.strat.setdefault(s, StratState())
            if st.last < 0:
                st.tokens = int(v["burst"]) * ONE

    def heartbeat(self, t):
        self.lim_t = t

    def set_reference(self, t, instr, price):
        self.ref[instr] = (price, t)

    # -- the check ----------------------------------------------------------------------------------------------
    def check(self, t, strat, instr, side, qty, price, cl):
        L = self.lim
        sv, iv = L.strategies[strat], L.instruments[instr]
        desk = sv["desk"]
        st = self.strat[strat]
        m = 0
        if ("firm", "") in self.killed or ("desk", desk) in self.killed or ("strategy", strat) in self.killed:
            m |= BIT["K"]
        if t - self.lim_t > L.max_age_ns:
            m |= BIT["S"]
        ref, rt = self.ref.get(instr, (0, -10**18))
        if ref <= 0 or t - rt > L.ref_max_age_ns:
            m |= BIT["R"]
        band = ref * int(iv["collar_bp"]) // 10_000
        if (side == "B" and price > ref + band) or (side == "S" and price < ref - band):
            m |= BIT["C"]
        if qty > iv["max_qty"]:
            m |= BIT["Q"]
        notional = qty * price
        if notional > iv["max_notional"]:
            m |= BIT["N"]
        pos = self.pos.get(instr, 0)
        if side == "B" and pos + self.open_buy.get(instr, 0) + qty > iv["max_long"]:
            m |= BIT["L"]
        if side == "S" and -pos + self.open_sell.get(instr, 0) + qty > iv["max_short"]:
            m |= BIT["H"]
        if st.open >= sv["max_open"]:
            m |= BIT["O"]
        if self.gross.get(desk, 0) + notional > L.desks[desk]["max_gross"] or \
                self.gross.get(None, 0) + notional > L.firm_gross:
            m |= BIT["G"]
        tokens = st.tokens if st.last < 0 else min(int(sv["burst"]) * ONE, st.tokens + int(sv["rate"]) * (t - st.last))
        if tokens < ONE:
            m |= BIT["T"]
        if L.dup_ns and any(t - r[0] <= L.dup_ns and r[1:] == (instr, side, qty, price) for r in st.recent):
            m |= BIT["D"]
        code = "." if m == 0 else CODES[(m & -m).bit_length() - 1]
        self.audit.append((t, cl, code, m))
        if m == 0:                                     # accepted: spend the token, count the order
            st.tokens, st.last = tokens - ONE, t
            st.open += 1
            st.recent = (st.recent + [(t, instr, side, qty, price)])[-DUP_SLOTS:]
            self.orders[cl] = Order(strat, instr, side, qty, price)
            book = self.open_buy if side == "B" else self.open_sell
            book[instr] = book.get(instr, 0) + qty
            for k in (desk, None):
                self.gross[k] = self.gross.get(k, 0) + notional
        return code, m

    # -- reports ------------------------------------------------------------------------------------------------
    def on_fill(self, cl, qty, price=None):
        o = self.orders.get(cl)
        if o is None:
            return
        o.filled += qty
        self.pos[o.instr] = self.pos.get(o.instr, 0) + (qty if o.side == "B" else -qty)
        book = self.open_buy if o.side == "B" else self.open_sell
        book[o.instr] -= qty
        if price is not None and price != o.price:       # executed notional replaces the open notional at its price
            d = qty * (price - o.price)
            for k in (self.lim.strategies[o.strat]["desk"], None):
                self.gross[k] += d
        if o.filled == o.qty:
            self.on_done(cl)

    def on_done(self, cl):
        """The order is finished (filled, cancelled or rejected): its unfilled part leaves the exposure."""
        o = self.orders.pop(cl, None)
        if o is None:
            return
        rest = o.qty - o.filled
        book = self.open_buy if o.side == "B" else self.open_sell
        book[o.instr] -= rest
        for k in (self.lim.strategies[o.strat]["desk"], None):
            self.gross[k] -= rest * o.price
        self.strat[o.strat].open -= 1

    # -- kill switch ------------------------------------------------------------------------------------------------
    def _under(self, level, name, o):
        return level == "firm" or (level == "desk" and self.lim.strategies[o.strat]["desk"] == name) or \
            (level == "strategy" and o.strat == name)

    def kill(self, t, level, name="", action="block"):
        """block: refuse every new order under the node; cancel: also return the open orders to cancel (a mass
        cancel); flatten: also return the orders that close the node's positions (at the reference price, which the
        collar admits). Positions are kept per instrument for the firm, so flatten closes the firm's positions."""
        self.killed.add((level, name if level != "firm" else ""))
        self.audit.append((t, 0, "K", BIT["K"]))
        if action == "block":
            return []
        cancels = sorted(cl for cl, o in self.orders.items() if self._under(level, name, o))
        if action == "cancel":
            return cancels
        return cancels + [(instr, "S" if p > 0 else "B", abs(p), self.ref.get(instr, (0, 0))[0])
                          for instr, p in sorted(self.pos.items()) if p]

    def unkill(self, level, name=""):
        self.killed.discard((level, name if level != "firm" else ""))


def replay(lines, limits_by_version):
    """Events: "t L version" (install a snapshot), "t H" (heartbeat), "t P instr price" (reference),
    "t O cl strat instr side qty price" (check), "t F cl qty price" (fill), "t X cl" (done),
    "t K level name action" (kill), "t U level name" (unkill). Returns the gate; its audit is the output."""
    g = None
    for line in lines:
        f = line.split()
        t, k = int(f[0]), f[1]
        if k == "L":
            lim = limits_by_version[int(f[2])]
            if g is None:
                g = Gate(lim, t)
            else:
                g.set_limits(t, lim)
        elif k == "H":
            g.heartbeat(t)
        elif k == "P":
            g.set_reference(t, int(f[2]), int(f[3]))
        elif k == "O":
            g.check(t, f[3], int(f[4]), f[5], int(f[6]), int(f[7]), int(f[2]))
        elif k == "F":
            g.on_fill(int(f[2]), int(f[3]), int(f[4]))
        elif k == "X":
            g.on_done(int(f[2]))
        elif k == "K":
            g.kill(t, f[2], "" if f[3] == "-" else f[3], f[4])
        elif k == "U":
            g.unkill(f[2], "" if f[3] == "-" else f[3])
    return g


def decisions(gate):
    """The audit as one string of codes (what the C++ and Rust replays must reproduce), and its counts."""
    s = "".join(code for _, cl, code, _ in gate.audit if cl)
    counts = {c: s.count(c) for c in "." + CODES if s.count(c)}
    return s, counts
