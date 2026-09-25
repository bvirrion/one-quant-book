import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "synthvol"))
from firm_synthvol import VolConfig  # noqa: E402
from firm_tailhedge import evaluate, put_programme, static_mix, trend_overlay  # noqa: E402


def test_a_still_market_only_bleeds():
    cfg = VolConfig(jump_rate=0.0)
    r, v = np.zeros(63), np.full(63, cfg.theta)
    p = put_programme(r, v, cfg, 0.05, 21)
    assert p["rolls"] == 4 and (p["hedge_pnl"] <= 1e-12).all() and p["nav"][-1] < 1


def test_the_put_pays_below_the_strike():
    cfg = VolConfig(jump_rate=0.0)
    r = np.zeros(21)
    r[5] = math.log(0.7)                             # a 30% fall inside the month
    v = np.full(21, cfg.theta)
    p = put_programme(r, v, cfg, 0.05, 21)
    assert p["nav"][-1] > 0.9                        # the put covers the fall below 95%


def test_static_mix_trend_and_evaluate():
    r = np.full(252, math.log(1.001))
    assert abs(static_mix(r, 1.0)[-1] - 1.001**252) < 1e-9
    assert abs(static_mix(r, 0.0)[-1] - 1.0) < 1e-12
    tr = trend_overlay(np.concatenate([np.full(252, 0.001), np.full(10, 0.001)]), 0.5, 252)
    assert abs(tr[-1] / tr[-11] - (1 + 1.5 * math.expm1(0.001)) ** 10) < 1e-9
    e = evaluate(np.concatenate([np.full(25, 1.0), np.full(25, 2.0), np.full(25, 1.0)]))
    assert e["max_dd"] == -0.5 and e["worst_month"] == -0.5
