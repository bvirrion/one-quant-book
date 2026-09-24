import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from etf_demo import ArbCosts, decay_factor, leveraged_path, rebalance_trade, simulate_premium, stale_nav


def test_premium_never_leaves_the_band():
    c = ArbCosts(4.0, 1.5, 1.0, 0.5)
    prem, _ = simulate_premium(c, 5_000, 1)
    assert c.band_bp == 7.0 and np.abs(prem).max() <= c.band_bp


def test_rebalance_trade_restores_the_leverage():
    beta, nav, r = 3.0, 100.0, 0.02
    exposure_after = beta * nav * (1 + r)
    nav_after = nav * (1 + beta * r)
    assert exposure_after + rebalance_trade(beta, nav, r) == pytest.approx(beta * nav_after)
    assert rebalance_trade(-1.0, 100.0, 0.02) == pytest.approx(4.0)       # an inverse fund also buys after a rise
    assert rebalance_trade(1.0, 100.0, 0.02) == 0.0


def test_decay_matches_simulation():
    rng = np.random.default_rng(3)
    sig, days = 0.30, 252
    ratios = []
    for _ in range(4_000):
        r = rng.normal(0.0, sig / np.sqrt(252), days)
        ratios.append(leveraged_path(r, 3.0)[-1] / np.prod(1 + r) ** 3)
    assert np.mean(np.log(ratios)) == pytest.approx(np.log(decay_factor(3.0, sig, 1.0)), rel=0.05)


def test_stale_nav_lags_and_converges():
    true = np.concatenate([np.full(5, 100.0), np.full(40, 90.0)])
    nav = stale_nav(true, 0.75)
    assert nav[5] == pytest.approx(97.5) and nav[-1] == pytest.approx(90.0, abs=1e-3)
