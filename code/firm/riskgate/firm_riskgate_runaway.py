"""A runaway child-order generator of the 2012 shape against Book 10's matching engine, through firm.riskgate.

The generator keeps sending buy child orders of 100 shares, in bursts of 15 a microsecond apart every 10 ms (1,500 a
second on average, the rate of 4 million orders in 45 minutes), priced 5 ticks above the last trade and immediate or
cancel, without looking at what has filled. A liquidity provider keeps a ladder of sell orders of 1,000 shares and
replaces each level taken with one a tick above the ladder's top, so the runaway pushes the price up by a tick every
ten fills. Every child order goes through the gate first; the gate's reference price is the last trade the firm
has heard of.

    run(config, seconds=5.0) -> Stats       config: dict of the checks switched on (see CONFIGS)
    CONFIGS                                 the chapter's table, one entry per check
Stats: orders sent, refused, filled shares, position, notional, first refusal time, orders sent in the last second,
and the position every 50 ms.
"""
import heapq
import pathlib
import sys
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
for c in ("exchsim", "tape"):
    sys.path.insert(0, str(HERE.parent / c))
sys.path.insert(0, str(HERE))
import firm_riskgate as rg  # noqa: E402

T0 = 34_200_000_000_000
TICK, START, CHILD, LEVEL = 100, 1_000_000, 100, 1_000
OUT_NS, IN_NS = 20_000, 50_000                   # venue -> firm, firm -> venue
BURST, BURST_EVERY = 15, 10_000_000
BIG = 10**15

CONFIGS = {
    "none": {},
    "collar": {"collar_bp": 500},
    "size and notional": {"max_qty": 1_000, "max_notional": 1_000 * START * 2},
    "throttle": {"rate": 500, "burst": 50},
    "duplicates": {"dup_ns": 100_000_000},
    "position (fills only)": {"max_long": 20_000, "inflight": False},
    "position (in flight)": {"max_long": 20_000},
    "capital threshold": {"max_gross": 25_000 * START},
    "position + kill switch": {"max_long": 20_000, "kill": True},
}


@dataclass
class Stats:
    sent: int = 0
    refused: int = 0
    filled: int = 0
    position: int = 0
    notional: int = 0
    first_refusal_ms: float = -1.0
    last_second: int = 0
    killed: bool = False
    last_price: int = START
    trace: list = None                  # (ms from the start, position) every 50 ms


def limits(cfg, seconds):
    return rg.Limits.from_dict({
        "version": 1, "max_age_ns": BIG, "ref_max_age_ns": BIG, "dup_ns": cfg.get("dup_ns", 0),
        "firm": {"max_gross": cfg.get("max_gross", BIG)}, "desks": {"D": {"max_gross": BIG}},
        "strategies": {"runaway": {"desk": "D", "rate": cfg.get("rate", 10**9), "burst": cfg.get("burst", 10**6),
                                   "max_open": 10**9}},
        "instruments": {"1": {"collar_bp": cfg.get("collar_bp", 10_000), "max_qty": cfg.get("max_qty", BIG),
                              "max_notional": cfg.get("max_notional", BIG), "max_long": cfg.get("max_long", BIG),
                              "max_short": BIG}}})


class FillsOnlyGate(rg.Gate):
    """A position limit that counts only what has filled: the limit that did not account for outstanding orders."""

    def check(self, t, strat, instr, side, qty, price, cl):
        saved = dict(self.open_buy)
        self.open_buy = {}
        try:
            code, m = super().check(t, strat, instr, side, qty, price, cl)
        finally:
            ob, self.open_buy = self.open_buy, saved
            for k, v in ob.items():
                self.open_buy[k] = self.open_buy.get(k, 0) + v
        return code, m


def run(cfg, seconds=5.0):
    import firm_exchsim as x
    import firm_exchsim_codec as c
    from firm_exchsim_engine import Engine
    e = Engine(x.ExchangeConfig().engine_config())
    nt = c.NT
    e.process(T0 - 3, 0, nt["ctl"]["S"]("O"))
    e.process(T0 - 2, 0, nt["ctl"]["L"](1, 1, "N"))
    e.process(T0 - 2, 0, nt["ctl"]["L"](2, 2, "N"))
    e.process(T0 - 1, 0, nt["ctl"]["P"](0, "T", "    "))
    gate = (FillsOnlyGate if cfg.get("inflight", True) is False else rg.Gate)(limits(cfg, seconds), T0)
    gate.set_reference(T0, 1, START)
    st = Stats(trace=[])
    q, n = [], [0]
    maker = {"top": START, "cl": 10**9}

    def push(t, kind, payload):
        n[0] += 1
        heapq.heappush(q, (t, n[0], kind, payload))

    def post(t, price):
        maker["cl"] += 1
        m = nt["in"]["O"](maker["cl"], 1, "S", LEVEL, price, "D", "Y", "N", 0, 0, 0, "N", 0)
        e.process(t, 2, m)

    for k in range(10):                               # the ladder: ten levels of 1,000 shares
        post(T0, START + k * TICK)
    maker["top"] = START + 9 * TICK
    end = T0 + int(seconds * 1e9)
    t = T0
    while t < end:
        for i in range(BURST):
            push(t + i * 1000, "child", None)
        t += BURST_EVERY
    for k in range(int(seconds * 20) + 1):
        push(T0 + k * 50_000_000 - 1, "trace", None)
    cl = 0
    while q:
        t, _, kind, payload = heapq.heappop(q)
        if kind == "child":
            cl += 1
            price = gate.ref[1][0] + 5 * TICK
            code, _ = gate.check(t, "runaway", 1, "B", CHILD, price, cl)
            if code != ".":
                st.refused += 1
                if st.first_refusal_ms < 0:
                    st.first_refusal_ms = (t - T0) / 1e6
                if cfg.get("kill") and code in "LG" and not st.killed:
                    st.killed = True
                    for c_ in gate.kill(t, "strategy", "runaway", "cancel"):
                        push(t + IN_NS, "cancel", c_)
                continue
            st.sent += 1
            if t >= end - 1_000_000_000:
                st.last_second += 1
            push(t + IN_NS, "venue", (cl, price))
        elif kind == "venue":
            ocl, price = payload
            _, reps = e.process(t, 1, nt["in"]["O"](ocl, 1, "B", CHILD, price, "I", "Y", "N", 0, 0, 0, "N", 0))
            for s, r in reps:
                name = type(r).__name__[-1]
                if s == 2 and name == "E" and r.leaves == 0:          # a level taken: the ladder moves up
                    maker["top"] += TICK
                    post(t, maker["top"])
                if s == 1:
                    push(t + OUT_NS, "report", r)
        elif kind == "trace":
            st.trace.append(((t + 1 - T0) // 1_000_000, gate.pos.get(1, 0)))
        elif kind == "cancel":
            e.process(t, 1, nt["in"]["X"](payload, 0))
        elif kind == "report":
            name = type(payload).__name__[-1]
            if name == "E":
                gate.on_fill(payload.cl_ord_id, payload.qty, payload.price)
                gate.set_reference(t, 1, payload.price)          # the last trade, as the firm hears of it
                st.filled += payload.qty
                st.notional += payload.qty * payload.price
                st.last_price = payload.price
                if payload.leaves == 0:
                    gate.on_done(payload.cl_ord_id)
            elif name in "CJ":
                gate.on_done(payload.cl_ord_id)
    st.position = gate.pos.get(1, 0)
    return st

