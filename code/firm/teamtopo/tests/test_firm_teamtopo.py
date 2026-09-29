import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_teamtopo as tp  # noqa: E402

S = [tp.Service("a", 3.0, 1.0), tp.Service("b", 1.0, 2.0), tp.Service("c", 2.0, 0.0)]
DEPS = [("a", "b"), ("b", "c"), ("a", "c")]


def test_cross_edges_and_coordination():
    d = tp.Design({"a": "t1", "b": "t1", "c": "t2"}, {"t1": 2, "t2": 1})
    assert tp.cross_edges(DEPS, d) == [("b", "c"), ("a", "c")] and tp.coordination(S, DEPS, d) == 4.0


def test_pages_bus_factor_and_move():
    d = tp.Design({"a": "t1", "b": "t1", "c": "t2"}, {"t1": 2, "t2": 1}, backups={"c": 1})
    assert tp.pages(S, d) == {"t1": 1.5, "t2": 0.0}
    assert tp.bus_factor(S, d) == (2, ["a", "b", "c"])
    m = tp.move(d, "t1", "t2")
    assert m.team_size == {"t1": 1, "t2": 2} and tp.bus_factor(S, m) == (1, ["a", "b"])
    r = tp.report(S, DEPS, d)
    assert r["cross_edges"] == 2 and r["pages_mean"] == 1.0 and r["teams"] == 2
