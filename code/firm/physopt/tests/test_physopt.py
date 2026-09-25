import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_physopt import (  # noqa: E402
    Facility,
    TwoFactor,
    diversion,
    hedge_programme,
    intrinsic,
    plans,
    spread_option_pairs,
    transport,
)

F0 = [2.60, 2.62, 2.68, 2.74, 2.78, 2.80, 2.90, 3.20, 3.45, 3.50, 3.30, 3.00]
T = [k / 12 + 1 / 24 for k in range(12)]
FAC = Facility(capacity=6, max_inject=2, max_withdraw=3, cost_in=0.02, cost_out=0.02)
MODEL = TwoFactor(1.5, 0.60, 0.20, 0.30)


def test_plans_match_book_6_intrinsic():
    value, plan = intrinsic(FAC, F0, [1.0] * 12)
    assert plans(FAC, np.array([F0]), np.array([0]))[0].tolist() == plan
    assert abs(hedge_programme(FAC, MODEL, F0, T, 20, roll=False)["intrinsic"] - value) < 1e-12


def test_static_locks_intrinsic_and_rolling_never_loses_without_costs():
    s = hedge_programme(FAC, MODEL, F0, T, 200, roll=False)
    r = hedge_programme(FAC, MODEL, F0, T, 200)
    assert np.allclose(s["pnl"], s["intrinsic"]) and (r["pnl"] >= r["intrinsic"] - 1e-9).all()
    assert (hedge_programme(FAC, MODEL, F0, T, 200, cost=0.05)["pnl"] < r["pnl"]).all()


def test_pairs_transport_and_diversion():
    assert len(spread_option_pairs(FAC, F0, T, MODEL)) == 6
    t = transport([3.0, 3.0], [3.5, 3.05], [0.1, 0.2], 0.1, 0.4, 0.4, 0.9)
    assert abs(t["intrinsic"] - 0.4) < 1e-12 and t["option"] > t["intrinsic"]
    d = diversion(10.0, 10.5, 0.8, 0.25, 0.6, 0.6, 0.8)
    assert d["intrinsic_switch"] == 0.0 and d["switch"] > 0
