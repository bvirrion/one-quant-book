import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_indexevent import event_path, event_push, predict, reconstitute  # noqa: E402


def test_band_rule_by_hand():
    cap = np.array([100.0, 90, 80, 70, 60, 50, 40, 30])
    members = np.array([1, 1, 0, 1, 0, 0, 1, 0], bool)          # size 4, band 1: join if rank <= 3, leave if rank > 5
    new, add, drop = reconstitute(cap, members, 4, 1)
    assert add.tolist() == [0, 0, 1, 0, 0, 0, 0, 0] and drop.tolist() == [0, 0, 0, 0, 0, 0, 1, 0]
    assert new.tolist() == [1, 1, 1, 1, 0, 0, 0, 0]


def test_prediction_certain_far_from_the_cut():
    cap = np.r_[np.full(10, 1000.0), np.full(10, 1.0)]
    p = predict(cap, np.full(20, 0.01), np.zeros(20, bool), 10, 0, 5, 50, np.random.default_rng(1))
    assert p[:10].tolist() == [1.0] * 10 and p[10:].tolist() == [0.0] * 10


def test_push_and_path():
    assert abs(event_push(0.25e6, 1e6, 0.02) - 0.7 * 0.02 * 0.5) < 1e-15
    path = event_path(0.04, 0.5, 0.5, pre=2, run=2, post=2)
    assert np.allclose(path, [0.01, 0.02, 0.02, 0.03, 0.04, 0.03, 0.02])
