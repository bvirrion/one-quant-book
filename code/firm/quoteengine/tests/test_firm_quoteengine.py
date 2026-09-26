import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_quoteengine as qe  # noqa: E402


def _live(e, acts):
    for a in acts:
        e.ack(a[1])


def test_new_then_nothing_then_move():
    e = qe.QuoteEngine()
    a = e.update(0.0, 1, [(100, 200), (99, 200)])
    assert [x[0] for x in a] == ["new", "new"]
    _live(e, a)
    assert e.update(0.1, 1, [(100, 200), (99, 200)]) == []            # already there: no message
    b = e.update(0.2, 1, [(101, 200), (100, 200)])
    assert ("cancel", 2) in b and any(x[0] == "new" and x[3] == 101 for x in b) and len(b) == 2


def test_size_decrease_amends_increase_adds():
    e = qe.QuoteEngine()
    _live(e, e.update(0.0, -1, [(101, 300)]))
    assert e.update(0.1, -1, [(101, 100)]) == [("amend", 1, 100)]
    e.ack(1)
    assert e.update(0.2, -1, [(101, 300)]) == [("new", 2, -1, 101, 200)]


def test_hysteresis_keeps_a_near_order():
    e = qe.QuoteEngine(min_move=2)
    _live(e, e.update(0.0, 1, [(100, 100)]))
    assert e.update(0.1, 1, [(101, 100)]) == []                        # within one tick: kept
    assert [x[0] for x in e.update(0.2, 1, [(102, 100)])] == ["cancel", "new"]


def test_throttle_drops_and_rederives():
    e = qe.QuoteEngine(rate=1.0, burst=2.0)
    a = e.update(0.0, 1, [(100, 100), (99, 100), (98, 100)])
    assert len(a) == 2 and e.stats["dropped"] == 1
    _live(e, a)
    b = e.update(1.0, 1, [(100, 100), (99, 100), (98, 100)])         # one token back: the missing level
    assert b == [("new", 3, 1, 98, 100)]


def test_cancel_fill_race_is_counted():
    e = qe.QuoteEngine()
    _live(e, e.update(0.0, 1, [(100, 100)]))
    e.update(0.1, 1, [])
    e.fill(1, 100)
    assert e.stats["races"] == 1 and 1 not in e.orders


def test_fixture_matches_the_reference():
    import csv

    import quoteengine_fixture as fx
    rows = fx.script()
    acts, _ = fx.replay(rows)
    d = pathlib.Path(__file__).resolve().parents[1] / "data"
    exp = [(int(r["step"]), r["action"]) for r in csv.DictReader(open(d / "fixture_expected.csv"))]
    assert acts == exp and len(exp) > 1000
