"""Numbers gate: every numerical answer printed in Book 18, chapter 3 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_apply import expected_max_normal, leaderboard_inflation, null_best_sharpe, recruiter_expected_fee, recruiter_fee


def test_cv_reading_time():
    seconds = 4 * 3600 / 400
    assert seconds == 36


def test_expected_max_values():
    assert round(expected_max_normal(2), 4) == round(1 / math.sqrt(math.pi), 4)
    assert round(expected_max_normal(10), 2) == 1.54
    assert round(expected_max_normal(60), 2) == 2.32
    assert round(expected_max_normal(100), 2) == 2.51
    assert round(expected_max_normal(400), 2) == 2.97
    # the asymptotic sqrt(2 ln k) overstates at these sizes
    assert round(math.sqrt(2 * math.log(400)), 2) == 3.46


def test_expected_max_simulation():
    for k in (10, 60, 400):
        est = np.mean([np.random.default_rng(s).standard_normal((5_000, k)).max(axis=1).mean() for s in range(10)])
        assert abs(est - expected_max_normal(k)) < 0.01


def test_q4_leaderboard():
    assert round(leaderboard_inflation(400, 0.01), 4) == 0.0297
    # the true skill spread among the top: winner's expected public edge is three noise sds


def test_q5_recruiter():
    assert recruiter_fee(150_000, 0.20) == 30_000
    # a 10k higher base raises the fee by 2k; a 10% risk of losing the placement costs 3k in expectation
    assert recruiter_fee(160_000, 0.20) - recruiter_fee(150_000, 0.20) == 2_000
    assert round(recruiter_expected_fee(160_000, 0.20, 0.9)) == 28_800
    assert round(recruiter_expected_fee(160_000, 0.20, 0.9) - recruiter_fee(150_000, 0.20)) == -1_200


def test_q7_best_backtest():
    assert round(null_best_sharpe(60, 5), 2) == 1.04
    assert round(1 / math.sqrt(5), 3) == 0.447
    # how many standard errors above the null expectation is 2.4?
    assert round((2.4 - null_best_sharpe(60, 5)) / (1 / math.sqrt(5)), 1) == 3.0


def test_worked_answers():
    gross = 0.9 * 0.10
    costs = 100 * 5e-4
    assert round(gross, 3) == 0.09 and round(costs, 3) == 0.05
    assert round((gross - costs) / 0.10, 2) == 0.4
    assert round((0.085 - 50 * 5e-4) / 0.10, 2) == 0.6
    assert round(12 / 2000 * 100, 1) == 0.6


def test_figure_bestof():
    import csv

    import fig_iv_bestof

    fig_iv_bestof.main()
    rows = list(csv.DictReader(open(fig_iv_bestof.OUT / "bestof.csv")))
    assert all(float(r["best"]) <= float(r["rule"]) for r in rows)
    assert round(expected_max_normal(400), 2) == 2.97
