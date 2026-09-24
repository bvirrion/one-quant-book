"""Numbers gate: every numerical answer printed in Book 2, Chapter 27 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/pblimits"))
from access_demo import day_of_orders, plan
from firm_pblimits import Book, Limits, Order, apply, check

USD = {"USD": 1.0, "EUR": 1.10, "JPY": 1 / 150}
P = plan()
D = day_of_orders()


def a_book() -> Book:
    return Book(Limits("A", 3, 100e6, 500e6, 7, frozenset({"EURUSD", "USDJPY"})))


def test_text():
    b = a_book()
    apply(b, Order("EURUSD", True, 50e6, 1.10, 2), USD)
    assert round(b.nop() / 1e6) == 55 and round(b.settlement(2) / 1e6) == 55
    apply(b, Order("USDJPY", True, 20e6, 150.0, 2), USD)
    assert round(b.net["USD"] / 1e6) == -35 and round(b.net["JPY"] / 1e6) == -20 and round(b.nop() / 1e6) == 55
    assert round((55e6 + 95e6 * 1.10) / 1e6, 1) == 159.5
    assert check(b, Order("EURUSD", True, 95e6, 1.10, 2), USD) == "nop"
    assert D["first_full_a"] == 107 and D["rejected"] == 0
    assert round(D["path"][-1][3]) == 76
    assert (P["total"], P["all_c"]) == (13_800, 24_600)


def test_exercises():
    b = Book(Limits("X", 1, 1e12, 1e12, 7, frozenset({"EURUSD"})))
    apply(b, Order("EURUSD", True, 100e6, 1.10, 2), USD)
    apply(b, Order("EURUSD", False, 60e6, 1.10, 2), USD)
    assert round(b.settlement(2) / 1e6) == 44 and 110 + 66 == 176
    cut = day_of_orders(nop_a=50e6)
    assert round(cut["gross"]["C"] / 1e6) == 485 and round(D["gross"]["C"] / 1e6) == 435
    assert {k: round(v / 1e6) for k, v in cut["nop"].items()} == {"A": 12, "B": 120, "C": 279}
    assert cut["rejected"] == 0


def test_problem():
    bb = Book(Limits("B", 5, 150e6, 600e6, 30, frozenset({"EURUSD"})))
    bb.limits.nop_limit = 1e12
    apply(bb, Order("EURUSD", True, 500e6, 1.10, 2), USD)
    assert check(bb, Order("EURUSD", True, 50e6, 1.10, 2), USD) == "settlement"
    assert round((550e6 + 55e6) / 1e6) == 605
    assert P["flow"] == {"A": 500, "B": 600, "C": 100} and P["position"] == {"A": 100, "B": 150, "C": 50}
    assert (P["fee_cost"], P["nop_cost"], P["year"]) == (5_300, 8_500, 3_450_000)
    assert {k: round(v / 1e6) for k, v in D["nop"].items()} == {"A": 51, "B": 150, "C": 229}
