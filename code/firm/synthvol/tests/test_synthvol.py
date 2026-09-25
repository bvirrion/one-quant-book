import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_synthvol import VolConfig, atm_iv, bs_delta, bs_price, expected_var, simulate_vol, smile_iv  # noqa: E402


def test_black_scholes_by_hand():
    c = float(bs_price(100.0, 100.0, 1.0, 0.2, "C"))
    assert abs(c - 7.9656) < 1e-3
    p = float(bs_price(100.0, 100.0, 1.0, 0.2, "P"))
    assert abs(c - p) < 1e-12                      # zero rates: at-the-money parity
    assert abs(float(bs_delta(100.0, 100.0, 1.0, 0.2, "C")) - 0.5398) < 1e-3


def test_expected_variance_and_premium():
    cfg = VolConfig(jump_rate=0.0)
    assert math.isclose(float(expected_var(cfg.theta, cfg, 0.5)), cfg.theta)
    hi = float(expected_var(4 * cfg.theta, cfg, 1e-6))
    assert abs(hi - 4 * cfg.theta) < 1e-6
    assert math.isclose(float(atm_iv(cfg.theta, cfg, 0.1)) ** 2, cfg.theta * (1 + cfg.vrp))
    assert float(smile_iv(0.2, -0.05, 0.1, cfg)) > 0.2 > float(smile_iv(0.2, 0.05, 0.1, cfg))


def test_simulation_shape_and_crash():
    cfg = VolConfig(days=2000, crashes=((1000, -0.3),))
    S = simulate_vol(cfg)
    assert S["r"].shape == (2000,) and S["R"].shape == (2000, 30)
    assert S["r"][1000:1010].sum() < -0.1 and S["v"][1000] >= cfg.crash_var
    assert np.corrcoef(S["R"][:, 0], S["r"])[0, 1] > 0.3
