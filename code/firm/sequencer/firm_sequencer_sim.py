"""Failover of firm.sequencer's primary against Book 10's matching engine.

A scripted scenario of market prices (one a millisecond) goes through the sequencer into the journal; the primary and a
hot backup apply every entry; the primary's gateway sends the orders to the venue on session 1, whose reports come back
through the sequencer. A liquidity provider on session 2 keeps a deep ladder on both sides. At a failure time F the
primary stops; the backup, which stops hearing heartbeats, takes over: it fences the journal's epoch, logs in to
session 1 again asking for the reports it has not journaled, and resends the orders no report acknowledges, by one of
three procedures:

    "fresh ids"                resend at once under new identifiers, then replay the missed reports
    "fresh ids, reconciled"    replay the missed reports first, then resend what is still unacknowledged (new ids)
    "idempotency keys"         resend at once under the original identifiers (the venue rejects copies), then replay

    run(fail_ns, procedure, scenario=SCENARIO) -> Outcome
    cut_points(scenario) -> [(order index, stage, fail time)]   every stage of every order of the scenario
Outcome: duplicates (keys executed twice), orders, final positions of the backup and at the venue, the replay check (a
fresh replica on the whole journal reaches the backup's hash), the largest position, recovery time, the journal.
"""
import heapq
import pathlib
import random
import sys
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
for c in ("exchsim", "tape"):
    sys.path.insert(0, str(HERE.parent / c))
sys.path.insert(0, str(HERE))
import firm_sequencer as sq  # noqa: E402

T0 = 34_200_000_000_000
START, TICK = 1_000_000, 100
SEQ_NS, APPLY_NS, WIRE_NS = 1_000, 1_000, 20_000     # sequencer, replica, network one way
HEARTBEAT_NS, TIMEOUT_NS = 1_000_000, 3_000_000
PROCEDURES = ("fresh ids", "fresh ids, reconciled", "idempotency keys")


def scenario(n=60, seed=4):
    rng = random.Random(seed)
    p, out = START, []
    for _ in range(n):
        p += TICK * rng.choice((-2, -1, 1, 2))
        out.append(p)
    return out


SCENARIO = scenario()


@dataclass
class Outcome:
    duplicates: int = 0
    orders: int = 0
    position: int = 0
    venue_position: int = 0
    replay_equal: bool = False
    max_abs_position: int = 0
    recovery_ns: int = -1
    resent: int = 0
    order_times: list = None
    journal: list = None


def engine():
    import firm_exchsim as x
    import firm_exchsim_codec as c
    from firm_exchsim_engine import Engine
    e = Engine(x.ExchangeConfig().engine_config())
    nt = c.NT
    e.process(T0 - 5, 0, nt["ctl"]["S"]("O"))
    e.process(T0 - 4, 0, nt["ctl"]["L"](1, 1, "N"))
    e.process(T0 - 4, 0, nt["ctl"]["L"](2, 2, "N"))
    e.process(T0 - 3, 0, nt["ctl"]["P"](0, "T", "    "))
    for k in range(40):                                  # the provider's ladder: 40 levels a side, 100,000 each
        for side, px in (("S", START + (k + 1) * TICK), ("B", START - (k + 1) * TICK)):
            e.process(T0 - 2, 2, nt["in"]["O"](9_000_000 + 2 * k + (side == "B"), 1, side, 100_000, px, "D", "Y",
                                               "N", 0, 0, 0, "N", 0))
    return e, nt


def run(fail_ns, procedure="idempotency keys", prices=None):
    """One scenario with the primary failing at T0 + fail_ns (None: never)."""
    prices = SCENARIO if prices is None else prices
    e, nt = engine()
    journal = sq.Journal()
    primary, backup = sq.Replica(), sq.Replica()
    q, n = [], [0]
    session_reports = []                                  # session 1's sequenced reports, as the venue keeps them
    out = Outcome(order_times=[])
    fail = None if fail_ns is None else T0 + fail_ns
    state = {"primary_alive": True, "epoch": 1, "leader": "primary", "last_hb": T0, "took_over": None}
    executed = {}                                         # key -> executions at the venue (orders that traded)
    key_of_cl = {}

    def push(t, kind, payload=None):
        n[0] += 1
        heapq.heappush(q, (t, n[0], kind, payload))

    def journal_append(t, kind, *fields):            # through the sequencer: appended SEQ_NS later, in time order
        push(t + SEQ_NS, "sequence", (kind, fields))

    def send(t, cl, side, qty, price):
        out.orders += 1
        out.order_times.append(t)
        push(t + WIRE_NS, "venue", (cl, side, qty, price))

    for k, p in enumerate(prices):
        push(T0 + k * 1_000_000, "market", p)
    t_hb = T0
    while t_hb < T0 + (len(prices) + 10) * 1_000_000:
        push(t_hb, "heartbeat")
        t_hb += HEARTBEAT_NS
    if fail is not None:
        push(fail, "fail")

    def takeover(t):
        state["leader"], state["took_over"] = "backup", t
        state["epoch"] += 1
        journal.fence(state["epoch"])
        pending = backup.unacknowledged()
        if procedure == "fresh ids, reconciled":
            push(t + 2 * WIRE_NS, "login")                # replay first; resend after it (see "login")
            return
        for i, (key, cl) in enumerate(pending):
            resend(t, key, cl, i)
        push(t + 2 * WIRE_NS, "login")

    def resend(t, key, cl, i):
        o = backup.open[cl]
        out.resent += 1
        if procedure == "idempotency keys":
            send(t, cl, o.side, o.qty, o.price)
        else:
            new = 10**9 * state["epoch"] + i + 1
            journal_append(t, "A", key[0], key[1], new)
            key_of_cl[new] = key
            send(t, new, o.side, o.qty, o.price)

    while q:
        t, _, kind, payload = heapq.heappop(q)
        if kind == "fail":
            state["primary_alive"] = False
        elif kind == "heartbeat":
            if state["primary_alive"]:
                state["last_hb"] = t
            elif state["leader"] == "primary" and t - state["last_hb"] >= TIMEOUT_NS:
                takeover(t)
        elif kind == "market":
            journal_append(t, "M", payload)
        elif kind == "sequence":
            journal.append(state["epoch"], payload[0], *payload[1])
            push(t + APPLY_NS, "apply", journal.entries[-1])
        elif kind == "apply":
            for name, r in (("primary", primary), ("backup", backup)):
                if name == "primary" and not state["primary_alive"]:
                    continue
                if r.applied >= payload[1]:
                    continue
                outputs = r.apply(payload)
                if name == state["leader"] and (name == "backup" or state["primary_alive"]):
                    for cl, side, qty, price in outputs:
                        key_of_cl[cl] = (payload[1], 0)
                        send(t, cl, side, qty, price)
                out.max_abs_position = max(out.max_abs_position, abs(backup.position))
        elif kind == "venue":
            cl, side, qty, price = payload
            m = nt["in"]["O"](cl, 1, side, qty, price, "I", "Y", "N", 0, 0, 0, "N", 0)
            _, reps = e.process(t, 1, m)
            for s, r in reps:
                if s != 1:
                    continue
                session_reports.append(r)
                name = type(r).__name__[-1]
                if name == "E":
                    key = key_of_cl.get(r.cl_ord_id, (r.cl_ord_id // 16, r.cl_ord_id % 16))
                    executed.setdefault(key, set()).add(r.cl_ord_id)
                    out.venue_position += r.qty if side == "B" else -r.qty
                connected = state["primary_alive"] if state["leader"] == "primary" else state.get("logged_in")
                if connected:
                    push(t + WIRE_NS, "report", r)
        elif kind == "report":
            if state["leader"] == "primary" and not state["primary_alive"]:
                continue                                  # on its way to a gateway that is gone: lost
            name = type(payload).__name__[-1]
            if name == "E":
                journal_append(t, "E", payload.cl_ord_id, payload.qty, payload.leaves)
            elif name == "J":
                journal_append(t, "J", payload.cl_ord_id, payload.reason)
            elif name in "CA":                        # cancelled, or accepted (journaled as Q: the count matters)
                journal_append(t, "C" if name == "C" else "Q", payload.cl_ord_id)
        elif kind == "login":                             # session 1 again: the reports the journal has not seen
            state["logged_in"] = True
            seen = sum(1 for x in journal.entries if x[2] in "ECJQ")
            for r in session_reports[seen:]:
                push(t + WIRE_NS, "report", r)
            if procedure == "fresh ids, reconciled":
                push(t + WIRE_NS + 2 * APPLY_NS + 1, "resend_after_replay")
            push(t + WIRE_NS + 2 * APPLY_NS + 2, "recovered")
        elif kind == "resend_after_replay":
            for i, (key, cl) in enumerate(backup.unacknowledged()):
                resend(t, key, cl, i)
        elif kind == "recovered":
            out.recovery_ns = t - fail if fail is not None else 0
    out.duplicates = sum(1 for cls in executed.values() if len(cls) > 1)
    out.journal = journal.entries
    out.position = backup.position
    fresh = sq.Replica()
    for entry in journal.entries:
        fresh.apply(entry)
    out.replay_equal = fresh.hash == backup.hash and fresh.position == backup.position
    return out


STAGES = ("journaled, not yet sent", "sent, in flight", "at the venue, not yet reported", "reported")


def cut_points(prices=None):
    """For every order of the failure-free run, a failure time in the middle of each stage of its life."""
    prices = SCENARIO if prices is None else prices
    free = run(None, prices=prices)
    points = []
    for k, t in enumerate(free.order_times):
        bounds = [t - APPLY_NS - SEQ_NS, t, t + WIRE_NS, t + 2 * WIRE_NS, t + 2 * WIRE_NS + 500_000]
        for s, name in enumerate(STAGES):
            points.append((k, name, (bounds[s] + bounds[s + 1]) // 2 - T0))
    return points
