import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_carrystrat import (  # noqa: E402
    book,
    curve_carry,
    dividend_carry,
    forward_discount,
    rank_weights,
    scale,
    skew_monthly,
    windows,
)


def test_carry_measures():
    assert math.isclose(curve_carry(math.log(100), math.log(98), 21), math.log(100 / 98) * 12)
    assert math.isclose(forward_discount(0.0, -0.01, 63), 0.04)
    assert math.isclose(dividend_carry(0.03, 0.05), -0.02)


def test_rank_weights_by_group():
    w = rank_weights(np.array([[3.0, 1.0, 2.0, 10.0, 20.0]]), np.array([0, 0, 0, 1, 1]))
    assert np.allclose(w[0], [0.5, -0.5, 0.0, -0.5, 0.5])


def test_book_scale_windows_skew():
    r = np.array([[0.0, 0.0], [0.01, -0.01], [0.02, 0.0]])
    w = np.array([[0.5, -0.5], [0.5, -0.5], [0.0, 0.0]])
    pnl = book(r, w, 0.001)
    assert np.allclose(pnl, [-0.001, 0.01, 0.01 - 0.001])
    assert windows(pnl, [(1, 3)]) == [float(pnl[1] + pnl[2])]
    x = np.random.default_rng(0).standard_normal(2520) * 0.01
    assert math.isclose(scale(x, 0.1).std() * math.sqrt(252), 0.1)
    y = np.zeros(210)
    y[0] = -1.0
    assert skew_monthly(y) < -2
