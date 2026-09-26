import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tape"))
from firm_lob import ArrayBook, LimitOrderBook, MessageBook, Order, apply_tape, l2_lines  # noqa: E402
from firm_tape import TapeConfig, simulate  # noqa: E402


def test_priority_displayed_before_hidden_then_time():
    b = LimitOrderBook()
    b.add(Order(1, 1, 100, 300, visible=False))
    b.add(Order(2, 1, 100, 200))
    b.add(Order(3, 1, 100, 100))
    b.add(Order(4, 1, 99, 500))
    assert [o.ref for o in b.level_orders(1, 100)] == [2, 3, 1]
    assert b.top() == (100, 300, None, 0)             # hidden size not quoted
    b.reduce(2, 200)
    assert [o.ref for o in b.level_orders(1, 100)] == [3, 1] and b.get(2) is None
    b.remove(3)
    assert b.best(1) == 100 and b.best_visible(1) == 99 and b.depth(1, 5) == [(99, 500)]
    b.check()
    with pytest.raises(KeyError):
        b.add(Order(1, -1, 101, 10))


def test_array_and_tree_books_agree_on_a_simulated_session():
    tape = simulate(TapeConfig(seconds=120.0, news_at=None, seed=3))
    tree, arr = MessageBook(), ArrayBook(9000, 11000)
    n = 0
    for a, b in zip(apply_tape(tree, tape.msgs), apply_tape(arr, tape.msgs), strict=True):
        assert a.top() == b.top()
        if n % 50 == 0:
            assert l2_lines(a, 10) == l2_lines(b, 10)
        n += 1
    tree.book.check()
    assert n == len(tape.msgs) > 1000


def test_replace_and_fixture_consistent():
    m = MessageBook()
    m.apply("A", 1, 1, 100, 300)
    m.apply("A", 2, 1, 100, 200)
    m.apply("U", 1, price=101, qty=100, new_ref=7)
    assert m.depth(1, 5) == [(101, 100), (100, 200)]
    m.apply("D", 2)
    m.apply("E", 7, qty=100)
    assert m.top() == (None, 0, None, 0)
    lines = (HERE / "data" / "fixture_l2.txt").read_text().splitlines()
    assert len(lines) == 3 * 147 and lines[0] == "# 25"
