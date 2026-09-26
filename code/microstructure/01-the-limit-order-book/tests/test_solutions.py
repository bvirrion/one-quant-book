"""Numbers gate: every numerical answer printed in Book 10, chapter 1 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_lob import (  # noqa: E402
    best_survival,
    depth_profile,
    event_mix,
    expected_wait,
    fill_probability,
    joiners,
    queue_mc,
    session,
    tree_vs_array,
    zi_market,
)


def r(x, d=2):
    return round(float(x), d)


def test_session_statistics():
    m = event_mix(session())
    assert (m["messages"], r(m["per_second"], 1), r(100 * m["add"], 1), r(100 * m["cancel"], 1),
            r(100 * m["execute"], 1)) == (31535, 8.8, 49.7, 47.8, 2.5)
    assert (r(m["messages_per_trade"], 0), r(100 * m["share_executed"], 1), r(m["median_life"], 1),
            r(m["median_life_executed"], 1), r(m["median_life_cancelled"], 1)) == (40.0, 3.8, 15.5, 24.9, 15.3)
    s = best_survival(session())
    assert (r(s["bid"][0], 1), r(s["ask"][0], 1)) == (4.5, 4.8)
    j = joiners(session())
    assert (j["orders"], j["median_ahead"], r(100 * j["traded"], 0), r(100 * j["filled"], 0)) == (2834, 1400.0, 13.0, 10.0)
    d = depth_profile(session())
    assert list(d[0, :3].round(0)) == [1366, 1508, 1333] and d[0].argmax() == 1 and d[1].argmax() == 1
    assert tree_vs_array(session()) == (3154, 0)


def test_fill_probability():
    assert [r(fill_probability(n, 2.0, 0.05, 0.05), 3) for n in (0, 1, 5, 12)] == [0.976, 0.952, 0.870, 0.755]
    assert abs(queue_mc(5, 2.0, 0.05, 0.05) - fill_probability(5, 2.0, 0.05, 0.05)) < 0.01
    assert r(expected_wait(5, 2.0, 0.05), 2) == 2.83


def test_zero_intelligence():
    sf, no = zi_market(improve=True), zi_market(improve=False)
    assert (r(sf["spread"]), r(sf["depth"])) == (2.55, 2.72)
    assert r(no["spread"], 0) > 1000                      # without improvement the two sides drift apart
    for n in (1, 3, 5, 8):                                # the proposition holds where improvement is off ...
        assert abs(no["fill"][n][0] - fill_probability(n, 2.0, 0.05, 0.05)) < 0.03
    assert (r(sf["fill"][1][0], 3), r(sf["fill"][5][0], 3), r(sf["fill"][8][0], 3)) == (0.912, 0.672, 0.535)
    assert all(sf["fill"][n][0] < fill_probability(n, 2.0, 0.05, 0.05) for n in range(1, 10))   # ... not here


def test_exercises():
    # exercise 2: an order behind 3 orders; mu = 1, theta = 0.1, nu = 0.2
    assert r(fill_probability(3, 1.0, 0.1, 0.2), 3) == 0.524
    # exercise 4: price-indexed array, 1% band on a 100.00 stock with a one-cent tick
    assert 2 * round(100.00 * 0.01 / 0.01) + 1 == 201
    # exercise 5: expected wait behind 10 with mu = 0.5/s, theta = 0.02
    assert r(expected_wait(10, 0.5, 0.02), 1) == 18.5


def test_exercise_7_and_problem():
    slow = zi_market(mu=1.0)
    assert (r(slow["spread"]), r(slow["depth"]), r(slow["fill"][5][0], 3)) == (1.64, 3.29, 0.602)
    assert r(fill_probability(5, 1.0, 0.05, 0.05), 3) == 0.769
    sf = zi_market(improve=True)
    assert round(100 * (1 - sf["fill"][5][0] / fill_probability(5, 2.0, 0.05, 0.05))) == 23
    assert round(100 * (1 - sf["fill"][8][0] / fill_probability(8, 2.0, 0.05, 0.05))) == 35
    # exercise 1: a market sell of 450 against 300, 200, 200 at the best bid
    assert (450 - 300, 200 - (450 - 300) + 200) == (150, 250)
