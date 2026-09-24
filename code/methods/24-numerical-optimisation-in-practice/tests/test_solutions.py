"""Numbers gate: every numerical answer printed in Book 4, Chapter 24 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_optim import (
    START,
    classify,
    daily,
    days,
    diagnostics,
    fit,
    lasso_prox,
    multistart,
    ncm_compare,
    rates,
    sgd_demo,
    valley,
)


def r(x, d=2):
    return round(float(x), d)


def test_rates_and_methods():
    rt = rates()
    assert (r(rt["gd"][0], 1), r(rt["gd"][100], 3), r(rt["gd"][200], 4), r(rt["nesterov"][100] * 1e6)) == (50.5, 0.067, 0.009, 5.14)
    assert np.allclose(rt["gd"][1:], rt["theory_gd"][1:], rtol=1e-9)
    assert (rt["newton_iters"], rt["lbfgs_iters"]) == (2, 7)
    lp = lasso_prox()
    assert (r(lp["ista"][50] * 1e4, 1), r(lp["ista"][100] * 1e4, 1)) == (7.6, 4.6)
    assert 5e-8 < lp["fista"][50] < 2e-7 and int(np.argmax(lp["fista"] < 1e-10)) == 65
    n = ncm_compare()
    assert (n["iters_admm"], n["iters_ap"], r(n["gap"] * 1e9, 1)) == (91, 74, 1.4)
    s = sgd_demo()
    assert (r(s["err_rm"], 3), r(s["err_const"], 3)) == (0.009, 0.113)


def test_calibration():
    out = fit(days(1)[0], START)
    assert (r(out["p"][0]), r(out["p"][1], 1), round(out["p"][2]), r(out["rmse"] * 1e4)) == (0.59, 2.9, 55, 96.33)
    ends = multistart()
    c = classify(ends, ends[:, 3].min())
    assert c == {"best": 28, "mirror": 35, "boundary": 26, "other": 11}
    assert np.all(ends[(np.maximum(ends[:, 1], ends[:, 2]) > 900), 3] >= 2 * ends[:, 3].min())
    d = diagnostics()
    assert (r(d["cond"], 1), r(d["corr"][0, 2])) == (10.5, 0.96)
    prof = dict((round(t), 1000 * e) for t, e in valley()["profile"])
    near = {t: e for t, e in prof.items() if t in (42, 62, 89)}
    assert {t: r(e, 1) for t, e in near.items()} == {42: 12.3, 62: 9.9, 89: 12.9}


def test_daily():
    d0, d1 = daily(0.0), daily(0.01)
    assert (r(d0["median_jump"], 1), r(d0["max_jump"], 1), d0["max_day"]) == (4.5, 30.7, 189)
    assert (r(d0["before"][2], 1), r(d0["after"][2], 1), r(d0["rmse_before"], 5), r(d0["rmse_after"], 5)) == (56.8, 87.6, 0.00926, 0.00921)
    assert (r(d1["median_jump"], 1), r(d1["max_jump"], 1)) == (1.9, 9.5)
    assert (r(d0["mean_rmse"], 5), r(d1["mean_rmse"], 5), r(100 * (d1["mean_rmse"] / d0["mean_rmse"] - 1), 1)) == (0.00945, 0.00952, 0.7)
    assert (r(d0["sd_tau2"], 1), r(d1["sd_tau2"], 1)) == (5.5, 2.7)
    P = d0["P"]
    assert r(np.percentile(P[:, 2], 5)) >= 53 and r(np.percentile(P[:, 2], 95)) <= 70.2


def test_penalty_table_and_stability():
    """WRITING section 9: the penalty's effect is monotone in its weight (the ablation is weight 0), and the jump
    statistics are stable on a fresh set of noisy days."""
    rows = {w: daily(w) for w in (0.001, 0.1)}
    assert (r(rows[0.001]["median_jump"]), r(1000 * rows[0.001]["mean_rmse"], 3)) == (3.93, 9.454)
    assert (r(rows[0.1]["median_jump"]), r(1000 * rows[0.1]["mean_rmse"], 3)) == (0.42, 9.643)


def test_exercises():
    assert (round(1000 * math.log(1e6)), round(math.sqrt(1000) * math.log(1e6))) == (13816, 437)
