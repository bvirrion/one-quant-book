import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fxflows import FlowFXConfig, fix_liquidity, flow_trade, simulate_months  # noqa: E402


def test_flow_sign_follows_the_hedges():
    cfg = FlowFXConfig(months=4, est_error=0.0, fx_vol=0.0, fix_noise=0.0)
    s = simulate_months(cfg)
    expect = -0.5 * s["home"] + 0.6 * 0.3 * s["foreign"]
    assert np.allclose(s["flow"], expect) and np.allclose(s["est"], s["flow"])
    assert np.allclose(s["before"], 0.065 * s["flow"]) and np.allclose(s["after"], -0.5 * 0.065 * s["flow"])


def test_trades_without_noise_earn_the_push_less_costs():
    cfg = FlowFXConfig(months=20, est_error=0.0, fx_vol=0.0, fix_noise=0.0)
    s = simulate_months(cfg)
    assert np.allclose(flow_trade(s, cfg), 1e4 * np.abs(s["before"]) - 1.0)
    assert np.allclose(fix_liquidity(s, cfg), 1e4 * 0.4 * np.abs(s["fix_push"]) - 0.5)
