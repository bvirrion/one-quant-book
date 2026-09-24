"""Numbers gate: every numerical answer printed in Book 4, Chapter 19 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_kalman import (
    compare,
    em_path,
    eurusd_returns,
    jump_response,
    load,
    local_level_check,
    local_level_gain,
    pf_vs_kalman,
    sv_filter,
    sv_grid,
    tradeoff,
)

D = load()
C = compare()


def r(x, d=2):
    return round(float(x), d)


def test_data():
    assert (str(D["dates"][0]), str(D["dates"][-1]), D["dates"].size, int(D["bad"].sum())) == ("2010-01-05", "2026-09-22", 4097, 2)
    i = int(np.flatnonzero(D["bad"])[0])
    assert D["wti"][i + 1] == -36.98
    raw_w, raw_b = np.diff(D["wti"]), np.diff(D["brent"])
    assert [r(v) for v in raw_w[D["bad"]]] == [-55.29, 45.89] and [r(v) for v in raw_b[D["bad"]]] == [-2.39, -8.24]
    years = np.array([int(x[:4]) for x in D["dates"]])
    ok = ~np.isnan(D["dw"])
    sl = {y: np.polyfit(D["dw"][ok & (years == y)], D["db"][ok & (years == y)], 1)[0] for y in (2014, 2021, 2026)}
    assert (r(sl[2014]), r(sl[2021]), r(sl[2026])) == (0.41, 0.94, 1.01)
    sd = {y: np.nanstd(D["dw"][years == y]) for y in (2017, 2026)}
    assert (r(sd[2017]), r(sd[2026])) == (0.78, 3.62)


def test_hedge():
    assert (r(C["h"], 3), r(C["q"], 6), r(C["snr"], 5), r(C["mean_x2"])) == (0.508, 0.000238, 0.00047, 1.12)
    assert round(C["half_days"]) == 30 and round(math.log(2) / math.sqrt(0.00047 * 1.12)) == 30
    assert C["n_eval"] == 4035
    assert (r(C["var_unhedged"], 3), r(C["var_static"], 3), r(C["var_roll"], 3), r(C["var_kalman"], 3)) == (3.324, 1.329, 1.276, 1.267)
    assert (r(100 * C["reduction"], 1), r(100 * C["reduction_unscaled"], 1)) == (0.7, -1.4)
    assert (r(C["q_unscaled"], 4), r(C["h_unscaled"])) == (0.0026, 1.14) and round(C["q_unscaled"] / C["h_unscaled"] / C["snr"]) in (4, 5)
    assert r(np.median(C["k_sd"][60:]), 2) == 0.10
    assert (r(C["k_filt"][-1]), r(C["roll"][-1])) == (1.20, 1.28)


def test_tradeoff_and_jump():
    t = {m: (v, h) for m, v, h in tradeoff()}
    assert (r(t[0.1][0], 3), round(t[0.1][1])) == (0.987, 96) and (r(t[1][0], 3), round(t[1][1])) == (0.993, 30)
    assert (r(100 * (t[10][0] - 1), 1), r(t[10][1], 1)) == (0.6, 9.6) and (r(100 * (t[100][0] - 1), 1), r(t[100][1], 1)) == (6.2, 3.0)
    j1, j10, j100 = jump_response(1), jump_response(10), jump_response(100)
    assert (j1["kalman"], j1["roll"], j10["kalman"], j100["kalman"]) == (50, 49, 18, 8)


def test_theory_em_and_particles():
    assert (r(local_level_gain(0.01), 3), r(local_level_gain(1.0), 2)) == (0.095, 0.62)
    c = local_level_check()
    assert abs(c["gain_last"] - c["gain_theory"]) < 1e-9
    e = em_path(40)
    assert (round(e["lls"][0]), round(e["lls"][9]), round(e["lls"][-1]), round(C["loglik"])) == (-4947, -4524, -4502, -4470)
    assert min(np.diff(e["lls"])) > 0 and round(C["loglik"] - e["lls"][-1]) == 32
    p = pf_vs_kalman()
    assert (r(p["ll_pf"]), r(p["ll_kf"]), r(p["max_mean_gap"]), r(p["sd_filter"]), round(p["ess_mean"])) == (-785.06, -784.22, 0.07, 0.45, 1678)
    g = sv_grid()
    assert (g["phi"], g["sigma"], r(g["loglik"], 1), r(g["grid"][(0.95, 0.2)], 1)) == (0.9, 0.4, -568.4, -572.3)
    dates, rr = eurusd_returns()
    sv = sv_filter(rr, 0.9, 0.4)
    k = int(np.argmin(sv["ess"]))
    assert (round(sv["ess"].mean()), round(sv["ess"].min()), str(dates[k]), r(rr[k], 1)) == (4449, 23, "2025-04-03", 2.7)


def test_stability():
    """WRITING section 9: the particle likelihood is stable across seeds at the chosen point, and the hedge comparison
    survives starting the evaluation a year later."""
    dates, rr = eurusd_returns()
    lls = [sv_filter(rr, 0.9, 0.4, seed=s)["loglik"] for s in (5, 6, 7)]
    assert max(lls) - min(lls) < 1.5
    c2 = compare(start=310)
    assert c2["var_kalman"] < c2["var_roll"]


def test_exercises():
    q = 0.04
    p = (q + math.sqrt(q * q + 4 * q)) / 2
    k = p / (1 + p)
    assert (r(p, 3), r(k, 3), r(math.log(0.5) / math.log(1 - k), 1)) == (0.221, 0.181, 3.5)
    P = 0.0102
    F = 4 * P + 0.5
    K = P * 2 / F
    assert (r(F, 4), r(K, 4), r(0.8 - 0.4 * K, 3), r(P * (1 - 2 * K), 4)) == (0.5408, 0.0377, 0.785, 0.0094)
    assert (r(local_level_gain(0.0004), 4), r(1 - local_level_gain(0.0004), 3)) == (0.0198, 0.980)
    assert r(1 / (0.25 + 0.09 + 0.01 + 0.0025 + 0.0025), 1) == 2.8
