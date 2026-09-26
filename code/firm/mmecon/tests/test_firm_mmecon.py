import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_mmecon as e  # noqa: E402


def test_breakeven_and_profit():
    v = e.breakeven_volume(0.5, 0.2, 30.0)
    assert math.isclose(v, 100.0) and math.isclose(float(e.profit(v, 0.5, 0.2, 30.0)), 0.0)
    assert e.breakeven_volume(0.2, 0.2, 1.0) == math.inf


def test_operating_leverage_is_elasticity():
    c, var, fix, v = 0.5, 0.2, 30.0, 150.0
    dv = 1e-6 * v
    num = (math.log(float(e.profit(v + dv, c, var, fix))) - math.log(float(e.profit(v, c, var, fix)))) / math.log(1 + 1e-6)
    assert math.isclose(e.operating_leverage(v, c, var, fix), num, rel_tol=1e-4)
    with pytest.raises(ValueError):
        e.operating_leverage(50.0, c, var, fix)


def test_capture_units_and_shares():
    assert math.isclose(e.capture_bp(2.5, 1e4), 2.5)
    s = e.cost_shares({"a": 1.0, "b": 3.0})
    assert math.isclose(s["b"], 0.75) and math.isclose(sum(s.values()), 1.0)
    assert np.allclose(e.profit_curve([0, 100], 0.5, 0.2, 30.0), [-30.0, 0.0])
