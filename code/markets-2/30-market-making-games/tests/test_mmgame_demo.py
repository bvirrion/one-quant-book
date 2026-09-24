"""Tests of the Chapter 30 demo: chart data shapes and orderings."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mmgame_demo import distribution, one_game


def test_distribution_is_symmetric():
    d = dict(distribution())
    assert all(abs(d[s] - d[70 - s]) < 1e-12 for s in d)


def test_one_game_shape():
    value, mids, _ = one_game()
    assert value == 31 and len(mids) == 21 and mids[0] == 35.0
