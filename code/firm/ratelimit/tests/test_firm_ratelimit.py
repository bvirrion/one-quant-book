"""Acceptance tests of the Book 3, Chapter 15 build (rate-limit governor), Python reference."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_ratelimit import Governor, Rule, binance_like


def test_weight_window_and_wait():
    g = Governor([Rule("weight", 60_000, 100)])
    assert g.try_send(1_000, 60, False) == (True, 0)
    assert g.try_send(2_000, 50, False) == (False, 58_000)          # would exceed; wait for the next minute
    assert g.try_send(60_000, 50, False) == (True, 0)               # new window


def test_orders_counted_separately():
    g = binance_like()
    for i in range(100):
        assert g.try_send(i, 1, True)[0]
    assert g.try_send(100, 1, True) == (False, 9_900)
    assert g.try_send(100, 1, False) == (True, 0)                   # a query is not an order


def test_backoff_on_429_and_418():
    g = binance_like()
    g.on_status(5_000, 429, 3_000)
    assert g.try_send(6_000, 1, False) == (False, 2_000)
    g.on_status(9_000, 418, 120_000)
    assert g.try_send(100_000, 1, False) == (False, 29_000) and g.log == ["429@5000", "418@9000"]
