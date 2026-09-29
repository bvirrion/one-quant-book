import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_dissem as d  # noqa: E402


def test_unicast_by_hand():
    servers = [d.Server("a", (2, 1)), d.Server("b", (1,), speed=2.0)]
    t = d.unicast_us(servers, c_centre=5, c_send=10, jitter=0)
    assert t[d.Member("a", 0, 0)] == 15 and t[d.Member("a", 0, 1)] == 25 and t[d.Member("a", 1, 0)] == 15
    assert t[d.Member("b", 0, 0)] == 10 + 20                    # second in the centre's order, a slower server
    f = d.fairness(t)
    assert (f["first"], f["last"], f["spread"]) == (15, 30, 15)


def test_multicast_is_flat_and_randomiser_breaks_ranks():
    servers = [d.Server(f"s{k}", (10, 10, 10)) for k in range(4)]
    m = d.fairness(d.multicast_us(servers, c_send=10, jitter=0))
    assert m["spread"] == 0 and m["first"] == 10
    assert d.rank_stability(servers, ticks=20, jitter=1.0) > 0.99
    assert abs(d.rank_stability(servers, ticks=40, jitter=1.0, shuffle=True)) < 0.1


def test_race():
    t = {"x": 0.0, "y": 50.0, "z": 0.0}
    assert d.race_win(t, "x", "y") == 1.0
    assert d.race_win(t, "x", "z") == pytest.approx(0.5, abs=0.02)
    rng = np.random.default_rng(0)
    assert len(d.unicast_us([d.Server("a", (3,))], rng=rng, shuffle=True)) == 3
