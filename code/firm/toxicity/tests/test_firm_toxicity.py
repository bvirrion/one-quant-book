import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_toxicity as tx  # noqa: E402


def test_flow_tracker_by_hand():
    f = tx.FlowTracker(window=2.0, lot=100)
    ext = {"bid": 99, "ask": 100, "bid_qty": 300, "ask_qty": 100}
    f.update(0.0, {"kind": b"E", "agg": -1, "qty": 200}, ext)       # a sale of 2 lots hits the bid
    f.update(1.0, {"kind": b"E", "agg": 1, "qty": 100}, ext)        # a buy of 1 lot
    x = f.features(1)
    assert x[0] == 1.0 and math.isclose(x[1], 0.25) and math.isclose(x[2], math.log1p(1.0)) and x[3] == 0.0
    f.update(3.5, {"kind": b"A", "agg": 0, "qty": 100}, {"bid": 99, "ask": 101, "bid_qty": 300, "ask_qty": 100})
    x = f.features(-1)
    assert x[0] == 0.0 and x[3] == 1.0 and x[2] == 0.0          # window emptied; mid changed; spread two ticks


def test_model_recovers_a_linear_markout():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(2000, 4))
    y = 0.3 - 0.2 * X[:, 0] - 0.5 * X[:, 1] + rng.normal(0, 0.1, 2000)
    m = tx.ToxicityModel.fit(X, y)
    assert np.allclose(m.coef, [0.3, -0.2, -0.5, 0.0, 0.0], atol=0.02)
    assert math.isclose(m.score(np.zeros(4)), -m.coef[0])


def test_grouped_markouts():
    g = tx.grouped(np.array([[1.0], [3.0], [-2.0]]), np.array([1, 1, 2]), np.array(["a", "a", "b"]))
    assert math.isclose(g["a"][0][0], 2.0) and math.isclose(g["b"][0][0], -2.0)
