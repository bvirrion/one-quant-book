import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_vecbt import BacktestResult, backtest, signal_to_weights


def test_lag_semantics():
    r = np.array([[0.01, 0.0], [0.02, 0.0], [-0.03, 0.0], [0.04, 0.0]])
    w = np.array([[1.0, 0.0]] * 4)
    for lag, want in ((0, [0.01, 0.02, -0.03, 0.04]), (1, [0.0, 0.02, -0.03, 0.04]), (2, [0.0, 0.0, -0.03, 0.04])):
        res = backtest(w, r, lag=lag)
        assert isinstance(res, BacktestResult) and np.allclose(res.gross, want)
    assert np.allclose(backtest(w, r, lag=1, compound=False).capital, 1 + np.cumsum([0.0, 0.02, -0.03, 0.04]))
    assert np.isclose(backtest(w, r, lag=1).capital[-1], 1.02 * 0.97 * 1.04)


def test_costs_drift_and_turnover():
    r = np.array([[0.10, -0.10], [0.0, 0.0], [0.0, 0.0]])
    w = np.array([[0.5, -0.5]] * 3)
    res = backtest(w, r, lag=0, cost=0.001)
    assert np.allclose(res.trades[0], [0.5, -0.5])
    after = np.array([0.55, -0.45]) / 1.10                     # the book drifted during period 0
    assert np.allclose(res.trades[1], np.array([0.5, -0.5]) - after)
    assert np.isclose(res.costs["trading"][0], 0.001) and np.isclose(res.turnover[0], 0.5)
    alt = backtest(np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]), np.zeros((3, 2)), lag=0, cost=0.002)
    assert np.allclose(alt.costs["trading"], [0.002, 0.004, 0.004]) and np.allclose(alt.turnover, [0.5, 1.0, 1.0])


def test_borrow_cash_universe_cap():
    z = np.zeros((2, 2))
    res = backtest(np.array([[0.5, -0.5]] * 2), z, lag=0, borrow=0.0252, periods=252)
    assert np.allclose(res.costs["borrow"], 0.5 * 0.0001)
    cash = backtest(np.zeros((2, 2)), z, lag=0, cash_rate=0.0504, periods=252)
    assert np.allclose(cash.costs["financing"], -0.0002) and np.allclose(cash.net, 0.0002)
    lev = backtest(np.array([[1.5, 0.0]] * 2), z, lag=0, cash_rate=0.0252, borrow_spread=0.0252, periods=252)
    assert np.allclose(lev.costs["financing"], 0.5 * 0.0002)
    u = np.array([[True, False]] * 2)
    assert np.allclose(backtest(np.array([[0.5, 0.5]] * 2), z, lag=0, universe=u).weights[:, 1], 0.0)
    assert np.allclose(backtest(np.array([[0.5, -0.5]] * 2), z, lag=0, cap=0.2).weights, [[0.2, -0.2]] * 2)
    assert math.isclose(float(res.gross_exposure[0]), 1.0) and math.isclose(float(res.net_exposure[0]), 0.0)


def test_signal_to_weights():
    s = np.array([[1.0, 2.0, 3.0, np.nan], [3.0, 1.0, 2.0, 5.0]])
    w = signal_to_weights(s, gross=2.0)
    assert np.allclose(np.abs(w).sum(axis=1), 2.0) and np.allclose(w.sum(axis=1), 0.0) and w[0, 3] == 0.0
    assert np.allclose(signal_to_weights(np.array([[1.0, 3.0]]), neutral=False), [[0.25, 0.75]])
    u = np.array([[True, True, False, True]] * 2)
    assert signal_to_weights(s, u)[1, 2] == 0.0
