"""Numbers gate: every numerical answer printed in Book 18, chapter 20 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_case import (
    BETA_BP,
    HALF_SPREAD_BP,
    SIGMA_BP,
    clean,
    data_checks,
    generate,
    imbalance_slope,
    lag1_autocorr,
    next_returns,
)


def test_small_runs():
    df = generate(seed=3, stocks=8, days=13, minutes=60, n_dup=5, n_crossed=4)
    chk = data_checks(df)
    assert chk["duplicates"] == 5 and chk["crossed"] == 4 and chk["splits"] == [(7, 12)]
    assert data_checks(clean(df)) == {"duplicates": 0, "crossed": 0, "splits": []}


def test_defects_and_effect():
    df = generate()
    assert len(df) == 20 * 20 * 390 + 40
    assert data_checks(df) == {"duplicates": 40, "crossed": 15, "splits": [(7, 12)]}
    d = next_returns(clean(df))
    b, se = imbalance_slope(d)
    assert round(b, 2) == 0.48 and round(se, 3) == 0.022 and round(b / se) == 22
    assert round(lag1_autocorr(d), 3) == -0.000


def test_bounce():
    d = next_returns(clean(generate()), "trade")
    roll = -(HALF_SPREAD_BP**2) / (SIGMA_BP**2 + 2 * HALF_SPREAD_BP**2)
    assert round(roll, 3) == -0.209
    assert round(lag1_autocorr(d), 2) == -0.21


def test_estimate_covers_plant_over_seeds():
    hits = 0
    for seed in range(10):
        d = next_returns(clean(generate(seed=100 + seed, stocks=10, days=10)))
        b, se = imbalance_slope(d)
        hits += abs(b - BETA_BP) < 2 * se
    assert hits >= 8


def test_tradability():
    gross = BETA_BP * 0.9  # mean imbalance above 0.8 is 0.9
    assert round(gross, 2) == 0.45 and 2 * HALF_SPREAD_BP == 6.0
    assert round(gross / (2 * HALF_SPREAD_BP), 3) == 0.075


def test_r2_tiny():
    r2 = (BETA_BP**2 / 3) / (BETA_BP**2 / 3 + SIGMA_BP**2)
    assert round(100 * r2, 2) == 0.33
    assert np.isclose(BETA_BP**2 / 3, 1 / 12)


def test_calendar_case():
    from iv_case import calendar_cells_false_alarm
    from scipy.stats import norm

    assert round(2 * norm.sf(3.1), 4) == 0.0019
    assert round(calendar_cells_false_alarm(60, 3.1), 2) == 0.11
    assert round(norm.isf(0.025 / 60), 2) == 3.34  # Bonferroni threshold for 60 cells at 5%


def test_worked_answers():
    n = (3 * 5 / 0.2) ** 2
    assert round(3 * 5 / 0.2) == 75 and round(n) == 5625 and round(n / 390, 1) == 14.4
    rng = np.random.default_rng(20)
    ts = []
    for _ in range(300):
        x = rng.standard_normal(5625)
        y = 0.2 * x + 5 * rng.standard_normal(5625)
        b = (x @ y) / (x @ x)
        se = np.std(y - b * x) / np.sqrt(x @ x)
        ts.append(b / se)
    assert abs(np.mean(ts) - 3) < 0.15
