import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_altstrat import diffuse, measure, nowcast_slope, pre_event_book  # noqa: E402


def test_measure_and_slope():
    rng = np.random.default_rng(0)
    s = rng.standard_normal(20000)
    m = measure(s, 1.0, rng)
    assert abs(nowcast_slope(m, s) - 0.5) < 0.02                   # var s / (var s + var noise)


def test_diffusion_moves_the_jump_earlier_and_keeps_the_total():
    R = np.zeros((20, 2))
    R[15, 0] = 0.06
    out = diffuse(R, [(15, 0)], np.array([0.03, 0.03]), 0.5, 10, [2.0], 0.5)
    move = 0.5 * 0.03 * 0.5 * 2.0
    assert abs(math.log1p(out[5, 0]) - move) < 1e-12
    assert abs(math.log1p(out[5, 0]) + math.log1p(out[15, 0]) - math.log1p(0.06)) < 1e-12


def test_book_by_hand():
    W = pre_event_book([(5, 0), (6, 1)], [1.0, -3.0], 2, 8, 2)
    assert W[3].tolist() == [1.0, 0.0] and W[4].tolist() == [0.25, -0.75] and W[5].tolist() == [0.0, -1.0]
    assert W[6].tolist() == [0.0, 0.0]
