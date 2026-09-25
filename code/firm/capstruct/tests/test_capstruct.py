import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_capstruct import CapConfig, hedge_ratio, implied_spread, simulate_firms, trades  # noqa: E402


def test_spread_rises_with_leverage_and_falls_with_equity():
    cfg = CapConfig()
    s = implied_spread(np.array([30.0, 50.0, 80.0]), 40.0, 0.35, cfg)
    assert s[0] > s[1] > s[2] > 0 and implied_spread(50.0, 80.0, 0.35, cfg) > s[1]
    assert hedge_ratio(50.0, 40.0, 0.35, cfg) > 0


def test_survival_by_hand():
    cfg = CapConfig()
    V, B, sig = 70.0, 20.0, 0.35 * 50 / 70
    x, nu, st = math.log(V / B), -0.5 * sig * sig, sig * math.sqrt(5)
    nc = lambda z: 0.5 * math.erfc(-z / math.sqrt(2))                   # noqa: E731
    q = nc((x + nu * 5) / st) - math.exp(x) * nc((-x + nu * 5) / st)
    assert abs(float(implied_spread(50.0, 40.0, 0.35, cfg)) - 0.6 * -math.log(q) / 5) < 1e-12


def test_no_mispricing_no_model_error_no_trades():
    cfg = CapConfig(firms=5, days=600, mis_sd=0.0, L_dispersion=0.0, shift_rate=0.0)
    sim = simulate_firms(cfg)
    sim["vol"][:] = cfg.sigma_E                                        # the trader knows the true vol
    res = trades(sim, cfg)
    assert res["trades"] == [] and (res["daily"] == 0).all()
