"""Numbers gate: every numerical answer printed in Book 5, Chapter 24 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_calib import daily, first_fit, profile, round_trip, scan, transform_study, weights_table, worst_day


def test_transforms():
    t = transform_study()
    assert round(t["atm"], 4) == 6.7509
    assert (round(t["cos"][64], 3), f"{t['cos'][128]:.1e}", f"{t['cos'][256]:.1e}") == (0.012, "8.6e-05", "4.1e-07")
    assert (f"{t['fft'][1024]:.1e}", f"{t['fft'][4096]:.1e}", f"{t['fft'][16384]:.0e}") == ("2.1e-04", "1.8e-06", "2e-07")
    assert f"{t['narrow']:.1e}" == "3.0e-05"
    assert min(n for n, e in t["cos"].items() if e < 1e-4) == 128
    assert 5 * 160 == 800


def test_first_day_and_weights():
    f = first_fit()
    m = f.model
    assert (round(m.v0, 4), round(m.kappa, 2), round(m.vbar, 4), round(m.eta, 3), round(m.rho, 3)) == (0.0451, 1.82, 0.0518, 0.488, -0.632)
    assert round(100 * f.rmse, 2) == 0.22
    assert (round(2 * m.kappa * m.vbar, 2), round(m.eta ** 2, 2)) == (0.19, 0.24)
    w = weights_table()
    assert w["counts"] == {"no bid": 0, "crossed": 1, "wide": 1, "far": 0} and w["kept"] == 18
    exp = (1 / 12, 0.25, 0.5, 1.0)
    assert [round(100 * w["vega"][t], 2) for t in exp] + [round(100 * w["vega"]["all"], 2)] == [0.35, 0.21, 0.14, 0.11, 0.22]
    assert [round(100 * w["equal"][t], 2) for t in exp] + [round(100 * w["equal"]["all"], 2)] == [0.46, 0.15, 0.12, 0.06, 0.24]
    assert round(math.sqrt(12) ** 2) == 12


def test_profile():
    p = profile()
    assert [round(100 * p[e]["rmse"], 2) for e in (0.35, 0.45, 0.55, 0.65)] == [0.29, 0.23, 0.23, 0.27]
    r = [100 * v["rmse"] for v in p.values()]
    assert max(r) - min(r) < 0.3


def test_daily_and_named_result():
    free, reg = daily(0.0), daily(1e-3)
    assert set(free["dropped"]) == {2}
    assert round(free["max_d_eta"], 3) == 0.235 and round(reg["max_d_eta"], 3) == 0.071
    assert (round(100 * free["sd_d_conv"], 2), round(100 * reg["sd_d_conv"], 2)) == (0.36, 0.07)
    assert (round(100 * free["mean_rmse"], 3), round(100 * reg["mean_rmse"], 3)) == (0.291, 0.303)
    assert round(float(np.mean(free["iterations"]))) == 8
    assert 100 * max(free["rmse"]) < 0.45 and round(100 * max(free["rmse"]), 2) == 0.42
    s = scan()
    assert s["chosen"] == 1e-3 and round(100 * s["rows"][1e-3]["d_rmse"], 3) == 0.012
    assert round(s["rows"][3e-4]["max_d_eta"], 3) == 0.133
    w = worst_day()
    assert (w["day"], round(w["eta_before"], 2), round(w["eta_after"], 2)) == (58, 0.51, 0.28)
    assert (round(100 * w["rmse_before"], 2), round(100 * w["rmse_after"], 2)) == (0.31, 0.31)
    assert (round(100 * w["conv_before"], 2), round(100 * w["conv_after"], 2)) == (1.32, 0.39)
    assert round(100 * (w["conv_before"] - w["conv_after"]), 2) == 0.93 and round(-100 * w["conv_move_reg"], 2) == 0.18
    assert round(100 * (w["conv_before"] - w["conv_after"]) * 100_000, -3) == 93_000


def test_equal_weights_wander():
    e, free = daily(0.0, True), daily(0.0)
    assert (round(e["max_d_eta"], 3), round(float(np.std(np.diff(e["eta"]))), 3)) == (0.255, 0.066)
    assert round(float(np.std(np.diff(free["eta"]))), 3) == 0.089


def test_round_trip():
    r = round_trip()
    got, want = r["clean"], r["truth"]
    assert all(abs(a - b) < 1e-11 for a, b in zip((got.v0, got.kappa, got.vbar, got.eta, got.rho),
                                                   (want.v0, want.kappa, want.vbar, want.eta, want.rho), strict=True))
    sd = r["sd"]
    assert (round(sd["v0"], 4), round(sd["eta"], 3), round(sd["rho"], 3), round(sd["vbar"], 4), round(sd["kappa"], 2)) == \
        (0.0007, 0.049, 0.046, 0.0024, 0.56)
    assert round(100 * r["atm_vol_sd"], 2) == 0.16 and round(100 * sd["kappa"] / 2.0) == 28 and round(r["condition"]) == 30


def test_expected_noise_floor():
    assert round(0.3 * math.sqrt(13 / 18), 3) == 0.255
