import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_optsignal import OptionConfig, signals, simulate_options  # noqa: E402


def test_informed_demand_moves_the_right_options_before_the_event():
    T, N = 40, 2
    flag = np.zeros((T, N), bool)
    flag[30, 0], flag[30, 1] = True, True
    sur = np.where(flag, np.array([-2.0, 2.0]), np.nan)
    cfg = OptionConfig(noise=0.0, os_noise=0.0, window=10, impact=0.01)
    opt = simulate_options(flag, sur, np.ones((T, N), bool), np.full((T, N), 0.3), cfg, np.random.default_rng(0))
    sig = signals(opt, np.full((T, N), 0.3))
    assert np.allclose(sig["skew"][:20, :], 0.03) and np.allclose(sig["skew"][25, 0], 0.03 + 0.01 * 1.5 * 2.0)
    assert np.allclose(sig["spread"][25, 1], -0.03 + 0.01 * 2.0) and np.allclose(sig["skew"][30:, :], 0.03)
    assert sig["os"][25, 0] > sig["os"][25, 1] > sig["os"][5, 1]
    assert np.allclose(sig["ivrv"], 0.02)
