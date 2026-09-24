"""Acceptance tests of the Book 3, Chapter 10 build (commodity curves)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_commcurve import ForwardCurve, decompose, full_carry_spread, net_convenience_yield, roll_weights, roll_yield


def test_curve_interpolation_and_shape():
    c = ForwardCurve((0.1, 0.2, 0.5), (80.0, 81.0, 84.0))
    assert c.price(0.1) == 80.0 and c.price(1.0) == 84.0 and 81.0 < c.price(0.35) < 84.0
    assert c.shape() == "contango"
    with pytest.raises(ValueError):
        ForwardCurve((0.2, 0.1), (1.0, 2.0))


def test_carry_identities():
    f1, r, u, y, dt = 80.0, 0.04, 0.03, 0.05, 1 / 12
    f2 = f1 * math.exp((r + u - y) * dt)
    assert math.isclose(net_convenience_yield(f1, f2, dt, r), y - u)
    assert math.isclose(f1 + full_carry_spread(f1, dt, r, u), f1 * math.exp((r + u) * dt))
    assert roll_yield(82.0, 80.0, 1 / 12) > 0                   # backwardation pays the roll


def test_roll_schedule_and_decomposition():
    assert [roll_weights(d) for d in (4, 5, 7, 9, 12)] == [0.0, 0.2, 0.6, 1.0, 1.0]
    d = decompose(0.10, 0.25, 0.05)
    assert math.isclose(d["roll"], -0.15) and math.isclose(d["total"], 0.15)
