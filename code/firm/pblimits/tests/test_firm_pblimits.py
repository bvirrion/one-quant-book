"""Acceptance tests of the Book 2, Chapter 27 build (prime-broker limit gate); the C++ and Rust
gates have the same tests."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_pblimits import Book, Order, apply, check, read_limits, route

HERE = pathlib.Path(__file__).resolve().parents[1]
USD = {"USD": 1.0, "EUR": 1.10, "JPY": 1 / 150, "GBP": 1.30, "MXN": 1 / 18}


def books():
    return [Book(lim) for lim in read_limits(str(HERE / "limits.csv"))]


def test_reader():
    a, b, c = read_limits(str(HERE / "limits.csv"))
    assert (a.pb, a.fee_per_m, a.nop_limit, a.max_tenor) == ("A", 3.0, 100e6, 7)
    assert "USDMXN" in c.pairs and "GBPUSD" not in a.pairs


def test_nop_and_settlement():
    a = books()[0]
    apply(a, Order("EURUSD", True, 50e6, 1.10, 2), USD)
    assert abs(a.nop() - 55e6) < 1e-6 and abs(a.settlement(2) - 55e6) < 1e-6
    apply(a, Order("USDJPY", True, 20e6, 150.0, 2), USD)          # long USD, short JPY
    assert abs(a.nop() - 55e6) < 1e-6                              # USD short shrinks: longs EUR 55, USD 0
    assert abs(a.settlement(2) - 55e6) < 1e-6


def test_limits_reject_and_reducing_trades_pass():
    a = books()[0]
    assert check(a, Order("EURUSD", True, 95e6, 1.10, 2), USD) == "nop"
    apply(a, Order("EURUSD", True, 90e6, 1.10, 2), USD)
    a.limits.nop_limit = 50e6                                      # limit cut below the position
    assert check(a, Order("EURUSD", True, 1e6, 1.10, 2), USD) == "nop"
    assert check(a, Order("EURUSD", False, 10e6, 1.10, 2), USD) == "ok"
    assert check(a, Order("GBPUSD", True, 1e6, 1.30, 2), USD) == "pair"
    assert check(a, Order("EURUSD", True, 1e6, 1.10, 30), USD) == "tenor"


def test_settlement_limit_by_value_date():
    b = books()[1]
    b.limits.nop_limit = 1e12
    apply(b, Order("EURUSD", True, 500e6, 1.10, 2), USD)          # 550m to receive on day 2
    assert check(b, Order("EURUSD", True, 50e6, 1.10, 2), USD) == "settlement"
    assert check(b, Order("EURUSD", True, 50e6, 1.10, 3), USD) == "ok"


def test_router_uses_cheapest_with_room():
    bs = books()
    pb, _ = route(bs, Order("EURUSD", True, 80e6, 1.10, 2), USD)
    assert pb == "A"
    pb, reasons = route(bs, Order("EURUSD", True, 80e6, 1.10, 2), USD)
    assert pb == "B" and reasons[0] == "A:nop"
    pb, _ = route(bs, Order("USDMXN", True, 10e6, 18.0, 2), USD)
    assert pb == "C"
