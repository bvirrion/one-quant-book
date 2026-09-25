import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bars"))
from firm_bars import Bars
from firm_evbt import Engine, PenetrationFill, Strategy, TouchFill, VolumeCapFill


def _bars(o, h, lo, c, v):
    n = len(c)
    a = lambda x: np.asarray(x, float)  # noqa: E731
    return Bars(np.arange(n, dtype=float), np.arange(1, n + 1, dtype=float), a(o), a(h), a(lo), a(c), a(v),
                a(c) * a(v), a(c), np.ones(n, int), np.arange(n), np.arange(n))


class BuyOnce(Strategy):
    def __init__(self, price, kind="limit", qty=10.0):
        self.price, self.kind, self.qty, self.oid = price, kind, qty, None

    def on_bar(self, ctx, i, bar):
        if i == 0:
            self.oid = ctx.submit(+1, self.qty, self.kind, self.price)


def test_fill_models_and_lifecycle():
    bars = _bars([100, 100, 99, 99], [100, 101, 100, 99], [100, 99, 98, 98], [100, 100, 99, 98], [100, 100, 100, 100])
    res, orders, fills = Engine(bars, BuyOnce(99.0), TouchFill()).run()
    assert [f.t for f in fills] == [2.0] and fills[0].price == 99.0 and orders[0].status == "filled"
    assert [s for _, s in orders[0].history] == ["pending", "working", "filled"]
    _, _, fp = Engine(bars, BuyOnce(99.0), PenetrationFill(1.0)).run()
    assert [f.t for f in fp] == [3.0]                                  # the low reached 98 only in bar 2
    _, _, fc = Engine(bars, BuyOnce(99.0, qty=25.0), VolumeCapFill(TouchFill(), 0.1)).run()
    assert [f.qty for f in fc] == [10.0, 10.0, 5.0]                    # partial fills, 10% of 100 a bar
    _, om, fm = Engine(bars, BuyOnce(None, "market"), TouchFill()).run()
    assert fm[0].price == 100.0 and fm[0].t == 2.0                     # the next bar's open


def test_latency_and_cancel():
    bars = _bars([100] * 4, [100] * 4, [100, 99, 99, 99], [100] * 4, [100] * 4)
    _, _, f0 = Engine(bars, BuyOnce(99.0), latency=0.0).run()
    _, _, f1 = Engine(bars, BuyOnce(99.0), latency=1.5).run()
    assert [f.t for f in f0] == [2.0] and [f.t for f in f1] == [4.0]   # active at 2.5: misses the bar starting at 2

    class Cancel(BuyOnce):
        def on_bar(self, ctx, i, bar):
            super().on_bar(ctx, i, bar)
            if i == 0:
                ctx.cancel(self.oid)
    _, oc, fc = Engine(bars, Cancel(99.0), latency=0.0).run()
    assert fc == [] and oc[0].status == "cancelled"
    _, oo, fo = Engine(bars, Cancel(99.0), latency=1.5, policy="optimistic").run()
    assert [f.t for f in fo] == [3.0] and oo[0].status == "filled"      # live an instant of bar 2: filled if optimistic
    _, _, fl = Engine(bars, BuyOnce(99.0), latency=1.5, policy="optimistic").run()
    assert [f.t for f in fl] == [3.0]


def test_pnl_split_and_determinism():
    bars = _bars([100, 100, 110, 55], [100, 100, 110, 55], [100, 99, 110, 55], [100, 100, 110, 55], [100] * 4)
    eng = Engine(bars, BuyOnce(100.0, qty=1.0), TouchFill(), fee=0.5, capital=1000.0, splits=[(3.0, 2.0)])
    res, _, fills = eng.run()
    assert eng.position == 2.0 and np.isclose(fills[0].fee, 0.5)
    assert np.allclose(res.capital, np.array([1000.0, 999.5, 1009.5, 1009.5]) / 1000.0)
    res2, _, _ = Engine(bars, BuyOnce(100.0, qty=1.0), TouchFill(), fee=0.5, capital=1000.0, splits=[(3.0, 2.0)]).run()
    assert np.array_equal(res.net, res2.net)
    assert np.isclose(res.costs["trading"][1], 0.5 / 1000.0) and np.isclose(res.gross[1] - res.net[1], 0.0005)
