"""Numbers gate: every number printed in Book 14, chapter 21 (text and solutions)."""
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_chain as c  # noqa: E402

cn = c.cn


def test_engines():
    assert len(c.ENGINES) == 8 and c.NODE_CITY[c.SOURCE] == "tokyo"


@pytest.mark.reference
def test_propagation():
    p = c.propagation()
    assert [round(x, 1) for x in p["flood"]] == [85.0, 99.5]
    assert [round(x, 1) for x in p["sqrt"]] == [113.9, 149.0]
    tails = [round(max(cn.spread(c.GRAPH, c.SOURCE, m)), 1) for m in ("flood", "sqrt")]
    assert tails == [158.5, 326.5] and c.N_NODES == 600 and c.PEERS == 8
    g16 = cn.Graph([c.CITIES[x] for x in c.NODE_CITY], 16, seed=c.SEED)
    a = cn.spread(g16, c.SOURCE)
    t50, t90 = cn.reach_time(a, 0.5), cn.reach_time(a, 0.9)
    assert (round(t50, 1), round(t90, 1)) == (80.3, 89.5)
    assert (round(p["flood"][0] - t50, 1), round(p["flood"][1] - t90, 1)) == (4.7, 10.0)


@pytest.mark.reference
def test_leaders():
    legs = {k: c.to_leader(k) for k in c.CITIES}
    f, s, t = legs["frankfurt"], legs["singapore"], legs["tokyo"]
    assert (round(f["gossip"], 1), round(f["direct"], 1), f["engine"]) == (83.5, 69.5, "frankfurt")
    assert (round(s["gossip"], 1), round(s["direct"], 1), round(s["gossip"] - s["direct"])) == (58.9, 39.9, 19)
    assert (round(t["gossip"], 1), round(t["direct"], 1)) == (40.0, 1.0)
    gaps = [round(x["gossip"] - x["direct"]) for x in legs.values()]
    assert (min(gaps), max(gaps)) == (14, 39)
    assert round(max(x["gossip"] for x in legs.values()), 1) == 99.5
    assert round(cn.one_way_ms(c.CITIES["tokyo"], c.CITIES["frankfurt"], 1.0), 1) == 45.6


@pytest.mark.reference
def test_timely():
    g, d = c.mean_timely(150)
    assert (round(100 * g), round(100 * d)) == (48, 61)
    g, d = c.mean_timely(300)
    assert (round(100 * g, 1), round(100 * d, 1)) == (74.0, 80.5)
    assert 4 * 300 == 1200


def test_small_runs():
    g = cn.Graph([c.CITIES[x] for x in c.NODE_CITY[:40]], 4, seed=2)
    a = cn.spread(g, 0)
    b = cn.spread(g, 0, "sqrt")
    assert all(x <= y + 1e-9 for x, y in zip(a, b, strict=True))
    assert c.timely_rates((0, 150))[-1][1:] == (1.0, 1.0)
