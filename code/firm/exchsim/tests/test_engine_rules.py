"""Rule-by-rule tests of the matching engine (PROTOCOL.md section 4)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from firm_exchsim_codec import NT  # noqa: E402
from firm_exchsim_engine import Engine  # noqa: E402

C, IN = NT["ctl"], NT["in"]


def cfg(matching="F", **kw):
    inst = {"locate": 1, "symbol": "SIM1", "tick": 100, "lot": 100, "matching": matching, "top_pct": kw.get("top", 0),
            "fifo_pct": 0, "min_alloc": 1, "start_price": 1_000_000}
    return {"venue": "SIMX", "session": "SIMX      ", "engine_ns": 100,
            "fees": {"unit": "share", "make": -2000, "take": 3000, "cross": 0},
            "throttle": {"rate": kw.get("rate", 0), "burst": kw.get("burst", 0)}, "instruments": [inst]}


class Run:
    def __init__(self, phase="T", **kw):
        self.e, self.t = Engine(cfg(**kw)), 0
        self.ctl(C["S"]("O"))
        for s in (1, 2, 3):
            self.ctl(C["L"](s, 7 if s < 3 else 8, "Y"))
        self.ctl(C["P"](0, phase, "TEST"))

    def ctl(self, m):
        return self.go(0, m)

    def go(self, s, m):
        self.t += 1000
        self.feed, self.reps = self.e.process(self.t, s, m)
        return self

    def o(self, s, cl, side, qty, px, tif="D", disp="Y", po="N", dq=0, mq=0, g=0, mode="N", stop=0):
        return self.go(s, IN["O"](cl, 1, side, qty, px, tif, disp, po, dq, mq, g, mode, stop))

    def kinds(self):
        return [type(m).__name__[-1] for m in self.feed], [(s, type(r).__name__[-1]) for s, r in self.reps]

    def top(self):
        return self.e.book(1).top()


def test_price_time_priority_and_partial_fill():
    r = Run().o(1, 1, "B", 300, 999_900).o(1, 2, "B", 200, 999_900).o(3, 9, "S", 400, 999_900)
    execs = [m for m in r.feed if type(m).__name__ == "Feed_E"]
    assert [(m.ref, m.shares) for m in execs] == [(1, 300), (2, 100)]
    assert r.top() == (999_900, 100, None, 0)
    e_maker = [x for s, x in r.reps if s == 1]
    assert e_maker[0].liquidity == "A" and e_maker[0].fee == -600_000 and e_maker[1].leaves == 100


def test_post_only_and_ioc_fok():
    r = Run().o(1, 1, "S", 100, 1_000_100)
    r.o(2, 2, "B", 100, 1_000_100, po="Y")
    assert r.reps == [(2, r.reps[0][1])] and r.reps[0][1].reason == "O"
    r.o(2, 3, "B", 300, 1_000_100, tif="F")                     # FOK: 100 available, 300 needed
    assert [type(x).__name__ for _, x in r.reps] == ["Out_A", "Out_C"] and r.top()[2] == 1_000_100
    r.o(2, 4, "B", 300, 1_000_100, tif="I")                     # IOC: fills 100, cancels 200
    assert [type(x).__name__ for _, x in r.reps] == ["Out_A", "Out_E", "Out_E", "Out_C"]
    assert r.reps[-1][1].decrement == 200 and r.reps[-1][1].reason == "I"


def test_market_order_never_rests_and_band():
    r = Run().o(1, 1, "S", 100, 1_000_100).o(2, 2, "B", 500, 0)
    assert r.reps[-1][1].decrement == 400 and r.top() == (None, 0, None, 0)
    r.ctl(C["R"](1, 1_000_000, 990_000, 1_010_000))
    r.o(1, 3, "B", 100, 1_020_000)
    assert r.reps[0][1].reason == "B"


def test_iceberg_refreshes_at_the_back_with_new_reference():
    r = Run().o(1, 1, "B", 500, 999_900, dq=100).o(1, 2, "B", 100, 999_900).o(3, 9, "S", 150, 999_900)
    names = [type(m).__name__[-1] for m in r.feed]
    assert names == ["E", "A", "E"]                              # slice executed, refreshed, then order 2
    assert r.feed[1].ref != 1 and r.feed[2].ref == 2
    assert r.top() == (999_900, 150, None, 0)                    # order 2's last 50 and the refreshed slice of 100


def test_self_trade_prevention_modes():
    r = Run().o(1, 1, "S", 100, 1_000_100, g=5).o(2, 2, "B", 100, 1_000_100, g=5, mode="O")   # same firm 7
    assert [(s, type(x).__name__, getattr(x, "reason", "")) for s, x in r.reps] == [(2, "Out_A", ""),
                                                                                    (1, "Out_C", "S")]
    assert r.top() == (1_000_100, 100, None, 0)                  # resting cancelled, incoming rests
    r.o(1, 3, "S", 300, 1_000_100, g=5, mode="D")                 # decrement both by 100: no trade
    assert not [m for m in r.feed if type(m).__name__ == "Feed_E"]
    assert r.top() == (None, 0, 1_000_100, 200)
    r.o(3, 4, "B", 100, 1_000_100, g=5, mode="W")                 # other firm (8): trades normally
    assert [m for m in r.feed if type(m).__name__ == "Feed_E"]


def test_replace_keeps_priority_only_on_a_decrease_at_the_same_price():
    r = Run().o(1, 1, "B", 300, 999_900).o(1, 2, "B", 100, 999_900)
    r.go(1, IN["U"](1, 11, 200, 999_900))
    assert r.reps[0][1].priority == "Y" and type(r.feed[0]).__name__ == "Feed_X"
    r.go(1, IN["U"](11, 12, 400, 999_900))
    assert r.reps[0][1].priority == "N" and type(r.feed[0]).__name__ == "Feed_U"
    assert [o.ref for o in r.e.book(1).level_orders(1, 999_900)] == [2, r.feed[0].new_ref]
    r.go(1, IN["X"](12, 0)).go(1, IN["X"](12, 0))
    assert r.reps[0][1].reason == "L"                             # too late / unknown


def test_midpoint_peg_and_min_qty():
    r = Run().o(1, 1, "B", 100, 999_900).o(1, 2, "S", 100, 1_000_100)
    r.o(2, 3, "B", 500, 0, disp="M", mq=300)
    r.o(3, 4, "S", 200, 0, disp="M")                              # below the buyer's minimum: no trade
    assert not [m for m in r.feed if type(m).__name__ == "Feed_P"]
    r.o(3, 5, "S", 400, 0, disp="M")
    p = [m for m in r.feed if type(m).__name__ == "Feed_P"]
    assert p and p[0].price == 1_000_000 and p[0].shares == 400


def test_stop_order_triggers_on_a_trade():
    r = Run().o(1, 1, "S", 100, 1_000_100).o(1, 2, "S", 100, 1_000_200)
    r.o(2, 3, "B", 100, 0, stop=1_000_100)
    assert r.reps[0][1].state == "S"
    r.o(3, 4, "B", 100, 1_000_100)                                # trade at 100.01 triggers the stop
    assert r.top() == (None, 0, None, 0)


def test_opening_auction_uncross_and_expiry():
    r = Run(phase="O").o(1, 1, "B", 300, 1_000_200).o(2, 2, "S", 200, 999_900).o(2, 3, "S", 200, 0)
    r.o(1, 4, "B", 100, 1_000_000, tif="O")
    r.ctl(C["I"](1, "O"))
    ind = r.feed[0]
    assert ind.paired == 400 and ind.imbalance == 0 or ind.paired > 0
    r.ctl(C["P"](1, "T", "OPEN"))
    q = [m for m in r.feed if type(m).__name__ == "Feed_Q"][0]
    assert q.shares == 400 and q.cross_type == "O"
    assert r.top()[0] is None or r.top()[0] < (r.top()[2] or 10**9)


def test_throttle_and_duplicates():
    r = Run(rate=1, burst=2)
    r.o(1, 1, "B", 100, 999_000).o(1, 2, "B", 100, 999_000).o(1, 3, "B", 100, 999_000)
    assert r.reps[0][1].reason == "T"
    r.t += 5_000_000_000
    r.o(1, 1, "B", 100, 999_000)
    assert r.reps[0][1].reason == "D"


def test_pro_rata_with_top_order():
    r = Run(matching="C", top=40).o(1, 1, "S", 100, 1_000_100).o(2, 2, "S", 300, 1_000_100).o(3, 3, "S", 600, 1_000_100)
    r.o(3, 9, "B", 500, 1_000_100, g=0)
    fills = {m.ref: m.shares for m in r.feed if type(m).__name__ == "Feed_E"}
    assert sum(fills.values()) == 500 and fills[1] == 100           # top order takes its whole 100 (40% cap = 200)
    assert fills[3] > fills[2]                                       # pro rata by size


def test_cancel_on_disconnect_and_mass_cancel():
    r = Run().o(1, 1, "B", 100, 999_000).o(1, 2, "S", 100, 1_001_000).o(2, 3, "B", 100, 998_000)
    r.go(2, IN["M"](0, "*"))
    assert [x.reason for _, x in r.reps] == ["M"]
    r.ctl(C["D"](1))
    assert [x.reason for _, x in r.reps] == ["D", "D"] and r.top() == (None, 0, None, 0)
    r.o(1, 9, "B", 100, 999_000)
    assert r.reps == []                                              # logged out: ignored


def test_snapshot_reflects_the_book():
    r = Run().o(1, 1, "B", 100, 999_000).o(2, 2, "B", 200, 999_000).o(2, 3, "S", 50, 1_001_000)
    snap = r.e.snapshot(1, seq=17)
    assert [type(m).__name__[-1] for m in snap] == ["G", "H", "A", "A", "A", "W"]
    assert snap[0].orders == 3 and snap[-1].seq == 17 and [m.ref for m in snap[2:5]] == [1, 2, 3]
