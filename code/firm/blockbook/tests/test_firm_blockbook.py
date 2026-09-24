"""Acceptance tests of the Book 3, Chapter 21 build (block-batched order book)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_blockbook import Action, Book, mark_price, order_block, run_block


def test_price_time_and_post_only():
    b = Book()
    run_block(b, [Action("alo", "M1", "sell", 101, 5, 1), Action("alo", "M2", "sell", 101, 5, 2),
                  Action("alo", "M3", "buy", 101, 5, 3)], "arrival")
    assert b.best() == (None, 101)                               # the crossing post-only buy is rejected
    fills = run_block(b, [Action("ioc", "T", "buy", 101, 7)], "arrival")
    assert [(f.maker, f.qty) for f in fills] == [("M1", 5), ("M2", 2)]
    assert b.positions == {"T": 7, "M1": -5, "M2": -2}


def test_cancels_first_protects_stale_quote():
    def block():
        return [Action("ioc", "T", "buy", 101, 5), Action("cancel", "M", oid=1),
                Action("alo", "M", "sell", 103, 5, 2)]
    for rule, picked in (("arrival", 5), ("cancels_first", 0)):
        b = Book()
        run_block(b, [Action("alo", "M", "sell", 101, 5, 1)], "arrival")
        fills = run_block(b, block(), rule)
        assert sum(f.qty for f in fills) == picked
    assert [a.kind for a in order_block(block(), "cancels_first")] == ["alo", "cancel", "ioc"]


def test_oi_cap_and_mark():
    b = Book(oi_cap=10)
    run_block(b, [Action("alo", "M", "sell", 100, 10, 1), Action("alo", "M2", "sell", 100, 11, 2)], "arrival")
    assert b.best() == (None, 100) and len(b.asks) == 1                # the 11-lot order breaks the cap
    assert run_block(b, [Action("ioc", "T", "buy", 100, 11)], "arrival") == []
    assert sum(f.qty for f in run_block(b, [Action("ioc", "T", "buy", 100, 10)], "arrival")) == 10
    assert mark_price(100.0, 130.0, 101.0) == 101.0
