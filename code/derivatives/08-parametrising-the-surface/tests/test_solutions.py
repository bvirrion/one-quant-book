"""Numbers gate: every numerical answer printed in Book 5, Chapter 8 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_svi import (
    KS,
    T3,
    business_time,
    earnings_problem,
    event_variance,
    fit_slice,
    fit_svi,
    implied_move,
    quotes,
    spline_through_mids,
    ssvi_fit,
    svi,
    true_vol,
)

F = fit_slice()
S = ssvi_fit()
E = earnings_problem()


def test_text():
    a, b, rho, m, s = F["params"]
    assert (round(a, 4), round(b, 3), round(rho, 2), round(m, 3), round(s, 3)) == (0.0019, 0.038, -0.63, 0.059, 0.066)
    assert F["inside"] == 27 and round(F["max_err_pts"], 2) == 0.18
    assert (round(F["wing_left"], 3), round(F["wing_right"], 3)) == (0.062, 0.014)
    rho_, eta, gam = S["params"]
    assert (round(rho_, 3), round(eta, 3), round(gam, 3)) == (-0.560, 1.095, 0.478) and all(S["check"].values())
    assert [round(x, 2) for x in (S["rmse_vol_pts"][3], S["rmse_vol_pts"][1], S["rmse_vol_pts"][0])] == [0.09, 0.76, 2.02]
    g = np.linspace(-0.4, 0.25, 261)
    _, spl = spline_through_mids(grid=g)
    sv = np.array([math.sqrt(float(svi(x, *F["params"])) / T3) for x in g])
    tv = np.array([true_vol(x, T3) for x in g])
    assert (round(100 * np.max(np.abs(spl - tv)), 2), round(100 * np.max(np.abs(sv - tv)), 2)) == (0.17, 0.08)
    bid, mid, ask = quotes()
    assert (round(100 * (ask[KS.tolist().index(0.0)] - bid[KS.tolist().index(0.0)]), 1), round(100 * (ask[0] - bid[0]), 1)) == (0.4, 2.0)
    assert (E["q4"], E["q11"], E["q18"], E["q25"]) == (0.32, 0.561, 0.482, 0.443)
    assert (round(E["event_var"], 4), round(100 * E["sd"], 1), round(100 * E["abs_move"], 1), round(100 * E["ex_vol_18"], 1)) == (0.0064, 8.0, 6.4, 32.0)
    w7 = E["w4"] + 3 / 7 * (E["w11"] - E["w4"])
    assert round(100 * math.sqrt(w7 / (7 / 365)), 1) == 49.5
    assert round(100 * business_time()["vol_c"], 2) == 20.34


def test_exercises():
    w0 = float(svi(0.0, *F["params"]))
    assert (round(w0, 5), round(100 * math.sqrt(w0 / T3), 1)) == (0.00670, 16.4)
    beta = F["wing_left"]
    assert round(1 / (2 * beta) + beta / 8 - 0.5, 1) == 7.6
    ev = event_variance(0.3 ** 2 * 5 / 365, 5 / 365, 0.5 ** 2 * 12 / 365, 12 / 365)
    sd, ab = implied_move(ev)
    assert (round(ev, 5), round(100 * sd, 1), round(100 * ab, 1)) == (0.00526, 7.3, 5.8)
    rho_, eta, gam = S["params"]
    phi = eta * 0.00183 ** (-gam)
    assert (round(0.00183 * phi * (1 + abs(rho_)), 3), round(0.00183 * phi * phi * (1 + abs(rho_)), 2)) == (0.064, 1.42)
    assert round(100 * business_time(0.25)["vol_c"], 2) == 25.43
    bid, mid, ask = quotes()
    pm, _ = fit_svi(KS, mid * mid * T3)
    f = np.sqrt(svi(KS, *pm) / T3)
    assert int(np.sum((f >= bid) & (f <= ask))) == 27
    assert (round(pm[1] * (1 - pm[2]), 4), round(pm[1] * (1 + pm[2]), 4)) == (0.0623, 0.0140)
    assert (round(F["wing_left"], 4), round(F["wing_right"], 4)) == (0.0621, 0.0142)


def test_problem():
    assert (round(E["w4"], 6), round(E["w11"], 6), round(0.32 ** 2 * 11 / 365, 6)) == (0.001122, 0.009485, 0.003086)
    t25 = 25 / 365
    assert round(100 * math.sqrt((E["q25"] ** 2 * t25 - E["event_var"]) / t25), 1) == 32.1
    assert round(100 * E["day_after"]) == 32
