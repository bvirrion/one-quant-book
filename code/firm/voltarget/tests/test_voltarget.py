import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_voltarget import banded, ewma_var, realised_var, run, spike_flows, weights  # noqa: E402


def test_variance_forecasts():
    r = np.full(100, 0.01)
    assert math.isclose(realised_var(r, 21)[50], 0.0001 * 252) and np.isnan(realised_var(r, 21)[5])
    assert math.isclose(ewma_var(r, 20)[-1], 0.0001 * 252)


def test_weights_band_run():
    w = weights(np.array([0.04, 0.01, np.nan]), 0.10, 2.0, 1)
    assert np.allclose(w, [0.5, 1.0, 0.0])
    assert np.allclose(weights(np.array([0.04]), 0.10, 2.0, 2), [0.25])
    assert banded(np.array([1.0, 1.05, 1.2, 1.25]), 0.1).tolist() == [1.0, 1.0, 1.2, 1.2]
    assert np.allclose(run(np.array([0.0, 0.01]), np.array([2.0, 2.0]), 0.001), [-0.002, 0.02])


def test_spike_selling_and_feedback():
    b = np.r_[np.full(60, 0.005) * np.tile([1, -1], 30), [-0.05], np.zeros(20)]
    o = spike_flows(b, 0.01, 0.01, 0.0, 0.10, 20.0, 2.0)
    assert o["flow"][61] < 0 and o["exposure"][61] < o["exposure"][59]
    f = spike_flows(b, 0.01, 0.01, 0.2, 0.10, 20.0, 2.0)
    assert f["r"][61] < o["r"][61]
