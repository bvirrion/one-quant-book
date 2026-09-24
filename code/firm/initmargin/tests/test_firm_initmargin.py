import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_initmargin as f


def test_overlapping_sums_and_hs():
    x = np.arange(10, dtype=float)[:, None]
    assert np.allclose(f.overlapping(x, 3)[:, 0], [3, 6, 9, 12, 15, 18, 21, 24])
    assert f.hs_im(-np.arange(1, 201, dtype=float), 0.99) == 199.0
    assert f.hs_im(np.ones(100), 0.99) == 0.0


def test_schedule_and_netting():
    assert f.schedule_rate("ir", 1.0) == 0.01 and f.schedule_rate("ir", 3.0) == 0.02
    assert f.schedule_rate("ir", 8.0) == 0.04 and f.schedule_rate("fx") == 0.06
    r = f.schedule_im([("ir", 100.0, 8.0), ("fx", -50.0, 0.0)], 0.0, 1.0)
    assert math.isclose(r["gross"], 7.0) and math.isclose(r["net"], 0.4 * 7.0)
    assert math.isclose(f.schedule_im([("ir", 100.0, 8.0)], 1.0, 1.0)["net"], 4.0)


def test_sensitivity_model():
    assert math.isclose(f.simm_like(np.array([10.0]), [5.0], [2.0]), 20.0)
    two = f.simm_like(np.array([10.0, -10.0]), [5.0, 5.5], [1.0, 1.0])
    assert two < 1.0                         # nearly offsetting neighbours


def test_apc_tools():
    model = np.array([1.0, 1.0, 2.0, 3.0, 2.0, 1.0])
    stress = np.array([False, False, True, True, False, False])
    b = f.apc_buffer(model, stress, 0.25, rebuild_days=1)
    assert b[0] == 1.25 and b[2] == 2.0 and b[3] == 3.0 and b[5] == 1.25
    assert np.all(f.apc_stressed_weight(model, 4.0) >= model)
    assert f.backtest(np.array([1.0, 2.0]), np.array([1.5, 1.5])) == 1
