"""Numbers in the solutions of Book 3, Chapter 21."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_perpdex as m
from firm_blockbook import Action, Book, run_block


def test_exercises():
    for rule, filled, rest in (("arrival", 5, [103]), ("cancels_first", 0, [103])):
        b = Book()
        run_block(b, [Action("alo", "M", "sell", 101, 5, 1)], "arrival")
        fills = run_block(b, [Action("ioc", "T", "buy", 101, 5), Action("cancel", "M", oid=1),
                              Action("alo", "M", "sell", 103, 5, 2)], rule)
        assert sum(f.qty for f in fills) == filled and [o[0] for o in b.asks] == rest
    assert round(100 * 0.5 / 20, 2) == 2.5 and round(100 * 2 / 3 * 0.025, 2) == 1.67
    assert round(m.squeeze_loss(4e6, 1.0, m.BUFFER_3X) / 1e6, 2) == 3.56
    assert m.replay("arrival", p_taker_first=0.9)[-1] == (1000, 980, 1480.0)
    assert m.replay("cancels_first", p_taker_first=0.9)[-1] == (1000, 0, 0.0)


def test_problem():
    b = m.BUFFER_3X
    assert round(100 / 6, 1) == 16.7 and round(10e6 * b / 1e6, 2) == 1.11
    assert round(m.squeeze_loss(10e6, 1.0, b) / 1e6, 2) == 8.89 and round(m.squeeze_loss(10e6, 4.0, b) / 1e6, 2) == 38.89
    assert round(m.oi_cap_for(5e6, 5.0, b) / 1e6, 2) == 1.02
    assert round(m.squeeze_loss(2e6, 4.0, b) / 1e6, 2) == 7.78
