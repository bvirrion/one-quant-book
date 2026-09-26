import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_rfqmm as rm  # noqa: E402


def test_fair_value():
    v = rm.fair_value([100.0, 100.2, 101.5], [2.0, 1.0, 10.0], [99.8, 100.4], [1.0, 1.0], curve_move=-0.1, half_life=5.0)
    assert 99.9 < v < 100.3


def test_simulation_and_curse():
    s = rm.simulate(3, 20.0, n=20000, seed=1)
    w = s["win"]
    assert np.allclose(s["pnl"][w], -s["our_bid"][w])
    assert s["our_error"][w].mean() > 0                       # the winner overestimated: the curse
    lone = rm.optimise(1, [0.0, 20.0, 40.0], n=20000)
    assert lone["rows"][40.0]["win"] < lone["rows"][0.0]["win"]


def test_equilibrium_and_naive():
    ms = np.arange(0.0, 80.1, 5.0)
    e1, e5 = rm.equilibrium(1, ms, n=10000), rm.equilibrium(5, ms, n=10000)
    assert e5["pnl"] < e1["pnl"] and e5["win"] < e1["win"]
    nv = rm.naive_markup(e5["rows"])
    assert nv < e5["markup"] and e5["rows"][nv]["pnl"] < e5["pnl"]


def test_win_model_and_etf():
    rng = np.random.default_rng(0)
    m = rng.uniform(0, 50, 5000)
    p = 1 / (1 + np.exp(-(1.0 - 0.1 * m)))
    a, b = rm.fit_win_model(m, rng.random(5000) < p)
    assert abs(a - 1.0) < 0.2 and abs(b + 0.1) < 0.02
    assert math.isclose(rm.etf_rfq_bid(100.0, 50000, 1250.0, 5.0, 1.0), 100.0 * (1 - 6e-4) - 0.025)
