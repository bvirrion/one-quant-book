import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_stresstest as f

COV = np.array([[4.0, 1.2], [1.2, 1.0]]) * 1e-4


def test_historical_moves():
    lv = np.array([[0.02, 100.0], [0.025, 90.0]])
    s = f.historical("x", ["a", "b"], lv, "a", "b", [1])
    assert math.isclose(s.moves[0], 0.005) and math.isclose(s.moves[1], math.log(0.9))


def test_conditioning_is_the_regression():
    x = f.condition(COV, [0], [0.02])
    assert math.isclose(x[1], 1.2 / 4.0 * 0.02)


def test_reverse_linear_is_the_closest_point_and_nonlinear_agrees_on_a_linear_book():
    d = np.array([1e6, -2e6])
    x, dist = f.reverse_linear(d, COV, 5e4)
    assert math.isclose(d @ x, -5e4) and math.isclose(dist, 5e4 / math.sqrt(d @ COV @ d))
    rng = np.random.default_rng(0)
    for _ in range(200):
        y = x + rng.normal(0, 1e-3, 2)
        y = y - ((d @ y + 5e4) / (d @ d)) * d            # back onto the loss line
        assert f.mahalanobis(y, COV) >= dist - 1e-9
    xn, dn = f.reverse_nonlinear(lambda z: float(d @ z), COV, 5e4, np.zeros(2))
    assert np.allclose(xn, x, atol=1e-9) and math.isclose(dn, dist, rel_tol=1e-9)
