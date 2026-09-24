import math
import pathlib
import sys
from statistics import NormalDist

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_xvafund as f


def test_bcbs_279_example_1():
    """Two USD swaps and a EUR swaption, unmargined: EAD = 1.4 (60 + 347) = 569 (thousands)."""
    delta = -NormalDist().cdf(-(math.log(0.06 / 0.05) + 0.5 * 0.5 ** 2) / 0.5)
    trades = [f.IrTrade("USD", 10_000, 0, 10, 1, 10), f.IrTrade("USD", 10_000, 0, 4, -1, 4),
              f.IrTrade("EUR", 5_000, 1, 11, delta, 1)]
    assert round(f.supervisory_duration(0, 10), 2) == 7.87 and round(f.supervisory_duration(0, 4), 2) == 3.63
    addon = f.ir_addon(trades)
    assert round(addon) == 347 and round(f.sa_ccr_ead(60, addon)) == 569


def test_margined_maturity_factor_and_multiplier():
    assert math.isclose(f.maturity_factor(5.0, 14), 1.5 * math.sqrt(14 / 250))
    assert f.multiplier(10.0, 50.0) == 1.0 and 0.05 < f.multiplier(-100.0, 50.0) < 1.0


def test_ba_cva_single_counterparty_and_funding():
    s = f.scva(0.03, 5.0, 1e6)
    assert math.isclose(f.ba_cva_capital([s]), 0.65 * s)
    t = np.linspace(0, 5, 11)
    assert math.isclose(f.fca(np.full(11, 2e6), t, 0.008), 0.008 * 2e6 * 5)
