import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mktquality import before_after, day_measures, did, event_study  # noqa: E402


def test_day_measures_on_a_hand_market():
    top = {"t": np.array([0.0, 50.0]), "bid": np.array([99.0, 99.0]), "ask": np.array([101.0, 101.0]),
           "bid_qty": np.array([100, 300]), "ask_qty": np.array([100, 300])}
    trades = np.array([(10.0, 101.0, 1, 100), (20.0, 99.0, -1, 100)],
                      dtype=[("t", "f8"), ("price", "f8"), ("sign", "i1"), ("qty", "i8")])
    m = day_measures(top, trades, messages=10, h=5.0, grid=(10.0, 20.0))
    assert np.isclose(m["quoted"], 200.0) and np.isclose(m["effective"], 200.0) and np.isclose(m["impact"], 0.0)
    assert np.isclose(m["depth"], 100.0) and m["otr"] == 5.0 and m["amihud"] == 0.0


def test_did_recovers_a_planted_effect_that_before_after_misses():
    rng = np.random.default_rng(0)
    units, periods = np.arange(40), np.arange(10)
    u, p = np.meshgrid(units, periods, indexing="ij")
    u, p = u.ravel(), p.ravel()
    treated = u < 20
    post = p >= 5
    y = 3.0 + 0.1 * u + 2.0 * post + 1.0 * (treated & post) + rng.normal(0, 0.5, len(u))
    d = did(y, treated, post, u, p)
    b = before_after(y, treated, post, u)
    assert abs(d["coef"] - 1.0) < 3 * d["se"] and abs(b["coef"] - 3.0) < 3 * b["se"]
    es = event_study(y, treated, p, u, base=4)
    assert abs(es[0][0]) < 0.5 and abs(es[7][0] - 1.0) < 0.5
