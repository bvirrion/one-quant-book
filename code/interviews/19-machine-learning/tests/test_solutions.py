"""Numbers gate: every numerical answer printed in Book 18, chapter 19 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_ml import boosting_on_noise, lasso_instability, leak_study, trade_threshold


def test_small_runs():
    res = leak_study(range(3), n=600)
    assert (res[:, 0] > res[:, 1]).all()


@pytest.mark.reference
def test_leak_full():
    res = leak_study(range(20))
    assert round(res[:, 0].mean(), 2) == 0.26 and round(res[:, 1].mean(), 2) == -0.61
    assert (res[:, 0] > 0).all() and (res[:, 1] < 0).all()


def test_leak_properties():
    res = leak_study(range(5))
    assert (res[:, 0] > 0).mean() >= 0.8 and (res[:, 1] < 0).all()


def test_lasso_instability():
    share, ridge = lasso_instability(range(200))
    assert round(share, 2) == 0.63
    assert np.allclose(ridge, [0.95, 0.95], atol=0.01)


def test_boosting_on_noise():
    train, test = boosting_on_noise(0)
    assert round(train, 2) == 0.65 and round(test, 2) == -0.18


def test_threshold():
    assert round(trade_threshold(1, 2), 3) == 0.667
    assert trade_threshold(1, 1) == 0.5


def test_accuracy_se():
    assert round(np.sqrt(0.55 * 0.45 / 250), 3) == 0.031


def test_worked_answers():
    toxic, flagged, hit = 10_000 * 3 // 100, 500, 240
    assert toxic == 300 and hit / toxic == 0.8 and hit / flagged == 0.48
    assert round((hit / flagged) / 0.03) == 16 and flagged - hit == 260
    assert 2520 // 20 == 126 and round(np.sqrt(20), 1) == 4.5
    rng = np.random.default_rng(19)
    r = rng.standard_normal((2000, 2540))
    fwd = np.lib.stride_tricks.sliding_window_view(r, 20, axis=1).sum(axis=2)[:, :2520]
    naive = fwd.mean(axis=1) / (fwd.std(axis=1) / np.sqrt(2520))
    assert abs(naive.std() - np.sqrt(20)) < 0.4
