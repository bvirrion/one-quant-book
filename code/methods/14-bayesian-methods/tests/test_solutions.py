"""Numbers gate: every numerical answer printed in Book 4, Chapter 14 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_bayes import (
    SE,
    average_mse,
    best_manager_average,
    eb_normal_means,
    hit_rate_example,
    mcmc,
    mse_table,
    platform,
    problem,
)

P = problem()
A = average_mse()
M = mcmc()


def r(x, d=2):
    return round(float(x), d)


def phi(z):
    return 0.5 * math.erfc(-z / math.sqrt(2))


def test_hook_and_example():
    assert (r(P["best"]), r(P["m"]), r(P["sd_x"]), r(P["tau"]), r(P["shrink"], 3)) == (2.41, 0.51, 0.71, 0.41, 0.665)
    assert r(math.sqrt(0.71**2 - 1 / 3)) == 0.41 and r(1 / math.sqrt(3), 3) == 0.577
    assert r(P["tau"] ** 2, 3) == 0.168 and r(1 - P["shrink"], 3) == 0.335
    assert (r(P["best_eb"]), r(P["best_eb_sd"]), r(P["best_js"])) == (1.14, 0.33, 1.20)
    assert [r(v) for v in P["top3_raw"]] == [2.41, 1.82, 1.45] and [r(v) for v in P["top3_eb"]] == [1.14, 0.95, 0.83]
    assert [r(v) for v in P["top3_theta"]] == [1.07, 0.96, 1.68] and [r(v) for v in P["top3_next"]] == [1.69, 0.57, 0.99]
    assert P["rank_by_eb_equals_raw"] and P["n_neg"] == 12 and r(P["js_factor"]) == 0.36
    h = hit_rate_example()
    assert (h["a"], h["b"], r(h["mean"], 3), r(h["ci"][0], 3), r(h["ci"][1], 3), r(h["p_above"], 3)) == (160, 140, 0.533, 0.477, 0.589, 0.876)


def test_mse_and_selection():
    t = P["mse"]
    assert (r(t["truth"]["raw"], 3), r(t["truth"]["eb"], 3)) == (0.335, 0.149) and round(100 * (1 - t["truth"]["eb"] / t["truth"]["raw"])) == 55
    assert (r(A["truth"]["raw"], 3), r(A["truth"]["eb"], 3), r(A["truth"]["js"], 3), r(A["truth"]["oracle"], 3)) == (0.336, 0.121, 0.121, 0.109)
    assert (r(A["next"]["raw"], 3), r(A["next"]["eb"], 3), r(A["next"]["js"], 3), r(A["next"]["oracle"], 3)) == (0.672, 0.457, 0.457, 0.445)
    assert round(100 * (1 - A["next"]["eb"] / A["next"]["raw"])) == 32 and round(100 * (1 - A["truth"]["eb"] / A["truth"]["raw"])) == 64
    assert round(100 * (1 - t["next"]["eb"] / t["next"]["raw"])) == 31
    b = best_manager_average()
    assert (r(b["best"]), r(b["theta"]), r(b["eb"]), r(b["next"]), r(b["best"] - b["theta"])) == (2.09, 1.01, 1.01, 1.02, 1.08)
    sd = math.sqrt(P["best_eb_sd"] ** 2 + SE**2)
    assert r(sd) == 0.67 and r(100 * phi(-P["best_eb"] / sd), 1) == 4.3 and r(100 * (1 - phi((P["best"] - P["best_eb"]) / sd)), 1) == 2.9


def test_mcmc():
    assert (r(M["best_post_mean"]), r(M["best_ci"][0]), r(M["best_ci"][1])) == (1.12, 0.41, 2.01)
    assert (r(M["tau_mean"]), r(M["tau_ci"][0]), r(M["tau_ci"][1]), r(M["tau_mean_mh"])) == (0.40, 0.13, 0.66, 0.39)
    assert (round(100 * M["acc_mh"]), r(M["rhat_mh_tau"], 3), round(M["ess_gibbs_tau"]), round(M["ess_mh_tau"])) == (50, 1.001, 506, 767)
    assert M["n_kept"] == 18_000 and round(100 * M["p_tau_small"]) == 7
    assert (r(P["best_eb"] - 1.96 * P["best_eb_sd"]), r(P["best_eb"] + 1.96 * P["best_eb_sd"])) == (0.49, 1.80)


def test_stability_and_ablation():
    """WRITING section 9: the Gibbs result is stable when the chain is four times longer, the MSE gain is stable across a
    fresh set of platforms, and the credited mechanism (noise large relative to the dispersion of skill) is ablated: with
    ten-year records the shrinkage and its gain shrink, with no dispersion of skill the shrunk estimate is the mean."""
    long = mcmc(n_iter=80_000, burn=8_000)
    assert abs(long["best_post_mean"] - M["best_post_mean"]) < 0.03 and abs(long["tau_mean"] - M["tau_mean"]) < 0.02
    a2 = average_mse(seed0=90_000)
    assert abs(a2["next"]["eb"] / a2["next"]["raw"] - A["next"]["eb"] / A["next"]["raw"]) < 0.02
    gain10 = []
    for s in range(500):
        p = platform(20_000 + s, se=1 / math.sqrt(10))
        e = eb_normal_means(p["x1"], 1 / math.sqrt(10))["post_mean"]
        gain10.append((np.mean((p["x1"] - p["theta"]) ** 2), np.mean((e - p["theta"]) ** 2)))
    g = np.array(gain10).mean(0)
    assert 1 - g[1] / g[0] < 0.6 * (1 - A["truth"]["eb"] / A["truth"]["raw"])      # 36% against 64%
    q = platform(7, tau=0.0)
    assert np.allclose(eb_normal_means(q["x1"], SE)["post_mean"], q["x1"].mean()) or eb_normal_means(q["x1"], SE)["tau2"] < 0.05
    assert mse_table(platform(1))["truth"]["eb"] < mse_table(platform(1))["truth"]["raw"]


def test_exercises():
    assert (r(80 / 150, 3), r(31 / 52, 3)) == (0.533, 0.596)
    assert (r(0.2 / 0.36, 3), r(0.5 + 0.16 / 0.36), r(0.2 * 0.16 / 0.36, 3), r(math.sqrt(0.2 * 0.16 / 0.36))) == (0.556, 0.94, 0.089, 0.30)
    assert round(10_000 * 0.2 / 1.8) == 1111
    assert r(1 / P["tau"] ** 2, 1) == 6.0 and r(1 / 0.16) == 6.25
