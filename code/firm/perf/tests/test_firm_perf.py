import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_perf import (
    BacktestResult,
    alpha_beta,
    calmar,
    drawdown,
    drawdown_spells,
    from_returns,
    hit_rate,
    holding_period,
    lo_sharpe,
    longest_drawdown,
    max_drawdown,
    omega,
    profit_factor,
    sharpe,
    smoothing_profile,
    sortino,
    tear_sheet,
    unsmooth,
)


def test_drawdowns_by_hand():
    r = np.array([0.1, -0.5, 0.2, 1.0, -0.1])
    assert np.allclose(drawdown(r), [0, -0.5, -0.4, 0, -0.1])
    assert max_drawdown(r) == -0.5 and drawdown_spells(r) == [(1, 1, 3), (4, 4, None)]
    assert longest_drawdown(r) == 2
    assert np.allclose(drawdown(r, compound=False), [0, -0.5, -0.3, 0, -0.1])
    assert abs(calmar(r, periods=5) - (1.1 * 0.5 * 1.2 * 2.0 * 0.9 - 1) / 0.5) < 1e-12


def test_ratios_by_hand():
    r = np.array([0.02, -0.01, 0.03, -0.02, 0.0])
    assert hit_rate(r) == 0.5 and abs(profit_factor(r) - 0.05 / 0.03) < 1e-12
    assert abs(omega(r) - (0.05 / 5) / (0.03 / 5)) < 1e-12 and abs(omega(r, float(r.mean())) - 1) < 1e-12
    dd = math.sqrt((0.01**2 + 0.02**2) / 5)
    assert abs(sortino(r, periods=1) - r.mean() / dd) < 1e-12


def test_sharpe_lo_and_smoothing():
    rng = np.random.default_rng(0)
    true = 0.01 + 0.03 * rng.standard_normal(20000)
    s = sharpe(from_returns(true, 12), 12)
    assert abs(lo_sharpe(true, 12) - s["sr"]) < 0.03                    # iid: q / sqrt(q) = sqrt(q)
    th = np.array([0.5, 0.3, 0.2])
    obs = np.convolve(true, th)[: len(true)]
    assert lo_sharpe(obs, 12) < 0.8 * sharpe(obs, 12)["sr"]              # smoothing flatters the naive ratio
    assert abs(lo_sharpe(obs, 12) - s["sr"]) < 0.05
    est = smoothing_profile(obs, 2)
    assert np.all(np.abs(est - th) < 0.05)
    assert np.allclose(unsmooth(obs, th)[200:], true[200:], atol=1e-9)             # the start-up error decays
    assert sharpe(obs, 12)["se_hac"] > 1.3 * sharpe(obs, 12)["se_iid"]


def test_alpha_beta_and_holding_period():
    rng = np.random.default_rng(1)
    b = 0.01 * rng.standard_normal(5000)
    x = 0.0002 + 0.5 * b + 0.005 * rng.standard_normal(5000)
    ab = alpha_beta(x, b)
    assert abs(ab["beta"] - 0.5) < 3 * ab["beta_se"] and abs(ab["alpha"] - 0.0504) < 0.03
    T = 100
    w = np.full((T, 2), 0.5)
    tr = np.full((T, 2), 0.05)                                           # one-way turnover 5% a period
    res = BacktestResult(np.arange(T), np.array(["a", "b"]), w, tr, np.zeros(T), {}, np.zeros(T), np.ones(T),
                         {"periods": 252})
    assert abs(holding_period(res) - 20.0) < 1e-12
    m, text = tear_sheet(from_returns(x), b, "demo")
    assert "Sharpe" in text and abs(m["beta"] - ab["beta"]) < 1e-12
