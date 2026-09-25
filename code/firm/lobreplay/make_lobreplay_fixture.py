"""Writes the shared fixture of firm.lobreplay: five minutes of a seeded firm.tape session, the shadow orders a touch
quoter sent with a 50-millisecond order-entry latency (with their arrival and cancellation times), and the fills the
Python 'fifo' model gives them. Run from the repository root:
    .venv/bin/python code/firm/lobreplay/make_lobreplay_fixture.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
from firm_lobreplay import Replay, Strategy, track_fifo  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402


class Touch(Strategy):
    def __init__(self):
        self.vids = {1: None, -1: None}

    def on_market(self, ctx, t, snap):
        for side, px in ((1, snap["bid"]), (-1, snap["ask"])):
            v = self.vids[side]
            sh = ctx.shadows[v] if v is not None else None
            live = sh is not None and sh.status in ("sent", "working") and sh.cancel_sent == float("inf")
            if live and ctx.shadows[v].price != px:
                ctx.cancel(v)
                live = False
            if not live and px is not None and abs(ctx.position + side * 100) <= 500:
                self.vids[side] = ctx.send(side, px, 100)


msgs = simulate(TapeConfig(seconds=300.0, news_at=None, seed=33)).msgs
res = Replay(msgs, Touch(), "fifo", entry_latency=0.05, data_latency=0.02).run()
orders = [(s.vid, s.side, s.price, s.qty, s.arrive, s.cancel_arrive) for s in res.shadows]
fills = track_fifo(msgs, orders)
assert [(v, t, q) for t, v, _, q, _ in res.fills] == fills          # the engine and the reference agree
d = HERE / "data"
d.mkdir(exist_ok=True)
with open(d / "fixture_msgs.csv", "w") as f:
    f.write("t,kind,oid,side,price,qty\n")
    for m in msgs:
        f.write(f"{float(m['t'])!r},{m['kind'].decode()},{m['oid']},{m['side']},{m['price']},{m['qty']}\n")
with open(d / "fixture_orders.csv", "w") as f:
    f.write("vid,side,price,qty,arrive,cancel\n")
    for v, sd, p, q, a, c in orders:
        f.write(f"{v},{sd},{p},{q},{a!r},{c!r}\n")
with open(d / "fixture_fills.csv", "w") as f:
    f.write("vid,t,qty\n")
    for v, t, q in fills:
        f.write(f"{v},{t!r},{q}\n")
print(len(msgs), "messages,", len(orders), "orders,", len(fills), "fills")
