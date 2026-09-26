import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_riskbid import auction, curse, liquidation, profile, risk_sd, transition  # noqa: E402


def test_liquidation_and_profile():
    liq = liquidation([1e6, 4e6], [1e7, 1e7], [100.0, 100.0], [10.0, 10.0], cap=0.2)
    assert np.allclose(liq["days"], [1.0, 2.0])
    assert np.allclose(liq["cost_bp"], [5 + 70 * np.sqrt(0.1), 5 + 70 * np.sqrt(0.2)])
    p = profile([1e6, 4e6, 5e6], [1e8, 1e7, 1e6], [1, 2, 2])
    assert np.allclose(p["buckets"], [0.1, 0.0, 0.4, 0.5]) and p["sectors"] == {1: 0.1, 2: 0.9}


def test_risk_of_a_straight_line_sale():
    # one name sold over d days: variance = w^2 var d / 3
    assert np.isclose(risk_sd([1.0], [[4.0]], [3.0]) ** 2, 4.0)
    # two names, perfectly correlated, one fully hedged by its loading
    sd = risk_sd([1.0, 1.0], [[1.0, 1.0], [1.0, 1.0]], [3.0, 3.0], hedge=([1.0, 1.0], 1.0))
    assert np.isclose(sd, 0.0)
    a, b = 2.0, 5.0
    ts = np.linspace(0, a, 200_001)
    num = np.trapezoid((1 - ts / a) * (1 - ts / b), ts)
    assert np.isclose(risk_sd([1.0, 1.0], [[0.0, 1.0], [1.0, 0.0]], [a, b]) ** 2, 2 * num, rtol=1e-6)


def test_winners_curse_and_transition():
    assert np.isclose(curse(2.0, 3), 2.0 * 1.029375, atol=1e-4)
    naive = auction(20.0, 2.0, 4, 0.0, trials=200_000)
    fixed = auction(20.0, 2.0, 4, curse(2.0, 3), trials=200_000)
    assert naive < -1.9 and abs(fixed) < 0.02
    t = transition({"a": 10.0, "b": 10.0}, {"b": 5.0, "c": 15.0}, cross_share=0.5)
    assert (t["full"], t["netted"]) == (40.0, 30.0) and t["crossed"] == 15.0
