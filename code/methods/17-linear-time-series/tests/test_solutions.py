"""Numbers gate: every numerical answer printed in Book 4, Chapter 17 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_tsa import (
    acf,
    ar1,
    df_distribution,
    half_life_mc,
    kendall_curve,
    load,
    long_memory,
    mackinnon_crit,
    problem,
    spread_memory,
    spurious,
)

P = problem()


def r(x, d=2):
    return round(float(x), d)


def test_data_and_series():
    assert (P["n"], str(P["start"]), str(P["end"])) == (12574, "1976-06-01", "2026-09-22")
    assert (r(P["mean"], 1), r(P["min"]), r(P["max"]), r(P["last"])) == (84.5, -241, 291, 25)
    assert r(P["acf1"], 4) == 0.9987 and r(acf(load()["spread"], 250)[250], 2) == 0.64
    assert r(P["sd_changes"], 1) == 4.6 and [r(v, 3) for v in P["acf_changes"][:3]] == [0.015, 0.015, -0.027]
    assert r(2 / math.sqrt(12573), 3) == 0.018 and P["p_aic"] == 10 and np.max(np.abs(P["yw_changes"])) < 0.035


def test_ar1_and_unit_root():
    assert (r(P["rho"], 5), r(P["se"], 5), round(P["half_life"]), r(P["t_unit"])) == (0.99875, 0.00045, 552, -2.79)
    assert r(P["p_normal"], 3) == 0.003 and r(P["half_life_years"], 1) == 2.2
    assert (r((1 + 3 * P["rho"]) / P["n"], 5), r(P["rho_kendall"], 5), round(P["half_life_kendall"]), r(P["half_life_kendall_years"], 1)) == (
        0.00032, 0.99906, 739, 2.9)
    c = P["crit"]
    assert (r(c[0]), r(c[1]), r(c[2])) == (-3.43, -2.86, -2.57)
    from firm_tsa import adf
    s = load()["spread"]
    assert [r(adf(s, lags=k)["tau"]) for k in (0, 5, 10, 20)] == [-2.79, -2.74, -3.13, -3.55]
    assert (P["adf_lags"], r(P["tau_adf"])) == (34, -3.14)
    d = load()
    assert r(ar1(d["spread"][d["dates"] >= "1990-01-02"])["t_unit"]) == -2.01


def test_simulations():
    tau = df_distribution()
    assert [r(q) for q in np.quantile(tau, [0.01, 0.05, 0.1])] == [-3.46, -2.89, -2.57]
    assert [r(v) for v in mackinnon_crit("c", 500)] == [-3.44, -2.87, -2.57]
    assert r(np.mean(df_distribution(n=2000, reps=20_000, seed=9) <= -2.792), 2) == 0.06
    s = spurious()
    assert (r(s["share"]), r(s["median_r2"]), r(s["share_diff"], 3)) == (0.89, 0.17, 0.050)
    m = half_life_mc(P["rho_kendall"], P["n"], reps=4000)
    assert (round(m["median"]), round(m["q10"]), round(m["q90"]), r(m["p_not_reject"])) == (576, 352, 969, 0.57)


def test_long_memory():
    lm = long_memory()
    assert (r(lm["rho1"]), r(lm["h_rs"]), r(lm["h_gph"]), r(lm["h_rs_white"]), r(lm["h_gph_white"])) == (0.41, 0.78, 0.71, 0.53, 0.46)
    assert lm["acf"][10] / lm["acf_ar1"][10] > 500
    sm = spread_memory()
    assert (r(sm["h_gph_changes"]), r(sm["h_gph_changes"] - 0.5), r(math.pi / math.sqrt(24 * 112))) == (0.34, -0.16, 0.06)
    assert int(12574**0.5) == 112


def test_ablation_and_step():
    """WRITING section 9: Kendall's formula is checked against simulation where it is claimed (moderate phi) and the
    half-life distribution is stable when the number of simulated histories is halved."""
    k = kendall_curve(1000, [0.5, 0.9], reps=4000)
    assert all(abs(b - f) < 0.0008 for _, b, f in k)
    m2 = half_life_mc(P["rho_kendall"], P["n"], reps=2000, seed=11)
    assert abs(m2["median"] - 576) < 30 and abs(m2["p_not_reject"] - 0.57) < 0.04


def test_exercises():
    assert (r(math.log(0.5) / math.log(0.98), 1), r(0.98**20)) == (34.3, 0.67)
    assert (r(2 / 5, 1), r(0.5 / 1.25, 1)) == (0.4, 0.4)
    w = [1.0]
    for j in range(1, 4):
        w.append(w[-1] * (j - 1 - 0.3) / j)
    assert [round(v, 4) for v in w] == [1.0, -0.3, -0.105, -0.0595]
    assert (r(-(1 + 3 * 0.99) / 1000, 4), r(math.log(0.5) / math.log(0.99), 1), r(math.log(0.5) / math.log(0.99 + 0.00397), 1)) == (
        -0.004, 69.0, 114.6)
    assert (r(0.5 / 1.3, 3), r(0.5 * 0.5 / 1.3 - 0.3, 3)) == (0.385, -0.108)
    assert (r(mackinnon_crit("c", 100)[1], 3), r(mackinnon_crit("c", 12574)[1], 3)) == (-2.891, -2.862)
    assert r(-4 / 250, 3) == -0.016
