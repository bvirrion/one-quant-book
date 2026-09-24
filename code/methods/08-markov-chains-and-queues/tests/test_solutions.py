"""Numbers gate: every numerical answer printed in Book 4, Chapter 8 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_queues import GRID, LAM, NU, depletion_cdf, fill_probability, mm1_simulation, problem, spread_chain

P = problem()
S = spread_chain()


def pct(x, k=1):
    return round(100 * x, k)


def test_text():
    assert (pct(P["p_fill"], 0), round(P["e_fill"])) == (73, 82) and pct(P["p_fill_a40"], 0) == 99
    assert [round(x, 3) for x in S["pi"]] == [0.676, 0.265, 0.059] and round(S["mean_ticks"], 2) == 1.38
    assert round(S["holding"][0], 2) == 0.5
    assert round(0.9 / 0.1) == 9 and round(0.95 / 0.05) == 19
    assert pct(P["p_up_80_20"]) == 95.4
    assert (pct(P["p_fill"]), pct(P["p_fill_sim"])) == (73.2, 73.4) and pct(P["p_fill_k20"]) == 99.3
    r = mm1_simulation(0.5, seed=14)
    assert abs(r["L"] - r["lamW"]) < 0.02 and abs(r["L"] - 1.0) < 0.05


def test_exercises():
    assert [round(x, 2) for x in S["holding"]] == [0.5, 0.17, 0.22]
    assert round(S["jump"][2, 1], 3) == 0.889
    assert (0.8 / 0.2, 1 / 0.2) == (4.0, 5.0)
    assert pct(P["p_reach40_from20"]) == 10.8
    pi, Q = S["pi"], S["Q"]
    assert (round(pi[0] * Q[0, 1], 2), round(pi[1] * Q[1, 0], 2)) == (1.35, 1.32)
    assert (round(P["mean_depletion_20"]), round(P["median_ask_depletion"]), pct(P["p_ask_by_60"])) == (200, 137, 15.6)
    assert 400 / 50 == 8


def test_problem():
    assert round(P["e_fill"], 1) == 81.7 and pct(P["p_ask_ever"]) == 99.6
    assert pct(P["p_fill_a40"]) == 99.0 and P["p_fill_a80"] > 0.9995
    assert pct(P["p_up_20_20"]) == 50.0 and round(P["exit_time_20"], 1) == 156.6


def test_interview():
    assert round(0.9 / 0.1) == 9 and round(0.81 / 0.1, 1) == 8.1 and 3 * 7 == 21


def test_time_step_and_ablation():
    """WRITING section 9. Uniformisation is exact up to its truncation: halving the time grid must
    not move the fill probability; and the mechanism credited (the ask queue can empty) is ablated
    by making the ask stable (joins faster than departures): the fill probability goes to one."""
    fine = np.linspace(0, 1200, 4801)
    from firm_queues import fill_time_cdf, race
    p_fine = race(fill_time_cdf(80, NU, 0.6, fine), depletion_cdf(LAM, NU, 20, fine), fine)
    assert abs(p_fine - P["p_fill"]) < 2e-4
    stable = race(fill_time_cdf(80, NU, 0.6, GRID), depletion_cdf(1.2, NU, 20, GRID), GRID)
    assert stable > 0.9 and fill_probability(80, 20) < 0.75
