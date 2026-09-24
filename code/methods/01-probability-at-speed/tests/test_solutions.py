"""Numbers gate: every numerical answer printed in Book 4, Chapter 1 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_martingales import (
    MINUTES,
    NEWS,
    T_IMB,
    card_forecasts,
    card_table,
    close_paths,
    close_variances,
    hit_up_probability,
    problem,
    simulate_hits,
    tail_estimates,
    underreacting,
)

P = problem()
CARDS = card_table()


def test_text():
    assert CARDS["m0"] == 35
    t = tail_estimates()
    assert round(t["exact"] * 1e5, 2) == 3.17 and round(t["plain"] * 1e5) == 3
    assert round(t["plain_se"] * 1e5, 1) == 1.7 and round(t["tilted_se"] * 1e7, 1) == 2.1
    assert 75 < t["plain_se"] / t["tilted_se"] < 85                       # "eighty times smaller"
    assert abs(t["tilted"] - t["exact"]) < 3 * t["tilted_se"]
    # fig. day: the news moved the forecast by +0.48 on the plotted day
    day = close_paths(1, seed=11)[0]
    assert round(day[NEWS] - day[T_IMB], 2) == 0.48
    # fig. resolved: 2.7% at the news, 2.5% in the last ten minutes
    v = close_variances()
    assert round(100 * v["share_jump"], 1) == 2.7
    assert round(100 * (v["share_after"] - v["share_jump"]), 1) == 2.5
    # fig. stops: 10 points of probability lost at b = 10 by a 1-point drift
    assert round(100 * (hit_up_probability(10, 10) - hit_up_probability(10, 10, 0.49))) == 10


def test_tutorial_table():
    assert round(CARDS["honest_mean"], 3) == 0.001 and round(CARDS["under_mean"], 3) == 0.001
    assert round(CARDS["honest_slope"], 3) == -0.005
    assert round(CARDS["under_slope"], 3) == 0.661 and round(CARDS["theory_slope"], 3) == 0.667
    assert round(CARDS["under_t"], 1) == 45.9


def test_exercises():
    assert round(13 + 4 * (364 - 13) / 51, 2) == 40.53
    assert hit_up_probability(1, 3) == 0.75 and 0.75 * 1 - 0.25 * 3 == 0
    assert round(100 * 30 / 390, 1) == 7.7
    # exercise 6: slope (1 - a)/a on F_4 - 35 as well as on the previous revision
    m = card_forecasts(20_000, seed=9)
    f = underreacting(m, 0.6)
    x, y = f[:, 4] - 35, f[:, 5] - f[:, 4]
    assert abs(float(x @ y / (x @ x)) - 2 / 3) < 0.03


def test_problem():
    assert round(P["var_total"], 2) == 3.33 and round(P["sd_total"], 2) == 1.82
    assert round(100 * P["p_move_14c"], 1) == 64.1
    assert round(100 * P["share_noon"], 1) == 37.4
    assert round(100 * P["share_jump"], 1) == 2.7 and round(100 * P["share_after"], 1) == 5.2
    assert round(100 * P["sim_share_after"], 2) == 5.23
    assert round(P["corr_revisions"], 2) == 0.46
    assert round(P["sim_slope"], 2) == 0.98 and round(P["sim_t"]) == 72
    assert round(P["days_for_t2"]) == 16
    assert round(P["edge_per_share"], 3) == 0.120
    assert round(100 * P["share_after_ushape"], 1) == 9.8
    assert round(3.24 * 30 / 410, 3) == 0.237


def test_simulation_is_stable_under_finer_steps_and_ablation():
    """WRITING section 9: the named result is a variance decomposition; it must not depend on the
    time step (sampling the forecast every minute or every quarter-minute of variance), and each
    mechanism the text credits must matter: without the news the share after 15:50 falls to the
    diffusive 2.6%, without the last ten minutes to the news alone, 2.8%."""
    v = close_variances()
    per_min = v["per_min"]
    fine = np.repeat(per_min / 4, 4)            # the same day in quarter-minute steps
    after_fine = (fine[4 * T_IMB:].sum() + 0.3**2) / (fine.sum() + 0.3**2)
    assert abs(after_fine - v["share_after"]) < 1e-12
    no_news = close_variances(s_j=0.0)
    assert round(100 * no_news["share_after"], 1) == 2.6          # 10/390 of the diffusive part only
    no_tail = 0.3**2 / (per_min[:T_IMB].sum() + 0.3**2)
    assert round(100 * no_tail, 1) == 2.8                        # news only, over a shorter day
    # the optional-stopping formula survives simulation
    freq, _ = simulate_hits(10, 10, 0.49, 20_000, seed=3)
    assert abs(freq - hit_up_probability(10, 10, 0.49)) < 0.012
    assert MINUTES == 390 and math.isclose(sum(per_min), 3.24)
