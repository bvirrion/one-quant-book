"""Numbers gate: every numerical answer printed in Book 4, Chapter 16 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_linreg import attenuation, factor_months, fit_all, flip, hedge, hedge_mc, panel_truth

F = factor_months()
A = fit_all()
H = hedge()
MC = hedge_mc()
T = panel_truth()


def r(x, d=2):
    return round(float(x), d)


def test_hook_and_collinearity():
    f = flip(1)
    assert [r(v) for v in f["b_prev"]] == [0.52, 0.84] and [r(v) for v in f["b_next"]] == [-1.59, 2.76]
    assert (r(f["sum_prev"]), r(f["sum_next"]), r(f["corr_fits"])) == (1.36, 1.17, 0.92)
    assert r(1 / (1 - 0.97**2), 1) == 16.9 and r(F["vif"][0], 1) == 18.5
    b = F["betas"]
    assert (r(b[:, 0].std()), r(b[:, 1].std()), r((b[:, 0] + b[:, 1]).std())) == (1.21, 1.23, 0.23)
    assert (int(np.sum(b[:, 0] < 0)), int(np.sum(b[:, 1] < 0))) == (6, 8)
    assert r(b[:, 2:].std(0).min()) == 0.26 and r(b[:, 2:].std(0).max()) == 0.32
    assert r(b[:, :2].min(), 1) == -2.7 and r(b[:, :2].max(), 1) == 3.3


def test_regularisation():
    assert (r(100 * A["oracle_r2"], 1), r(100 * A["ols"]["r2"], 1), r(100 * A["ridge"]["r2"], 1), r(100 * A["lasso"]["r2"], 1),
            r(100 * A["enet"]["r2"], 1)) == (5.0, 1.5, 3.5, 3.4, 3.2)
    nz = list(np.flatnonzero(np.abs(A["lasso"]["beta"]) > 1e-12))
    assert nz == [0, 11, 18, 22, 25] and len(set(nz) & {0, 3, 11, 12, 25}) == 3
    assert r(A["lasso"]["lam"], 3) == 0.040 and A["lasso"]["nonzero"] == 5
    assert {18 // 10, 22 // 10} == {1, 2}                                          # the misses are neighbours in the true blocks


def test_hedge():
    assert (r(H["b_ols"]), r(H["lam"]), r(H["lam_hat"]), r(H["b_corrected"]), r(H["b_week"]), r(H["b_tls"])) == (0.68, 0.80, 0.80, 0.85, 0.80, 0.74)
    assert (r(H["rho1"], 3), r(H["lam_week"])) == (-0.098, 0.95) and r(2 * 0.14**2, 3) == 0.039
    assert (r(MC["mean"][0], 3), r(MC["sd"][0], 3), r(MC["mean"][1], 3), r(MC["sd"][1], 3), r(MC["mean"][2], 3), r(MC["sd"][2], 3)) == (
        0.683, 0.017, 0.862, 0.095, 0.810, 0.022)
    assert (r(H["resid_true"], 3), r(H["resid_ols"], 3), r(H["resid_corrected"], 3), r(H["resid_week"], 3), r(H["resid_unhedged"])) == (
        0.049, 0.086, 0.049, 0.053, 0.34)
    assert round(100 * (H["resid_ols"] / H["resid_true"] - 1)) == 74
    assert r(attenuation(sd_level=0.07)) == 0.94 and r(attenuation(horizon=21)) == 0.99 and r(0.8 * 0.85, 3) == 0.68


def test_panel():
    assert (r(T["sd_ols"], 3), r(T["classical"], 3), r(T["hc"], 3), r(T["cluster"], 3), r(T["fm"], 3), r(T["fm_nw"], 3)) == (
        0.105, 0.026, 0.026, 0.101, 0.023, 0.022)


def test_ablation_and_sample_size():
    """WRITING section 9: the attenuation disappears when its mechanism (the level error) is removed, and the Monte Carlo
    means are stable when the number of histories is halved (independent seeds)."""
    import qm_linreg as q
    old = q.SD_LEVEL
    q.SD_LEVEL = 0.0
    try:
        h0 = q.hedge_mc(500)
    finally:
        q.SD_LEVEL = old
    assert abs(h0["mean"][0] - 0.85) < 0.005
    h2 = hedge_mc(1000, seed0=90_000)
    assert abs(h2["mean"][0] - MC["mean"][0]) < 0.003 and abs(h2["mean"][2] - MC["mean"][2]) < 0.004


def test_exercises():
    assert (r(1 / 0.19, 1), r(math.sqrt(1 / 0.19), 1)) == (5.3, 2.3) and r(2 / 1.25, 1) == 1.6
    assert (r((0.199 - 0.0392) / 0.199), r(5 * (0.199 - 0.0392) / (5 * (0.199 - 0.0392) + 0.0392))) == (0.80, 0.95)
    rho = 0.97
    assert (r(1 / (1 - rho**2), 1), r(2 / (1 + rho)), r(math.sqrt((1 / (1 - rho**2)) / (2 / (1 + rho))), 1), r(2 / (1 - rho), 1)) == (
        16.9, 1.02, 4.1, 66.7)
