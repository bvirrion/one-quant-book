import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_chainnet as c  # noqa: E402


def test_engines_and_chooser():
    e = c.load_engines()
    assert len(e) == 8 and all(x.source and x.as_of for x in e)
    fra = (50.11, 8.68)
    assert c.choose_engine(e, fra).region == "frankfurt"
    assert c.one_way_ms((0.0, 0.0), (0.0, 0.0)) == 0.0


def test_spread_line_graph_by_hand():
    g = c.Graph([(0.0, 0.0)] * 4, 1, factor=1.0, hop_ms=5.0, seed=0)
    g.adj = {0: {1}, 1: {0, 2}, 2: {1, 3}, 3: {2}}
    g.edges = {(i, j): 5.0 for i in g.adj for j in g.adj[i]}
    assert c.spread(g, 0, "flood") == [0.0, 5.0, 10.0, 15.0]
    # sqrt mode on a line: each node has at most 2 peers, pushes to ceil(sqrt(2)) = 2, so the same
    assert c.spread(g, 0, "sqrt") == [0.0, 5.0, 10.0, 15.0]
    assert c.reach_time([0, 5, 10, 15], 0.5) == pytest.approx(7.5)


def test_sqrt_is_slower_and_timely():
    e = c.load_engines()
    g = c.Graph([(x.lat, x.lon) for x in e] * 20, 8, seed=2)
    f, s = c.spread(g, 0, "flood"), c.spread(g, 0, "sqrt")
    assert c.reach_time(s, 0.9) >= c.reach_time(f, 0.9)
    tok, fra = (35.68, 139.76), (50.11, 8.68)
    eng = c.choose_engine(e, fra)
    assert c.timely(tok, eng, fra, 100.0) and not c.timely(tok, eng, fra, 50.0)
