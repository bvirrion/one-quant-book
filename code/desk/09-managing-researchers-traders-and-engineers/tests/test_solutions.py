"""Numbers gate: every numerical answer printed in Book 16, chapter 9 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_research as m  # noqa: E402

ps = m.ps


def r(x, d=2):
    return round(float(x), d)


def test_credit():
    c = m.credit()
    assert [r(x) for x in c["alone"]] == [22.77, 22.84, 4.55] and [r(x) for x in c["loo"]] == [2.46, 2.67, 4.64]
    assert [r(x) for x in c["orders"]["ABC"]] == [22.77, 2.59, 4.64] and [r(x) for x in c["shapley"]] == [12.63, 12.77, 4.61]
    assert r(c["loo"].sum()) == 9.77 and r(30 - c["loo"].sum()) == 20.23 and r(c["shapley"].sum()) == 30.0
    assert r(c["corr_ab"], 1) == 0.8
    assert [r(x, 1) for x in (2.46, 2.67, 4.64)] == [2.5, 2.7, 4.6]
    p = m.pool_split()
    assert [r(x) for x in p["leave-one-out"]] == [1.51, 1.64, 2.85] and [r(x) for x in p["Shapley"]] == [2.53, 2.55, 0.92]
    assert [r(x) for x in p["order ABC"]] == [4.55, 0.52, 0.93]
    c12 = m.credit(seed=12)
    assert [r(x, 1) for x in c12["loo"]] == [1.0, 2.7, 13.0] and [r(x, 1) for x in c12["shapley"]] == [7.8, 9.5, 12.7]


def test_toy_game():
    table = {(): 0, (0,): 20, (1,): 20, (2,): 10, (0, 1): 20, (0, 2): 30, (1, 2): 30, (0, 1, 2): 30}

    def v(S):
        return table[tuple(sorted(S))]
    assert list(ps.leave_one_out(v, 3)) == [0, 0, 10] and np.allclose(ps.shapley(v, 3), [10, 10, 10])


def test_projects_and_trials():
    fut, mom = m.PROJECTS[0], m.PROJECTS[4]
    assert r(ps.expected_net(fut)) == 2.1 and r(ps.expected_net(fut) / fut.cost) == 1.4 and r(ps.expected_net(mom)) == -0.28
    d = m.deflated()
    assert (r(d["psr"], 3), r(d["dsr"], 2), r(d["sr0_annual"], 2)) == (0.996, 0.59, 1.09)
    assert next(t for t in range(40, 100) if m.deflated(trials=t)["dsr"] < 0.5) == 70
    assert r(m.deflated(trials=200)["dsr"], 2) == 0.34


@pytest.mark.reference
def test_portfolio():
    p = m.portfolio()
    assert p["chosen"] == ["execution model v2", "new futures signal", "auction imbalance model", "options flow features",
                           "crypto basis book", "borrow-cost signal"]
    assert (r(p["cost"], 1), r(p["expected"]), r(p["greedy_mean"]), r(100 * p["greedy_p_loss"], 1), r(p["random_mean"]),
            r(100 * p["random_p_loss"], 1)) == (10.0, 8.15, 8.08, 28.5, 3.65, 44.8)


def test_small_runs():
    p = m.portfolio(n=2000)
    assert p["greedy_mean"] > p["random_mean"] and p["greedy_p_loss"] < p["random_p_loss"]
