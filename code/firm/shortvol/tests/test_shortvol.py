import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "synthvol"))
from firm_shortvol import hedged_straddle, lever, overwrite, periods, put_write, short_variance  # noqa: E402
from firm_synthvol import VolConfig, atm_iv, bs_price  # noqa: E402


def test_periods_and_variance_by_hand():
    assert periods(100, 21).tolist() == [0, 21, 42, 63]
    cfg = VolConfig(jump_rate=0.0)
    v = np.full(50, cfg.theta)
    r = np.zeros(50)
    x = short_variance(r, v, cfg, 21)
    assert np.allclose(x, cfg.theta * (1 + cfg.vrp) * 21 / 252)     # nothing realised: keep the strike


def test_flat_path_keeps_premia():
    cfg = VolConfig(jump_rate=0.0)
    v = np.full(50, cfg.theta)
    r = np.zeros(50)
    prem = float(2 * bs_price(1.0, 1.0, 21 / 252, atm_iv(cfg.theta, cfg, 21 / 252), "C"))
    assert np.allclose(hedged_straddle(r, v, cfg, 21), prem)
    assert (overwrite(r, v, cfg, 21) > 0).all() and (put_write(r, v, cfg, 21) > 0).all()


def test_lever_wipes_out():
    cap, dead = lever([0.1, -0.6], 2.0)
    assert dead and cap[-1] == 0.0 and math.isclose(cap[0], 1.2)
