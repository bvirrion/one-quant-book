"""Numbers gate: every numerical answer printed in Book 4, Chapter 29 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import qm_games as q  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_games_and_single_unit():
    mw = q.multiplicative_weights(q.RPS)
    assert [r(v, 3) for v in mw["x"]] == [0.25, 0.502, 0.248] and r(mw["gap"], 3) == 0.005
    assert np.allclose(q.RPS @ np.array([0.25, 0.5, 0.25]), 0)
    br = q.best_response_curve()
    assert (br["best"], r(br["eq"])) == (0.64, 0.64)
    e = q.equivalence()
    assert (r(e["first"][0], 4), r(e["second"][0], 4), r(e["english"][0], 4), r(e["dutch"][0], 4)) == (0.6665, 0.6665, 0.6715, 0.6614)
    assert r(e["first"][2], 3) == 0.2
    g2, g5 = q.reserve_gain(2), q.reserve_gain(5)
    assert (g2["rstar"], r(g2["with"] * 12, 6), r(g2["unsold"])) == (0.5, 5.0, 0.25)
    assert (r(g5["with"], 4), r(g5["without"], 4), r(100 * (g5["with"] / g5["without"] - 1), 1), r(100 * g5["unsold"], 1)) == (0.6719, 0.6667, 0.8, 3.1)
    assert r(g5["sim_with"], 4) == 0.672 and r(100 * (g2["with"] / g2["without"] - 1)) == 25.0


def test_multiunit_and_curse():
    t = q.treasury_switch()
    u, p = t["uniform"], t["payasbid"]
    assert (t["theory"], r(u["revenue"], 4), r(p["revenue"], 4)) == (1.0, 0.9994, 0.9999)
    assert (r(u["winning_bid_spread"], 3), r(p["winning_bid_spread"], 3), r(u["revenue_sd"], 3), r(p["revenue_sd"], 3)) == (0.167, 0.087, 0.378, 0.16)
    assert [r(t["pab_bid_at"][v]) for v in (0.5, 0.8, 1.0)] == [0.36, 0.54, 0.6]
    w = q.winners_curse()
    assert (r(w["naive"]["profit"], 3), r(w["naive"]["p_loss"]), r(w["expected_max_error"], 3)) == (-0.067, 0.97, 0.067)
    assert abs(w["adjusted"]["profit"]) < 3 * w["adjusted"]["profit_se"]
    s = q.nonuniform_shading()
    assert [r(v, 4) for v in s["numeric"]] == [0.2667, 0.5333, 0.8]


def test_information():
    k = q.kelly_growth(0.6)
    assert (r(k["hx"], 3), r(k["without"], 3), r(k["with"], 3), r(k["mi"], 3)) == (1.846, -0.165, 0.198, 0.363)
    assert abs(k["gain"] - k["mi"]) < 1e-12 and r(1 / -k["without"], 1) == 6.1
    assert r(sum(1 / q.ODDS), 2) == 1.12 and r(100 * (1 - 1 / sum(1 / q.ODDS)), 0) == 11.0
    s = q.simulate_races(0.6)
    assert (r(s["gain"], 3), r(s["gain_se"], 3)) == (0.363, 0.002)
    assert abs(q.kelly_growth(0.25)["mi"]) < 1e-12 and abs(q.kelly_growth(1.0)["mi"] - k["hx"]) < 1e-12


def test_exercises():
    assert (r(0.9 * 0.7), r(9 / 11, 3), r(math.log2(6), 3)) == (0.63, 0.818, 2.585)
    J = np.zeros((6, 2))
    for f in range(6):
        J[f, f % 2] = 1 / 6
    assert abs(q.mutual_information(J) - 1.0) < 1e-12
    x = 3 / 7
    assert abs((3 * x - 2 * (1 - x)) - 1 / 7) < 1e-12 and abs((-x + (1 - x)) - 1 / 7) < 1e-12


def test_auction_size_and_clock_tick():
    """WRITING section 9: halving the clock tick halves the English and Dutch deviations from revenue equivalence, and
    doubling the number of bidders moves revenue to (n-1)/(n+1)."""
    e1 = q.equivalence(n_auctions=400_000, tick=0.01)
    e2 = q.equivalence(n_auctions=400_000, tick=0.005)
    d1 = e1["english"][0] - e1["dutch"][0]
    d2 = e2["english"][0] - e2["dutch"][0]
    assert 1.8 < d1 / d2 < 2.2
    e10 = q.equivalence(n=10, n_auctions=400_000, tick=0.001)
    assert abs(e10["second"][0] - 9 / 11) < 0.001
