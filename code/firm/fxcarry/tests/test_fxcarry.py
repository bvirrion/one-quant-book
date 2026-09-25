import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fxcarry import BasisConfig, basis_trade, carry_basket, crash_hedge, simulate_basis  # noqa: E402


def test_basket_goes_long_high_carry_and_short_low():
    carry = np.tile(np.arange(6.0), (30, 1))
    r = np.tile(np.array([-1, -1, 0, 0, 1, 1.0]) * 1e-3, (30, 1))
    b = carry_basket(r, carry, 2, 10)
    assert np.allclose(b["pos"][5], [-0.5, -0.5, 0, 0, 0.5, 0.5]) and np.allclose(b["r"][1:], 2e-3)


def test_put_price_and_payoff_by_hand():
    rng = np.random.default_rng(0)
    b = rng.normal(0, 0.005, 400)
    h = crash_hedge(b, 21, 1.5, 1.0, 63)
    s = h["start"][0]
    sd = b[s - 63:s].std() * math.sqrt(21)
    K = 1 - 1.5 * sd
    d1 = (math.log(1 / K) + 0.5 * sd * sd) / sd
    nc = lambda x: 0.5 * math.erfc(-x / math.sqrt(2))                  # noqa: E731
    assert abs(h["premium"][0] - (K * nc(-(d1 - sd)) - nc(-d1))) < 1e-12
    assert np.allclose(h["hedged"], h["raw"] - h["premium"] + h["payoff"])


def test_basis_windows_and_trade():
    cfg = BasisConfig(noise_sd=0.0)
    b = simulate_basis(cfg)
    assert b["basis"][252 - 1] == -80.0 and b["basis"][63 - 1] == -50.0 and b["basis"][40] == -20.0
    assert abs(basis_trade(b, cfg)[40] * 252 - 5.0) < 1e-12
    assert basis_trade(b, cfg, b["quarter_end"])[40] == 0.0
