"""Numbers gate: every numerical answer printed in Book 5, Chapter 4 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_greeks import derman_kamal_sd, gamma_path, hedge_short_straddle, problem, straddle

P = problem()


def test_text():
    assert round(P["vega_usd"], -3) == 23_000 and round(-P["theta_day"] * 1e5, -2) == 7_600
    assert round(P["exp_loss_usd"], -2) == 115_100
    assert (round(P["premium"], 4), round(P["straddle25"], 4), round(P["vega_pt"], 4)) == (4.6059, 5.7570, 0.2302)
    d, pnl, pred = gamma_path()
    assert np.max(np.abs(pnl - pred)) < 0.09 and round(abs(pnl[-1] - pred[-1]), 2) == 0.04
    assert (round(P["dk_daily"], 3), round(P["fair_sd"], 3)) == (0.890, 0.865)
    daily = hedge_short_straddle(20_000, 21, vol_real=0.20, seed=4)
    eight = hedge_short_straddle(20_000, 168, vol_real=0.20, seed=4)
    assert (round(daily.std(), 2), round(eight.std(), 2), round(eight.std(), 3)) == (0.85, 0.31, 0.308)
    assert round(2 * P["vega_pt"], 2) == 0.46 and round(P["fair_sd"], 2) == 0.87
    assert (round(-P["theta_day"], 4), round(P["gamma"], 4), round(P["be_move"], 3)) == (0.0757, 0.1381, 1.047)
    assert round(P["be_move_252"], 2) == 1.26
    a = hedge_short_straddle(20_000, 84, seed=6)
    b = hedge_short_straddle(20_000, 84, hedge_vol=0.25, seed=6)
    assert (round(a.std(), 2), round(b.std(), 2)) == (0.72, 0.54) and abs(a.mean() - b.mean()) < 0.05
    assert round(P["exp_loss"], 3) == 1.151


def test_exercises():
    assert round(P["delta"], 4) == 0.0230
    assert round(-0.5 * 0.04 * 1e4 * P["gamma"], 2) == -27.63
    cg = 5000
    assert (round(cg * 0.02 ** 2, 2), round(-cg * 0.04 / 365, 2), round(cg * 0.02 ** 2 - cg * 0.04 / 365, 2)) == (2.00, -0.55, 1.45)
    assert round(derman_kamal_sd(straddle(100, 100, 1 / 12, 0, 0.2)["vega"], 0.2, 21), 3) == 0.890
    assert (round(P["at_real_mean"], 3), round(P["at_real_sd"], 3)) == (-1.147, 1.082)


def test_problem():
    assert round(P["premium_usd"]) == 460_595
    assert round(P["delta"] * 1e5) == 2_303
    assert (round(P["cash_gamma"], 2), round(P["gamma_1pct"], 2)) == (690.70, 13.81)
    assert (round(P["vega_usd"]), round(-P["theta_day"] * 1e5)) == (23_023, 7_569)
    assert (round(P["be_move"], 3), round(P["be_move_252"], 3)) == (1.047, 1.260)
    assert (round(P["exp_loss"], 4), round(P["exp_loss_usd"])) == (1.1510, 115_104)
    assert round(P["loss_from_vega"], 4) == 1.1512
    assert (round(P["daily_mean"], 3), round(P["daily_sd"], 3)) == (-1.145, 1.183)
    assert round(P["hourly_sd"], 3) == 0.620 and round(100 * P["p_loss_daily"], 1) == 87.3
    assert (round(P["fair_sd"], 3), round(problem()["fair_sd"], 3)) == (0.865, 0.865)
    assert round(P["daily_sd_usd"], -2) == 118_300
    fair = hedge_short_straddle(20_000, 21, vol_real=0.20, seed=1)
    assert round(fair.mean(), 3) == 0.003 and math.isclose(fair.std(), P["fair_sd"])
