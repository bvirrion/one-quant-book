import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "synthvol"))
from firm_synthvol import VolConfig  # noqa: E402
from firm_vixetp import curve_path, etp, flow  # noqa: E402


def test_rebalancing_flow_by_hand():
    r = np.array([0.1, -0.05])
    for lev, first in ((-1, 0.2), (2, 0.2), (1, 0.0)):
        p = etp(r, lev)
        assert abs(flow(p, r, lev)[0] - first) < 1e-12
    p = etp(r, -1)
    assert abs(flow(p, r, -1)[1] - 0.9 * 2 * -0.05) < 1e-12        # value 0.9 after day one


def test_acceleration_freezes_the_product():
    p = etp(np.array([0.1, 0.85, -0.5, 0.2]), -1)
    assert p["alive"].tolist() == [True, True, False, False, False]
    assert np.allclose(p["value"], [1.0, 0.9, 0.135, 0.135, 0.135])
    assert (flow(p, np.array([0.1, 0.85, -0.5, 0.2]), -1)[2:] == 0).all()


def test_flat_index_rolls_down_only_through_the_premium():
    cfg = VolConfig()
    v = np.full(100, cfg.theta)
    flat = curve_path(v, cfg, premium=0.0)
    assert np.allclose(flat["cm"], 0) and np.allclose(flat["f1"], flat["vix"])
    c = curve_path(v, cfg, premium=0.5)
    assert (c["cm"][1:] < 0).all() and (c["f2"] > c["f1"]).all()
