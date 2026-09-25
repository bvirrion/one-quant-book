import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "synthvol"))
from firm_synthvol import VolConfig  # noqa: E402
from firm_volrv import SurfaceConfig, attribution, features, surface_path, trade_pnl  # noqa: E402


def _flat(T, cfg, skew=-0.12):
    v = np.full(T, cfg.theta)
    s = surface_path(np.zeros(T), v, cfg, SurfaceConfig(skew_sd=0.0, slope_sd=0.0))
    s["skew"] = np.full(T, skew)
    s["fair_skew"] = s["skew"].copy()
    return s


def test_residuals_remove_a_linear_level_effect():
    x = np.linspace(0.1, 0.4, 400)
    s = {"atm1": x, "atm3": x + 0.02 - 0.1 * x, "skew": -0.1 - 0.4 * x}
    f = features(s, warmup=50)
    assert np.allclose(f["slope_res"][50:], 0, atol=1e-9) and np.allclose(f["skew_res"][50:], 0, atol=1e-9)
    assert (f["skew_res"][:50] == 0).all()


def test_buckets_add_up_and_a_still_surface_has_no_skew_or_slope_pnl():
    cfg = VolConfig(jump_rate=0.0)
    T = 70
    r = np.random.default_rng(1).normal(0, 0.01, T)
    s = _flat(T, cfg)
    for kind in ("skew", "calendar"):
        b = trade_pnl(r, s, kind, np.ones(T), cfg)
        assert np.allclose(b["skew"], 0) and np.allclose(b["slope"], 0) and np.allclose(b["level"], 0)
        parts = b["spot_time"] + b["level"] + b["skew"] + b["slope"] + b["cost"]
        assert np.allclose(parts, b["total"]) and np.allclose(b["cost"], -2.0)
        assert abs(sum(attribution(b).values()) - 1) < 1e-9


def test_a_risk_reversal_gains_when_the_skew_flattens():
    cfg = VolConfig(jump_rate=0.0)
    T = 30
    s = _flat(T, cfg, skew=-0.20)
    s["skew"][1:] = -0.10                        # puts cheapen, calls richen after day 0
    b = trade_pnl(np.zeros(T), s, "skew", np.ones(T), cfg)
    assert b["skew"][0] > 5                     # both legs: about 0.1 x one standardised unit x 100 each
    b = trade_pnl(np.zeros(T), s, "skew", -np.ones(T), cfg)
    assert b["skew"][0] < -5
