"""Acceptance tests for firm.careerdec."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_careerdec as fd  # noqa: E402


def test_scale_and_value():
    s = fd.scale([[10, 5], [20, 1]], [True, False])
    assert s.tolist() == [[0.0, 0.0], [1.0, 1.0]]
    assert fd.value(s, fd.swing_weights([3, 1])).tolist() == [0.0, 1.0]


def test_dominance():
    m = [[10, 1], [20, 1], [5, 3]]
    assert fd.dominated(m, [True, False]) == [0, 2] and fd.dominated(m, [True, True]) == [0]


def test_rank_acceptability_symmetric():
    s = np.array([[1.0, 0.0], [0.0, 1.0]])
    ra = fd.rank_acceptability(s, 20_000, np.random.default_rng(0))
    assert ra.sum(axis=1) == pytest.approx([1.0, 1.0]) and abs(ra[0, 0] - 0.5) < 0.02


def test_flip():
    s = np.array([[1.0, 0.0], [0.0, 1.0]])
    shift, b = fd.flip_shift(s, [0.6, 0.4], 0, step=0.01)
    assert b == 1 and shift == pytest.approx(-0.11)
    assert fd.flip_shift(np.array([[1.0, 1.0], [0.0, 0.0]]), [0.5, 0.5], 0) is None
