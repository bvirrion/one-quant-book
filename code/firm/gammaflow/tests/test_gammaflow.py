import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_gammaflow import FlowConfig, dealer_gamma, flip_level, gamma, simulate_days, strikes  # noqa: E402


def test_gamma_peaks_at_the_strike_and_grows_near_expiry():
    g_far, g_near = gamma(100.0, 100.0, 0.01, 0.16), gamma(100.0, 100.0, 0.0001, 0.16)
    assert g_near > 9 * g_far and gamma(101.0, 100.0, 0.0001, 0.16) < g_near


def test_no_impact_gives_the_free_paths():
    d = simulate_days(FlowConfig(days=20, impact=0.0))
    assert np.allclose(d["S"], d["S_free"])


def test_flip_level_between_long_calls_and_short_puts():
    cfg = FlowConfig()
    K = strikes(cfg)
    pos_c = np.where(np.isclose(K, 101.0), 1.0, 0.0)
    pos_p = np.where(np.isclose(K, 99.0), -1.0, 0.0)
    assert abs(flip_level(pos_c, pos_p, cfg, 0.001) - 100.0) < 0.02
    assert dealer_gamma(100.5, 0.001, pos_c, pos_p, cfg) > 0 > dealer_gamma(99.5, 0.001, pos_c, pos_p, cfg)
