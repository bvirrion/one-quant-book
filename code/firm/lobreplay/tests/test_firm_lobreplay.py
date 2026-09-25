import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_lobreplay import Book, Replay, Strategy, track_fifo

MSG = np.dtype([("t", "f8"), ("kind", "S1"), ("oid", "i8"), ("side", "i1"), ("price", "i8"), ("qty", "i8"),
                ("agg", "i1"), ("trade", "i8")])


def msgs(rows):
    return np.array([(t, k, o, s, p, q, 0, -1) for t, k, o, s, p, q in rows], dtype=MSG)


BASE = [(0.0, b"A", 1, 1, 100, 300), (0.0, b"A", 2, 1, 100, 200), (0.0, b"A", 3, -1, 101, 500)]


def test_book():
    b = Book()
    for m in msgs(BASE + [(1.0, b"E", 1, 1, 100, 300), (2.0, b"X", 2, 1, 100, 50)]):
        b.apply(m)
    assert b.best(1) == 100 and b.size(1, 100) == 150 and b.levels[1][100] == [[2, 150]] and 1 not in b.where


def test_fifo_queue():
    # our 100 joins behind 500 at 100; 300 executes, 150 cancels, 50 executes (ahead empty), then 80 executes on order 4
    rows = BASE + [(1.0, b"A", 4, 1, 100, 400), (2.0, b"E", 1, 1, 100, 300), (3.0, b"X", 2, 1, 100, 150),
                   (4.0, b"E", 2, 1, 100, 50), (5.0, b"E", 4, 1, 100, 80), (6.0, b"E", 4, 1, 100, 80)]
    fills = track_fifo(msgs(rows), [(0, 1, 100, 100, 0.5, float("inf"))])
    assert fills == [(0, 5.0, 80), (0, 6.0, 20)]
    assert track_fifo(msgs(rows), [(0, 1, 100, 100, 0.5, 5.5)]) == [(0, 5.0, 80)]       # cancelled before the last
    assert track_fifo(msgs(rows), [(0, 1, 100, 100, 1.5, float("inf"))]) == []          # behind order 4 too


class Once(Strategy):
    """Send one order at the first market update seen at or after `start`."""

    def __init__(self, side=1, price=100, qty=100, start=0.5):
        self.args, self.start, self.sent = (side, price, qty), start, False

    def on_market(self, ctx, t, snap):
        if not self.sent and t >= self.start:
            ctx.send(*self.args)
            self.sent = True


def test_models_and_latency():
    # the order joins at t = 1 behind 400 (orders 1 and 2 after the first execution)
    rows = BASE + [(1.0, b"E", 1, 1, 100, 100), (2.0, b"X", 1, 1, 100, 100), (3.0, b"A", 5, 1, 100, 300),
                   (4.0, b"X", 5, 1, 100, 300), (5.0, b"E", 1, 1, 100, 100), (6.0, b"E", 2, 1, 100, 200)]
    m = msgs(rows)
    front, fifo, prob = (Replay(m, Once(), model).run() for model in ("front", "fifo", "prob"))
    assert [(f[0], f[3]) for f in front.fills] == [(5.0, 100)]        # the next execution at the price
    assert fifo.fills == []                                           # the 400 ahead are all that trades
    assert [(f[0], f[3]) for f in prob.fills] == [(6.0, 100)]         # the cancellations were half ahead, half behind
    late = Replay(m, Once(), "front", entry_latency=4.5).run()
    assert [f[0] for f in late.fills] == [6.0]
    seen = Replay(m, Once(), "front", data_latency=4.2, entry_latency=0.5).run()
    assert [f[0] for f in seen.fills] == [5.0]                        # sees the opening at 4.2, arrives at 4.7
    assert front.position == 100 and front.cash == -100 * 100


def test_fixture_matches_reference():
    d = pathlib.Path(__file__).resolve().parents[1] / "data"
    rows = [line.split(",") for line in (d / "fixture_msgs.csv").read_text().splitlines()[1:]]
    m = np.array([(float(t), k.encode(), int(o), int(s), int(p), int(q), 0, -1) for t, k, o, s, p, q in rows], dtype=MSG)
    orders = [(int(v), int(s), int(p), int(q), float(a), float(c))
              for v, s, p, q, a, c in (line.split(",") for line in (d / "fixture_orders.csv").read_text().splitlines()[1:])]
    want = [(int(v), float(t), int(q)) for v, t, q in (line.split(",") for line in (d / "fixture_fills.csv").read_text().splitlines()[1:])]
    assert track_fifo(m, orders) == want and len(want) == 29
