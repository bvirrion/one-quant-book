"""Tutorial of Book 4, Chapter 1: the printed steps reproduce the printed end state."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_martingales import DECK, card_forecasts, close_paths, stop_table, underreacting


def test_card_forecast_is_a_martingale_in_mean():
    m = card_forecasts(5000, seed=2)
    assert np.all(m[:, 0] == 35) and DECK.sum() == 364
    d = np.diff(m, axis=1)
    assert np.all(np.abs(d.mean(axis=0)) < 0.25)
    assert np.all((m[:, -1] >= 5) & (m[:, -1] <= 65))


def test_underreacting_keeps_the_endpoints():
    m = card_forecasts(100, seed=3)
    f = underreacting(m, 0.5)
    assert np.allclose(f[:, 0], m[:, 0]) and np.allclose(f[:, -1], m[:, -1])


def test_close_paths_shape_and_variance():
    p = close_paths(4000, seed=5)
    assert p.shape == (4000, 392)
    assert abs(p[:, -1].var() - 3.33) < 0.2


def test_stop_table_matches_theory():
    for row in stop_table(n=4000):
        assert abs(row[1] - row[2]) < 0.03 and abs(row[3] - row[4]) < 0.03
