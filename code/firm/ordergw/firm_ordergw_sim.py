"""firm.ordergw against Book 10's matching engine: a strategy quoting one buy order through the gateway, a counterparty
selling into it at random, and latencies on every path. Used by the tests (conformance, random interleavings), by the
fixture of the C++ and Rust replays, and by chapter 21's figure.

    run(seed, cancel_ns, fill_rate, cycles, mode="cancel"|"replace", max_long=10**9) -> Result
Result: gateway, journal (lines "t Q|R ..." the replays read), drop copy, cancels, max position.
The strategy keeps one buy order working: it places it, holds it for an exponential time, then cancels it (mode
cancel: and places the next when the cancel is answered) or replaces it (mode replace); a fill ends the order and the
next one is placed when the report arrives.
"""
import heapq
import math
import pathlib
import random
import sys
from dataclasses import dataclass, field

HERE = pathlib.Path(__file__).resolve().parent
for c in ("exchsim", "tape"):
    sys.path.insert(0, str(HERE.parent / c))
sys.path.insert(0, str(HERE))
import firm_ordergw as gw  # noqa: E402

T0 = 34_200_000_000_000
PRICE, QTY = 999_900, 100
OUT_NS = 20_000                        # venue -> gateway, every report


@dataclass
class Result:
    gateway: object
    journal: list = field(default_factory=list)
    drop_copy: list = field(default_factory=list)
    cancels: int = 0
    max_position: int = 0


def engine():
    import firm_exchsim as x
    import firm_exchsim_codec as c
    from firm_exchsim_engine import Engine
    e = Engine(x.ExchangeConfig().engine_config())
    nt = c.NT
    e.process(T0 - 3, 0, nt["ctl"]["S"]("O"))
    e.process(T0 - 2, 0, nt["ctl"]["L"](1, 1, "N"))
    e.process(T0 - 2, 0, nt["ctl"]["L"](2, 2, "N"))
    e.process(T0 - 1, 0, nt["ctl"]["P"](0, "T", "    "))
    return e, nt


def run(seed, cancel_ns, fill_rate, cycles, mode="cancel", max_long=10**9, hold_ns=1_000_000, rate=10_000, burst=100):
    rng = random.Random(seed)
    e, nt = engine()
    g = gw.Gateway(rate, burst, max_long=max_long)
    res = Result(g)
    q = []                                            # (t, order, kind, payload)
    n = 0

    def push(t, kind, payload):
        nonlocal n
        n += 1
        heapq.heappush(q, (t, n, kind, payload))

    def to_venue(t, msg):                             # our message reaches the venue after cancel_ns (every path)
        push(t + cancel_ns, "venue", msg)

    next_cl = [1]

    def place(t):
        cl = next_cl[0]
        next_cl[0] += 1
        r = g.new(t, cl, "B", QTY, PRICE)
        res.journal.append(f"{t} Q N {cl} B {QTY} {PRICE} {r[0]}")
        if r[0] == "send":
            to_venue(t, ("O", cl))
            push(t + int(rng.expovariate(1 / hold_ns)), "cancel", cl)
        elif r[1] == "throttle":
            del_cl = cl                                   # the budget is spent: try again a millisecond later
            push(t + 1_000_000, "place", del_cl)

    # the counterparty: market sells of one lot at Poisson times
    t = T0
    horizon = T0 + cycles * (hold_ns + 2 * cancel_ns + 2 * OUT_NS)
    while t < horizon:
        t += int(rng.expovariate(fill_rate) * 1e9) + 1
        push(t, "sell", None)
    place(T0)
    while q:
        t, _, kind, payload = heapq.heappop(q)
        if kind == "sell":
            _, reports = e.process(t, 2, nt["in"]["O"](t, 1, "S", QTY, 0, "I", "Y", "N", 0, 0, 0, "N", 0))
            for s, r in reports:
                if s == 1:
                    push(t + OUT_NS, "report", r)
        elif kind == "venue":
            tag = payload[0]
            if tag == "O":
                m = nt["in"]["O"](payload[1], 1, "B", QTY, PRICE, "D", "Y", "N", 0, 0, 0, "N", 0)
            elif tag == "X":
                m = nt["in"]["X"](payload[1], 0)
            else:
                m = nt["in"]["U"](payload[1], payload[2], QTY, PRICE)
            _, reports = e.process(t, 1, m)
            for s, r in reports:
                if s == 1:
                    push(t + OUT_NS, "report", r)
        elif kind == "place":
            place(t)
        elif kind == "cancel":
            o = g.orders.get(payload)
            if o is None or o.state not in ("pending_new", "live", "partial"):
                continue
            res.cancels += 1
            if mode == "replace":
                new_cl = next_cl[0]
                next_cl[0] += 1
                r = g.replace(t, payload, new_cl, QTY, PRICE)
                res.journal.append(f"{t} Q U {payload} {new_cl} {QTY} {PRICE} {r[0]}")
                if r[0] == "send":
                    to_venue(t, ("U", payload, new_cl))
                    push(t + int(rng.expovariate(1 / hold_ns)), "cancel", new_cl)
                continue
            r = g.cancel(t, payload)
            res.journal.append(f"{t} Q X {payload} {r[0]}")
            if r[0] == "send":
                to_venue(t, ("X", payload))
        elif kind == "report":
            k = type(payload).__name__[-1]
            cl = payload.cl_ord_id
            f = dict(qty=getattr(payload, "qty", 0), price=getattr(payload, "price", 0),
                     leaves=getattr(payload, "leaves", 0), reason=getattr(payload, "reason", ""),
                     new_cl=getattr(payload, "new_cl_ord_id", 0))
            g.on_report(t, k, cl, **f)
            res.journal.append(f"{t} R {k} {cl} {f['qty']} {f['price']} {f['leaves']} {f['reason'] or '-'} "
                               f"{f['new_cl']}")
            if k in "EC":
                res.drop_copy.append((k, cl, f["qty"] if k == "E" else 0))
            res.max_position = max(res.max_position, g.position)
            if len(g.orders) < cycles and not any(x.state not in gw.TERMINAL for x in g.orders.values()):
                place(t)
    return res


def race_probability(fill_rate, cancel_ns, report_ns=OUT_NS):
    """A fill the strategy has not heard of when it cancels, or one that happens while the cancel travels: Poisson
    fills at rate lambda over the report's delay plus the cancel's (orders living much longer than a round trip)."""
    return 1 - math.exp(-fill_rate * (cancel_ns + report_ns) * 1e-9)
