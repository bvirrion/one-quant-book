"""Tutorial of Book 4, Chapter 3: the printed steps reproduce the printed end state."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_ito import SIG_D, backtest, gbm_quantiles, trend_signal


def test_trend_signal_has_unit_variance_on_a_random_walk():
    rng = np.random.default_rng(1)
    s = np.concatenate([[0.0], np.cumsum(SIG_D * rng.standard_normal(200_000))])
    th = trend_signal(s)[100:]
    assert abs(th.var() - 1) < 0.03


def test_backtest_curves_start_at_zero_and_split():
    b = backtest(days=1000, seed=3)
    assert b["honest"][0] == 0 and b["cheat"][0] == 0 and b["cheat"][-1] > b["honest"][-1]


def test_gbm_rows():
    rows = gbm_quantiles(n=20_000)
    assert len(rows) == 11 and abs(rows[10][1] / rows[10][2] - 1) < 0.05
