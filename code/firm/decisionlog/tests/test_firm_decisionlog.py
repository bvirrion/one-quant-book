import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_decisionlog as dl  # noqa: E402


def test_brier_and_murphy_identity():
    p = np.array([0.15, 0.15, 0.85, 0.85, 0.55, 0.55])          # constant within bins: the identity is exact
    y = np.array([0, 1, 1, 1, 0, 1])
    d = dl.murphy(p, y, 10)
    assert d["brier"] == pytest.approx(d["reliability"] - d["resolution"] + d["uncertainty"])
    assert dl.calibration(p, y, 10)[0] == (pytest.approx(0.15), 0.5, 2)


def test_aggregation():
    P = np.array([[0.6, 0.2], [0.8, 0.4]])
    assert np.allclose(dl.aggregate(P, "mean"), [0.7, 0.3])
    lo = dl.aggregate(P, "logodds")
    assert lo[0] == pytest.approx(float(dl.expit((dl.logit(0.6) + dl.logit(0.8)) / 2)))
    assert dl.aggregate(P, "extremised", 2.0)[0] > lo[0]


def test_outcome_bias():
    e = [dl.Entry("a", "x", 0.7, 1, 0.4), dl.Entry("b", "x", 0.7, 0, 0.4), dl.Entry("c", "x", 0.3, 0, -0.4)]
    assert dl.outcome_bias(e) == {"positive_ev": 2, "lost": 1, "share_misjudged_by_outcome": 0.5}
