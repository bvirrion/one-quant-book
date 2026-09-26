import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_hfalpha as a  # noqa: E402


def test_ofi_and_flow_by_hand():
    e = a.FeatureEngine(window=1.0, lot=100, leader=([0.0, 0.5], [100.0, 101.0]))
    e.update(0.0, b"A", 0, 100, 99, 300, 100, 200)
    f = e.update(0.2, b"A", 0, 100, 99, 400, 100, 200)           # bid queue +1 lot: ofi +1
    assert f[1] == 1.0 and math.isclose(f[0], (4 - 2) / 6)
    f = e.update(0.4, b"E", -1, 100, 99, 300, 100, 200)          # a sale of 1 lot at the bid: ofi -1, flow -1
    assert f[1] == 0.0 and f[2] == -1.0
    f = e.update(0.9, b"X", 0, 200, 99, 300, 101, 100)           # the ask moves up a tick: + the old ask size (2)
    assert f[1] == 2.0 and f[3] == 1.0 and f[4] == 0.5            # leader +1 tick over the window; own mid +0.5
    f = e.update(2.0, b"A", 0, 100, 99, 300, 101, 100)           # the window has emptied
    assert f[1] == 0.0 and f[2] == 0.0 and f[4] == 0.0


def test_target_and_ridge():
    t = np.arange(0.0, 10.0, 0.5)
    mid = np.arange(len(t), dtype=float)
    y = a.target(t, mid, 1.0)
    assert np.allclose(y[:-2], 2.0) and np.isnan(y[-2:]).all()
    rng = np.random.default_rng(0)
    X = rng.normal(size=(5000, 5))
    yy = 0.5 * X[:, 0] - 0.2 * X[:, 3] + rng.normal(0, 0.5, 5000)
    m = a.Ridge.fit(X, yy, lam=1.0)
    assert a.ic(m.predict(X), yy) > 0.6 and abs(m.coef[0] * 1 / m.scale[0] - 0.5) < 0.05
