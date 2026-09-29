import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_gardenleave as gl  # noqa: E402


def test_identities():
    P, L, lam, r = 20.0, 0.5, math.log(2) / 1.0, 0.1
    assert math.isclose(gl.protected(P, L, lam, r, 1.0) + gl.loss_if_start(P, L, lam, r, 1.0), L * P / (lam + r))
    assert math.isclose(gl.leave_cost(1.0, 0.0, 2.0), 2.0)


def test_best_length_is_the_net_maximum():
    P, L, lam, r, S = 20.0, 0.5, math.log(2) / 0.5, 0.1, 1.5
    t = gl.best_length(P, L, lam, S)
    grid = np.linspace(0, 5, 5001)
    best = grid[np.argmax([gl.net(P, L, lam, r, S, x) for x in grid])]
    assert abs(best - t) < 2e-3
    assert gl.best_length(1.0, 0.5, 1.0, 1.0) == 0.0


def test_half_life_estimate():
    m = np.arange(1, 49)
    edge = 2.0 * 0.5 ** (m / 9.0)
    hl, lvl = gl.half_life_from_series(m, edge)
    assert abs(hl - 9.0) / 9.0 < 0.1 and lvl > 0
