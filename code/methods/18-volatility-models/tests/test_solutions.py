"""Numbers gate: every numerical answer printed in Book 4, Chapter 18 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_vol import evaluate, fits, garch_fit, ghost, har_vs_ar1, load, rv_convergence

F = fits()
G = ghost()
E = evaluate()


def r(x, d=2):
    return round(float(x), d)


def test_fits():
    n, t, j = F["normal"], F["t"], F["gjr_t"]
    assert load()["r"].size == 7098
    assert (r(n["omega"], 4), r(n["alpha"], 3), r(n["beta"], 3), r(n["se"][1], 3), r(n["se"][2], 3)) == (0.0010, 0.029, 0.968, 0.003, 0.004)
    assert (r(t["omega"], 4), r(t["alpha"], 3), r(t["beta"], 3), r(t["nu"], 1), r(t["se"][1], 3), r(t["se"][2], 3), r(t["se"][3], 1)) == (
        0.0007, 0.030, 0.968, 7.2, 0.003, 0.003, 0.6)
    assert (r(j["omega"], 4), r(j["alpha"], 3), r(j["beta"], 3), r(j["gamma"], 3), r(j["se"][1], 3), r(j["se"][2], 3), r(j["se"][3], 3)) == (
        0.0006, 0.027, 0.969, 0.006, 0.005, 0.004, 0.005)
    assert (r(n["persistence"], 4), round(n["half_life"]), r(t["persistence"], 4), round(t["half_life"]), r(j["persistence"], 4), round(j["half_life"])) == (
        0.9973, 255, 0.9984, 445, 0.9986, 482)
    assert round(t["loglik"] - n["loglik"]) == 141
    assert (r(math.sqrt(t["uncond_var"])), r(load()["r"].std())) == (0.67, 0.58)
    assert (r(n["se_hessian"][1], 4), r(n["se"][1], 4), r(n["se_hessian"][2], 4), r(n["se"][2], 4)) == (0.0026, 0.0033, 0.0028, 0.0035)
    assert (r(t["se"][1], 4), r(t["se_hessian"][1], 4)) == (0.0032, 0.0033)
    assert round(100 * (n["se"][1] / n["se_hessian"][1] - 1)) in (24, 25, 26)


def test_ghost_and_impulse():
    assert (str(G["exit_date"]), r(G["exit_return"], 1), str(G["day"]), r(G["day_return"], 1)) == ("2022-11-11", 3.5, "2023-11-02", 1.2)
    assert (r(G["win_before"], 3), r(G["win_after"], 3), r(G["drop_pct"], 1)) == (0.538, 0.496, -7.8)
    assert (r(G["garch_before"], 3), r(G["garch_after"], 3), r(G["ewma_before"], 3), r(G["ewma_after"], 3)) == (0.424, 0.465, 0.410, 0.490)
    assert round(math.log(0.5) / math.log(0.94)) == 11


def test_evaluation():
    assert E["n_test"] == 3002
    assert (r(E["garch"]["qlike"], 3), r(E["ewma"]["qlike"], 3), r(E["window"]["qlike"], 3)) == (-0.521, -0.495, -0.435)
    assert (r(E["dm_garch_ewma"][0]), r(E["dm_garch_ewma"][1], 3), r(E["dm_garch_window"][0]), r(E["dm_ewma_window"][0])) == (-2.76, 0.006, -4.10, -2.48)
    assert (r(E["garch"]["mz"][1]), r(E["ewma"]["mz"][1]), r(E["window"]["mz"][1])) == (0.77, 0.60, 0.56)
    assert (r(E["garch"]["mz"][2], 3), r(E["ewma"]["mz"][2], 3), r(E["window"]["mz"][2], 3)) == (0.030, 0.027, 0.010)
    f = E["fit_train"]
    assert (r(f["persistence"], 4), round(f["half_life"])) == (0.9982, 392)
    assert (r(E["garch"]["qlike"] - E["window"]["qlike"], 3), r(E["ewma"]["qlike"] - E["window"]["qlike"], 3)) == (-0.086, -0.060)


def test_realised_and_har():
    rc = dict(rv_convergence())
    assert (round(100 * rc[1]), round(100 * rc[78]), r(100 * rc[390], 1)) == (144, 16, 7.3)
    assert (round(100 * math.sqrt(2)), round(100 * math.sqrt(2 / 78)), r(100 * math.sqrt(2 / 390), 1)) == (141, 16, 7.2)
    h = har_vs_ar1()
    assert [r(v) for v in h["beta"][1:]] == [0.35, 0.27, 0.20] and r(h["r2"]) == 0.37
    assert (r(h["q_har"], 3), r(h["q_ar"], 3), r(h["dm"][0], 1)) == (-0.479, -0.473, -4.5)
    assert (r(h["mse_har_iv"], 4), r(h["mse_ar_iv"], 4)) == (0.0073, 0.0079)


def test_ablation_and_stability():
    """WRITING section 9: the forecast ranking survives a different split (2012), and the ghost is the window's alone:
    removing the exiting return from the history removes the drop."""
    e2 = evaluate("2012-01-01")
    assert e2["garch"]["qlike"] < e2["ewma"]["qlike"] < e2["window"]["qlike"]
    from firm_volfcst import rolling_var
    rr = load()["r"].copy()
    i = int(np.flatnonzero(load()["dates"] == "2022-11-11")[0])
    rr[i] = 0.0
    w = np.sqrt(rolling_var(rr, 250))
    assert w[G["index"] + 1] > w[G["index"]]                                 # without the exit, the window rises with the day


def test_exercises():
    hb = 0.02 / (1 - 0.98)
    assert (r(hb), r(math.sqrt(252 * hb), 1), r(math.log(0.5) / math.log(0.98), 1)) == (1.0, 15.9, 34.3)
    assert (r(math.log(0.5) / math.log(0.94), 1), round(100 * (1 - 0.94**20))) == (11.2, 71)
    assert r(100 * math.sqrt(2 / 288), 1) == 8.3
    avg = np.mean([hb + 0.98 ** (k - 1) * 3 * hb for k in range(1, 11)])
    assert (r(avg), r(math.sqrt(avg))) == (3.74, 1.93)
    assert (r(1 / 0.5 + math.log(0.5)), r(1 / 1.5 + math.log(1.5))) == (1.31, 1.07)
    w = math.sqrt((249 * 0.25 + 12.25) / 250)
    assert (r(w * w, 3), r(w, 3), r(100 * (0.5 / w - 1), 1)) == (0.298, 0.546, -8.4)
    assert garch_fit is not None
