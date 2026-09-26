import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tca import (  # noqa: E402
    adjusted_difference,
    attribute,
    benchmarks,
    cluster_ols,
    peer_compare,
    pretrade,
    reversion,
)


def test_attribution_adds_up_to_the_shortfall():
    mid = (np.array([0.0, 10.0, 20.0]), np.array([100.0, 101.0, 102.0]))
    cf = (np.array([0.0, 20.0]), np.array([100.0, 100.5]))
    fills = [(5.0, 100.5, 60, 0.01), (15.0, 101.5, 30, 0.01)]
    a = attribute(1, 100, 99.8, 100.0, fills, mid, cf, 103.0, 0.0)
    assert np.isclose(a["delay"], 90 * 0.2 / 100) and np.isclose(a["spread"], (60 * 0.5 + 30 * 0.5) / 100)
    assert np.isclose(a["impact"], 30 * 1.0 / 100) and np.isclose(a["timing"], 0.0)
    assert np.isclose(a["opportunity"], 10 * 3.2 / 100) and np.isclose(a["fees"], 0.9 / 100)
    assert abs(a["check"]) < 1e-12 and np.isclose(a["filled"], 0.9)
    b = benchmarks(1, [(100.5, 60), (101.5, 30)], 100.0, [(101.0, 100)], [(100.0, 50), (102.0, 50)], 102.0)
    assert np.isclose(b["arrival"], 100.8333333 - 100) and np.isclose(b["interval_vwap"], -0.1666667)
    assert np.isclose(b["close"], -1.1666667) and np.isclose(b["day_vwap"], -0.1666667)
    assert np.allclose(reversion(-1, 10.0, mid, (5.0, 10.0)), [0.0, -1.0])
    assert np.isclose(pretrade(0.5, 1.0, 10.0, 0.04), 2.5)


def test_clustered_regression_and_adjustment():
    rng = np.random.default_rng(0)
    days = np.repeat(np.arange(200), 2)
    hard = rng.random(400)
    treat = (rng.random(400) < 0.2 + 0.6 * hard).astype(float)       # the treated get the hard orders
    y = 1.0 + 1.0 * treat + 4.0 * hard + rng.normal(0, 1, 400) + np.repeat(rng.normal(0, 1, 200), 2)
    d = adjusted_difference(y, treat, hard[:, None], days)
    assert d["raw"] > 1.5 and abs(d["adj"] - 1.0) < 2.5 * d["adj_se"] and d["lo"] < 1.0 < d["hi"]
    b, v = cluster_ols(y, np.c_[np.ones(400), hard], days)
    assert v.shape == (2, 2) and v[1, 1] > 0
    p = peer_compare(y, 1.0 + 4.0 * hard, np.where(treat > 0, "b", "a"), days)
    assert abs(p["a"][0]) < 3 * p["a"][1] + 0.1 and abs(p["b"][0] - 1.0) < 3 * p["b"][1]
