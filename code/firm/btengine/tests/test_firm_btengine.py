"""Acceptance tests of firm.btengine (One Quant Book 15, chapter 11)."""
import pathlib
import sys

import numpy as np
import pyarrow as pa
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_btengine as B  # noqa: E402
import firm_exchsim as X  # noqa: E402
import firm_lobreplay  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402
from firm_vecbt import backtest  # noqa: E402


class Q(B.QuoteStrategy):
    """Works on the engine's context and on Book 7's replay context (working() gives shadows there)."""

    def __init__(self):
        self.mine = {}

    def on_market(self, ctx, t, snap):
        b, a = snap["bid"], snap["ask"]
        if b is None or a is None:
            return
        live = {getattr(w, "vid", w) for w in ctx.working()}
        self.mine = {v: sp for v, sp in self.mine.items() if v in live}
        have = set()
        for v, (side, px) in list(self.mine.items()):
            if px != (b if side == 1 else a):
                ctx.cancel(v)
                del self.mine[v]
            else:
                have.add(side)
        for side, px in ((1, b), (-1, a)):
            if side not in have and side * ctx.position < 300:
                self.mine[ctx.send(side, px, 100)] = (side, px)


class Mom(B.TargetStrategy):
    def target(self, close, i):
        return 0.0 if i < 5 else float(np.sign(close[i] - close[i - 5]))


def test_event_order_is_total():
    ev = B.event_queue_demo([(1.0, "order", (1,)), (1.0, "market", (2,)), (0.5, "cancel", (3,)),
                             (1.0, "fill", (4,)), (1.0, "market", (5,))])
    assert [(e.t, e.cls, e.data[0]) for e in ev] == [(0.5, "cancel", 3), (1.0, "market", 2), (1.0, "market", 5),
                                                     (1.0, "fill", 4), (1.0, "order", 1)]


def test_data_access_hash_is_content(tmp_path):
    d = B.DataAccess(tmp_path)
    t = pa.table({"x": np.arange(5), "y": np.ones(5)})
    h1 = d.put("a/b", t)
    h2 = d.put("c", t)
    assert h1 == h2 == d.hash("a/b") and d.get("a/b").equals(t.replace_schema_metadata(d.get("a/b").schema.metadata))
    assert d.put("a/b", pa.table({"x": np.arange(5), "y": np.zeros(5)})) != h1
    name = d.tape(30.0, 3)
    assert d.meta(name)["seed"] == 3 and len(B.msgs_of(d.get(name))) > 100


def test_levels_and_strategy_types(tmp_path):
    d = B.DataAccess(tmp_path)
    with pytest.raises(TypeError):
        B.Engine(1, Q(), d, {"dataset": "x"})
    with pytest.raises(ValueError):
        B.Engine(5, Q(), d, {"dataset": "x"})


def test_level1_is_vecbt_unchanged(tmp_path):
    d = B.DataAccess(tmp_path)
    name = d.daily(200, 3)
    r = B.Engine(1, Mom(), d, {"dataset": name}).run()
    c = d.get(name)["close"].to_numpy()
    w = Mom().targets(c)
    direct = backtest(w[:, None], np.r_[0.0, c[1:] / c[:-1] - 1][:, None], lag=1)
    assert r.pnl == pytest.approx(direct.capital[-1] - 1.0)
    r2 = B.Engine(2, Mom(), d, {"dataset": name}).run()
    assert len(r2.fills) > 0 and abs(r2.pnl - r.pnl) < 0.5


def test_level3_is_replay_unchanged(tmp_path):
    d = B.DataAccess(tmp_path)
    name = d.tape(90.0, 5)
    r = B.Engine(3, Q(), d, {"dataset": name, "latency": 20e-6}).run()
    direct = firm_lobreplay.Replay(B.msgs_of(d.get(name)), Q(), "fifo", 20e-6, 20e-6).run()
    assert r.pnl == pytest.approx(direct.pnl()) and len(r.fills) == len(direct.fills) > 0
    assert [e.cls for e in r.events[:1]] == ["market"]


def test_level4_is_the_simulator_with_the_same_session(tmp_path):
    d = B.DataAccess(tmp_path)
    name = d.tape(90.0, 5)
    r = B.Engine(4, Q(), d, {"dataset": name, "latency": 20e-6, "seed": 1}).run()
    ph = X.Phases(start_ns=X.OPEN_NS - X.SEC, open_ns=X.OPEN_NS, close_ns=X.OPEN_NS + 90 * X.SEC,
                  end_ns=X.OPEN_NS + 91 * X.SEC)
    sim = X.Simulator(X.ExchangeConfig(phases=ph, fees=X.FeeSchedule(make=0.0, take=0.0)), seed=1)
    sim.add_background(X.TapeBackground(TapeConfig(seconds=90.0, seed=5, news_at=None)))
    lm = X.LatencyModel(entry_ns=20_000, ack_ns=20_000, data_ns=20_000)
    sim.add_agent(X.ReplayStrategyAdapter(Q()), X.SessionSpec(firm="BT", latency=lm))
    ctx = sim.run().agents["quote"]
    assert len(ctx.fills) == len(r.fills) > 0 and ctx.position(1) == r.position
    assert len(simulate(TapeConfig(seconds=90.0, seed=5, news_at=None)).msgs) == len(B.msgs_of(d.get(name)))


def test_results_store_ids_and_queries(tmp_path):
    d, s = B.DataAccess(tmp_path / "d"), B.ResultsStore(tmp_path / "r")
    name = d.tape(60.0, 2)
    a = B.Engine(3, Q(), d, {"dataset": name, "latency": 0.0}).run()
    b = B.Engine(3, Q(), d, {"dataset": name, "latency": 0.0}).run()
    c = B.Engine(3, Q(), d, {"dataset": name, "latency": 1e-3}).run()
    assert a.run_id == b.run_id != c.run_id
    ids = {s.save(x) for x in (a, b, c)}
    assert len(ids) == 2 and len(s.query(level=3)) == 2 and len(s.query(latency=1e-3)) == 1
    back = s.load(a.run_id)
    assert back["manifest"]["data"][name] == d.hash(name) and back["fills"].num_rows == len(a.fills)
    assert B.first_divergence(a, b) is None


def test_classify_and_markouts():
    mids = np.array([[0.0, 100.0], [10.0, 102.0]])
    fills_a = np.array([[1.0, 1, 100, 100.0], [5.0, -1, 100, 101.0]])
    fills_b = np.array([[1.0005, 1, 100, 100.0]])
    a = B.Run(4, 0.0, 0, fills_a, [], mids, {})
    b = B.Run(3, 0.0, 0, fills_b, [], mids, {})
    assert B.classify_fills(a, b).tolist() == [False, True]
    assert B.markouts(a, 10.0).tolist() == [200.0, -100.0]
