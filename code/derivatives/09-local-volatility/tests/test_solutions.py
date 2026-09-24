"""Numbers gate: every numerical answer printed in Book 5, Chapter 9 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_localvol import (
    GRID_K,
    GRID_T,
    S0,
    atm_skew,
    dynamics,
    forward_smile,
    fwd_skew_ratio,
    implied,
    local,
    mc_smile,
    w_fn,
)
from firm_bs import black, implied_vol
from firm_localvol import build_grid, simulate

FS = forward_smile()
R = fwd_skew_ratio(FS)
MC = {r["strike"]: r for r in mc_smile()}


def test_text_local_vs_implied():
    assert (round(100 * implied(0, 0.25), 1), round(100 * implied(-0.1, 0.25), 1)) == (16.4, 21.1)
    assert (round(100 * local(0, 0.25), 1), round(100 * local(-0.1, 0.25), 1)) == (17.7, 27.4)
    assert (round(atm_skew(implied, 0.25), 2), round(atm_skew(local, 0.25), 2)) == (-0.47, -0.92)
    assert round(atm_skew(local, 0.25) / atm_skew(implied, 0.25), 2) == 1.98


def test_text_repricing_and_bias():
    errs = {k: 100 * (r["mc_vol"] - r["surface_vol"]) for k, r in MC.items()}
    assert max(abs(e) for e in errs.values()) < 0.11 and all(e > 0 for e in errs.values())
    fine = build_grid(w_fn, GRID_T, GRID_K)
    st, _ = simulate(fine, S0, 0.5, 504, 200_000, 7)
    for k in (80, 90, 100, 110, 120):
        right = "C" if k >= S0 else "P"
        pay = np.maximum(st - k, 0) if right == "C" else np.maximum(k - st, 0)
        e = 100 * (implied_vol(float(pay.mean()), S0, k, 0.5, 1.0, right) - implied(math.log(k / S0), 0.5))
        assert abs(e) < 0.12
    st4, _ = simulate(fine, S0, 0.5, 504 * 2, 200_000, 7)
    for k in (80, 100, 120):
        right = "C" if k >= S0 else "P"
        pay = np.maximum(st4 - k, 0) if right == "C" else np.maximum(k - st4, 0)
        assert abs(100 * (implied_vol(float(pay.mean()), S0, k, 0.5, 1.0, right) - implied(math.log(k / S0), 0.5))) < 0.07


def test_text_dynamics_and_forward():
    d = dynamics()
    before = dict(zip(d["strikes"], d["before"], strict=True))
    after = dict(zip(d["strikes"], d["after"], strict=True))
    assert (round(100 * before[100], 1), round(100 * after[95], 1), round(100 * before[95], 1)) == (16.4, 23.4, 18.8)
    assert round((after[95] - before[100]) / (before[95] - before[100]), 1) == 2.9
    d1 = dynamics(move=-0.01, strikes=(99, 100, 101), n=400_000)
    lv, ss = d1["after"][0] - d1["before"][1], d1["before"][0] - d1["before"][1]
    assert round(lv / ss, 1) == 2.7 and round(100 * lv, 2) == 1.31
    assert (round(R["fwd_skew"], 2), round(R["today_skew"], 2), round(R["ratio"], 2)) == (-0.19, -0.34, 0.57)
    assert (round(100 * R["fwd_atm"], 1), round(100 * R["today_atm"], 1)) == (20.7, 17.8)
    assert all(d1["after"][i] > d1["before"][i] for i in range(3))


def test_exercises():
    assert round(100 * math.sqrt(0.045 / 0.9), 1) == 22.4
    assert round(100 * (implied(0, 0.25) + 2 * atm_skew(implied, 0.25) * -0.1), 1) == 25.7
    assert (round(100 * math.sqrt(0.5 * 0.0225 + 0.5 * 0.09), 1), round(100 * math.sqrt(0.8 * 0.09 + 0.2 * 0.0225), 1)) == (23.7, 27.7)
    fwd = math.sqrt((implied(0, 1.0) ** 2 - implied(0, 0.5) ** 2 * 0.5) / 0.5)
    assert (round(100 * implied(0, 0.5), 2), round(100 * implied(0, 1.0), 2), round(100 * fwd, 2), round(100 * R["fwd_atm"], 2)) == (17.79, 19.19, 20.49, 20.68)
    assert round(2 * 0.47 * 0.01 * 100, 2) == 0.94
    r50 = {r["strike"]: r for r in mc_smile(n=50_000)}
    assert (round(100 * (r50[90]["mc_vol"] - r50[90]["surface_vol"]), 2), round(100 * r50[90]["se_vol"], 2)) == (-0.04, 0.13)
    assert (round(100 * (MC[90]["mc_vol"] - MC[90]["surface_vol"]), 2), round(100 * MC[90]["se_vol"], 2)) == (0.11, 0.06)


def test_problem():
    errs = [round(100 * (MC[k]["mc_vol"] - MC[k]["surface_vol"]), 2) for k in (80, 100, 110)]
    assert errs == [0.08, 0.06, 0.09]
    by = {round(x, 3): (v, t) for x, v, t in FS}
    shifted = by[0.95][1] - R["today_atm"] + R["fwd_atm"]
    assert (round(100 * by[0.95][0], 1), round(100 * shifted, 1)) == (21.8, 22.5)
    p_lv, p_sh = 100 * black(1, 0.95, 0.5, 1, by[0.95][0], "P"), 100 * black(1, 0.95, 0.5, 1, shifted, "P")
    assert (round(p_lv, 2), round(p_sh, 2), round(p_sh - p_lv, 2)) == (3.82, 4.00, 0.18)
