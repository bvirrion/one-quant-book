import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_cryptofeed as f  # noqa: E402

L = f.LIMITS["binance-spot"]


def test_shards():
    assert f.plan_shards(800, L)["connections"] == 1
    assert f.plan_shards(1025, L)["connections"] == 2
    p = f.plan_shards(800, L, max_streams_per_conn=20, reconnect_window_s=10)
    assert (p["connections"], p["addresses"]) == (40, 4)


def test_resync_under_the_governor():
    rules = [f.frl.Rule("weight", 60_000, 1000)]
    a = f.resync_staleness(4, 250, rules, rtt_ms=100)
    assert a["done_ms"] == pytest.approx(103) and a["symbol_seconds"] == pytest.approx(0.406)
    b = f.resync_staleness(5, 250, rules, rtt_ms=100)
    assert b["done_ms"] == pytest.approx(60_100)                  # the fifth waits for the next minute
    assert f.resync_staleness(0, 250, rules)["done_ms"] == 0


def test_allocate_and_skew():
    s = f.allocate(100, {"a": 80, "b": 80, "c": 10}, {"a": 1, "b": 1, "c": 1})
    assert s["c"] == 10 and s["a"] == pytest.approx(45) and s["b"] == pytest.approx(45)
    assert f.allocate(100, {"a": 10, "b": 20}, {"a": 1, "b": 5}) == {"a": 10, "b": 20}
    est = f.skew([0, 10, 20, 30], [3, 12, 25, 33], 2)
    assert est == [(12.0, 2.0), (33.0, 3.0)]
