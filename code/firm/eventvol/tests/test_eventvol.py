import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_eventvol import EventConfig, event_variance, implied_move, straddle_pnl, windows  # noqa: E402


def test_event_variance_is_recovered_from_two_expiries():
    d, E, t1, t2 = 0.3**2, 0.05**2, 10 / 252, 30 / 252
    v1, v2 = math.sqrt(d + E / t1), math.sqrt(d + E / t2)
    assert abs(event_variance(v1, t1, v2, t2) - E) < 1e-12
    assert abs(implied_move(E) - 0.05 * math.sqrt(2 / math.pi)) < 1e-12


def test_crush_and_no_event_paths():
    cfg = EventConfig(n=200)
    w = windows(cfg, 3, True)
    b = straddle_pnl(w, cfg, 8)
    assert (b["iv_after"] < b["iv_before"]).all()                      # the event variance is gone after the gap
    w0 = windows(cfg, 3, False)
    b0 = straddle_pnl(w0, cfg, 8)
    assert np.allclose(b0["iv_before"] ** 2, w0["vol"] ** 2 * 1.25)


def test_flat_path_loses_only_time_and_costs():
    cfg = EventConfig(n=5, vrp=0.0)
    w = windows(cfg, 2, False)
    w["S"] = np.ones_like(w["S"])
    b = straddle_pnl(w, cfg, 1)
    assert (b["hedge"] == 0).all() and (b["option"] < 0).all()        # theta only, no hedge P&L on a still path
    assert np.allclose(b["total"], b["option"] - b["option_cost"] - b["hedge_cost"])
