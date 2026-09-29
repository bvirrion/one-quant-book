import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_treasury as tr  # noqa: E402

B = tr.Broker("x", 0.10, 0.20, 50.0, 0.5, 50.0, 20.0)


def test_margin_and_financing():
    pos = [100.0, -60.0]
    assert abs(tr.margin(B, pos) - (0.1 * 160 + 0.2 * 40 + 0.5 * 60)) < 1e-12
    assert abs(tr.financing(B, pos) - (50 * 100 + 20 * 60) * 1e-4) < 1e-12


def test_optimiser_beats_every_single_broker():
    brokers = [B, tr.Broker("y", 0.05, 0.5, 1e9, 0.0, 30.0, 30.0)]
    pos = np.array([80.0, 40.0, -70.0, -30.0])
    a = tr.optimise(brokers, pos, 0.05)
    assert np.allclose(a.sum(axis=1), 1.0) and (a >= -1e-9).all()
    best = tr.annual_cost(brokers, a, pos, 0.05)
    for j in range(2):
        one = np.zeros((4, 2))
        one[:, j] = 1
        assert best <= tr.annual_cost(brokers, one, pos, 0.05) + 1e-9


def test_forecast_and_horizon():
    pnl = np.array([[-5.0, 2.0], [-5.0, 2.0], [0.0, 0.0]])
    req = np.full((3, 2), 10.0)
    cash, calls, stuck = tr.forecast(8.0, [10.0, 10.0], pnl, req, np.array([False, True]))
    assert list(cash) == [3.0, -2.0, -2.0] and list(calls) == [5.0, 5.0, 0.0] and list(stuck) == [2.0, 4.0, 4.0]
    assert tr.survival_horizon(cash) == 2 and tr.buffer_needed(cash) == 2.0 and tr.survival_horizon([1.0, 2.0]) == 3
    assert list(tr.house_path([1.2, 1.4, 1.6], 2)) == [1.0, 1.0, 1.6]


def test_fcm_margin_scales_with_notional():
    h = np.random.default_rng(0).normal(0, 0.01, 300)
    a, b = tr.fcm_margin(h, 10.0), tr.fcm_margin(h, 20.0)
    assert a > 0 and abs(b - 2 * a) < 1e-12
